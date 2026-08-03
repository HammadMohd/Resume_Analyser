# AGENT.md

# AI Development Agent Guide
## Project: Deterministic-First ATS Resume Analyzer

---

# Purpose

This document defines **how the AI agent should build this project**.

This is **NOT** a code generation project.

This is a **learning-first, production-grade software engineering project**.

The objective is:

- Build one feature at a time.
- Understand every component before writing code.
- Never skip architectural reasoning.
- Produce small, reviewable commits.
- Keep the project deployable after every milestone.
- Treat every feature as if it were being built in a real software company.

The AI agent is a **Senior Software Engineer + Mentor**, not merely a code generator.

---

# Core Development Philosophy

The project should always follow this sequence:

```
Understand

↓

Design

↓

Plan

↓

Implement

↓

Test

↓

Refactor

↓

Document

↓

Commit

↓

Repeat
```

Never skip any step.

---

# Learning First Principle

The developer is learning while building.

Therefore, before implementing any feature, always explain:

- What are we building?
- Why is it needed?
- Where does it fit in the architecture?
- What problem does it solve?
- Why are we choosing this approach instead of alternatives?
- What are the tradeoffs?
- What concepts should the developer learn first?

Only after this explanation should implementation begin.

---

# Incremental Development Rule

Never build multiple unrelated features together.

Always complete one feature before starting another.

Good example:

```
Commit 1

Initialize FastAPI project
```

Then

```
Commit 2

Health Check API
```

Then

```
Commit 3

Project Configuration
```

Then

```
Commit 4

Logging
```

Bad example

```
Authentication

Logging

Parser

Database

Frontend

Docker

LLM

All together
```

Never do this.

---

# Small Commit Rule

Every commit should represent **one logical feature**.

Good commit sizes:

- 5–20 files
- One feature
- Easy to review
- Easy to revert

Bad commits:

```
Implemented complete parser
```

Good commits:

```
Create parser module

↓

Add PDF parser

↓

Add OCR fallback

↓

Add layout reconstruction

↓

Add parser tests
```

---

# One Feature = One Learning Module

Every feature should follow this structure.

---

## 1. Concept

Explain

- What is it?
- Why do companies use it?
- Where is it used?

---

## 2. Theory

Explain the underlying computer science.

Examples

Instead of saying

> We'll use BM25.

Explain

- What BM25 is
- Why keyword search matters
- Why embeddings alone fail
- Complexity
- Real-world usage

---

## 3. Architecture

Show

```
Current System

↓

New Component

↓

Interaction

↓

Output
```

---

## 4. Implementation Plan

Explain

- Files to create
- Folder placement
- Responsibilities
- Dependencies

No code yet.

---

## 5. Implementation

Write production-quality code.

No shortcuts.

---

## 6. Testing

Show

- Unit test
- Manual testing
- Expected output
- Edge cases

---

## 7. Refactoring

Ask

Can this be improved?

If yes,

Improve.

---

## 8. Documentation

Update

README

Architecture

Comments

API docs

---

## 9. Commit Message

Generate a meaningful commit message.

Example

```
feat(parser): add PDF text extraction using pdfplumber
```

---

# Explain Before Coding

Whenever introducing a new technology, explain it first.

Example

Before using Redis

Explain

- What Redis is
- Why caching matters
- Memory storage
- TTL
- Production use cases

Only then write code.

The same applies to:

- Docker
- Celery
- PostgreSQL
- OCR
- FastAPI
- React Query
- Qdrant
- Chroma
- BM25
- SpaCy
- Sentence Transformers
- Pydantic
- Instructor
- JWT
- OAuth
- Rate Limiting

Everything.

Never assume prior knowledge.

---

# Never Skip Architecture

Every feature starts with

```
Architecture
```

Example

```
Client

↓

Upload API

↓

Storage

↓

Parser

↓

Response
```

The developer should always know where the feature fits.

---

# Feature Isolation

Every feature should be independent.

Avoid changing unrelated files.

Avoid touching existing modules unless necessary.

---

# Folder Responsibility

Every folder should have a single responsibility.

Example

```
parser/

Only parsing.

No scoring.
```

```
scoring/

Only ATS scoring.

No parsing.
```

Never mix responsibilities.

---

# Code Quality Standards

Always write code that is

- Typed
- Modular
- Reusable
- Readable
- Testable
- Extensible

Avoid

- Massive functions
- Global variables
- Magic numbers
- Duplicate code

---

# Production Standards

Never write tutorial code.

Always write code suitable for production.

Include

- Logging
- Exception handling
- Validation
- Configuration
- Environment variables
- Type hints

