"""
Database module for EduMind AI.
Provides SQLite connection management, schema initialization, and parameterized data access helpers.
"""

import json
import os
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

import firebase_db

DB_PATH = Path(os.environ.get("DATABASE_PATH", Path(__file__).parent / "data" / "edumind.db"))


def is_cloud_mode():
    """Return True if Firebase Firestore is configured and connected."""
    return firebase_db.is_firebase_configured() and firebase_db.get_firestore_client() is not None


def get_active_db_type():
    """Return active database engine name."""
    return "Firebase Firestore (Cloud)" if is_cloud_mode() else "SQLite (Local)"


def get_db():
    """Establish a database connection with row factory and foreign keys enabled."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Create all relational tables and indexes if they do not exist. Also initializes Firestore if configured."""
    if is_cloud_mode():
        firebase_db.init_firestore()

    conn = get_db()
    with conn:
        conn.executescript("""
            -- Users Table
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Student Profiles Table
            CREATE TABLE IF NOT EXISTS student_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                degree TEXT DEFAULT '',
                field_of_study TEXT DEFAULT '',
                current_year TEXT DEFAULT '',
                institution TEXT DEFAULT '',
                country TEXT DEFAULT '',
                bio TEXT DEFAULT '',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Global Career Catalog Table
            CREATE TABLE IF NOT EXISTS career_catalog (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                industry TEXT DEFAULT '',
                minimum_education TEXT DEFAULT '',
                recommended_qualifications TEXT DEFAULT '',
                description TEXT DEFAULT '',
                responsibilities_json TEXT DEFAULT '[]',
                technical_skills_json TEXT DEFAULT '[]',
                soft_skills_json TEXT DEFAULT '[]',
                courses_json TEXT DEFAULT '[]',
                certifications_json TEXT DEFAULT '[]',
                entrance_exams_json TEXT DEFAULT '[]',
                job_opportunities_json TEXT DEFAULT '[]',
                related_titles_json TEXT DEFAULT '[]',
                progression_json TEXT DEFAULT '[]',
                industry_sectors_json TEXT DEFAULT '[]',
                learning_difficulty TEXT DEFAULT 'Moderate',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Career Assessments History Table
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                input_data_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Career Recommendations Table
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assessment_id INTEGER NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
                career_id TEXT NOT NULL,
                career_title TEXT NOT NULL,
                match_score INTEGER NOT NULL,
                match_reasons_json TEXT DEFAULT '[]',
                matched_skills_json TEXT DEFAULT '[]',
                skills_to_learn_json TEXT DEFAULT '[]',
                ai_explanation TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Saved Careers (Bookmarks) Table
            CREATE TABLE IF NOT EXISTS saved_careers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                career_id TEXT NOT NULL REFERENCES career_catalog(id) ON DELETE CASCADE,
                notes TEXT DEFAULT '',
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, career_id)
            );

            -- Personalized Learning Roadmaps Table
            CREATE TABLE IF NOT EXISTS learning_roadmaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                career_id TEXT NOT NULL REFERENCES career_catalog(id) ON DELETE CASCADE,
                duration_months INTEGER DEFAULT 6,
                stages_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Indexes for fast queries
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_assessments_user ON assessments(user_id);
            CREATE INDEX IF NOT EXISTS idx_recommendations_assessment ON recommendations(assessment_id);
            CREATE INDEX IF NOT EXISTS idx_saved_careers_user ON saved_careers(user_id);
            CREATE INDEX IF NOT EXISTS idx_catalog_category ON career_catalog(category);
            CREATE INDEX IF NOT EXISTS idx_roadmaps_user ON learning_roadmaps(user_id);
        """)
    conn.close()


# ---------------- USER AUTHENTICATION HELPERS ----------------

