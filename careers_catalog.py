"""
Career Catalog service module for EduMind AI.
Provides query, search, filtering, comparison, and dynamic roadmap generation
for all global careers stored in the SQLite database and JSON catalog.
"""

import json
from pathlib import Path
import database

DATA_FILE = Path(__file__).parent / "data" / "careers_data.json"


def _row_to_career(row):
    """Convert an SQLite Row from career_catalog into a clean Python dictionary."""
    if not row:
        return None
    return {
        "id": row["id"],
        "title": row["title"],
        "category": row["category"],
        "industry": row["industry"] or "",
        "minimum_education": row["minimum_education"] or "",
        "recommended_qualifications": row["recommended_qualifications"] or "",
        "description": row["description"] or "",
        "responsibilities": json.loads(row["responsibilities_json"] or "[]"),
        "technical_skills": json.loads(row["technical_skills_json"] or "[]"),
        "soft_skills": json.loads(row["soft_skills_json"] or "[]"),
        "courses": json.loads(row["courses_json"] or "[]"),
        "certifications": json.loads(row["certifications_json"] or "[]"),
        "entrance_exams": json.loads(row["entrance_exams_json"] or "[]"),
        "job_opportunities": json.loads(row["job_opportunities_json"] or "[]"),
        "related_titles": json.loads(row["related_titles_json"] or "[]"),
        "progression": json.loads(row["progression_json"] or "[]"),
        "industry_sectors": json.loads(row["industry_sectors_json"] or "[]"),
        "learning_difficulty": row["learning_difficulty"] or "Moderate",
    }


def get_all_careers():
    """Retrieve all careers from database."""
    conn = database.get_db()
    try:
        rows = conn.execute("SELECT * FROM career_catalog ORDER BY title ASC").fetchall()
        return [_row_to_career(r) for r in rows]
    finally:
        conn.close()


def get_career_by_id(career_id):
    """Fetch a career by its unique ID (or fallback to matching by title)."""
    if not career_id:
        return None
    clean_id = career_id.strip().lower().replace(" ", "-")
    conn = database.get_db()
    try:
        row = conn.execute("SELECT * FROM career_catalog WHERE id = ?", (clean_id,)).fetchone()
        if not row:
            # Fallback check by title
            row = conn.execute(
                "SELECT * FROM career_catalog WHERE LOWER(title) = ?",
                (career_id.strip().lower(),)
            ).fetchone()
        return _row_to_career(row)
    finally:
        conn.close()


def get_all_categories():
    """Retrieve list of distinct career categories."""
    conn = database.get_db()
    try:
        rows = conn.execute(
            "SELECT DISTINCT category FROM career_catalog ORDER BY category ASC"
        ).fetchall()
        return [r["category"] for r in rows if r["category"]]
    finally:
        conn.close()


def get_all_difficulties():
    """Return available learning difficulty levels."""
    return ["Beginner", "Moderate", "Challenging", "Advanced"]


def get_all_educations():
    """Return distinct education levels."""
    conn = database.get_db()
    try:
        rows = conn.execute(
            "SELECT DISTINCT minimum_education FROM career_catalog WHERE minimum_education != '' ORDER BY minimum_education ASC"
        ).fetchall()
        return [r["minimum_education"] for r in rows]
    finally:
        conn.close()


def get_filtered_careers(query="", category="", difficulty="", education="", sort_by="title"):
    """
    Search and filter careers with multi-parameter facets.
    Supports search query over title, description, skills, and industry.
    """
    all_careers = get_all_careers()

    filtered = []
    q = query.strip().lower()
    cat = category.strip().lower()
    diff = difficulty.strip().lower()
    edu = education.strip().lower()

    for c in all_careers:
        # Category filter
        if cat and c["category"].lower() != cat:
            continue

        # Difficulty filter
        if diff and c["learning_difficulty"].lower() != diff:
            continue

        # Education filter
        if edu and edu not in c["minimum_education"].lower():
            continue

        # Keyword search across title, description, skills, category, and industry
        if q:
            searchable_text = " ".join([
                c["title"],
                c["category"],
                c["industry"],
                c["description"],
                " ".join(c["technical_skills"]),
                " ".join(c["soft_skills"]),
                " ".join(c["related_titles"]),
            ]).lower()

            if q not in searchable_text:
                continue

        filtered.append(c)

    # Sorting
    if sort_by == "title":
        filtered.sort(key=lambda x: x["title"].lower())
    elif sort_by == "title_desc":
        filtered.sort(key=lambda x: x["title"].lower(), reverse=True)
    elif sort_by == "category":
        filtered.sort(key=lambda x: (x["category"].lower(), x["title"].lower()))
    elif sort_by == "difficulty":
        diff_order = {"beginner": 1, "moderate": 2, "challenging": 3, "advanced": 4}
        filtered.sort(key=lambda x: diff_order.get(x["learning_difficulty"].lower(), 2))

    categories = get_all_categories()
    difficulties = get_all_difficulties()
    educations = get_all_educations()

    return filtered, categories, difficulties, educations


def get_related_careers(career_id, limit=3):
    """Find related careers sharing the same category or overlapping technical skills."""
    career = get_career_by_id(career_id)
    if not career:
        return []

    all_careers = get_all_careers()
    career_skills = set(s.lower() for s in career["technical_skills"])

    scored_relatives = []
    for other in all_careers:
        if other["id"] == career["id"]:
            continue

        score = 0
        # Category match
        if other["category"] == career["category"]:
            score += 5

        # Skill overlap
        other_skills = set(s.lower() for s in other["technical_skills"])
        overlap = len(career_skills.intersection(other_skills))
        score += overlap * 2

        if score > 0:
            scored_relatives.append((score, other))

    scored_relatives.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored_relatives[:limit]]


