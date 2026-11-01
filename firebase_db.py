"""
Firebase Firestore Cloud Database Module for EduMind AI.
Provides cloud persistence for users, student profiles, global career catalog,
assessment history, saved careers (bookmarks), and learning roadmaps.
"""

import os
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

import firebase_admin
from firebase_admin import credentials, firestore

_firestore_client = None
_firebase_initialized = False

# Possible locations for Firebase Service Account Key
KEY_LOCATIONS = [
    Path(os.environ.get("FIREBASE_KEY_PATH", "")),
    Path(__file__).parent / "firebase-key.json",
    Path(__file__).parent / "serviceAccountKey.json",
]


def is_firebase_configured():
    """
    Check if Firebase credentials are provided via:
    1. FIREBASE_CREDENTIALS_JSON env variable (raw JSON string)
    2. Local service account JSON file (firebase-key.json or serviceAccountKey.json)
    3. GOOGLE_APPLICATION_CREDENTIALS env variable
    """
    if os.environ.get("FIREBASE_CREDENTIALS_JSON"):
        return True

    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and os.path.exists(os.environ["GOOGLE_APPLICATION_CREDENTIALS"]):
        return True

    for p in KEY_LOCATIONS:
        if p and p.is_file() and p.exists():
            return True

    return False


def get_firestore_client():
    """
    Initialize Firebase Admin app if needed and return the Cloud Firestore client.
    Returns None if credentials are not configured.
    """
    global _firestore_client, _firebase_initialized

    if _firestore_client is not None:
        return _firestore_client

    if not is_firebase_configured():
        return None

    try:
        # Avoid re-initializing if already done
        if not firebase_admin._apps:
            raw_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
            if raw_json:
                cred_dict = json.loads(raw_json)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
            elif os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and os.path.exists(os.environ["GOOGLE_APPLICATION_CREDENTIALS"]):
                cred = credentials.Certificate(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
                firebase_admin.initialize_app(cred)
            else:
                for p in KEY_LOCATIONS:
                    if p and p.is_file() and p.exists():
                        cred = credentials.Certificate(str(p))
                        firebase_admin.initialize_app(cred)
                        break

        _firestore_client = firestore.client()
        _firebase_initialized = True
        return _firestore_client
    except Exception as e:
        print(f"[Firebase] Warning: Failed to initialize Firebase Firestore: {e}")
        return None


def init_firestore(seed_file=None):
    """
    Initialize Firestore collections. If career_catalog collection is empty,
    automatically seed it from data/careers_data.json.
    """
    db = get_firestore_client()
    if not db:
        return False

    try:
        # Check if career_catalog has any documents
        catalog_ref = db.collection("career_catalog")
        existing_docs = list(catalog_ref.limit(1).stream())

        if not existing_docs:
            if seed_file is None:
                seed_file = Path(__file__).parent / "data" / "careers_data.json"

            if Path(seed_file).exists():
                with open(seed_file, "r", encoding="utf-8") as f:
                    careers = json.load(f)

                batch = db.batch()
                batch_count = 0
                for c in careers:
                    doc_id = c.get("id") or c["title"].lower().replace(" ", "-")
                    doc_ref = catalog_ref.document(doc_id)
                    batch.set(doc_ref, c)
                    batch_count += 1
                    if batch_count >= 400:  # Firestore batch limit is 500
                        batch.commit()
                        batch = db.batch()
                        batch_count = 0

                if batch_count > 0:
                    batch.commit()
                print(f"[Firebase] Seeded {len(careers)} careers into Cloud Firestore!")
        return True
    except Exception as e:
        print(f"[Firebase] Initialization error: {e}")
        return False


# ---------------- USER AUTHENTICATION & PROFILES ----------------

def create_user(email, password, full_name, degree="", current_year="", field_of_study="", institution="", country=""):
    """Register a new student user in Cloud Firestore."""
    db = get_firestore_client()
    if not db:
        return None

    clean_email = email.strip().lower()
    clean_name = full_name.strip()
    password_hash = generate_password_hash(password)
    user_id = str(uuid.uuid4())

    try:
        # Check if email already exists
        existing = list(db.collection("users").where("email", "==", clean_email).limit(1).stream())
        if existing:
            return None

        # Create user document
        now_str = datetime.now(timezone.utc).isoformat()
        user_data = {
            "id": user_id,
            "email": clean_email,
            "password_hash": password_hash,
            "full_name": clean_name,
            "created_at": now_str,
        }
        db.collection("users").document(user_id).set(user_data)

        # Create student profile document
        profile_data = {
            "user_id": user_id,
            "degree": degree.strip(),
            "field_of_study": field_of_study.strip(),
            "current_year": current_year.strip(),
            "institution": institution.strip(),
            "country": country.strip(),
            "bio": "",
            "updated_at": now_str,
        }
        db.collection("student_profiles").document(user_id).set(profile_data)

        return {"id": user_id, "email": clean_email, "full_name": clean_name}
    except Exception as e:
        print(f"[Firebase] Error creating user: {e}")
        return None


def authenticate_user(email, password):
    """Authenticate student by email and password using Cloud Firestore."""
    db = get_firestore_client()
    if not db:
        return None

    clean_email = email.strip().lower()
    try:
        query = db.collection("users").where("email", "==", clean_email).limit(1).stream()
        for doc in query:
            user = doc.to_dict()
            if check_password_hash(user.get("password_hash", ""), password):
                return user
        return None
    except Exception as e:
        print(f"[Firebase] Authentication error: {e}")
        return None


def get_user_by_email(email):
    """Fetch user by email from Cloud Firestore."""
    db = get_firestore_client()
    if not db:
        return None

    clean_email = email.strip().lower()
    try:
        docs = list(db.collection("users").where("email", "==", clean_email).limit(1).stream())
        if docs:
            user = docs[0].to_dict()
            user["id"] = docs[0].id
            return user
        return None
    except Exception as e:
        print(f"[Firebase] Error getting user by email: {e}")
        return None


def get_user_by_id(user_id):
    """Fetch user by id from Cloud Firestore."""
    db = get_firestore_client()
    if not db or not user_id:
        return None

    try:
        doc = db.collection("users").document(str(user_id)).get()
        if doc.exists:
            user = doc.to_dict()
            user["id"] = doc.id
            return user
        return None
    except Exception as e:
        print(f"[Firebase] Error getting user by id: {e}")
        return None


def get_student_profile(user_id):
    """Fetch merged user and student profile data from Cloud Firestore."""
    db = get_firestore_client()
    if not db or not user_id:
        return None

    try:
        user_doc = db.collection("users").document(str(user_id)).get()
        if not user_doc.exists:
            return None
        user_data = user_doc.to_dict()

        profile_doc = db.collection("student_profiles").document(str(user_id)).get()
        profile_data = profile_doc.to_dict() if profile_doc.exists else {}

        return {
            "user_id": str(user_id),
            "email": user_data.get("email", ""),
            "full_name": user_data.get("full_name", ""),
            "created_at": user_data.get("created_at", ""),
            "degree": profile_data.get("degree", ""),
            "field_of_study": profile_data.get("field_of_study", ""),
            "current_year": profile_data.get("current_year", ""),
            "institution": profile_data.get("institution", ""),
            "country": profile_data.get("country", ""),
            "bio": profile_data.get("bio", ""),
            "updated_at": profile_data.get("updated_at", ""),
        }
    except Exception as e:
        print(f"[Firebase] Error getting student profile: {e}")
        return None


def update_student_profile(user_id, profile_data):
    """Update profile details for a student in Cloud Firestore."""
    db = get_firestore_client()
    if not db or not user_id:
        return False

    try:
        uid_str = str(user_id)
        now_str = datetime.now(timezone.utc).isoformat()

        if "full_name" in profile_data and profile_data["full_name"].strip():
            db.collection("users").document(uid_str).update({
                "full_name": profile_data["full_name"].strip()
            })

        update_fields = {
            "user_id": uid_str,
            "degree": profile_data.get("degree", "").strip(),
            "field_of_study": profile_data.get("field_of_study", "").strip(),
            "current_year": profile_data.get("current_year", "").strip(),
            "institution": profile_data.get("institution", "").strip(),
            "country": profile_data.get("country", "").strip(),
            "bio": profile_data.get("bio", "").strip(),
            "updated_at": now_str,
        }
        db.collection("student_profiles").document(uid_str).set(update_fields, merge=True)
        return True
    except Exception as e:
        print(f"[Firebase] Error updating profile: {e}")
        return False


# ---------------- ASSESSMENTS & RECOMMENDATIONS ----------------

def save_assessment_record(user_id, input_data, recommendations):
    """Persist an assessment and generated career recommendations to Cloud Firestore."""
    db = get_firestore_client()
    if not db:
        return None

    try:
        assessment_id = str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).isoformat()

        rec_list = []
        for rec in recommendations:
            rec_list.append({
                "career_id": rec.get("career_id", rec.get("id", rec.get("name", ""))),
                "name": rec.get("name", rec.get("title", "")),
                "match": int(rec.get("match", 0)),
                "reasons": rec.get("reasons", []),
                "matched_skills": rec.get("matched_skills", []),
                "skills_to_learn": rec.get("skills_to_learn", []),
                "ai_explanation": rec.get("ai_explanation", ""),
            })

        doc_data = {
            "id": assessment_id,
            "user_id": str(user_id),
            "created_at": now_str,
            "input_data": input_data,
            "recommendations": rec_list,
        }

        db.collection("assessments").document(assessment_id).set(doc_data)
        return assessment_id
    except Exception as e:
        print(f"[Firebase] Error saving assessment: {e}")
        return None


