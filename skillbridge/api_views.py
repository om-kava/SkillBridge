from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    CareerProfile, Resume, JobDescription, Analysis, 
    Roadmap, RoadmapItem, InterviewQuestion
)
from .serializers import (
    CareerProfileSerializer, ResumeSerializer, JobDescriptionSerializer,
    AnalysisSerializer, RoadmapSerializer, InterviewQuestionSerializer
)

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def api_profile(request):
    profile, _ = CareerProfile.objects.get_or_create(user=request.user)
    if request.method == 'GET':
        serializer = CareerProfileSerializer(profile)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = CareerProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_resumes(request):
    if request.method == 'GET':
        resumes = Resume.objects.filter(user=request.user).order_by('-uploaded_at')
        serializer = ResumeSerializer(resumes, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = ResumeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_jobs(request):
    if request.method == 'GET':
        jobs = JobDescription.objects.filter(user=request.user).order_by('-created_at')
        serializer = JobDescriptionSerializer(jobs, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = JobDescriptionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_analyses(request, pk=None):
    if pk:
        analysis = Analysis.objects.filter(id=pk, user=request.user).first()
        if not analysis:
            return Response({'error': 'Analysis not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AnalysisSerializer(analysis)
        return Response(serializer.data)
    
    analyses = Analysis.objects.filter(user=request.user).order_by('-created_at')
    serializer = AnalysisSerializer(analyses, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_dashboard(request):
    profile, _ = CareerProfile.objects.get_or_create(user=request.user)
    analyses = Analysis.objects.filter(user=request.user).order_by('-created_at')
    
    latest_analysis = analyses.first()
    
    data = {
        'username': request.user.username,
        'target_role': profile.target_role,
        'total_analyses': analyses.count(),
        'current_readiness': latest_analysis.readiness_score if latest_analysis else 0,
        'highest_readiness': max([a.readiness_score for a in analyses], default=0),
        'score_label': latest_analysis.get_score_label() if latest_analysis else 'No Data'
    }
    return Response(data)
