# Deterministic-First ATS Resume Analyzer
## End-to-End Production Project Plan

**Project Type:** AI + Backend Engineering + Information Retrieval + NLP

**Difficulty:** Advanced

**Architecture Style:** Hybrid Deterministic + LLM

**Goal**

Instead of sending an entire resume directly to an LLM, build a production-grade ATS Resume Analyzer where deterministic software engineering performs parsing, extraction, scoring, validation, and ranking, while the LLM is only responsible for improving language.

---

# 1. Project Vision

Most resume analyzers are simply:

```
Resume
    ↓
LLM
    ↓
Feedback
```

This approach has several drawbacks:

- High API cost
- High latency
- Hallucinations
- Non-reproducible ATS scores
- Poor explainability

Our project follows a Deterministic-First Architecture.

```
Resume
     ↓
Parsing
     ↓
Information Extraction
     ↓
Rule Engine
     ↓
ATS Scoring
     ↓
Skill Gap Analysis
     ↓
LLM Refinement
     ↓
Dashboard
```

LLM is the final editor, **not the decision maker**.

---

# 2. High-Level Architecture

```
                    +----------------------+
                    | Upload Resume        |
                    | PDF / DOCX / Image   |
                    +----------+-----------+
                               |
                               |
                               ▼
               +------------------------------+
               | File Validation              |
               | • Extension                  |
               | • Size                       |
               | • Malware Scan               |
               +--------------+---------------+
                              |
                              ▼
               +------------------------------+
               | Document Parsing Layer       |
               |                              |
               | PDFPlumber                   |
               | PyMuPDF                      |
               | OCR Fallback                 |
               +--------------+---------------+
                              |
                              ▼
               +------------------------------+
               | Layout Reconstruction        |
               |                              |
               | Header Detection             |
               | Reading Order                |
               | Two Columns                  |
               | Tables                       |
               +--------------+---------------+
                              |
                              ▼
               +------------------------------+
               | Resume JSON Builder          |
               +--------------+---------------+
                              |
                              ▼
               +------------------------------+
               | Deterministic Engine         |
               |                              |
               | Regex                        |
               | SpaCy                        |
               | Rule Engine                  |
               | Timeline Validation          |
               +--------------+---------------+
                              |
                              ▼
               +------------------------------+
               | Hybrid Search Engine         |
               |                              |
               | BM25                         |
               | Dense Embeddings             |
               | Cosine Similarity            |
               +--------------+---------------+
                              |
                              ▼
               +------------------------------+
               | ATS Scoring Engine           |
               +--------------+---------------+
                              |
                              ▼
               +------------------------------+
               | Gap Detection JSON           |
               +--------------+---------------+
                              |
                              ▼
               +------------------------------+
               | LLM Refinement               |
               | Instructor + Pydantic        |
               +--------------+---------------+
                              |
                              ▼
               +------------------------------+
               | Frontend Dashboard           |
               +------------------------------+
```

---

# 3. System Workflow

```
User uploads resume

↓

Validate file

↓

Extract text

↓

Recover document layout

↓

Create normalized JSON

↓

Extract structured information

↓

Run ATS rule engine

↓

Extract job description

↓

Compare resume vs JD

↓

Calculate ATS score

↓

Detect missing skills

↓

Generate structured gaps

↓

Send only gaps to LLM

↓

Validate LLM output

↓

Display dashboard
```

---

# 4. Folder Structure

```
resume-analyzer/

│
├── backend/
│
│   ├── api/
│   ├── parser/
│   ├── ocr/
│   ├── extractor/
│   ├── ats/
│   ├── scoring/
│   ├── embeddings/
│   ├── llm/
│   ├── validators/
│   ├── schemas/
│   ├── services/
│   ├── utils/
│   ├── config/
│   └── main.py
│
├── frontend/
│
│   ├── components/
│   ├── pages/
│   ├── hooks/
│   ├── services/
│   ├── charts/
│   ├── diff-view/
│   └── dashboard/
│
├── models/
│
├── datasets/
│
├── tests/
│
├── docker/
│
└── docs/
```

---

# 5. Core Modules

## Module 1 — Upload Service

Responsibilities

- Resume upload
- Job Description upload
- Authentication
- File validation

Supported

- PDF
- DOCX
- TXT
- PNG
- JPG

---

## Module 2 — Multi Engine Parser

Libraries

- PDFPlumber
- PyMuPDF
- pdfminer.six

OCR

- Tesseract

Output

```
Raw Text

+

Coordinates

+

Fonts

+

Bounding Boxes
```

Example

```
{
  "text":"Software Engineer",
  "page":1,
  "x":70,
  "y":210,
  "font":"Helvetica-Bold",
  "size":16
}
```

