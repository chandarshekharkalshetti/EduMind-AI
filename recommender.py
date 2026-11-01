
CAREERS = {
    "Python Developer": {
        "interests": ["Software", "AI", "Data"],
        "programming": ["Python"],
        "technical": ["SQL", "Git"],
        "work": ["Coding"],
        "skills": ["Python", "SQL", "Git"],
    },
    "Web Developer": {
        "interests": ["Web", "Software"],
        "programming": ["JavaScript", "Python", "Java"],
        "technical": ["HTMLCSS", "Git"],
        "work": ["Design", "Coding"],
        "skills": ["HTML/CSS", "JavaScript", "Git"],
    },
    "Data Analyst": {
        "interests": ["Data", "AI"],
        "programming": ["Python"],
        "technical": ["SQL", "Statistics", "DataViz"],
        "work": ["Data"],
        "skills": ["SQL", "Statistics", "Data Visualization"],
    },
    "Data Scientist": {
        "interests": ["Data", "AI"],
        "programming": ["Python"],
        "technical": ["SQL", "Statistics", "ML", "DataViz"],
        "work": ["Data", "AI"],
        "skills": ["Python", "Statistics", "Machine Learning"],
    },
    "AI/ML Engineer": {
        "interests": ["AI", "Data", "Software"],
        "programming": ["Python", "C++"],
        "technical": ["ML", "Statistics"],
        "work": ["AI", "Coding"],
        "skills": ["Python", "Machine Learning", "Statistics"],
    },
    "Software Tester / QA Engineer": {
        "interests": ["Testing", "Software"],
        "programming": ["Python", "Java"],
        "technical": ["SQL", "Git"],
        "work": ["Testing"],
        "skills": ["Testing", "SQL", "Git"],
    },
}


# Weights total 100%.
WEIGHTS = {
    "interests": 30,
    "programming": 25,
    "technical": 25,
    "work": 10,
    "proficiency": 10,
}


def _overlap_score(selected, required):
    """Return the fraction of required options that were selected."""
    if not required:
        return 0.0

    return len(set(selected).intersection(required)) / len(required)


def recommend_careers(student):
    """
    Rank careers using a transparent, rule-based scoring system.

    Expected student fields:
        interests: list[str]
        programming: list[str]
        technical: list[str]
        work: str
        proficiency: Beginner, Intermediate, or Advanced

    Returns the top three careers with scores, reasons, and skill gaps.
    These scores are not ML probabilities.
    """
    interests = set(student.get("interests", []))
    programming = set(student.get("programming", []))
    technical = set(student.get("technical", []))
    work = student.get("work", "")
    proficiency = student.get("proficiency", "Beginner")

    # Normalize the proficiency input safely.
    proficiency_levels = {
        "beginner": 0,
        "intermediate": 1,
        "advanced": 2,
    }
    proficiency_key = str(proficiency).strip().lower()
    proficiency_level = proficiency_levels.get(proficiency_key, 0)

    scores = []

    for career, requirements in CAREERS.items():
        matched_interests = interests.intersection(
            requirements["interests"]
        )
        matched_programming = programming.intersection(
            requirements["programming"]
        )
        matched_technical = technical.intersection(
            requirements["technical"]
        )
        matched_work = (
            {work}.intersection(requirements["work"])
            if work else set()
        )

        # Normalize each category so careers with more listed
        # requirements are not automatically penalized.
        interest_score = _overlap_score(
            matched_interests, requirements["interests"]
        )
        programming_score = _overlap_score(
            matched_programming, requirements["programming"]
        )
        technical_score = _overlap_score(
            matched_technical, requirements["technical"]
        )
        work_score = _overlap_score(
            matched_work, requirements["work"]
        )

        # Proficiency is a small, transparent modifier.
        # It does not claim that the student has more skills.
        proficiency_score = proficiency_level / 2

        match = round(
            WEIGHTS["interests"] * interest_score
            + WEIGHTS["programming"] * programming_score
            + WEIGHTS["technical"] * technical_score
            + WEIGHTS["work"] * work_score
            + WEIGHTS["proficiency"] * proficiency_score
        )

        # Explain the actual areas of overlap.
        reasons = []

        if matched_interests:
            reasons.append(
                "Your interests match: "
                + ", ".join(sorted(matched_interests))
            )

        if matched_programming:
            reasons.append(
                "Relevant programming knowledge: "
                + ", ".join(sorted(matched_programming))
            )

        if matched_technical:
            reasons.append(
                "Relevant technical skills: "
                + ", ".join(sorted(matched_technical))
            )

        if matched_work:
            reasons.append(
                "Your preferred work matches: "
                + ", ".join(sorted(matched_work))
            )

        if proficiency_key in proficiency_levels:
            reasons.append(
                "Self-reported proficiency: "
                + proficiency_key.title()
            )

        if not reasons:
            reasons.append(
                "Your selected interests and skills have limited "
                "overlap with this career's listed requirements."
            )

        # Convert form values to the display names used by CAREERS.
        selected_skills = set()

        programming_display = {
            "Python": "Python",
            "JavaScript": "JavaScript",
            "Java": "Java",
            "C++": "C++",
        }

        technical_display = {
            "SQL": "SQL",
            "Git": "Git",
            "HTMLCSS": "HTML/CSS",
            "Statistics": "Statistics",
            "ML": "Machine Learning",
            "DataViz": "Data Visualization",
        }

        for value in programming:
            if value in programming_display:
                selected_skills.add(programming_display[value])

        for value in technical:
            if value in technical_display:
                selected_skills.add(technical_display[value])

        # Preserve the existing career skills field for results.html.
        career_skills = requirements["skills"]

        matched_skills = [
            skill for skill in career_skills
            if skill in selected_skills
        ]

        skills_to_learn = [
            skill for skill in career_skills
            if skill not in selected_skills
        ]

        scores.append({
            "name": career,
            "match": match,
            "skills": career_skills,
            "reasons": reasons,
            "matched_skills": matched_skills,
            "skills_to_learn": skills_to_learn,
        })

    # Python's sort is stable, so ties preserve CAREERS order.
    scores.sort(
        key=lambda item: item["match"],
        reverse=True
    )

    return scores[:3]


