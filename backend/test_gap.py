from resume_parser import extract_text, extract_skills
from skill_gap import skill_gap, available_roles

print("Roles available:", available_roles())

text = extract_text("backend/data/sample_resume.pdf")
skills = extract_skills(text)
print("Your skills:", skills)

result = skill_gap(skills, "Frontend Developer")   # change the role to test others

print(f"\nRole: {result['role']}   Match: {result['match_percent']}%")
print("You have:", result["you_have"])
print("\nYou need to learn:")
for item in result["you_need_to_learn"]:
    imp = item["importance_percent"]
    note = f"  (asked in {imp}% of jobs)" if imp is not None else ""
    print(" -", item["skill"], note)
    for link in item["learn"]:
        print("     ", link["name"], ":", link["url"])

if result["also_in_demand"]:
    print("\nAlso in demand:", [x["skill"] for x in result["also_in_demand"]])
print("\nJobs analyzed:", result["jobs_analyzed"])