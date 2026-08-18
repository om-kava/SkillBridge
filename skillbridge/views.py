from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import auth, messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
import json

from .models import (
    CareerProfile, Resume, JobDescription, Skill, Analysis, 
    AnalysisSkill, Roadmap, RoadmapItem, InterviewQuestion, ProgressRecord
)
from .doc_parser import extract_text_from_file
from .scoring import calculate_readiness_score
from .ai_service import analyze_career_gap


# Public Views
def landing_view(request):
    return render(request, 'skillbridge/landing.html')


def about_view(request):
    return render(request, 'skillbridge/about.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('sb_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not username or not password:
            messages.error(request, 'Please provide both username and password.')
        else:
            user = auth.authenticate(request, username=username, password=password)
            if user is not None:
                auth.login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('sb_dashboard')
            else:
                messages.error(request, 'Invalid username or password. Please try again.')
    return render(request, 'skillbridge/login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('sb_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '').strip()
        password2 = request.POST.get('password2', '').strip()

        if not username:
            messages.error(request, 'Username is required.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username is already taken. Please choose a different username.')
        elif len(password1) < 4:
            messages.error(request, 'Password must be at least 4 characters long.')
        elif password1 != password2:
            messages.error(request, 'Passwords do not match. Please verify your passwords.')
        else:
            try:
                user = User.objects.create_user(username=username, email=email, password=password1)
                user.save()
                CareerProfile.objects.create(user=user, full_name=username)
                auth.login(request, user)
                messages.success(request, f'Account created successfully! Welcome to SkillBridge, {username}!')
                return redirect('sb_dashboard')
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
    return render(request, 'skillbridge/register.html')


def logout_view(request):
    auth.logout(request)
    return redirect('sb_landing')


# Authenticated Views
@login_required
def dashboard_view(request):
    profile, created = CareerProfile.objects.get_or_create(user=request.user)
    analyses = Analysis.objects.filter(user=request.user).order_by('-created_at')
    
    latest_analysis = analyses.first()
    recent_analyses = analyses[:5]
    
    # Aggregated Stats
    total_analyses = analyses.count()
    highest_readiness = max([a.readiness_score for a in analyses], default=0)
    current_readiness = latest_analysis.readiness_score if latest_analysis else 0
    
    # Roadmap Progress Stats
    completed_items_count = 0
    total_items_count = 0
    if latest_analysis and hasattr(latest_analysis, 'roadmap'):
        total_items_count = latest_analysis.roadmap.items.count()
        completed_items_count = latest_analysis.roadmap.items.filter(status='completed').count()

    roadmap_progress = int(round((completed_items_count / total_items_count) * 100)) if total_items_count > 0 else 0
    remaining_items_count = max(0, total_items_count - completed_items_count) if total_items_count > 0 else 1

    matched_skills_count = 0
    missing_skills_count = 0
    interview_questions_count = 0
    if latest_analysis:
        matched_skills_count = latest_analysis.analysis_skills.filter(status='matched').count()
        missing_skills_count = latest_analysis.analysis_skills.filter(status='missing').count()
        interview_questions_count = latest_analysis.interview_questions.count()

    # Chart JSON Data
    analyses_list = list(analyses)
    chronological = list(reversed(analyses_list))
    chart_labels = [a.created_at.strftime('%b %d') for a in chronological] if chronological else ['Initial']
    chart_data = [a.readiness_score for a in chronological] if chronological else [0]

    context = {
        'profile': profile,
        'latest_analysis': latest_analysis,
        'recent_analyses': recent_analyses,
        'total_analyses': total_analyses,
        'highest_readiness': highest_readiness,
        'current_readiness': current_readiness,
        'completed_items_count': completed_items_count,
        'total_items_count': total_items_count,
        'remaining_items_count': remaining_items_count,
        'roadmap_progress': roadmap_progress,
        'matched_skills_count': matched_skills_count,
        'missing_skills_count': missing_skills_count,
        'interview_questions_count': interview_questions_count,
        'chart_labels_json': json.dumps(chart_labels),
        'chart_data_json': json.dumps(chart_data),
    }
    return render(request, 'skillbridge/dashboard.html', context)


@login_required
def profile_view(request):
    profile, created = CareerProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        profile.full_name = request.POST.get('full_name', profile.full_name)
        profile.target_role = request.POST.get('target_role', profile.target_role)
        profile.experience_level = request.POST.get('experience_level', profile.experience_level)
        profile.education = request.POST.get('education', profile.education)
        profile.current_skills = request.POST.get('current_skills', profile.current_skills)
        profile.weekly_learning_hours = int(request.POST.get('weekly_learning_hours', profile.weekly_learning_hours))
        profile.career_goal = request.POST.get('career_goal', profile.career_goal)
        profile.save()
        messages.success(request, 'Career profile updated successfully!')
        return redirect('sb_profile')

    analyses = Analysis.objects.filter(user=request.user).order_by('-created_at')
    latest_analysis = analyses.first()

    context = {
        'profile': profile,
        'total_analyses': analyses.count(),
        'latest_analysis': latest_analysis,
        'readiness_score': latest_analysis.readiness_score if latest_analysis else 0,
    }
    return render(request, 'skillbridge/profile.html', context)


@login_required
def resume_view(request):
    resumes = Resume.objects.filter(user=request.user).order_by('-uploaded_at')
    
    if request.method == 'POST' and request.FILES.get('resume_file'):
        file_obj = request.FILES['resume_file']
        
        # Server side extension validation
        ext = file_obj.name.split('.')[-1].lower()
        if ext not in ['pdf', 'docx', 'doc', 'txt']:
            messages.error(request, 'Invalid file format. Please upload a PDF, DOCX, or TXT resume.')
            return redirect('sb_resume')

        resume = Resume.objects.create(user=request.user, file=file_obj)
        
        # Extract text server-side
        file_path = resume.file.path
        extracted_text = extract_text_from_file(file_path)
        resume.extracted_text = extracted_text
        resume.save()
        
        messages.success(request, 'Resume uploaded and parsed successfully!')
        return redirect('sb_resume')

    return render(request, 'skillbridge/resume.html', {'resumes': resumes})


@login_required
def analyze_view(request):
    profile, _ = CareerProfile.objects.get_or_create(user=request.user)
    resumes = Resume.objects.filter(user=request.user).order_by('-uploaded_at')

    if request.method == 'POST':
        target_role = request.POST.get('target_role', profile.target_role)
        weekly_hours = int(request.POST.get('weekly_learning_hours', profile.weekly_learning_hours))
        jd_text = request.POST.get('job_description', '').strip()
        
        # Resume text source
        resume_id = request.POST.get('resume_id')
        resume_obj = None
        resume_text = ""

        if request.FILES.get('resume_file'):
            file_obj = request.FILES['resume_file']
            resume_obj = Resume.objects.create(user=request.user, file=file_obj)
            resume_text = extract_text_from_file(resume_obj.file.path)
            resume_obj.extracted_text = resume_text
            resume_obj.save()
        elif resume_id:
            resume_obj = Resume.objects.filter(id=resume_id, user=request.user).first()
            if resume_obj:
                resume_text = resume_obj.extracted_text or extract_text_from_file(resume_obj.file.path)
        
        if not resume_text:
            resume_text = f"Target Role: {target_role}. Skills: {profile.current_skills}. Education: {profile.education}"

        if not jd_text:
            messages.error(request, 'Please provide a Job Description (paste text or upload file).')
            return redirect('sb_analyze')

        # 1. Create JobDescription object
        jd_obj = JobDescription.objects.create(
            user=request.user,
            title=target_role,
            source_text=jd_text,
            extracted_text=jd_text
        )

        # 2. Run AI Career Gap Analysis
        ai_data = analyze_career_gap(resume_text, jd_text, target_role, weekly_hours)

        matched_skills = ai_data.get('matched_skills', [])
        partial_skills = ai_data.get('partial_skills', [])
        missing_skills = ai_data.get('missing_skills', [])
        optional_skills = []

        # 3. Calculate Backend Score (PRD Section 51)
        score = calculate_readiness_score(
            matched_skills=matched_skills,
            partial_skills=partial_skills,
            missing_skills=missing_skills,
            optional_skills=optional_skills,
            has_project_evidence=True,
            experience_years=0 if profile.experience_level == 'Fresher' else 1
        )

        # 4. Create Analysis object
        analysis = Analysis.objects.create(
            user=request.user,
            resume=resume_obj,
            job_description=jd_obj,
            readiness_score=score,
            summary=ai_data.get('summary', 'Career gap analysis completed successfully.')
        )

        # 5. Save AnalysisSkills
        for item in matched_skills:
            skill_name = item.get('name', 'Unknown')
            skill_obj, _ = Skill.objects.get_or_create(
                name=skill_name,
                defaults={'normalized_name': skill_name.lower(), 'category': item.get('category', 'Concepts')}
            )
            AnalysisSkill.objects.create(
                analysis=analysis,
                skill=skill_obj,
                status='matched',
                importance='high',
                priority=5,
                evidence=item.get('evidence', 'Found in resume')
            )

        for item in partial_skills:
            skill_name = item.get('name', 'Unknown')
            skill_obj, _ = Skill.objects.get_or_create(
                name=skill_name,
                defaults={'normalized_name': skill_name.lower(), 'category': item.get('category', 'Concepts')}
            )
            AnalysisSkill.objects.create(
                analysis=analysis,
                skill=skill_obj,
                status='partial',
                importance='high',
                priority=3,
                evidence=item.get('reason', 'Partially demonstrated')
            )

        for item in missing_skills:
            skill_name = item.get('name', 'Unknown')
            skill_obj, _ = Skill.objects.get_or_create(
                name=skill_name,
                defaults={'normalized_name': skill_name.lower(), 'category': item.get('category', 'Concepts')}
            )
            AnalysisSkill.objects.create(
                analysis=analysis,
                skill=skill_obj,
                status='missing',
                importance=item.get('importance', 'high'),
                priority=item.get('priority', 1),
                recommendation=item.get('recommendation', 'Learn fundamentals')
            )

        # 6. Save Roadmap & RoadmapItems
        roadmap = Roadmap.objects.create(
            analysis=analysis,
            title=f"Learning Roadmap for {target_role}",
            description=f"Actionable step-by-step roadmap tailored for {weekly_hours} weekly learning hours.",
            total_estimated_hours=sum([item.get('estimated_hours', 8) for item in ai_data.get('roadmap', [])]) or 24
        )

        for idx, r_item in enumerate(ai_data.get('roadmap', []), start=1):
            skill_name = r_item.get('skill', '')
            skill_obj = Skill.objects.filter(name=skill_name).first() if skill_name else None
            
            RoadmapItem.objects.create(
                roadmap=roadmap,
                skill=skill_obj,
                title=r_item.get('title', f'Week {idx} Learning Focus'),
                description=r_item.get('description', ''),
                estimated_hours=r_item.get('estimated_hours', 8),
                priority=r_item.get('priority', 'High'),
                prerequisites=r_item.get('prerequisites', ''),
                learning_objectives=r_item.get('learning_objectives', ''),
                practice_task=r_item.get('practice_task', ''),
                status='not_started',
                order=idx
            )

        # 7. Save Interview Questions
        for q_item in ai_data.get('interview_questions', []):
            InterviewQuestion.objects.create(
                analysis=analysis,
                category=q_item.get('category', 'technical'),
                difficulty=q_item.get('difficulty', 'beginner'),
                question=q_item.get('question', ''),
                expected_topics=q_item.get('expected_topics', '')
            )

        return redirect('sb_analysis_detail', analysis_id=analysis.id)

    return render(request, 'skillbridge/analyze.html', {'profile': profile, 'resumes': resumes})


@login_required
def analysis_detail_view(request, analysis_id):
    analysis = get_object_or_404(Analysis, id=analysis_id, user=request.user)
    analysis_skills = analysis.analysis_skills.all().select_related('skill')
    
    matched_skills = [s for s in analysis_skills if s.status == 'matched']
    partial_skills = [s for s in analysis_skills if s.status == 'partial']
    missing_skills = [s for s in analysis_skills if s.status == 'missing']
    
    roadmap = getattr(analysis, 'roadmap', None)
    interview_questions = analysis.interview_questions.all()

    context = {
        'analysis': analysis,
        'matched_skills': matched_skills,
        'partial_skills': partial_skills,
        'missing_skills': missing_skills,
        'roadmap': roadmap,
        'interview_questions': interview_questions,
    }
    return render(request, 'skillbridge/analysis_detail.html', context)


@login_required
def roadmap_view(request, analysis_id=None):
    if analysis_id:
        analysis = get_object_or_404(Analysis, id=analysis_id, user=request.user)
        roadmap = getattr(analysis, 'roadmap', None)
    else:
        latest_analysis = Analysis.objects.filter(user=request.user).order_by('-created_at').first()
        roadmap = getattr(latest_analysis, 'roadmap', None) if latest_analysis else None

    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        if item_id:
            item = get_object_or_404(RoadmapItem, id=item_id, roadmap__analysis__user=request.user)
            # Cycle status: not_started -> in_progress -> completed -> not_started
            status_map = {
                'not_started': 'in_progress',
                'in_progress': 'completed',
                'completed': 'not_started'
            }
            item.status = status_map.get(item.status, 'in_progress')
            item.save()
            ProgressRecord.objects.create(user=request.user, roadmap_item=item, status=item.status)

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'item_id': item.id, 'new_status': item.status})

            messages.success(request, f'Updated status for "{item.title}"')
            if roadmap and roadmap.analysis:
                return redirect('sb_roadmap_detail', analysis_id=roadmap.analysis.id)
            return redirect('sb_roadmap')

    items = roadmap.items.all().order_by('order') if roadmap else []
    total_count = items.count() if items else 0
    completed_count = items.filter(status='completed').count() if items else 0
    remaining_hours = sum([i.estimated_hours for i in items if i.status != 'completed']) if items else 0
    all_analyses = Analysis.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'roadmap': roadmap,
        'items': items,
        'total_count': total_count,
        'completed_count': completed_count,
        'remaining_hours': remaining_hours,
        'all_analyses': all_analyses,
    }
    return render(request, 'skillbridge/roadmap.html', context)


