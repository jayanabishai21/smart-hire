import pandas as pd

jobs = pd.read_csv("backend/data/jobs.csv")
print(jobs.shape)
print(jobs.columns.tolist())
print(jobs[["job_title", "company", "location", "skills"]].head(3))