---

## Module 3 — Layout Reconstruction

Purpose

Recover actual reading order.

Detect

- Two columns
- Headers
- Bullets
- Tables
- Sidebars
- Footer
- Header

Output

```
Experience

↓

Projects

↓

Skills

↓

Education
```

---

## Module 4 — Resume JSON Builder

Everything becomes structured.

Example

```json
{
  "name": "",
  "email": "",
  "phone": "",
  "linkedin": "",
  "github": "",
  "summary": "",
  "skills": [],
  "experience": [],
  "projects": [],
  "education": [],
  "certifications": []
}
```

---

# 6. Deterministic Information Extraction

## Contact Extraction

Regex

- Email
- Phone
- LinkedIn
- GitHub
- Portfolio

---

## Entity Extraction

SpaCy

Extract

- Organization
- Degree
- Skills
- Date
- Location
- Person

---

## Timeline Extraction

Find

```
Jan 2021

↓

May 2023
```

Detect

- Missing dates
- Overlapping jobs
- Reverse chronology
- Career gaps

---

# 7. Resume Rule Engine

Checks

## Contact Score

- Email
- Phone
- LinkedIn

---

## Resume Sections

Required

- Summary
- Experience
- Skills
- Education

---

## Bullet Quality

Each bullet scored.

Example

```
Implemented REST APIs.
```

Checks

✔ Action Verb

✘ Metrics

✔ Technology

✘ Business Impact

---

## Quantification Detector

Detect

```
Improved APIs
```

vs

```
Reduced latency by 45%
```

Regex

```
\d+%

\d+

million

thousand

users

hours
```

---

## Resume Length

Rules

- 0-2 years → 1 page

- 3-8 years → 1-2 pages

- 10+ years → 2 pages

---

# 8. Job Description Processing

Extract

- Skills
- Experience
- Education
- Responsibilities
- Keywords

Convert into

```
JD JSON
```

---

# 9. Hybrid Search Engine

Purpose

Semantic ATS matching.

Components

## BM25

Hard skills

Examples

```
Docker

AWS

Redis

Kafka
```

---

## Dense Embeddings

Sentence Transformers

Examples

```
ETL

≈

Data Pipeline

≈

Data Ingestion
```

---

## Final Similarity

```
Final Score

=

0.6 BM25

+

0.4 Cosine Similarity
```

---

# 10. ATS Scoring Engine

Formula

```
ATS Score

=

35% Skills

+

25% Experience

+

15% Projects

+

10% Education

+

10% Resume Structure

+

5% Formatting
```

Score

```
87/100
```

Explain every deduction.

---

# 11. Skill Gap Analysis

Output

```
Missing Skills

Docker

Kafka

Terraform

Redis
```

Priority

High

Medium

Low

---

# 12. Resume Quality Metrics

Calculate

Grammar

Readability

Action Verbs

Passive Voice

Buzzwords

Repeated Words

Sentence Length

Bullet Consistency

---

# 13. LLM Refinement Layer

LLM receives ONLY

```
{
  "weak_bullets":[],
  "missing_skills":[],
  "summary":"",
  "issues":[]
}
```

Prompt

```
Rewrite only these bullets.

Do not invent experience.

Return JSON.
```

---

# 14. Pydantic Validation

Schema

```python
class BulletSuggestion(BaseModel):

    original:str

    improved:str

    confidence:float
```

Reject

- Fake metrics

- Long responses

- New technologies

- Hallucinations

---

# 15. API Design

## Upload Resume

```
POST

/api/upload
```

---

## Upload JD

```
POST

/api/job
```

---

## Parse Resume

```
POST

/api/parse
```

---

## ATS Score

```
GET

/api/score
```

---

## Skill Gap

```
GET

/api/skills
```

---

## Rewrite Bullets

```
POST

/api/rewrite
```

---

## Dashboard

```
GET

/api/dashboard
```

---

# 16. Database Schema

Tables

Users

Projects

Resumes

JobDescriptions

Skills

Scores

LLMResponses

Analytics

---

# 17. Frontend Features

Dashboard

Resume Upload

Job Upload

ATS Score

Resume Breakdown

Skill Match

Missing Skills

Timeline

Bullet Improvement

Original vs Improved

Download Report

Dark Mode

History

---

# 18. Dashboard Layout

```
--------------------------------------------------

ATS Score

92%

--------------------------------------------------

Skill Match

██████████

--------------------------------------------------

Missing Skills

Docker

Redis

Kafka

--------------------------------------------------

Resume Sections

✔ Experience

✔ Skills

✔ Education

✘ Summary

--------------------------------------------------

Timeline

Intern

↓

Engineer

↓

Senior Engineer

--------------------------------------------------

Bullet Improvements

Original

↓

Improved

--------------------------------------------------
```

