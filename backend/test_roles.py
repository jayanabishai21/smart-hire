from resume_parser import extract_text
from role_model import predict_roles

text = extract_text("backend/data/sample_resume.pdf")
for r in predict_roles(text):
    print(r)