def get_user_assessments(user_id, limit=10):
    """Retrieve assessment history for a specific student from Cloud Firestore."""
    db = get_firestore_client()
    if not db or not user_id:
        return []

    try:
        query = (
            db.collection("assessments")
            .where("user_id", "==", str(user_id))
            .stream()
        )
        assessments = [doc.to_dict() for doc in query]
        # Sort in memory by created_at descending (avoids requiring compound Firestore indexes)
        assessments.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return assessments[:limit]
    except Exception as e:
        print(f"[Firebase] Error getting assessments: {e}")
        return []


def get_latest_assessment(user_id):
    """Retrieve the most recent assessment for a student."""
    assessments = get_user_assessments(user_id, limit=1)
    return assessments[0] if assessments else None


# ---------------- SAVED CAREERS (BOOKMARKS) ----------------

def toggle_save_career(user_id, career_id):
    """Toggle bookmark on a career in Cloud Firestore. Returns True if saved, False if removed."""
    db = get_firestore_client()
    if not db or not user_id:
        return False

    doc_id = f"{user_id}_{career_id}"
    try:
        doc_ref = db.collection("saved_careers").document(doc_id)
        doc = doc_ref.get()

        if doc.exists:
            doc_ref.delete()
            return False
        else:
            now_str = datetime.now(timezone.utc).isoformat()
            doc_ref.set({
                "user_id": str(user_id),
                "career_id": str(career_id),
                "notes": "",
                "saved_at": now_str,
            })
            return True
    except Exception as e:
        print(f"[Firebase] Error toggling career bookmark: {e}")
        return False


