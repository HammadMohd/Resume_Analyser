# Upload Workflow

## Overview

The upload pipeline processes resume files through validation, storage, and metadata generation.

## Pipeline

```
Client
    ↓
POST /api/v1/resumes/
    ↓
Resume Router (HTTP layer)
    ↓
UploadService (orchestration)
    ↓
ValidationService (checks)
    ↓
StorageService (writes to disk)
    ↓
UploadResponse (JSON)
```

## Step-by-Step Flow

### 1. Client Uploads File

Client sends multipart/form-data with file field.

```
POST /api/v1/resumes/
Content-Type: multipart/form-data

file: resume.pdf
```

### 2. Router Extracts File

FastAPI extracts `UploadFile` from request.

```python
@router.post("/")
async def upload_resume(file: UploadFile = File(...)):
    ...
```

### 3. ValidationService Checks File

Runs 5 checks in order:

1. **Empty check** — reads 1 byte, detects empty files
2. **Extension check** — must be `.pdf` or `.docx`
3. **MIME check** — must be allowed MIME type
4. **MIME-extension match** — MIME must match extension
5. **Size check** — must be under 10 MB

If any check fails → `FileValidationError` → 422 response.

### 4. StorageService Writes File

1. Generates UUID filename: `{uuid}.{ext}`
2. Creates `uploads/resumes/` if missing
3. Writes bytes to disk
4. Returns file path

### 5. UploadService Builds Metadata

```python
metadata = {
    "id": uuid4(),
    "original_filename": "resume.pdf",
    "stored_filename": "a1b2c3d4.pdf",
    "content_type": "application/pdf",
    "size_bytes": 12345,
    "upload_timestamp": "2026-08-03T14:00:00Z"
}
```

### 6. Router Returns Response

```json
{
  "success": true,
  "message": "File uploaded and stored successfully",
  "data": { ... }
}
```

## Error Flow

```
Validation fails
    ↓
FileValidationError raised
    ↓
Router catches exception
    ↓
Returns 422 with error details
```

## File Naming

| Before | After |
|--------|-------|
| `resume.pdf` | `a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf` |
| `John_Doe_CV.docx` | `123e4567-e89b-12d3-a456-426614174000.docx` |

UUID prevents:
- Path traversal attacks
- Filename collisions
- Overwriting existing files

## Logging

```
Upload started: resume.pdf
Running validation for resume.pdf
Validation passed for resume.pdf
File read complete: resume.pdf (12345 bytes)
Storing file resume.pdf
Storage started for resume.pdf (12345 bytes)
Storage successful: resume.pdf -> uuid.pdf
File stored: resume.pdf -> uuid.pdf
Upload completed successfully: resume.pdf (ID: xxx)
```
