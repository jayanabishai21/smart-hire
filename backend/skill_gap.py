from collections import Counter
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"

# ---------- 1. Roles and their core skills (from roles.csv) ----------
def load_roles():
    df = pd.read_csv(DATA_DIR / "roles.csv").fillna("")
    return {row["role"].strip():
            {s.strip().lower() for s in row["skills"].split("|") if s.strip()}
            for _, row in df.iterrows()}

ROLE_SKILLS = load_roles()

# Words that appear in job titles for each role (used to find real jobs for that role)
ROLE_KEYWORDS = {
    "Frontend Developer":        ["frontend", "front end", "front-end", "react", "ui developer"],
    "Backend Developer":         ["backend", "back end", "back-end", "node", "api developer"],
    "Full Stack Developer":      ["full stack", "fullstack", "full-stack", "mern", "mean stack"],
    "Python Developer":          ["python"],
    "Data Analyst":              ["data analyst", "business intelligence", "bi analyst"],
    "Data Scientist":            ["data scientist"],
    "Machine Learning Engineer": ["machine learning", "ml engineer", "ai engineer"],
    "Java Developer":            ["java developer", "java engineer", "java software"],
    "PHP Developer":             ["php"],
    "UI/UX Designer":            ["ux", "ui/ux", "product designer"],
    "DevOps Engineer":           ["devops", "cloud engineer", "site reliability"],
}

# ---------- 2. Learning links ----------
DOCS = {
    "html": "https://developer.mozilla.org/en-US/docs/Learn/HTML",
    "css": "https://developer.mozilla.org/en-US/docs/Learn/CSS",
    "javascript": "https://developer.mozilla.org/en-US/docs/Learn/JavaScript",
    "react.js": "https://react.dev/learn",
    "node.js": "https://nodejs.org/en/learn",
    "express.js": "https://expressjs.com/",
    "python": "https://docs.python.org/3/tutorial/",
    "git": "https://git-scm.com/doc",
    "docker": "https://docs.docker.com/get-started/",
    "fastapi": "https://fastapi.tiangolo.com/tutorial/",
    "flask": "https://flask.palletsprojects.com/",
    "django": "https://docs.djangoproject.com/",
    "bootstrap": "https://getbootstrap.com/docs/",
    "tailwind css": "https://tailwindcss.com/docs",
    "typescript": "https://www.typescriptlang.org/docs/",
    "pandas": "https://pandas.pydata.org/docs/getting_started/",
    "numpy": "https://numpy.org/learn/",
    "scikit-learn": "https://scikit-learn.org/stable/user_guide.html",
    "tensorflow": "https://www.tensorflow.org/tutorials",
}

def learning_links(skill):
    """A YouTube search link ALWAYS works for any skill; official docs are added when known."""
    links = [{"name": "YouTube tutorials",
              "url": "https://www.youtube.com/results?search_query="
                     + quote_plus(skill + " tutorial for beginners")}]
    if skill in DOCS:
        links.insert(0, {"name": "Official docs / guide", "url": DOCS[skill]})
    return links

# ---------- 3. What do real job postings for this role ask for? ----------
def market_skill_counts(role):
    """Returns (Counter of skills, number of jobs). Empty if the job index isn't built."""
    try:
        from job_matcher import load_index
        jobs, _ = load_index()
    except Exception:
        return Counter(), 0
    titles = jobs["job_title"].str.lower()
    mask = titles.apply(lambda t: any(k in t for k in ROLE_KEYWORDS.get(role, [])))
    role_jobs = jobs[mask]
    counter = Counter()
    for skills in role_jobs["job_skills"]:
        counter.update(set(skills))
    return counter, len(role_jobs)

# ---------- 4. The skill gap ----------
def skill_gap(resume_skills, role, min_jobs=8, demand_threshold=0.3):
    lookup = {r.lower(): r for r in ROLE_SKILLS}
    if role.lower() not in lookup:
        raise ValueError(f"Unknown role '{role}'. Available: {sorted(ROLE_SKILLS)}")
    role = lookup[role.lower()]

    have_set = {s.lower() for s in resume_skills}
    required = ROLE_SKILLS[role]
    counts, n_jobs = market_skill_counts(role)
    use_market = n_jobs >= min_jobs          # only trust job data if we have enough jobs

    def importance(skill):
        return round(100 * counts[skill] / n_jobs) if use_market else None

    # Most requested skills first
    missing = sorted(required - have_set, key=lambda s: (-(counts[s] if use_market else 0), s))
    to_learn = [{"skill": s, "importance_percent": importance(s),
                 "learn": learning_links(s)} for s in missing]

    # Extra skills that many real jobs ask for but are not in our core list
    also = []
    if use_market:
        for s, c in counts.most_common():
            if c / n_jobs >= demand_threshold and s not in required and s not in have_set:
                also.append({"skill": s, "importance_percent": round(100 * c / n_jobs),
                             "learn": learning_links(s)})

    return {
        "role": role,
        "match_percent": round(100 * len(required & have_set) / len(required)),
        "you_have": sorted(required & have_set),
        "you_need_to_learn": to_learn,
        "also_in_demand": also[:5],
        "jobs_analyzed": n_jobs if use_market else 0,
    }

def available_roles():
    return sorted(ROLE_SKILLS)