def is_career_saved(user_id, career_id):
    """Check if a career is bookmarked by a student in Cloud Firestore."""
    db = get_firestore_client()
    if not db or not user_id:
        return False

    doc_id = f"{user_id}_{career_id}"
    try:
        doc = db.collection("saved_careers").document(doc_id).get()
        return doc.exists
    except Exception as e:
        print(f"[Firebase] Error checking saved career: {e}")
        return False


def get_user_saved_careers(user_id):
    """Fetch all saved careers with catalog metadata for a student from Cloud Firestore."""
    db = get_firestore_client()
    if not db or not user_id:
        return []

    try:
        query = db.collection("saved_careers").where("user_id", "==", str(user_id)).stream()
        saved_items = [doc.to_dict() for doc in query]

        careers = []
        for item in saved_items:
            cid = item.get("career_id")
            catalog_doc = db.collection("career_catalog").document(cid).get()
            if catalog_doc.exists:
                cdata = catalog_doc.to_dict()
                careers.append({
                    "id": cdata.get("id", cid),
                    "title": cdata.get("title", cid),
                    "category": cdata.get("category", "General"),
                    "industry": cdata.get("industry", ""),
                    "minimum_education": cdata.get("minimum_education", ""),
                    "description": cdata.get("description", ""),
                    "learning_difficulty": cdata.get("learning_difficulty", "Moderate"),
                    "saved_at": item.get("saved_at", ""),
                })
        # Sort by saved_at descending
        careers.sort(key=lambda x: x.get("saved_at", ""), reverse=True)
        return careers
    except Exception as e:
        print(f"[Firebase] Error fetching saved careers: {e}")
        return []


