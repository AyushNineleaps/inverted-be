from google import genai

from google.genai import types

from config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

from pydantic import BaseModel

class ResumeAnalysis(BaseModel):
    summary: str
    skills: list[str]
    feedback: str


def gemini_content_generator(file_path: str, mime_type: str):
    with open(file_path, 'rb') as f:
        file_bytes = f.read()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data = file_bytes,mime_type = mime_type),
            """You are a Senior Technical Recruiter and Talent Acquisition Strategist. 
            Analyze the attached resume objectively to provide high-signal, actionable feedback for the hiring manager and interview panel.

            Provide your analysis structured exactly against the required schema:
            1. SUMMARY: A dense, 3-4 sentence professional profile. Quantify impact where possible (e.g., years of experience, scale of systems managed). Absolutely zero generic corporate buzzwords.
            2. SKILLS: Categorized extraction of technical and soft skills. Only include skills backed by concrete evidence or projects in the text. Do not assume proficiency.
            3. FEEDBACK:  Focus on high-leverage achievements, scale handled, or unique domain expertise that makes this candidate stand out. Look for what is *missing* or weak based on their target level. Note short tenures, sudden role shifts, stagnant progression, lack of ownership metrics, or technologies listed but never applied in a project.
            """
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ResumeAnalysis,
        )
    )

    return response.parsed