# 🧭 SkillBridge — AI Career Placement & Skill-Gap Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![REST Framework](https://img.shields.io/badge/Django_REST_Framework-3.14-red?style=for-the-badge&logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![Render](https://img.shields.io/badge/Render-Live_Deployed-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.style=for-the-badge)](#license)

> **SkillBridge** is an AI-powered career intelligence platform designed for MCA candidates, software engineering students, and backend developers. It bridges the gap between candidate resumes and real-world Job Descriptions (JDs) by delivering **transparent 0–100 readiness scoring**, **personalized multi-week learning roadmaps**, **company-specific interview prep packs**, and **ATS resume optimizations**.

---

## 🚀 Key Features

### 1. 🎯 3-Layer Skill-Gap Analysis & Transparent Scoring
- **Document Parsing**: Extracts text from `.pdf` and `.docx` resumes and job descriptions using deterministic parsers (`pdfplumber`, `PyPDF2`, `python-docx`).
- **3-Layer Skill Matching**:
  - *Layer 1 (Exact)*: Direct keyword matching (`Python` $\to$ `Python`).
  - *Layer 2 (Alias)*: Known technology synonym matching (`DRF` $\to$ `Django REST Framework`).
  - *Layer 3 (Semantic AI)*: Contextual relationship matching via LLM intelligence.
- **Transparent 0–100 Readiness Score**: Backend algorithm based on PRD Section 51 (50% Required Skills, 15% Preferred Skills, 15% Experience Alignment, 10% Project Evidence, 10% Technical Evidence).

### 2. 🗺️ Personalized AI Learning Roadmap
- **Week-by-Week Sequencing**: Automatically organizes missing skill gaps into prioritized learning milestones (Critical, High, Medium, Low).
- **Direct Learning Resources**: Provides links to official documentation, video tutorials, and practical hands-on exercises.
- **Interactive Expansion & Progress Tracking**: Expand roadmaps dynamically and mark topics as `Not Started`, `In Progress`, or `Completed`.

### 3. 💬 Company Interview Hub & AI Mock Coach
- **10 Round-Specific Questions**: Generates 10 targeted interview questions categorized by hiring rounds (Aptitude/Technical, Coding, System Design, HR/Behavioral).
- **Company Placement Presets**: Practice drive questions tailored to top recruiters (*TCS*, *Streebo*, *Google*, *Amazon*, etc.).
- **Interactive AI Mock Coach**: Submit practice answers to receive instant score ratings, model answers, and improvement feedback.

### 4. 📄 ATS Resume Doctor & STAR Bullet Generator
- **ATS Compatibility Audit**: Scans resumes against target job titles to generate a 0-100 ATS score and keyword gap analysis.
- **STAR Bullet Rewriter**: Rewrites weak resume experience bullet points into high-impact **Situation-Task-Action-Result (STAR)** format.

### 5. 📊 Executive Dashboard & Progression History
- **Visual Analytics**: Line chart for readiness score growth over time and doughnut chart for milestone completion ratios using **Chart.js**.
- **Score Growth Diffs**: Compare previous and current position evaluations to track concrete score improvement (*e.g., +19 points growth*).

### 6. 📑 Executive PDF Report Exports
- Export clean, printable PDF career intelligence reports for recruiters, placement officers, or offline review.

### 7. 🔌 REST API Infrastructure
- Fully equipped with **Django REST Framework** and **SimpleJWT** token authentication (`/api/auth/token/`) for mobile or external integrations.

---

## 🛠️ Tech Stack & Architecture

| Component | Technology Used |
| :--- | :--- |
| **Core Framework** | Python 3.13 + Django 4.2 |
| **REST APIs** | Django REST Framework (DRF) + SimpleJWT |
| **Frontend UI** | Vanilla JavaScript, HTML5, CSS3 Glassmorphism Aesthetics, Chart.js, FontAwesome 6 |
| **AI Integration** | Google Gemini / OpenAI API (Structured JSON parsing & prompt engineering) |
| **Document Processing** | `pdfplumber`, `PyPDF2`, `python-docx` |
| **Production WSGI & Static Server** | `Gunicorn` + `WhiteNoise` |
| **Database** | SQLite3 / MySQL / PostgreSQL support |

---

## 📁 Repository Structure

```
SkillBridge/
├── manage.py
├── Procfile
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── SkillBridge_AI.pdf           # Master PRD Specification Document
├── django_chatbot/              # Project Configuration Package
│   ├── settings.py              # Production-ready settings with WhiteNoise
│   ├── urls.py                  # Root URL Router
│   ├── wsgi.py                  # WSGI Application entrypoint
│   └── asgi.py
├── skillbridge/                 # Core SkillBridge Application App
│   ├── models.py                # CareerProfile, Analysis, Roadmap, InterviewQuestion
│   ├── views.py                 # Web Views & Controllers
│   ├── api_views.py             # DRF REST API Viewsets
│   ├── ai_service.py            # AI Engine & Prompt Engineering Layer
│   ├── doc_parser.py            # PDF & DOCX Document Parser Service
│   ├── scoring.py               # Documented Weighted Scoring Engine
│   ├── pdf_service.py           # PDF Export Generator
│   ├── serializers.py           # DRF Serializers
│   └── urls.py                  # SkillBridge Routing Table
└── templates/                   # HTML Templates & View Components
    └── skillbridge/
        ├── base.html
        ├── landing.html
        ├── about.html
        ├── login.html
        ├── register.html
        ├── dashboard.html
        ├── profile.html
        ├── analyze.html
        ├── analysis_detail.html
        ├── roadmap.html
        ├── interview_prep.html
        ├── resume.html
        └── history.html
```

---

## 💻 Local Installation & Setup

Follow these steps to run **SkillBridge** locally on your machine:

### 1. Clone the Repository
```bash
git clone https://github.com/om-kava/SkillBridge.git
cd SkillBridge
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables
Create a `.env` file in the root directory (refer to `.env.example`):
```ini
SECRET_KEY=django-insecure-local-dev-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### 5. Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 7. Run Local Development Server
```bash
python manage.py runserver
```

Open your browser and visit: **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** 🎉

---

## ⚙️ Environment Variables

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `SECRET_KEY` | Django security secret key | `django-insecure-...` |
| `DEBUG` | Toggle debug mode (`True` locally, `False` in production) | `True` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed host domains | `localhost,127.0.0.1,.render.com` |
| `OPENAI_API_KEY` | OpenAI API Key for AI roadmap & interview parsing | `sk-...` |

---

## 🌐 Production Cloud Deployment (Render / Railway)

This repository is pre-configured for 1-click deployment using **Gunicorn** and **WhiteNoise**:

1. **Build Command**:
   ```bash
   pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
   ```
2. **Start Command**:
   ```bash
   gunicorn django_chatbot.wsgi:application
   ```

---

## 📄 Privacy & Ethical Notice
> SkillBridge provides career guidance based on input candidate data and job descriptions. It does not guarantee employment or selection.

---

## 📝 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

<p center="text-align: center;">Crafted with ❤️ for MCA Candidates & Software Engineers</p>
