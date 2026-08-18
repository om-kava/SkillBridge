from django.urls import path
from . import views, api_views

urlpatterns = [
    # Public Pages
    path('', views.landing_view, name='sb_landing'),
    path('about/', views.about_view, name='sb_about'),
    path('login/', views.login_view, name='sb_login'),
    path('register/', views.register_view, name='sb_register'),
    path('logout/', views.logout_view, name='sb_logout'),

    # Authenticated Web Pages
    path('dashboard/', views.dashboard_view, name='sb_dashboard'),
    path('profile/', views.profile_view, name='sb_profile'),
    path('resume/', views.resume_view, name='sb_resume'),
    path('analyze/', views.analyze_view, name='sb_analyze'),
    path('history/', views.history_view, name='sb_history'),

    # Static AJAX & AI Feature Endpoints (BEFORE Parameterized Routes)
    path('profile/recommend-skills/', views.ajax_profile_recommend_skills, name='sb_ajax_profile_recommend_skills'),
    path('resume/doctor/', views.ajax_resume_doctor, name='sb_ajax_resume_doctor'),
    path('interview-prep/coach/', views.ajax_interview_coach, name='sb_ajax_interview_coach'),
    path('interview-prep/generate-pack/', views.ajax_generate_interview_pack, name='sb_ajax_generate_interview_pack'),
    path('interview-prep/company-pack/', views.ajax_generate_company_pack, name='sb_ajax_generate_company_pack'),
    path('interview-prep/gap-pack/', views.ajax_generate_gap_pack, name='sb_ajax_generate_gap_pack'),
    path('roadmap/guide/', views.ajax_roadmap_guide, name='sb_ajax_roadmap_guide'),
    path('roadmap/resources/', views.ajax_roadmap_resources, name='sb_ajax_roadmap_resources'),
    path('roadmap/expand/', views.ajax_expand_roadmap, name='sb_ajax_expand_roadmap'),

    # Parameterized Detail Web Views & PDF Export
    path('analysis/<int:analysis_id>/', views.analysis_detail_view, name='sb_analysis_detail'),
    path('analysis/<int:analysis_id>/pdf/', views.export_pdf_view, name='sb_export_pdf'),
    path('roadmap/', views.roadmap_view, name='sb_roadmap'),
    path('roadmap/<int:analysis_id>/', views.roadmap_view, name='sb_roadmap_detail'),
    path('interview-prep/', views.interview_prep_view, name='sb_interview_prep'),
    path('interview-prep/<int:analysis_id>/', views.interview_prep_view, name='sb_interview_prep_detail'),

    # DRF REST API Endpoints
    path('api/profile/', api_views.api_profile, name='api_profile'),
    path('api/resumes/', api_views.api_resumes, name='api_resumes'),
    path('api/jobs/', api_views.api_jobs, name='api_jobs'),
    path('api/analyses/', api_views.api_analyses, name='api_analyses'),
    path('api/analyses/<int:pk>/', api_views.api_analyses, name='api_analysis_detail'),
    path('api/dashboard/', api_views.api_dashboard, name='api_dashboard'),
]
