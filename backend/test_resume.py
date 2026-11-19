from resume_parser import extract_text, clean_text, extract_skills

text = extract_text("backend/data/sample_resume.pdf")

print("----- First 500 characters -----")
print(clean_text(text)[:500])

print("\n----- Total words:", len(text.split()))

skills = extract_skills(text)
print("\n----- Skills found -----")
print(skills)