def recommend_global_careers(student, catalog_careers=None, top_k=5):
    """
    Match student profile against the comprehensive 22-category global career catalog.
    Uses transparent, deterministic multi-dimensional scoring (Interests, Skills,
    Work Style, Academic Background, and Proficiency).

    Returns top candidate careers with match scores, transparent explanations,
    matched skills, and skills to learn next.
    """
    import careers_catalog

    if catalog_careers is None:
        catalog_careers = careers_catalog.get_all_careers()

    if not catalog_careers:
        # Fallback to the 6 tech careers if database catalog is empty
        return recommend_careers(student)

    # Normalize student inputs
    degree = str(student.get("degree", "")).strip().lower()
    field_of_study = str(student.get("field_of_study", "")).strip().lower()
    interests = set(str(i).strip().lower() for i in student.get("interests", []))
    programming = set(str(p).strip() for p in student.get("programming", []))
    technical = set(str(t).strip() for t in student.get("technical", []))
    work = str(student.get("work", "")).strip().lower()
    proficiency = str(student.get("proficiency", "Beginner")).strip().lower()

    # Combine all student skills
    selected_skills = set()
    for p in programming:
        selected_skills.add(p.lower())
    for t in technical:
        selected_skills.add(t.lower())
        if t.lower() == "htmlcss":
            selected_skills.add("html5")
            selected_skills.add("css3")
            selected_skills.add("html/css")
        elif t.lower() == "ml":
            selected_skills.add("machine learning")
            selected_skills.add("scikit-learn")
        elif t.lower() == "dataviz":
            selected_skills.add("data visualization")
            selected_skills.add("power bi / tableau")

    proficiency_levels = {"beginner": 0, "intermediate": 1, "advanced": 2}
    prof_mod = proficiency_levels.get(proficiency, 0) / 2  # 0.0, 0.5, 1.0

    scores = []

    for career in catalog_careers:
        c_title = career["title"]
        c_cat = career["category"].lower()
        c_ind = career["industry"].lower()
        c_desc = career["description"].lower()
        c_skills = career["technical_skills"]
        c_skills_lower = [s.lower() for s in c_skills]

        # 1. Interests Score (30%)
        interest_matches = []
        interest_weight = 30
        for interest in interests:
            if (interest in c_cat) or (interest in c_ind) or (interest in c_desc) or (interest in c_title.lower()):
                interest_matches.append(interest.title())

        interest_score = min(len(interest_matches) / max(len(interests), 1), 1.0) if interests else 0.2

        # 2. Skills Match (35%)
        matched_skills_display = []
        skills_to_learn_display = []

        for skill, skill_lower in zip(c_skills, c_skills_lower):
            matched = False
            for user_skill in selected_skills:
                if user_skill in skill_lower or skill_lower in user_skill:
                    matched = True
                    break
            if matched:
                matched_skills_display.append(skill)
            else:
                skills_to_learn_display.append(skill)

        skill_overlap_ratio = len(matched_skills_display) / max(len(c_skills), 1) if c_skills else 0.0
        skill_score = skill_overlap_ratio * 35

        # 3. Preferred Work Match (15%)
        work_score = 0
        work_match_note = None
        if work:
            work_keywords = {
                "coding": ["software", "developer", "engineer", "python", "programming", "devops", "cloud"],
                "data": ["data", "analytics", "analyst", "scientist", "statistics", "business intelligence"],
                "ai": ["ai", "machine learning", "nlp", "artificial intelligence", "deep learning"],
                "testing": ["tester", "qa", "quality assurance", "testing"],
                "design": ["design", "ui", "ux", "architect", "creative", "web developer", "content"],
                "management": ["manager", "hr", "business", "supply chain", "hotel", "consultant"],
                "healthcare": ["doctor", "physician", "pharmacist", "nurse", "medical", "health"],
                "finance": ["accountant", "financial", "auditor", "finance", "banker"],
                "research": ["scientist", "researcher", "professor", "biotechnology"],
            }
            target_words = work_keywords.get(work, [work])
            for word in target_words:
                if word in c_title.lower() or word in c_desc or word in c_cat:
                    work_score = 15
                    work_match_note = f"Matches your preferred focus on {work.title()}"
                    break

        # 4. Degree & Academic Background (10%)
        academic_score = 0
        if degree:
            if degree in ["b.tech", "mca", "bca", "m.tech"] and ("software" in c_cat or "ai" in c_cat or "data" in c_cat or "engineering" in c_cat or "cyber" in c_cat):
                academic_score = 10
            elif degree in ["b.com", "mba", "bba"] and ("commerce" in c_cat or "business" in c_cat or "finance" in c_cat or "logistics" in c_cat):
                academic_score = 10
            elif degree in ["mbbs", "b.pharm"] and ("medical" in c_cat or "healthcare" in c_cat):
                academic_score = 10
            elif degree in ["llb"] and "law" in c_cat:
                academic_score = 10
            elif degree in ["b.sc"] and ("science" in c_cat or "data" in c_cat or "software" in c_cat or "environment" in c_cat or "agri" in c_cat):
                academic_score = 10
            elif degree in ["ba"] and ("media" in c_cat or "creative" in c_cat or "education" in c_cat or "government" in c_cat):
                academic_score = 10
            else:
                academic_score = 5

        # 5. Proficiency Bonus (10%)
        prof_score = prof_mod * 10

        # Total Match Percentage
        total_match = round(
            (interest_score * interest_weight)
            + skill_score
            + work_score
            + academic_score
            + prof_score
        )
        total_match = max(0, min(total_match, 98))  # Cap at 98% to represent transparent recommendation

        # Generate transparent reasons
        reasons = []
        if interest_matches:
            reasons.append(f"Field interests aligned: {', '.join(interest_matches)}")
        if matched_skills_display:
            reasons.append(f"Existing skill foundation: {', '.join(matched_skills_display[:3])}")
        if work_match_note:
            reasons.append(work_match_note)
        if academic_score >= 10:
            reasons.append(f"Well-suited to your academic program ({degree.upper()})")
        if not reasons:
            reasons.append("Exploratory career match with transferrable potential based on your responses.")

        scores.append({
            "id": career["id"],
            "career_id": career["id"],
            "name": career["title"],
            "title": career["title"],
            "category": career["category"],
            "industry": career["industry"],
            "minimum_education": career["minimum_education"],
            "description": career["description"],
            "match": total_match,
            "skills": c_skills,
            "matched_skills": matched_skills_display,
            "skills_to_learn": skills_to_learn_display[:5],
            "reasons": reasons,
            "courses": career.get("courses", []),
            "certifications": career.get("certifications", []),
            "progression": career.get("progression", []),
            "learning_difficulty": career.get("learning_difficulty", "Moderate"),
        })

    scores.sort(key=lambda item: item["match"], reverse=True)
    return scores[:top_k]

