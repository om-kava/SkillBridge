from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    CareerProfile, Resume, JobDescription, Skill, Analysis, 
    AnalysisSkill, Roadmap, RoadmapItem, InterviewQuestion, ProgressRecord
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class CareerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = CareerProfile
        fields = '__all__'

class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ['id', 'user', 'file', 'extracted_text', 'parsed_data', 'uploaded_at']
        read_only_fields = ['user', 'uploaded_at']

class JobDescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobDescription
        fields = '__all__'
        read_only_fields = ['user', 'created_at']

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'

class AnalysisSkillSerializer(serializers.ModelSerializer):
    skill = SkillSerializer(read_only=True)
    class Meta:
        model = AnalysisSkill
        fields = '__all__'

class RoadmapItemSerializer(serializers.ModelSerializer):
    skill = SkillSerializer(read_only=True)
    class Meta:
        model = RoadmapItem
        fields = '__all__'

class RoadmapSerializer(serializers.ModelSerializer):
    items = RoadmapItemSerializer(many=True, read_only=True)
    class Meta:
        model = Roadmap
        fields = '__all__'

class InterviewQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewQuestion
        fields = '__all__'

class AnalysisSerializer(serializers.ModelSerializer):
    job_description = JobDescriptionSerializer(read_only=True)
    analysis_skills = AnalysisSkillSerializer(many=True, read_only=True)
    roadmap = RoadmapSerializer(read_only=True)
    score_label = serializers.CharField(source='get_score_label', read_only=True)

    class Meta:
        model = Analysis
        fields = '__all__'