def create_user(email, password, full_name, degree="", current_year="", field_of_study="", institution="", country=""):
    """Register a new student user and create their profile. Returns user dict or None if email exists."""
    if is_cloud_mode():
        return firebase_db.create_user(email, password, full_name, degree, current_year, field_of_study, institution, country)

    clean_email = email.strip().lower()
    clean_name = full_name.strip()
    password_hash = generate_password_hash(password)

    conn = get_db()
    try:
        with conn:
            cursor = conn.execute(
                "INSERT INTO users (email, password_hash, full_name) VALUES (?, ?, ?)",
                (clean_email, password_hash, clean_name),
            )
            user_id = cursor.lastrowid
            conn.execute(
                """
                INSERT INTO student_profiles (user_id, degree, current_year, field_of_study, institution, country)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, degree.strip(), current_year.strip(), field_of_study.strip(), institution.strip(), country.strip()),
            )
            return {"id": user_id, "email": clean_email, "full_name": clean_name}
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def authenticate_user(email, password):
    """Authenticate student by email and password. Returns user dict on success, None on failure."""
    if is_cloud_mode():
        return firebase_db.authenticate_user(email, password)

    clean_email = email.strip().lower()
    conn = get_db()
    try:
        user = conn.execute("SELECT * FROM users WHERE email = ?", (clean_email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            return dict(user)
        return None
    finally:
        conn.close()


def get_user_by_email(email):
    """Fetch user by email."""
    if is_cloud_mode():
        return firebase_db.get_user_by_email(email)

    clean_email = email.strip().lower()
    conn = get_db()
    try:
        user = conn.execute("SELECT id, email, full_name, created_at FROM users WHERE email = ?", (clean_email,)).fetchone()
        return dict(user) if user else None
    finally:
        conn.close()


def get_user_by_id(user_id):
    """Fetch user by id."""
    if is_cloud_mode():
        return firebase_db.get_user_by_id(user_id)

    conn = get_db()
    try:
        user = conn.execute("SELECT id, email, full_name, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(user) if user else None
    finally:
        conn.close()


def get_student_profile(user_id):
    """Fetch profile data for a specific student."""
    if is_cloud_mode():
        return firebase_db.get_student_profile(user_id)

    conn = get_db()
    try:
        row = conn.execute(
            """
            SELECT u.id AS user_id, u.email, u.full_name, u.created_at,
                   p.degree, p.field_of_study, p.current_year, p.institution, p.country, p.bio, p.updated_at
            FROM users u
            LEFT JOIN student_profiles p ON u.id = p.user_id
            WHERE u.id = ?
            """,
            (user_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_student_profile(user_id, profile_data):
    """Update profile details for a student."""
    if is_cloud_mode():
        return firebase_db.update_student_profile(user_id, profile_data)

    conn = get_db()
    try:
        with conn:
            if "full_name" in profile_data and profile_data["full_name"].strip():
                conn.execute(
                    "UPDATE users SET full_name = ? WHERE id = ?",
                    (profile_data["full_name"].strip(), user_id),
                )
            conn.execute(
                """
                INSERT INTO student_profiles (user_id, degree, field_of_study, current_year, institution, country, bio, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    degree = excluded.degree,
                    field_of_study = excluded.field_of_study,
                    current_year = excluded.current_year,
                    institution = excluded.institution,
                    country = excluded.country,
                    bio = excluded.bio,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    user_id,
                    profile_data.get("degree", "").strip(),
                    profile_data.get("field_of_study", "").strip(),
                    profile_data.get("current_year", "").strip(),
                    profile_data.get("institution", "").strip(),
                    profile_data.get("country", "").strip(),
                    profile_data.get("bio", "").strip(),
                ),
            )
            return True
    finally:
        conn.close()


# ---------------- ASSESSMENT & RECOMMENDATION PERSISTENCE ----------------

