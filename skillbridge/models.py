from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class CareerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='career_profile')
    full_name = models.CharField(max_length=150, blank=True)
    target_role = models.CharField(max_length=150, default='Python Backend Developer')
    experience_level = models.CharField(max_length=50, default='Fresher') # Fresher, Student, Early-Career
    education = models.CharField(max_length=200, blank=True, default='MCA / B.Tech')
    current_skills = models.TextField(blank=True, default='Python, HTML, CSS, SQL')
    weekly_learning_hours = models.IntegerField(default=15)
    career_goal = models.TextField(blank=True, default='Land a backend developer role in campus placements')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile - {self.target_role}"


class Resume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    file = models.FileField(upload_to='resumes/')
    extracted_text = models.TextField(blank=True)
    parsed_data = models.JSONField(default=dict, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Resume #{self.id} for {self.user.username} ({self.uploaded_at.strftime('%Y-%m-%d')})"


class JobDescription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_descriptions')
    title = models.CharField(max_length=200, default='Python Backend Developer')
    company = models.CharField(max_length=150, blank=True, default='Tech Company')
    source_text = models.TextField()
    extracted_text = models.TextField(blank=True)
    parsed_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} at {self.company}"


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    normalized_name = models.CharField(max_length=100)
    category = models.CharField(max_length=100, default='Concepts') # Programming Languages, Frameworks, Databases, Tools, Cloud, Concepts, Soft Skills

    def __str__(self):
        return f"{self.name} ({self.category})"


class Analysis(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analyses')
    resume = models.ForeignKey(Resume, on_delete=models.SET_NULL, null=True, blank=True)
    job_description = models.ForeignKey(JobDescription, on_delete=models.CASCADE)
    readiness_score = models.IntegerField(default=0) # 0 to 100
    summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_score_label(self):
        score = self.readiness_score
        if score >= 90: return "Highly Ready"
        if score >= 75: return "Strong Candidate"
        if score >= 60: return "Developing"
        if score >= 40: return "Significant Gaps"
        return "Early Stage"

    def __str__(self):
        return f"Analysis #{self.id} - Score: {self.readiness_score}/100"


class AnalysisSkill(models.Model):
    STATUS_CHOICES = (
        ('matched', 'Matched'),
        ('partial', 'Partial'),
        ('missing', 'Missing'),
        ('optional', 'Optional'),
    )
    IMPORTANCE_CHOICES = (
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    )

    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name='analysis_skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='matched')
    importance = models.CharField(max_length=20, choices=IMPORTANCE_CHOICES, default='high')
    priority = models.IntegerField(default=3) # 1 (Critical) to 5 (Low)
    evidence = models.TextField(blank=True)
    recommendation = models.TextField(blank=True)

    def __str__(self):
        return f"{self.skill.name} - {self.status.upper()} (Priority {self.priority})"


class Roadmap(models.Model):
    analysis = models.OneToOneField(Analysis, on_delete=models.CASCADE, related_name='roadmap')
    title = models.CharField(max_length=200, default='Personalized SkillBridge Roadmap')
    description = models.TextField(blank=True)
    total_estimated_hours = models.IntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Roadmap for Analysis #{self.analysis.id}"


class RoadmapItem(models.Model):
    STATUS_CHOICES = (
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    )

    roadmap = models.ForeignKey(Roadmap, on_delete=models.CASCADE, related_name='items')
    skill = models.ForeignKey(Skill, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    estimated_hours = models.IntegerField(default=8)
    priority = models.CharField(max_length=20, default='High') # Critical, High, Medium, Low
    prerequisites = models.CharField(max_length=200, blank=True)
    learning_objectives = models.TextField(blank=True)
    practice_task = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    order = models.IntegerField(default=1)

    def __str__(self):
        return f"Week {self.order}: {self.title} [{self.status}]"


class InterviewQuestion(models.Model):
    CATEGORY_CHOICES = (
        ('technical', 'Technical'),
        ('project', 'Project'),
        ('skill_gap', 'Skill Gap'),
        ('hr', 'HR / Behavioral'),
    )
    DIFFICULTY_CHOICES = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    )

    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name='interview_questions')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='technical')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    question = models.TextField()
    expected_topics = models.TextField(blank=True)
    resource_title = models.CharField(max_length=255, blank=True, default='')
    resource_url = models.URLField(max_length=500, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.difficulty.capitalize()}] {self.question[:50]}"


class ProgressRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress_records')
    roadmap_item = models.ForeignKey(RoadmapItem, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='completed')
    completed_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} completed {self.roadmap_item.title}"
