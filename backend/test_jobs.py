from resume_parser import extract_text
from job_matcher import match_jobs

text = extract_text("backend/data/sample_resume.pdf")

for job in match_jobs(text, top_n=5):
    print(f"{job['match_percent']}%  {job['title']}  at  {job['company']}  ({job['location']})")
    print("   Have :", job["skills_you_have"])
    print("   Learn:", job["skills_to_learn"])
    print("   Apply:", job["url"])
    print()