import re
from pathlib import Path

import pandas as pd
import pdfplumber
import docx

DATA_DIR = Path(__file__).parent / "data"


# ---------- 1. Read the file ----------
def extract_text(file_path):
    file_path = str(file_path)
    if file_path.lower().endswith(".pdf"):
        with pdfplumber.open(file_path) as pdf:
            return " ".join(page.extract_text() or "" for page in pdf.pages)
    elif file_path.lower().endswith(".docx"):
        d = docx.Document(file_path)
        return " ".join(p.text for p in d.paragraphs)
    else:
        raise ValueError("Only PDF and DOCX files are supported")


# ---------- 2. Clean the text ----------
def clean_text(text):
    text = text.lower()
    text = re.sub(r"\s+", " ", text)   # many spaces/new lines -> one space
    return text.strip()


# ---------- 3. Load the skills list ----------
def load_skill_map():
    """Returns a dictionary like {'reactjs': 'react.js', 'react.js': 'react.js', ...}"""
    df = pd.read_csv(DATA_DIR / "skills.csv").fillna("")
    skill_map = {}
    for _, row in df.iterrows():
        main = row["skill"].strip().lower()
        if not main:
            continue
        skill_map[main] = main
        for alias in row["aliases"].split("|"):
            alias = alias.strip().lower()
            if alias:
                skill_map[alias] = main
    return skill_map


SKILL_MAP = load_skill_map()


# ---------- 4. Find skills in the text ----------
def extract_skills(text):
    text = clean_text(text)
    found = set()
    for phrase, main_skill in SKILL_MAP.items():
        # The phrase must not be stuck to other letters/digits/+/#
        pattern = r"(?<![a-z0-9+#])" + re.escape(phrase) + r"(?![a-z0-9+#])"
        if re.search(pattern, text):
            found.add(main_skill)
    return sorted(found)