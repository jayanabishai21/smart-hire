import pandas as pd
from pathlib import Path

from resume_parser import extract_skills, SKILL_MAP
from role_model import predict_roles as ml_predict

DATA_DIR = Path(__file__).parent / "data"

# ---------- 1. Load the role-skill table ----------
def load_roles():
    df = pd.read_csv(DATA_DIR / "roles.csv").fillna("")
    roles = {}
    for _, row in df.iterrows():
        skills = {s.strip().lower() for s in row["skills"].split("|") if s.strip()}
        roles[row["role"].strip()] = skills
    return roles

ROLE_SKILLS = load_roles()

# Warn about skills in roles.csv that are missing from skills.csv
_known = set(SKILL_MAP.values())
for _role, _skills in ROLE_SKILLS.items():
    for _s in _skills - _known:
        print(f"WARNING: '{_s}' (role: {_role}) is not in skills.csv")


# ---------- 2. Link the ML model's categories to our roles ----------
CATEGORY_TO_ROLES = {
    "Web Designing":      ["Frontend Developer", "Full Stack Developer", "UI/UX Designer"],
    "Java Developer":     ["Java Developer", "Backend Developer"],
    "Python Developer":   ["Python Developer", "Backend Developer"],
    "Data Science":       ["Data Scientist", "Data Analyst", "Machine Learning Engineer"],
    "DevOps Engineer":    ["DevOps Engineer"],
    "Database":           ["Backend Developer", "Data Analyst"],
    "Business Analyst":   ["Data Analyst"],
    "Testing":            ["QA / Test Engineer"],
}


# ---------- 3. Score each role by skills ----------
def skill_based_roles(resume_skills):
    resume_skills = set(resume_skills)
    results = []
    for role, required in ROLE_SKILLS.items():
        matched = resume_skills & required
        if len(matched) < 2:          # ignore roles with almost no match
            continue
        results.append({
            "role": role,
            "skill_score": round(100 * len(matched) / len(required)),
            "matched_skills": sorted(matched),
            "missing_skills": sorted(required - resume_skills),
        })
    return results


# ---------- 4. Combine skill score + ML model ----------
def recommend_roles(resume_text, top_n=4):
    resume_skills = extract_skills(resume_text)
    candidates = skill_based_roles(resume_skills)

    # ML model: how strongly does each category fit? (top category = 1.0)
    ml = ml_predict(resume_text, top_n=25)
    top_conf = ml[0]["confidence"] or 1
    ml_strength = {m["role"]: m["confidence"] / top_conf for m in ml}

    for c in candidates:
        links = [ml_strength.get(cat, 0)
                 for cat, roles in CATEGORY_TO_ROLES.items() if c["role"] in roles]
        ml_score = 100 * max(links, default=0)
        c["ml_score"] = round(ml_score)
        c["final_score"] = round(0.75 * c["skill_score"] + 0.25 * ml_score)
        c["reason"] = ("You already have: " + ", ".join(c["matched_skills"])
                       if c["matched_skills"] else "")

    candidates.sort(key=lambda c: c["final_score"], reverse=True)
    return {"skills_found": resume_skills, "roles": candidates[:top_n]}