def get_career_roadmap(career_id_or_title, duration_months=6):
    """
    Return dynamic, personalized roadmap stages for any career in the catalog.
    Adapts according to requested duration (3, 6, or 12 months).
    """
    career = get_career_by_id(career_id_or_title)

    # If career exists in JSON seed with defined roadmap_stages, use them as base
    base_stages = None
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                json_data = json.load(f)
                for item in json_data:
                    if item["id"] == (career["id"] if career else "") or item["title"].lower() == str(career_id_or_title).lower():
                        base_stages = item.get("roadmap_stages")
                        break
        except Exception:
            pass

    if not career:
        # Fallback to general tech career
        career_title = str(career_id_or_title).title()
        category = "General Professional Field"
        description = f"Structured development path for {career_title}."
    else:
        career_title = career["title"]
        category = career["category"]
        description = career["description"]

    # Adapt stages based on duration
    duration = int(duration_months)
    if duration <= 3:
        duration_label = "3-Month Accelerated Track"
        time_chunks = ["Month 1", "Month 2", "Month 3"]
    elif duration >= 12:
        duration_label = "12-Month In-Depth Mastery Track"
        time_chunks = ["Months 1-4", "Months 5-8", "Months 9-12"]
    else:
        duration_label = "6-Month Comprehensive Track"
        time_chunks = ["Months 1-2", "Months 3-4", "Months 5-6"]

    if base_stages and len(base_stages) == 3:
        stages = [
            {
                "stage_number": 1,
                "label": "STAGE 01",
                "title": f"Fundamentals & Core Knowledge ({time_chunks[0]})",
                "duration": time_chunks[0],
                "topics": base_stages[0].get("topics", [
                    "Core domain principles",
                    "Essential toolchains & standards",
                    "Fundamental workflows"
                ]),
                "project": base_stages[0].get("project", f"{career_title} Baseline Project"),
            },
            {
                "stage_number": 2,
                "label": "STAGE 02",
                "title": f"Applied Execution & Intermediate Skills ({time_chunks[1]})",
                "duration": time_chunks[1],
                "topics": base_stages[1].get("topics", [
                    "Intermediate methods",
                    "Industry standard software / frameworks",
                    "Quality validation and analysis"
                ]),
                "project": base_stages[1].get("project", f"{career_title} Practical Implementation Project"),
            },
            {
                "stage_number": 3,
                "label": "STAGE 03",
                "title": f"Portfolio, Certifications & Career Readiness ({time_chunks[2]})",
                "duration": time_chunks[2],
                "topics": base_stages[2].get("topics", [
                    "Advanced domain problem solving",
                    "Professional portfolio presentation",
                    "Interview and industry readiness"
                ]),
                "project": base_stages[2].get("project", f"Capstoned {career_title} Portfolio Showcase"),
            },
        ]
    else:
        # Synthesize from skills and courses
        tech_skills = career["technical_skills"] if career else ["Core Principles", "Industry Tools"]
        soft_skills = career["soft_skills"] if career else ["Problem Solving", "Communication"]
        courses = career["courses"] if career else ["Professional Specialization Course"]

        stages = [
            {
                "stage_number": 1,
                "label": "STAGE 01",
                "title": f"Foundational Competencies ({time_chunks[0]})",
                "duration": time_chunks[0],
                "topics": [
                    f"Introduction to {career_title} and industry context",
                    f"Core foundational concepts: {', '.join(tech_skills[:2]) if tech_skills else 'Domain basics'}",
                    f"Recommended course study: {courses[0] if courses else 'Fundamental Domain Training'}",
                    "Foundational practical exercises and workflow mastery"
                ],
                "project": f"{career_title} Discovery & Fundamental Practice Project",
            },
            {
                "stage_number": 2,
                "label": "STAGE 02",
                "title": f"Technical Application & Process Mastery ({time_chunks[1]})",
                "duration": time_chunks[1],
                "topics": [
                    f"Advanced domain techniques: {', '.join(tech_skills[2:5]) if len(tech_skills) > 2 else 'Applied practices'}",
                    f"Key soft skills development: {', '.join(soft_skills[:2]) if soft_skills else 'Teamwork & Communication'}",
                    "Simulated industry case studies and real-world scenarios",
                    "Quality review, regulatory compliance, and standards"
                ],
                "project": f"{career_title} Comprehensive Application Project",
            },
            {
                "stage_number": 3,
                "label": "STAGE 03",
                "title": f"Professional Portfolio & Interview Readiness ({time_chunks[2]})",
                "duration": time_chunks[2],
                "topics": [
                    f"Certification preparation: {', '.join(career['certifications'][:2]) if career and career['certifications'] else 'Recognized professional credentials'}",
                    "Portfolio compilation, resume optimization, and LinkedIn presence",
                    "Mock technical interviews and situational problem solving",
                    "Internship and entry-level job applications strategy"
                ],
                "project": f"Production-Grade {career_title} Portfolio Case Study",
            },
        ]

    return {
        "career_id": career["id"] if career else career_id_or_title,
        "career_title": career_title,
        "category": category,
        "description": description,
        "duration_months": duration,
        "duration_label": duration_label,
        "stages": stages,
    }
