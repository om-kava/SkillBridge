from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status

from .models import (
    CareerProfile, Resume, JobDescription, Skill, Analysis, 
    AnalysisSkill, Roadmap, RoadmapItem, InterviewQuestion
)
from .scoring import calculate_readiness_score
from . import ai_service


class ModelTests(TestCase):
    """Unit tests for SkillBridge models and methods."""

    def setUp(self):
        self.user = User.objects.create_user(username='qa_tester', password='password123')
        self.profile = CareerProfile.objects.create(
            user=self.user,
            full_name='QA Tester',
            target_role='Full Stack Python Developer',
            weekly_learning_hours=20
        )
        self.jd = JobDescription.objects.create(
            user=self.user,
            title='Python Engineer',
            company='Acme Corp',
            source_text='Looking for Python, Django, REST APIs, Docker experience.'
        )
        self.analysis = Analysis.objects.create(
            user=self.user,
            job_description=self.jd,
            readiness_score=82,
            summary='Solid candidate with minor gaps in Docker.'
        )

    def test_career_profile_str(self):
        self.assertIn('qa_tester', str(self.profile))
        self.assertIn('Full Stack Python Developer', str(self.profile))

    def test_analysis_score_label(self):
        self.analysis.readiness_score = 95
        self.assertEqual(self.analysis.get_score_label(), "Highly Ready")

        self.analysis.readiness_score = 80
        self.assertEqual(self.analysis.get_score_label(), "Strong Candidate")

        self.analysis.readiness_score = 65
        self.assertEqual(self.analysis.get_score_label(), "Developing")

        self.analysis.readiness_score = 45
        self.assertEqual(self.analysis.get_score_label(), "Significant Gaps")

        self.analysis.readiness_score = 25
        self.assertEqual(self.analysis.get_score_label(), "Early Stage")

    def test_roadmap_completion_percentage(self):
        roadmap = Roadmap.objects.create(
            analysis=self.analysis,
            title='Test Roadmap',
            total_estimated_hours=40
        )
        # 0 items
        self.assertEqual(roadmap.get_completion_percentage(), 0)

        # Add 2 items, 1 completed
        item1 = RoadmapItem.objects.create(
            roadmap=roadmap,
            title='Phase 1: Django ORM',
            status='completed',
            order=1
        )
        item2 = RoadmapItem.objects.create(
            roadmap=roadmap,
            title='Phase 2: Docker Containers',
            status='not_started',
            order=2
        )

        self.assertEqual(roadmap.get_completion_percentage(), 50)
        self.assertEqual(item1.phase_number, 1)
        self.assertEqual(item2.phase_number, 2)

        # Complete second item
        item2.status = 'completed'
        item2.save()
        self.assertEqual(roadmap.get_completion_percentage(), 100)

    def test_interview_question_str(self):
        iq = InterviewQuestion.objects.create(
            analysis=self.analysis,
            category='technical',
            difficulty='intermediate',
            question='Explain Django ORM select_related vs prefetch_related.'
        )
        self.assertIn('Intermediate', str(iq))
        self.assertIn('Django ORM', str(iq))


class ScoringAlgorithmTests(TestCase):
    """Unit tests for the PRD readiness score calculation."""

    def test_perfect_score(self):
        matched = [{'name': 'Python'}, {'name': 'Django'}, {'name': 'PostgreSQL'}]
        partial = []
        missing = []
        optional = [{'name': 'AWS'}]
        score = calculate_readiness_score(matched, partial, missing, optional, has_project_evidence=True, experience_years=3)
        self.assertGreaterEqual(score, 85)
        self.assertLessEqual(score, 100)

    def test_zero_skills_fresher(self):
        score = calculate_readiness_score([], [], [{'name': 'Python'}, {'name': 'Django'}], [], has_project_evidence=False, experience_years=0)
        self.assertGreaterEqual(score, 0)
        self.assertLess(score, 40)

    def test_empty_lists_no_crash(self):
        score = calculate_readiness_score([], [], [], [])
        self.assertIsInstance(score, int)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)


