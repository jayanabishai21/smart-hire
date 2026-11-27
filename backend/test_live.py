import live_jobs

if not live_jobs.live_jobs_available():
    raise SystemExit("No JOOBLE_API_KEY found. Add it to the .env file in the smart-hire folder.")

jobs = live_jobs.search_live_jobs("python developer", "Chennai", limit=5)
print("Jobs returned:", len(jobs))
for j in jobs:
    print("-", j["title"], "|", j["company"], "|", j["location"])

if not jobs:
    print("Reason:", live_jobs.LAST_ERROR or "Jooble found no matching jobs")