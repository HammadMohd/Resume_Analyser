# Phase 11 — Frontend (Minimal)

## Overview
A minimal vanilla HTML/CSS/JS frontend that provides a simple interface to upload resumes and view ATS compatibility scores.

## Files Created

### `frontend/index.html`
- Main page with upload form and results display
- No build step required
- Loads Chart.js from CDN for score visualization

### `frontend/styles.css`
- Clean, responsive design
- Loading spinner
- Color-coded skill tags (green=matched, red=missing)
- Score breakdown cards

### `frontend/app.js`
- API calls to all backend endpoints
- Dynamic UI updates
- Chart.js integration for score visualization

### `backend/main.py`
- Added static file serving with `StaticFiles`
- Health check endpoint moved before static mount

### `tests/test_frontend.py`
- 4 tests for static file serving
- Verifies HTML, CSS, JS accessibility
- Confirms health endpoint still works

## Architecture

```
Browser → index.html → app.js → Backend API
                           ↓
                    Display results
```

## Why Vanilla JS?

| Approach | Pros | Cons |
|----------|------|------|
| Vanilla JS | No build step, fast, simple | More code |
| React | Component reuse, state mgmt | Build step, node_modules bloat |
| Vue | Gentle learning curve | Still needs build |
| Svelte | Compile-time, fast | Build step |

**Decision**: Vanilla JS keeps it simple for a minimal frontend. Can upgrade to React later if needed.

## API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/resume/upload` | POST | Upload resume file |
| `/api/resume/{id}/parse` | POST | Parse resume |
| `/api/resume/{id}/normalize` | POST | Normalize to JSON |
| `/api/resume/{id}/extract` | POST | Extract entities |
| `/api/resume/{id}/validate` | POST | Validate rules |
| `/api/jd/parse-text` | POST | Parse job description |
| `/api/score/analyze` | POST | Get ATS score |
| `/api/rewrite/bullets` | POST | Rewrite bullets |

## Running the Frontend

```bash
# Start server
$env:DEBUG="true"; fastapi dev backend/main.py

# Open browser
http://localhost:8000
```

## Learning Notes

### StaticFiles Mount Order Matters
```python
# WRONG: StaticFiles catches /health
app.mount("/", StaticFiles(...))
app.get("/health")  # Never reached!

# CORRECT: Define routes first
app.get("/health")
app.mount("/", StaticFiles(...))
```

### Chart.js CDN
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
```

### Fetch API Pattern
```javascript
const response = await fetch('/api/endpoint', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
});
const result = await response.json();
```