def save_assessment_record(user_id, input_data, recommendations):
    """Persist an assessment and its generated career recommendations."""
    if is_cloud_mode():
        return firebase_db.save_assessment_record(user_id, input_data, recommendations)

    conn = get_db()
    try:
        with conn:
            cursor = conn.execute(
                "INSERT INTO assessments (user_id, input_data_json) VALUES (?, ?)",
                (user_id, json.dumps(input_data)),
            )
            assessment_id = cursor.lastrowid

            for rec in recommendations:
                conn.execute(
                    """
                    INSERT INTO recommendations
                    (assessment_id, career_id, career_title, match_score, match_reasons_json,
                     matched_skills_json, skills_to_learn_json, ai_explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        assessment_id,
                        rec.get("career_id", rec.get("name", "")),
                        rec.get("name", rec.get("title", "")),
                        int(rec.get("match", 0)),
                        json.dumps(rec.get("reasons", [])),
                        json.dumps(rec.get("matched_skills", [])),
                        json.dumps(rec.get("skills_to_learn", [])),
                        rec.get("ai_explanation", ""),
                    ),
                )
            return assessment_id
    finally:
        conn.close()


def get_user_assessments(user_id, limit=10):
    """Retrieve assessment history for a specific student."""
    if is_cloud_mode():
        return firebase_db.get_user_assessments(user_id, limit)

    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT id, user_id, input_data_json, created_at
            FROM assessments
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()

        assessments = []
        for r in rows:
            recs = conn.execute(
                """
                SELECT career_id, career_title, match_score, match_reasons_json,
                       matched_skills_json, skills_to_learn_json, ai_explanation
                FROM recommendations
                WHERE assessment_id = ?
                ORDER BY match_score DESC
                """,
                (r["id"],),
            ).fetchall()

            rec_list = []
            for item in recs:
                rec_list.append({
                    "career_id": item["career_id"],
                    "name": item["career_title"],
                    "match": item["match_score"],
                    "reasons": json.loads(item["match_reasons_json"] or "[]"),
                    "matched_skills": json.loads(item["matched_skills_json"] or "[]"),
                    "skills_to_learn": json.loads(item["skills_to_learn_json"] or "[]"),
                    "ai_explanation": item["ai_explanation"] or "",
                })

            assessments.append({
                "id": r["id"],
                "created_at": r["created_at"],
                "input_data": json.loads(r["input_data_json"] or "{}"),
                "recommendations": rec_list,
            })
        return assessments
    finally:
        conn.close()


def get_latest_assessment(user_id):
    """Retrieve the most recent assessment for a student."""
    if is_cloud_mode():
        return firebase_db.get_latest_assessment(user_id)

    assessments = get_user_assessments(user_id, limit=1)
    return assessments[0] if assessments else None


# ---------------- SAVED CAREERS HELPERS ----------------

def toggle_save_career(user_id, career_id):
    """Toggle bookmark on a career. Returns True if saved, False if removed."""
    if is_cloud_mode():
        return firebase_db.toggle_save_career(user_id, career_id)

    conn = get_db()
    try:
        with conn:
            existing = conn.execute(
                "SELECT id FROM saved_careers WHERE user_id = ? AND career_id = ?",
                (user_id, career_id),
            ).fetchone()
            if existing:
                conn.execute(
                    "DELETE FROM saved_careers WHERE user_id = ? AND career_id = ?",
                    (user_id, career_id),
                )
                return False
            else:
                conn.execute(
                    "INSERT INTO saved_careers (user_id, career_id) VALUES (?, ?)",
                    (user_id, career_id),
                )
                return True
    finally:
        conn.close()


def is_career_saved(user_id, career_id):
    """Check if a career is bookmarked by a student."""
    if not user_id:
        return False
    if is_cloud_mode():
        return firebase_db.is_career_saved(user_id, career_id)

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT 1 FROM saved_careers WHERE user_id = ? AND career_id = ?",
            (user_id, career_id),
        ).fetchone()
        return bool(row)
    finally:
        conn.close()


def get_user_saved_careers(user_id):
    """Fetch all saved careers with catalog metadata for a student."""
    if is_cloud_mode():
        return firebase_db.get_user_saved_careers(user_id)

    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT c.*, s.saved_at
            FROM saved_careers s
            JOIN career_catalog c ON s.career_id = c.id
            WHERE s.user_id = ?
            ORDER BY s.saved_at DESC
            """,
            (user_id,),
        ).fetchall()

        careers = []
        for r in rows:
            careers.append({
                "id": r["id"],
                "title": r["title"],
                "category": r["category"],
                "industry": r["industry"],
                "minimum_education": r["minimum_education"],
                "description": r["description"],
                "learning_difficulty": r["learning_difficulty"],
                "saved_at": r["saved_at"],
            })
        return careers
    finally:
        conn.close()


# ---------------- LEARNING ROADMAP PERSISTENCE ----------------

def save_user_roadmap(user_id, career_id, duration_months, stages):
    """Save or update a student's active roadmap for a career."""
    if is_cloud_mode():
        return firebase_db.save_user_roadmap(user_id, career_id, duration_months, stages)

    conn = get_db()
    try:
        with conn:
            conn.execute(
                "DELETE FROM learning_roadmaps WHERE user_id = ? AND career_id = ?",
                (user_id, career_id),
            )
            conn.execute(
                """
                INSERT INTO learning_roadmaps (user_id, career_id, duration_months, stages_json)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, career_id, int(duration_months), json.dumps(stages)),
            )
            return True
    finally:
        conn.close()


def get_user_roadmaps(user_id):
    """Fetch saved roadmaps for a student."""
    if is_cloud_mode():
        return firebase_db.get_user_roadmaps(user_id)

    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT r.id, r.career_id, r.duration_months, r.stages_json, r.created_at,
                   c.title AS career_title, c.category AS career_category
            FROM learning_roadmaps r
            JOIN career_catalog c ON r.career_id = c.id
            WHERE r.user_id = ?
            ORDER BY r.created_at DESC
            """,
            (user_id,),
        ).fetchall()

        roadmaps = []
        for r in rows:
            roadmaps.append({
                "id": r["id"],
                "career_id": r["career_id"],
                "career_title": r["career_title"],
                "career_category": r["career_category"],
                "duration_months": r["duration_months"],
                "stages": json.loads(r["stages_json"] or "[]"),
                "created_at": r["created_at"],
            })
        return roadmaps
    finally:
        conn.close()