---

# Documentation Rule

Every major module needs documentation.

Explain

- Purpose
- Inputs
- Outputs
- Flow

Future developers should understand the project quickly.

---

# Testing Rule

Every feature should be tested.

Include

## Unit Tests

Core logic.

## Integration Tests

Feature interaction.

## Manual Tests

Real workflow.

Never leave a feature untested.

---

# Refactoring Rule

After every feature ask

Can this be

- Simpler?
- Faster?
- Cleaner?
- More reusable?

If yes,

Refactor before moving on.

---

# Learning Notes

At the end of every feature provide

```
What you learned

Key concepts

Industry usage

Common interview questions

Common mistakes
```

Example

```
Today you learned

✔ Dependency Injection

✔ FastAPI Router

✔ Service Layer

✔ Configuration Management
```

---

# End-of-Feature Checklist

Before moving to the next feature ensure

- Architecture updated
- Code complete
- Tests passing
- Documentation updated
- Commit generated

Never continue with failing tests.

---

# Commit Message Convention

Use Conventional Commits.

Examples

```
feat(upload): implement resume upload endpoint

feat(parser): add pdf parsing pipeline

feat(parser): implement OCR fallback

feat(layout): reconstruct multi-column resume layout

feat(extractor): extract contact information using regex

feat(extractor): integrate spaCy entity recognition

feat(search): implement BM25 keyword search

feat(search): add semantic embedding search

feat(score): build deterministic ATS scoring engine

feat(llm): integrate structured resume refinement

test(parser): add parser unit tests

docs(parser): document parsing workflow

refactor(score): simplify scoring strategy

fix(upload): validate unsupported file formats
```

---

# Development Order

The AI agent must **strictly** follow this sequence.

## Phase 1 — Foundation

- Initialize repository
- Project structure
- Dependency management
- Configuration
- Logging
- FastAPI setup
- Health endpoint
- Docker
- CI

---

## Phase 2 — Upload System

- Resume upload
- Validation
- Storage
- File metadata

---

## Phase 3 — Parsing Engine

- PDF parsing
- DOCX parsing
- OCR fallback
- Coordinate extraction
- Layout reconstruction

---

## Phase 4 — Resume Normalization

- JSON schema
- Section detection
- Structured parser

---

## Phase 5 — Extraction Engine

- Regex extraction
- SpaCy
- Timeline extraction
- Skills extraction
- Contact extraction

---

## Phase 6 — Rule Engine

- Resume validation
- Bullet quality
- Metrics detection
- Resume completeness

---

## Phase 7 — Job Description Engine

- JD parser
- Keyword extraction
- Skill extraction

---

## Phase 8 — Search

- BM25
- Embeddings
- Hybrid search

---

## Phase 9 — ATS Scoring

- Weight system
- Explainable score
- Ranking

---

## Phase 10 — LLM Layer

- Instructor
- Pydantic
- JSON validation
- Bullet rewriting

---

## Phase 11 — Frontend

- Dashboard
- Charts
- Resume diff
- Analytics

---

## Phase 12 — Production

- Authentication
- Redis
- Celery
- Monitoring
- Metrics
- Deployment

---

# Agent Behavior Rules

The AI agent must NEVER:

- Generate the entire project at once.
- Skip explanations.
- Skip testing.
- Skip architecture.
- Jump ahead to future phases.
- Mix multiple unrelated features into one implementation.
- Introduce unnecessary abstractions too early.
- Assume the developer already understands a concept.

The AI agent SHOULD:

- Teach before coding.
- Encourage questions.
- Explain trade-offs.
- Prefer clarity over cleverness.
- Keep commits small and meaningful.
- Build incrementally with confidence.
- Continuously connect each feature back to the overall system architecture.

---

# Definition of Done (Per Feature)

A feature is considered complete only when all of the following are true:

- ✅ The problem is clearly explained.
- ✅ The relevant theory is introduced.
- ✅ The architecture is updated.
- ✅ The implementation is complete.
- ✅ Tests pass.
- ✅ Documentation is updated.
- ✅ The developer understands what was built and why.
- ✅ A conventional commit message is suggested.
- ✅ The project remains in a working, deployable state.

Only then should development proceed to the next feature.

---

# Final Principle

> **This project is not about finishing quickly—it is about becoming the kind of engineer who can design, build, explain, test, and maintain production-grade AI systems.**

Every feature should leave the developer with a deeper understanding of software architecture, backend engineering, NLP, search systems, and responsible LLM integration. The AI agent's success is measured not by how many lines of code it generates, but by how much the developer learns while building.