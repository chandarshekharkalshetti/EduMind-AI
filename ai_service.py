"""
Google Gemini AI Integration Service for EduMind AI.
Provides qualitative career guidance and personalized reasoning using Gemini API
with robust validation and seamless fallback to deterministic matching.
"""

import json
import logging
import os
import re
import requests
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"


def get_gemini_api_key():
    """Retrieve Google Gemini API key from environment variable."""
    return os.environ.get("GEMINI_API_KEY", "").strip()


def enhance_recommendations_with_gemini(student, candidate_careers):
    """
    Enhance candidate career matches with Gemini qualitative reasoning.
    If Gemini API key is missing or call fails, returns candidates unchanged
    with a transparent fallback notice.
    """
    api_key = get_gemini_api_key()
    if not api_key:
        logger.info("GEMINI_API_KEY not configured. Using deterministic recommendation output.")
        for career in candidate_careers:
            career["ai_analyzed"] = False
            career["ai_notice"] = "Algorithmic match score computed. Configure GEMINI_API_KEY for qualitative AI insights."
            career["ai_explanation"] = "Algorithmic match score computed from your skill and interest overlap."
        return candidate_careers

    # Format student profile safely
    student_summary = {
        "degree": student.get("degree", "Not specified"),
        "year": student.get("year", "Not specified"),
        "field_of_study": student.get("field_of_study", ""),
        "interests": student.get("interests", []),
        "programming": student.get("programming", []),
        "technical_skills": student.get("technical", []),
        "proficiency": student.get("proficiency", "Beginner"),
        "preferred_work": student.get("work", ""),
    }

    # Format candidate careers summary
    candidates_summary = []
    for c in candidate_careers:
        candidates_summary.append({
            "career_id": c.get("id", c.get("career_id", c.get("name", ""))),
            "title": c.get("title", c.get("name", "")),
            "category": c.get("category", ""),
            "algorithmic_match_score": c.get("match", 0),
            "matched_skills": c.get("matched_skills", []),
            "skills_to_learn": c.get("skills_to_learn", []),
        })

    prompt = f"""You are an expert career counselor and academic mentor for EduMind AI.
Analyze the following student profile against their top algorithmically matched career candidates.
Provide personalized, qualitative guidance for EACH career candidate.
DO NOT invent new careers outside this candidate list.
DO NOT alter the algorithmic match scores.

STUDENT PROFILE:
{json.dumps(student_summary, indent=2)}

CANDIDATE CAREERS:
{json.dumps(candidates_summary, indent=2)}

Respond with a valid JSON array where each object has:
- "career_id": string (must match one of the candidate career IDs)
- "why_it_fits": string (2-3 sentences explaining specifically why this suits their combination of interests and strengths)
- "key_strengths": array of strings (top 2-3 student strengths relevant to this role)
- "priority_missing_skills": array of strings (top 2-3 most critical skills the student should focus on learning first)
- "recommended_projects": array of strings (1-2 practical, resume-worthy project ideas)
- "tailored_advice": string (1-2 sentences of encouraging, actionable career preparation advice)

Format your response as pure JSON without markdown backticks or extra text.
"""

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 2048,
        }
    }

    try:
        response = requests.post(
            f"{GEMINI_API_URL}?key={api_key}",
            headers=headers,
            json=payload,
            timeout=12,
        )

        if response.status_code == 200:
            data = response.json()
            raw_text = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
                .strip()
            )

            # Strip markdown code blocks if returned
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                raw_text = re.sub(r"\s*```$", "", raw_text)

            ai_insights = json.loads(raw_text)
            insights_by_id = {}
            if isinstance(ai_insights, list):
                for item in ai_insights:
                    cid = item.get("career_id", "").strip().lower()
                    insights_by_id[cid] = item

            # Merge AI insights into candidate records
            for career in candidate_careers:
                cid = career.get("id", career.get("career_id", career.get("name", ""))).strip().lower()
                title_key = career.get("name", career.get("title", "")).strip().lower()

                insight = insights_by_id.get(cid) or insights_by_id.get(title_key)
                if insight:
                    career["ai_analyzed"] = True
                    career["ai_explanation"] = insight.get("why_it_fits", "")
                    career["ai_strengths"] = insight.get("key_strengths", [])
                    career["ai_priority_skills"] = insight.get("priority_missing_skills", [])
                    career["ai_projects"] = insight.get("recommended_projects", [])
                    career["ai_advice"] = insight.get("tailored_advice", "")
                else:
                    career["ai_analyzed"] = False
                    career["ai_explanation"] = "Algorithmic match based on skills and academic alignment."

            return candidate_careers

        else:
            logger.warning("Gemini API call failed with status %d: %s", response.status_code, response.text)

    except Exception as exc:
        logger.warning("Gemini API integration error: %s. Reverting to deterministic output.", exc)

    # Graceful fallback on any failure
    for career in candidate_careers:
        career["ai_analyzed"] = False
        career["ai_explanation"] = "Algorithmic match calculated from skill and interest compatibility."

    return candidate_careers