---

# 19. Advanced Features

## OCR Fallback

Scanned PDFs

---

## Resume Version History

Track edits.

---

## Resume Comparison

Compare V1

vs

V2

---

## Resume Heatmap

Highlight weak sections.

---

## ATS Simulator

Simulate different company ATS rules.

---

## Multi-Language Resume Parsing

English

German

French

Spanish

---

## Explainable ATS Score

Every score has reasoning.

Example

```
Experience

22/25

Reason

Missing Docker.
```

---

## Analytics

Most missing skills

Average ATS score

Resume trends

Keyword frequency

Most common mistakes

---

# 20. Tech Stack

## Backend

- FastAPI
- Python 3.12

---

## Parsing

- PDFPlumber
- PyMuPDF
- pdfminer.six
- python-docx
- Tesseract OCR

---

## NLP

- SpaCy
- NLTK
- RapidFuzz

---

## Search

- rank-bm25
- scikit-learn

---

## Embeddings

- Sentence Transformers

---

## Vector Database

- Qdrant

or

- ChromaDB

---

## LLM

- OpenAI
- Gemini
- Groq

Using

- Instructor
- Pydantic

---

## Database

- PostgreSQL

---

## Cache

- Redis

---

## Queue

- Celery

or

- RQ

---

## Storage

- AWS S3

or

- MinIO

---

## Frontend

- Vanilla HTML/CSS/JS (minimal approach, no build step)
- Chart.js for score visualization
- Fetch API for backend communication
- Static file serving via FastAPI

---

## Deployment

- Docker
- Docker Compose
- Nginx
- GitHub Actions
- AWS EC2 / Render / Railway

---

# 21. End-to-End Flowchart

```
                 User Uploads Resume
                         │
                         ▼
                 File Validation
                         │
                         ▼
                 Multi-Engine Parser
         (PDFPlumber / PyMuPDF / OCR)
                         │
                         ▼
              Layout Reconstruction
                         │
                         ▼
             Resume Normalization JSON
                         │
                         ▼
          Deterministic Extraction Engine
      (Regex + SpaCy + Rule Validation)
                         │
                         ▼
          Job Description Processing
                         │
                         ▼
             Hybrid Matching Engine
      (BM25 + Embeddings + Cosine Similarity)
                         │
                         ▼
              ATS Scoring Algorithm
                         │
                         ▼
             Skill Gap Identification
                         │
                         ▼
          Structured Gap JSON Generation
                         │
                         ▼
            LLM Bullet Point Refiner
       (Strict JSON via Instructor/Pydantic)
                         │
                         ▼
             Validation & Sanitization
                         │
                         ▼
              Analytics & Report Builder
                         │
                         ▼
          Interactive React Dashboard
```

---

# 22. Future Enhancements

- AI Interview Question Generator
- Resume-to-Portfolio Generator
- LinkedIn Profile Analyzer
- GitHub Repository Analyzer
- Resume Benchmark Against Top Candidates
- Company-Specific ATS Profiles (Amazon, Google, Microsoft, etc.)
- Cover Letter Generator using Resume + Job Description
- Personalized Learning Roadmap for Missing Skills
- Recruiter Collaboration Dashboard
- Resume Quality Trends Across Versions
- Batch Resume Processing for Recruiters
- Resume API for HRMS Integration
- RAG-powered Resume Knowledge Base
- Explainable AI (XAI) dashboard showing why every ATS score was assigned
- Multi-tenant SaaS architecture with role-based access control (RBAC)

---

# 23. Why This Project Stands Out

Unlike a generic "LLM Resume Analyzer," this system emphasizes **software engineering, deterministic processing, and explainable AI**.

Key differentiators include:

- Multi-engine PDF parsing with coordinate-aware layout reconstruction
- OCR fallback for scanned resumes
- Structured resume normalization into JSON
- Regex and SpaCy-based deterministic information extraction
- Rule-based validation for resume quality and ATS compliance
- Hybrid search combining BM25 and semantic embeddings
- Transparent, reproducible ATS scoring algorithm
- Skill gap analysis with semantic understanding
- LLM limited to rewriting and refinement tasks only
- Strict JSON responses validated with Pydantic/Instructor
- Interactive dashboard with visual diffs, analytics, and explainable scoring

This architecture demonstrates expertise in backend engineering, NLP, information retrieval, search systems, API design, scalable software architecture, and responsible LLM integration—making it significantly more compelling to recruiters than a simple prompt-based AI application.