import sys
from pathlib import Path

import numpy as np
import pandas as pd

from resume_parser import extract_skills

DATA_DIR = Path(__file__).parent / "data"
JOBS_FILE = DATA_DIR / "jobs.csv"
INDEX_FILE = DATA_DIR / "jobs_index.pkl"     # saved job table
EMB_FILE = DATA_DIR / "job_embeddings.npy"   # saved job "meaning numbers"

MODEL_NAME = "all-MiniLM-L6-v2"
_model = None


def get_model():
    """Load the embedding model only once (it is slow to load)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
    return _model


# ---------- 1. Build the job index (run ONCE) ----------
def build_job_index():
    df = pd.read_csv(JOBS_FILE).drop_duplicates(subset="job_id").reset_index(drop=True)
    df["job_title"] = df["job_title"].fillna("").str.strip()
    df["job_description"] = df["job_description"].fillna("")
    df["company"] = df["company"].fillna("Company not listed")

    print("Finding skills in each job (about 20-60 seconds)...")
    df["job_skills"] = (df["job_title"] + " " + df["job_description"]).apply(extract_skills)

    # Keep only jobs that mention at least 2 tech skills from skills.csv
    df = df[df["job_skills"].str.len() >= 2].reset_index(drop=True)
    print("Tech jobs kept:", len(df))

    # Text that represents each job: title + skills + start of description
    texts = (df["job_title"] + ". Skills: " + df["job_skills"].apply(", ".join)
             + ". " + df["job_description"].str[:1000]).tolist()

    print("Creating embeddings (a few minutes the first time)...")
    embs = get_model().encode(texts, batch_size=32, show_progress_bar=True,
                              normalize_embeddings=True)

    df.to_pickle(INDEX_FILE)
    np.save(EMB_FILE, embs)
    print("Done! Saved the job index.")


# ---------- 2. Load the saved index ----------
_jobs = None
_job_embs = None


def load_index():
    global _jobs, _job_embs
    if _jobs is None:
        if not INDEX_FILE.exists():
            raise FileNotFoundError(
                "Job index not found. Run:  python backend/job_matcher.py build")
        _jobs = pd.read_pickle(INDEX_FILE)
        _job_embs = np.load(EMB_FILE)
    return _jobs, _job_embs


# ---------- 3. Match a resume to the jobs ----------
def match_jobs(resume_text, top_n=10):
    jobs, job_embs = load_index()
    resume_skills = extract_skills(resume_text)

    # The model reads only about the first 200 words, so we put the skills FIRST
    query = "Skills: " + ", ".join(resume_skills) + ". " + resume_text[:1000]
    resume_emb = get_model().encode(query, normalize_embeddings=True)

    # Score 1: similarity of meaning (0 to 1)
    cos = job_embs @ resume_emb
    meaning_score = np.clip((cos - 0.15) / 0.45, 0, 1)

    # Score 2: how many of the job's skills does the resume already have?
    resume_set = set(resume_skills)
    overlap, have_list, learn_list = [], [], []
    for job_skills in jobs["job_skills"]:
        job_set = set(job_skills)
        have = job_set & resume_set
        overlap.append(len(have) / len(job_set) if job_set else 0)
        have_list.append(sorted(have))
        learn_list.append(sorted(job_set - resume_set))
    overlap = np.array(overlap)

    # Final score = 60% meaning + 40% skills
    final = 0.6 * meaning_score + 0.4 * overlap

    results = []
    for i in np.argsort(final)[::-1][:top_n]:
        row = jobs.iloc[i]
        results.append({
            "title": row["job_title"],
            "company": row["company"],
            "location": row["location"],
            "work_type": row["formatted_work_type"],
            "experience_level": row["formatted_experience_level"]
                                if pd.notna(row["formatted_experience_level"]) else "Not listed",
            "url": row["job_posting_url"],
            "match_percent": int(round(final[i] * 100)),
            "skills_you_have": have_list[i],
            "skills_to_learn": learn_list[i],
        })
    return results


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        build_job_index()
    else:
        print("Run:  python backend/job_matcher.py build")