class ViewNavigationTests(TestCase):
    """Tests ensuring all web views load successfully with valid HTTP status."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='alex_qa', password='securepass123')
        self.profile = CareerProfile.objects.create(user=self.user, target_role='Backend Developer')
        self.jd = JobDescription.objects.create(
            user=self.user,
            title='Backend Engineer',
            company='InnovateX',
            source_text='Python, Django, PostgreSQL'
        )
        self.analysis = Analysis.objects.create(
            user=self.user,
            job_description=self.jd,
            readiness_score=78,
            summary='Strong foundation.'
        )
        self.roadmap = Roadmap.objects.create(
            analysis=self.analysis,
            title='Backend Path'
        )
        self.item = RoadmapItem.objects.create(
            roadmap=self.roadmap,
            title='Advanced Python Patterns',
            order=1,
            status='in_progress'
        )

    def test_public_pages_return_200(self):
        public_urls = [
            reverse('sb_landing'),
            reverse('sb_about'),
            reverse('sb_login'),
            reverse('sb_register'),
            reverse('chatbot'),
            reverse('login'),
            reverse('register'),
        ]
        for url in public_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f"Failed for url: {url}")

    def test_unauthenticated_chatbot_navigation_links(self):
        response = self.client.get(reverse('chatbot'))
        self.assertEqual(response.status_code, 200)
        # Verify SkillBridge button points to landing page for unauthenticated visitors
        self.assertContains(response, 'href="/"')

    def test_login_and_register_pages_have_navbar(self):
        for url in [reverse('login'), reverse('register')]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'auth-navbar')
            self.assertContains(response, 'SkillBridge')

    def test_authenticated_pages_redirect_when_logged_out(self):
        protected_urls = [
            reverse('sb_dashboard'),
            reverse('sb_profile'),
            reverse('sb_resume'),
            reverse('sb_analyze'),
            reverse('sb_roadmap'),
            reverse('sb_interview_prep'),
            reverse('sb_history'),
        ]
        for url in protected_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, f"Should redirect for unauthenticated url: {url}")

    def test_authenticated_pages_return_200_when_logged_in(self):
        self.client.login(username='alex_qa', password='securepass123')
        authenticated_urls = [
            reverse('sb_dashboard'),
            reverse('sb_profile'),
            reverse('sb_resume'),
            reverse('sb_analyze'),
            reverse('sb_roadmap'),
            reverse('sb_roadmap_detail', args=[self.analysis.id]),
            reverse('sb_interview_prep'),
            reverse('sb_interview_prep_detail', args=[self.analysis.id]),
            reverse('sb_history'),
            reverse('sb_analysis_detail', args=[self.analysis.id]),
        ]
        for url in authenticated_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f"Failed for logged-in user at url: {url}")


class DRFApiTests(TestCase):
    """Tests for DRF REST API endpoints."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='api_tester', password='securepass123')
        self.profile = CareerProfile.objects.create(user=self.user, target_role='DevOps Engineer')

    def test_api_endpoints_require_authentication(self):
        endpoints = [
            reverse('api_profile'),
            reverse('api_resumes'),
            reverse('api_jobs'),
            reverse('api_analyses'),
            reverse('api_dashboard'),
        ]
        for ep in endpoints:
            response = self.client.get(ep)
            self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_api_profile_authenticated(self):
        self.client.login(username='api_tester', password='securepass123')
        response = self.client.get(reverse('api_profile'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['target_role'], 'DevOps Engineer')

    def test_api_dashboard_authenticated(self):
        self.client.login(username='api_tester', password='securepass123')
        response = self.client.get(reverse('api_dashboard'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['username'], 'api_tester')
        self.assertEqual(data['target_role'], 'DevOps Engineer')
        self.assertEqual(data['total_analyses'], 0)


class AIFallbackServiceTests(TestCase):
    """Tests guaranteeing that AI services never crash and return valid structured mock data when no API key is set."""

    def test_analyze_career_gap_fallback(self):
        result = ai_service.analyze_career_gap("Python, SQL experience", "Need Python, Docker, Kubernetes")
        self.assertIn('matched_skills', result)
        self.assertIn('missing_skills', result)
        self.assertIn('roadmap', result)
        self.assertIn('interview_questions', result)

    def test_ai_interview_coach_fallback(self):
        result = ai_service.ai_interview_coach(
            "What is Django middleware?",
            "It is a hook that processes request and response.",
            "request/response processing, order of execution"
        )
        self.assertIn('score', result)
        self.assertTrue('missing_points' in result or 'missing_concepts' in result)
        self.assertTrue('improved_answer' in result or 'model_answer' in result)

    def test_ai_roadmap_guide_fallback(self):
        result = ai_service.ai_roadmap_guide("Docker Containerization", "Student", "Backend Developer")
        self.assertIn('key_concepts', result)
        self.assertIn('practice_exercise', result)

    def test_ai_recommend_skills_fallback(self):
        result = ai_service.ai_recommend_skills("Machine Learning Engineer")
        self.assertIn('recommended_skills', result)
        self.assertIsInstance(result['recommended_skills'], list)

    def test_ai_generate_company_pack_fallback(self):
        result = ai_service.ai_generate_company_interview_pack("Google", "Site Reliability Engineer")
        self.assertIn('questions', result)
        self.assertIsInstance(result['questions'], list)
        self.assertGreater(len(result['questions']), 0)

    def test_ai_generate_gap_targeted_questions_fallback(self):
        questions = ai_service.ai_generate_gap_targeted_questions(["Redis", "Celery"], "Backend Developer")
        self.assertIsInstance(questions, list)
        self.assertGreater(len(questions), 0)

    def test_ai_resume_doctor_fallback(self):
        result = ai_service.ai_resume_doctor("Curriculum Vitae: Python Developer with MCA", "Python Backend Developer")
        self.assertIn('ats_score', result)
        self.assertIn('critical_fixes', result)
        self.assertIn('missing_keywords', result)
