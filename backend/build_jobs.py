import pandas as pd
from pathlib import Path

RAW = Path("backend/data/raw")
OUT = Path("backend/data/jobs.csv")

# 1. Main job postings (only the columns we need)
postings = pd.read_csv(
    RAW / "postings.csv",
    usecols=[
        "job_id", "title", "company_name", "location", "description",
        "skills_desc", "formatted_experience_level",
        "formatted_work_type", "job_posting_url",
    ],
)

# 2. Skill names for each job
job_skills = pd.read_csv(RAW / "job_skills.csv")
skill_names = pd.read_csv(RAW / "skills.csv")
job_skills = job_skills.merge(skill_names, on="skill_abr", how="left")
skills = (
    job_skills.groupby("job_id")["skill_name"]
    .apply(lambda s: ", ".join(s.dropna().unique()))
    .reset_index()
    .rename(columns={"skill_name": "skills"})
)

# 3. Combine and tidy
df = postings.merge(skills, on="job_id", how="left")
df = df.rename(columns={
    "title": "job_title",
    "company_name": "company",
    "description": "job_description",
})
df = df.dropna(subset=["job_title", "job_description"])
df["skills"] = df["skills"].fillna("")

# 4. Keep a random 5,000 jobs so the file stays small
df = df.sample(n=min(5000, len(df)), random_state=42)
df.to_csv(OUT, index=False)

print("Saved", OUT, "with", len(df), "jobs")
print(df[["job_title", "company", "location"]].head())