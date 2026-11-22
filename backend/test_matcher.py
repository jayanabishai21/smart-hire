from resume_parser import extract_text
from role_matcher import recommend_roles

text = extract_text("backend/data/sample_resume.pdf")
result = recommend_roles(text)

print("Skills found:", result["skills_found"])
print()
for r in result["roles"]:
    print(f"{r['role']}: {r['final_score']}%  (skills {r['skill_score']}%, ML {r['ml_score']}%)")
    print("   Have   :", r["matched_skills"])
    print("   Missing:", r["missing_skills"])