# Multi-ATS Resume Analyzer & AI Tailoring Studio

> **Production-Grade, Deterministic-First ATS Engine & AI Resume Tailoring Platform**

A full-stack, enterprise-ready resume engineering system that parses, validates, emulates major ATS software, scores bullet impact, tailors resumes using the **STAR methodology**, and exports clean, ATS-compliant PDF & DOCX documents.

---

## 🌟 Key Features & Highlights

### 🎯 1. Multi-ATS Software Emulation Engine
Emulates parsing behaviors, layout penalties, and scoring criteria of top 5 enterprise ATS platforms:
- **Workday:** Evaluates section header standardization, double-column penalties, and table layout warnings.
- **Greenhouse:** Measures embedded skill-to-experience context density.
- **Lever:** Checks contact placement, email/phone validation, and LinkedIn profile integration.
- **Taleo:** Enforces word-count thresholds per bullet, exact phrase matching, and character compliance.
- **iCIMS:** Checks degree hierarchy and keyword distribution.

### ⚡ 2. Impact Quantification & Readability Analytics
- **Metric Quantifier:** Detects percentages (`%`), dollar amounts (`$`), multipliers (`10x`), and scale counts in experience bullets.
- **Action Verb Intensity:** Classifies leading verbs into High-Impact (*Engineered, Spearheaded*), Moderate, or Weak (*Worked on, Assisted*).
- **Buzzword & Readability Detector:** Identifies overused corporate jargon and recommends concrete alternatives.

### 🪄 3. AI-Powered STAR Resume Tailor
- **Target JD Alignment:** Identifies missing target skills from any Job Description.
- **STAR Framework Rewriter:** Transforms generic bullets into high-impact Situation-Task-Action-Result statements (via Google Gemini API or deterministic fallback).
- **Zero Hallucination Guarantee:** Preserves candidate experience facts while elevating structure and keywords.

### 📄 4. ATS-Proof PDF & DOCX Exporter
- Exports tailored resumes in single-column, 1-page/2-page clean layouts engineered to pass 100% of ATS parsers.

### 🗄️ 5. Database & History Tracking
- Powered by **Async SQLAlchemy 2.0** (SQLite for zero-config local dev, PostgreSQL for production).
- Stores parsed resumes, job descriptions, analysis records, and tailored versions.

### 🎨 6. Premium Glassmorphic UI Dashboard
- Dark-mode glassmorphic interface with multi-tab navigation (Overview, Multi-ATS Hub, Impact Analytics, AI Tailor Studio, Export Hub).

---

## 🏗️ System Architecture

```
                                  ┌───────────────────────────┐
                                  │   Glassmorphic Dashboard  │
                                  └─────────────┬─────────────┘
                                                │
                                  ┌─────────────▼─────────────┐
                                  │    FastAPI HTTP Router    │
                                  └─────────────┬─────────────┘
                                                │
     ┌──────────────────┬───────────────────────┼───────────────────────┬──────────────────┐
     │                  │                       │                       │                  │
┌────▼────────┐  ┌──────▼──────┐       ┌────────▼────────┐     ┌────────▼────────┐ ┌──────▼──────┐
│ PDF / DOCX  │  │  Multi-ATS  │       │  Impact Metric  │     │   AI Tailor     │ │  ReportLab / │
│   Parser    │  │  Emulator   │       │    Analyzer     │     │ (Gemini / STAR) │ │  DOCX Export │
└────┬────────┘  └──────┬──────┘       └────────┬────────┘     └────────┬────────┘ └──────┬──────┘
     │                  │                       │                       │                  │
     └──────────────────┴───────────────────────┼───────────────────────┴──────────────────┘
                                                │
                                  ┌─────────────▼─────────────┐
                                  │ Async SQLAlchemy / SQLite │
                                  └───────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.11+
- `uv` (recommended fast package installer) or `pip`

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/HammadMohd/Resume_Analyser.git
cd Resume_Analyser

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev,ocr,nlp,search,llm,database,cache,queue]"
```

### 3. Environment Setup

```bash
cp .env.example .env
# Set your GEMINI_API_KEY (optional, fallback rules work out-of-the-box!)
```

### 4. Run Application

```bash
# Start FastAPI Dev Server
uv run fastapi dev backend/main.py
```

Open your browser at `http://localhost:8000` to access the Dashboard, or `http://localhost:8000/docs` for the interactive API Documentation.

---

## 🧪 Testing & Quality Assurance

```bash
# Run pytest test suite
uv run pytest tests/ -v
```

---

## 🛰️ API Endpoints Summary

| Category | Method | Endpoint | Description |
|----------|--------|----------|-------------|
| **Resumes** | `POST` | `/api/v1/resumes/` | Upload & store resume file |
| **Resumes** | `POST` | `/api/v1/resumes/parse` | Parse resume into layout structured text |
| **Resumes** | `POST` | `/api/v1/resumes/extract` | Extract entities, skills, contact info |
| **Resumes** | `POST` | `/api/v1/resumes/export/pdf` | Export ATS-compliant clean PDF |
| **Resumes** | `POST` | `/api/v1/resumes/export/docx` | Export ATS-compliant clean DOCX |
| **Multi-ATS**| `POST` | `/api/v1/score/multi-ats` | Evaluate Workday, Greenhouse, Lever, Taleo, iCIMS |
| **Impact** | `POST` | `/api/v1/score/impact` | Score metric quantification & action verbs |
| **Tailor** | `POST` | `/api/v1/rewrite/tailor` | Auto-tailor experience bullets to target JD |

---

## 📜 License
MIT License. Created by Hammad Mohd.