@login_required
def interview_prep_view(request, analysis_id=None):
    profile, _ = CareerProfile.objects.get_or_create(user=request.user)
    if analysis_id:
        analysis = get_object_or_404(Analysis, id=analysis_id, user=request.user)
    else:
        analysis = Analysis.objects.filter(user=request.user).order_by('-created_at').first()

    questions = analysis.interview_questions.all() if analysis else []

    return render(request, 'skillbridge/interview_prep.html', {
        'profile': profile,
        'analysis': analysis,
        'questions': questions
    })


@login_required
def history_view(request):
    analyses = Analysis.objects.filter(user=request.user).order_by('-created_at')
    
    # Comparison feature (Compare 2 latest or selected)
    comparison_data = None
    if analyses.count() >= 2:
        current_a = analyses[0]
        previous_a = analyses[1]
        score_diff = current_a.readiness_score - previous_a.readiness_score
        comparison_data = {
            'current': current_a,
            'previous': previous_a,
            'score_diff': score_diff
        }

    return render(request, 'skillbridge/history.html', {'analyses': analyses, 'comparison_data': comparison_data})


@login_required
def ajax_interview_coach(request):
    if request.method == 'POST':
        question = request.POST.get('question', '')
        user_answer = request.POST.get('answer', '')
        target_role = request.POST.get('target_role', 'Python Backend Developer')
        
        from .ai_service import ai_interview_coach
        evaluation = ai_interview_coach(question, user_answer, target_role)
        return JsonResponse(evaluation)
    return JsonResponse({'error': 'POST method required'}, status=400)