# ---------------- LEARNING ROADMAP PERSISTENCE ----------------

def save_user_roadmap(user_id, career_id, duration_months, stages):
    """Save or update a student's active roadmap in Cloud Firestore."""
    db = get_firestore_client()
    if not db or not user_id:
        return False

    doc_id = f"{user_id}_{career_id}"
    try:
        now_str = datetime.now(timezone.utc).isoformat()
        db.collection("learning_roadmaps").document(doc_id).set({
            "user_id": str(user_id),
            "career_id": str(career_id),
            "duration_months": int(duration_months),
            "stages": stages,
            "created_at": now_str,
        })
        return True
    except Exception as e:
        print(f"[Firebase] Error saving roadmap: {e}")
        return False


def get_user_roadmaps(user_id):
    """Fetch saved roadmaps for a student from Cloud Firestore."""
    db = get_firestore_client()
    if not db or not user_id:
        return []

    try:
        query = db.collection("learning_roadmaps").where("user_id", "==", str(user_id)).stream()
        roadmaps = []

        for doc in query:
            r = doc.to_dict()
            cid = r.get("career_id", "")
            catalog_doc = db.collection("career_catalog").document(cid).get()
            cat_data = catalog_doc.to_dict() if catalog_doc.exists else {}

            roadmaps.append({
                "id": doc.id,
                "career_id": cid,
                "career_title": cat_data.get("title", cid.replace("-", " ").title()),
                "career_category": cat_data.get("category", "Career Pathway"),
                "duration_months": r.get("duration_months", 6),
                "stages": r.get("stages", []),
                "created_at": r.get("created_at", ""),
            })

        roadmaps.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return roadmaps
    except Exception as e:
        print(f"[Firebase] Error getting user roadmaps: {e}")
        return []


# ---------------- CATALOG QUERIES ----------------

def get_all_careers():
    """Retrieve all careers from Cloud Firestore catalog."""
    db = get_firestore_client()
    if not db:
        return []

    try:
        docs = db.collection("career_catalog").stream()
        careers = [doc.to_dict() for doc in docs]
        careers.sort(key=lambda x: x.get("title", "").lower())
        return careers
    except Exception as e:
        print(f"[Firebase] Error fetching catalog: {e}")
        return []


def get_career_by_id(career_id):
    """Fetch a career by its unique ID from Cloud Firestore."""
    db = get_firestore_client()
    if not db or not career_id:
        return None

    clean_id = career_id.strip().lower().replace(" ", "-")
    try:
        doc = db.collection("career_catalog").document(clean_id).get()
        if doc.exists:
            return doc.to_dict()

        # Fallback check by title
        docs = list(db.collection("career_catalog").where("title", "==", career_id.strip()).limit(1).stream())
        if docs:
            return docs[0].to_dict()
        return None
    except Exception as e:
        print(f"[Firebase] Error getting career: {e}")
        return None
