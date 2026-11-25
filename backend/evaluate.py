"""Run the system on every resume in backend/data/test_resumes and print a report.
Usage (from the smart-hire folder):  python backend/evaluate.py
"""
import re
import time
from pathlib import Path

from resume_parser import extract_text, extract_skills, SKILL_MAP

FOLDER = Path(__file__).parent / "data" / "test_resumes"


def candidate_skills(raw_text):
    """Words in the 'Skills' section of the resume that are NOT in skills.csv.
    These are skills you might want to add (review them by eye - the list is noisy)."""
    found = set()
    for m in re.finditer(r"(?is)skills\s*[:\-]?\s*(.{0,400})", raw_text):
        for part in re.split(r"[,\n|\u2022\u00b7;:/()]+", m.group(1)):
            p = part.strip().lower()
            if 2 <= len(p) <= 25 and len(p.split()) <= 3 and p not in SKILL_MAP:
                found.add(p)
    return sorted(found)


def main():
    files = sorted(f for f in FOLDER.glob("*") if f.suffix.lower() in (".pdf", ".docx"))
    if not files:
        print(f"Put some resumes (PDF/DOCX) in {FOLDER}")
        return

    try:
        from role_matcher import recommend_roles
        have_roles = True
    except Exception as e:
        print("Role matcher unavailable:", e)
        have_roles = False
    try:
        from job_matcher import match_jobs
        have_jobs = True
    except Exception as e:
        print("Job matcher unavailable:", e)
        have_jobs = False

    for f in files:
        print("=" * 70)
        print("RESUME:", f.name)
        start = time.time()
        try:
            text = extract_text(f)
        except Exception as e:
            print("  CANNOT READ FILE:", e)
            continue
        if len(text.strip()) < 50:
            print("  PROBLEM: almost no text found (scanned image?)")
            continue

        skills = extract_skills(text)
        print("  Words in resume :", len(text.split()))
        print("  Skills found    :", skills)
        print("  Maybe missing   :", candidate_skills(text))

        if have_roles:
            for r in recommend_roles(text)["roles"]:
                print(f"  Role: {r['role']} - {r['final_score']}%")
        if have_jobs:
            try:
                for j in match_jobs(text, top_n=3):
                    print(f"  Job : {j['match_percent']}%  {j['title']} at {j['company']}")
            except Exception as e:
                print("  Job matching failed:", e)
        print(f"  Time: {time.time() - start:.1f} seconds")


if __name__ == "__main__":
    main()