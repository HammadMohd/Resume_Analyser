# API Documentation

## Base URL

```
http://localhost:8000
```

## Endpoints

### Upload Resume

Upload a resume file (PDF or DOCX).

**Request:**

```
POST /api/v1/resumes/
Content-Type: multipart/form-data
```

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| file | file | Yes | Resume file (PDF or DOCX) |

**Response (200):**

```json
{
  "success": true,
  "message": "File uploaded and stored successfully",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "original_filename": "resume.pdf",
    "stored_filename": "a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf",
    "content_type": "application/pdf",
    "size_bytes": 12345,
    "upload_timestamp": "2026-08-03T14:00:00Z"
  }
}
```

**Error Response (422):**

```json
{
  "success": false,
  "message": "File validation failed",
  "errors": [
    "Invalid file extension 'txt'. Allowed: docx, pdf",
    "Invalid MIME type 'text/plain'. Allowed: application/pdf, ..."
  ]
}
```

**Error Codes:**

| Code | Description |
|------|-------------|
| 200 | Upload successful |
| 422 | Validation failed (wrong type, empty, bad MIME) |
| 413 | File too large |
| 500 | Internal server error |

**Example (curl):**

```bash
curl -X POST http://localhost:8000/api/v1/resumes/ \
  -F "file=@resume.pdf"
```

**Example (Python):**

```python
import requests

files = {"file": open("resume.pdf", "rb")}
response = requests.post("http://localhost:8000/api/v1/resumes/", files=files)
print(response.json())
```

---

### Health Check

Check if the server is running.

**Request:**

```
GET /health
```

**Response (200):**

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "development"
}
```

---

## Validation Rules

| Rule | Allowed | Error |
|------|---------|-------|
| Extension | `.pdf`, `.docx` | Invalid extension |
| MIME type | `application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | Invalid MIME type |
| File size | < 10 MB | File too large |
| Empty file | Not empty | File is empty |

## Authentication

None required (Phase 2).

## Rate Limiting

None implemented (Phase 12).
