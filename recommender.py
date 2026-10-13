
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
