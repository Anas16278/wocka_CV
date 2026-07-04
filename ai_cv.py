import os
import json
import requests
import subprocess
import tempfile

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "PASTE_YOUR_GROQ_KEY_HERE")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"

CANDIDATE_CV = """
NAME: Anas Ali
CONTACT: +44 7405716041 | anasalihooyo@gmail.com | London, Greater London

WORK EXPERIENCE:
Sales Associate – Asda, London | 2024 (1 Month)
- Worked on the shop floor in a busy environment, keeping up with a fast pace throughout each shift
- Restocked shelves and managed stock levels, making sure products were correctly placed and counted
- Helped customers find products and dealt with any questions or issues in a polite and friendly way
- Worked as part of a team and communicated well with colleagues to get tasks done efficiently
- Followed all health and safety rules and kept my work area clean and tidy at all times
- Handled deliveries and checked incoming stock against orders, developing accuracy under pressure

EDUCATION:
GCSEs 2024: Mathematics Grade 5, English Language Grade 5, English Literature Grade 5
Currently studying T-Level in Digital Production, Design and Development (Sixth Form)

SKILLS:
Good attention to detail, teamwork, time management, physical hands-on work, flexible shift patterns,
health and safety awareness, punctual and reliable, numeracy, digital/IT skills from T-Level study
"""

SYSTEM_PROMPT = """You are an expert CV writer. Given a candidate's CV and a job description, produce a tailored CV and cover letter as a JSON object.

RULES:
- Never invent qualifications or experience they don't have
- Do reframe and strengthen their real experience using the job's exact language
- Mirror keywords from the job description throughout
- Make their limited experience sound as strong and relevant as possible
- Personal statement must mention the specific role and company
- Cover letter must be warm, human, 4 paragraphs, not corporate-sounding
- Bullet points should be strong, start with action verbs, and directly reflect the job requirements

Return ONLY a valid JSON object with NO markdown, NO backticks, exactly this structure:
{
  "name": "Anas Ali",
  "phone": "+44 7405716041",
  "email": "anasalihooyo@gmail.com",
  "location": "London, Greater London",
  "personal_statement": "tailored personal statement here",
  "job_title": "exact job title from their CV (Sales Associate)",
  "company": "Asda",
  "duration": "2024 (1 Month)",
  "bullets": ["bullet 1", "bullet 2", "bullet 3", "bullet 4", "bullet 5", "bullet 6"],
  "skills": ["skill 1", "skill 2", "skill 3", "skill 4", "skill 5", "skill 6", "skill 7", "skill 8"],
  "cover_letter": "full cover letter with paragraphs separated by double newlines"
}"""


def tailor_cv(job_description: str) -> dict:
    prompt = f"""Candidate CV:
{CANDIDATE_CV}

Job Description:
{job_description}

Tailor this candidate's CV for this specific job. Return JSON only."""

    response = requests.post(
        GROQ_URL,
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 3000,
            "temperature": 0.7,
        },
        timeout=60,
    )

    data = response.json()
    if "error" in data:
        raise Exception(data["error"].get("message", "Groq error"))

    raw = data["choices"][0]["message"]["content"].strip()

    # Strip markdown fences if present
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


def generate_docx(cv_data: dict) -> tuple[str, str]:
    """Call the Node.js script to generate both docx files, return their paths"""
    json_str = json.dumps(cv_data)
    result = subprocess.run(
        ["node", "generate_cv.js", json_str],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        raise Exception(f"DOCX generation failed: {result.stderr}")

    return "/tmp/tailored_cv.docx", "/tmp/cover_letter.docx"
