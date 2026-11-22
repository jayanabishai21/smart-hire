import os
import tempfile

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from resume_parser import extract_text, extract_skills
from role_matcher import recommend_roles
from job_matcher import match_jobs
from skill_gap import skill_gap, available_roles

app = FastAPI(title="Smart Hire API")

# Allow the website (frontend) to call this API from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # during development; restrict to your site when you deploy
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_MB = 5
ALLOWED_TYPES = (".pdf", ".docx")


@app.get("/")
def home():
    return {"message": "Smart Hire API is running"}


@app.get("/roles")
def roles():
    """List of roles the student can choose for the skill gap page."""
    return {"roles": available_roles()}


@app.post("/analyze")
def analyze(file: UploadFile = File(...)):
    """Feature 1 + 2: upload a resume, get skills, roles and matching jobs."""
    name = (file.filename or "").lower()
    if not name.endswith(ALLOWED_TYPES):
        raise HTTPException(400, "Please upload a PDF or DOCX file.")

    data = file.file.read()
    if len(data) == 0:
        raise HTTPException(400, "The file is empty.")
    if len(data) > MAX_FILE_MB * 1024 * 1024:
        raise HTTPException(400, f"File is too large. Maximum is {MAX_FILE_MB} MB.")

    # Save to a temporary file, read it, then ALWAYS delete it (resumes are personal data)
    suffix = os.path.splitext(name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        try:
            text = extract_text(tmp_path)
        except Exception:
            raise HTTPException(400, "Could not read this file. Is it damaged or password protected?")
    finally:
        os.remove(tmp_path)

    if len(text.strip()) < 50:
        raise HTTPException(422, "No readable text found. The resume may be a scanned image.")

    skills = extract_skills(text)
    if not skills:
        raise HTTPException(422, "No known skills were found in this resume.")

    role_result = recommend_roles(text)
    try:
        jobs = match_jobs(text, top_n=10)
    except FileNotFoundError as e:
        raise HTTPException(503, str(e))

    return {
        "skills": skills,
        "roles": role_result["roles"],
        "jobs": jobs,
    }


class GapRequest(BaseModel):
    skills: list[str]
    role: str


@app.post("/skill-gap")
def gap(req: GapRequest):
    """Feature 3: compare the student's skills with the skills a role needs."""
    try:
        return skill_gap(req.skills, req.role)
    except ValueError as e:
        raise HTTPException(404, str(e))