@login_required
def ajax_roadmap_guide(request):
    if request.method == 'POST':
        skill_name = request.POST.get('skill', '')
        title = request.POST.get('title', '')
        description = request.POST.get('description', '')
        target_role = request.POST.get('target_role', 'Python Backend Developer')
        
        from .ai_service import ai_roadmap_guide
        guide = ai_roadmap_guide(skill_name, title, description, target_role)
        return JsonResponse(guide)
    return JsonResponse({'error': 'POST method required'}, status=400)


@login_required
def export_pdf_view(request, analysis_id):
    analysis = get_object_or_404(Analysis, id=analysis_id, user=request.user)
    from .pdf_service import generate_analysis_pdf_html
    html_content = generate_analysis_pdf_html(analysis)
    return HttpResponse(html_content, content_type='text/html')


@login_required
def ajax_resume_doctor(request):
    if request.method == 'POST':
        resume_id = request.POST.get('resume_id')
        custom_role = request.POST.get('target_role', '').strip()
        resume = get_object_or_404(Resume, id=resume_id, user=request.user) if resume_id else Resume.objects.filter(user=request.user).order_by('-uploaded_at').first()
        
        resume_text = resume.extracted_text if resume else "Python, Django, REST APIs, HTML, SQL"
        profile, _ = CareerProfile.objects.get_or_create(user=request.user)
        target_role = custom_role or profile.target_role

        from .ai_service import ai_resume_doctor
        feedback = ai_resume_doctor(resume_text, target_role)
        return JsonResponse(feedback)
    return JsonResponse({'error': 'POST method required'}, status=400)


@login_required
def ajax_roadmap_resources(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        if item_id:
            item = get_object_or_404(RoadmapItem, id=item_id, roadmap__analysis__user=request.user)
            if item.learning_objectives:
                try:
                    res_list = json.loads(item.learning_objectives)
                    if isinstance(res_list, list) and len(res_list) > 0:
                        return JsonResponse({'resources': res_list})
                except Exception:
                    pass

        skill_name = request.POST.get('skill', '')
        target_role = request.POST.get('target_role', 'Python Backend Developer')
        
        from .ai_service import ai_find_resources
        resources = ai_find_resources(skill_name, target_role)
        if isinstance(resources, list):
            return JsonResponse({'resources': resources})
        return JsonResponse(resources)
    return JsonResponse({'error': 'POST method required'}, status=400)


@login_required
def ajax_expand_roadmap(request):
    if request.method == 'POST':
        roadmap_id = request.POST.get('roadmap_id')
        roadmap = get_object_or_404(Roadmap, id=roadmap_id, analysis__user=request.user)
        
        current_count = roadmap.items.count()
        target_role = roadmap.analysis.job_description.title if (roadmap.analysis and roadmap.analysis.job_description) else "Python Backend Developer"
        missing_skills = [s.skill.name for s in roadmap.analysis.analysis_skills.filter(status='missing')] if roadmap.analysis else ["Docker", "Celery", "Redis"]
        existing_titles = [item.title for item in roadmap.items.all().order_by('order')]

        from .ai_service import ai_expand_roadmap_items
        new_items = ai_expand_roadmap_items(target_role, current_count, missing_skills, existing_titles)

        for idx, item_data in enumerate(new_items, start=current_count + 1):
            resources_json = json.dumps(item_data.get('resources', []))
            RoadmapItem.objects.create(
                roadmap=roadmap,
                title=item_data.get('title', f'Week {idx}: Advanced Skill Module'),
                description=item_data.get('description', ''),
                estimated_hours=item_data.get('estimated_hours', 10),
                priority=item_data.get('priority', 'High'),
                prerequisites=item_data.get('prerequisites', ''),
                learning_objectives=resources_json,
                practice_task=item_data.get('practice_task', ''),
                status='not_started',
                order=idx
            )

        roadmap.total_estimated_hours += sum([i.get('estimated_hours', 10) for i in new_items])
        roadmap.save()

        return JsonResponse({'status': 'success', 'added_count': len(new_items)})
    return JsonResponse({'error': 'POST method required'}, status=400)


@login_required
def ajax_generate_interview_pack(request):
    if request.method == 'POST':
        analysis_id = request.POST.get('analysis_id')
        analysis = get_object_or_404(Analysis, id=analysis_id, user=request.user) if analysis_id else Analysis.objects.filter(user=request.user).order_by('-created_at').first()
        
        target_role = analysis.job_description.title if analysis else "Python Backend Developer"
        missing_skills = ", ".join([s.skill.name for s in analysis.analysis_skills.filter(status='missing')]) if analysis else "Docker, Testing, REST APIs"

        from .ai_service import ai_generate_full_interview_pack
        questions_data = ai_generate_full_interview_pack(target_role, missing_skills)

        if analysis:
            for q_item in questions_data:
                InterviewQuestion.objects.create(
                    analysis=analysis,
                    category=q_item.get('category', 'technical'),
                    difficulty=q_item.get('difficulty', 'intermediate'),
                    question=q_item.get('question', ''),
                    expected_topics=q_item.get('expected_topics', '')
                )

        return JsonResponse({'status': 'success', 'generated_count': len(questions_data)})
    return JsonResponse({'error': 'POST method required'}, status=400)


@login_required
def ajax_profile_recommend_skills(request):
    if request.method == 'POST':
        target_role = request.POST.get('target_role', 'Python Backend Developer')
        from .ai_service import ai_recommend_skills
        data = ai_recommend_skills(target_role)
        return JsonResponse(data)
    return JsonResponse({'error': 'POST method required'}, status=400)


@login_required
def ajax_generate_company_pack(request):
    if request.method == 'POST':
        company_name = request.POST.get('company', 'TCS').strip()
        custom_role = request.POST.get('target_role', '').strip()
        round_category = request.POST.get('round_category', 'all').strip()
        
        analysis_id = request.POST.get('analysis_id')
        analysis = get_object_or_404(Analysis, id=analysis_id, user=request.user) if analysis_id else Analysis.objects.filter(user=request.user).order_by('-created_at').first()

        profile, _ = CareerProfile.objects.get_or_create(user=request.user)
        target_role = custom_role or (analysis.job_description.title if analysis else profile.target_role)
        jd_text = analysis.job_description.source_text if analysis else ""

        from .ai_service import ai_generate_company_interview_pack
        pack_result = ai_generate_company_interview_pack(company_name, target_role, round_category, jd_text)
        questions_data = pack_result.get('questions', [])
        summary = pack_result.get('company_summary', '')
        focus_areas = pack_result.get('key_focus_areas', [])

        if analysis:
            # Clear previous questions for a fresh company pack
            analysis.interview_questions.all().delete()
            for q_item in questions_data:
                InterviewQuestion.objects.create(
                    analysis=analysis,
                    category=q_item.get('category', 'technical'),
                    difficulty=q_item.get('difficulty', 'intermediate'),
                    question=q_item.get('question', ''),
                    expected_topics=q_item.get('expected_topics', ''),
                    resource_title=q_item.get('resource_title', f'{company_name} Preparation Guide'),
                    resource_url=q_item.get('resource_url', 'https://geeksforgeeks.org/')
                )

        return JsonResponse({
            'status': 'success',
            'company': company_name,
            'target_role': target_role,
            'summary': summary,
            'key_focus_areas': focus_areas,
            'generated_count': len(questions_data)
        })
    return JsonResponse({'error': 'POST method required'}, status=400)


@login_required
def ajax_generate_gap_pack(request):
    if request.method == 'POST':
        analysis_id = request.POST.get('analysis_id')
        analysis = get_object_or_404(Analysis, id=analysis_id, user=request.user) if analysis_id else Analysis.objects.filter(user=request.user).order_by('-created_at').first()

        target_role = analysis.job_description.title if analysis else "Python Backend Developer"
        missing_skills = [s.skill.name for s in analysis.analysis_skills.filter(status='missing')] if analysis else ["Docker", "REST APIs", "Testing"]

        from .ai_service import ai_generate_gap_targeted_questions
        questions_data = ai_generate_gap_targeted_questions(missing_skills, target_role)

        if analysis:
            for q_item in questions_data:
                InterviewQuestion.objects.create(
                    analysis=analysis,
                    category='skill_gap',
                    difficulty=q_item.get('difficulty', 'intermediate'),
                    question=q_item.get('question', ''),
                    expected_topics=q_item.get('expected_topics', '')
                )

        return JsonResponse({'status': 'success', 'generated_count': len(questions_data)})
    return JsonResponse({'error': 'POST method required'}, status=400)
