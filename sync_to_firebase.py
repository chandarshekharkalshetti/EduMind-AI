"""
Firebase Firestore Sync & Migration Utility for EduMind AI.
Allows syncing career catalog and migrating local SQLite data to Cloud Firestore.

Usage:
  python sync_to_firebase.py --seed-catalog
  python sync_to_firebase.py --migrate-all
  python sync_to_firebase.py --status
"""

import sys
import json
import argparse
from pathlib import Path

import firebase_db
import database


def print_banner():
    print("=" * 60)
    print(" [FIREBASE] EduMind AI - Cloud Firestore Sync Tool")
    print("=" * 60)


def check_status():
    print_banner()
    configured = firebase_db.is_firebase_configured()
    print(f"Firebase Configured: {'[OK] YES' if configured else '[NO] NOT CONFIGURED'}")

    if not configured:
        print("\nTo configure Firebase Cloud Firestore:")
        print("1. Go to Firebase Console: https://console.firebase.google.com/")
        print("2. Create a project and enable 'Cloud Firestore' (in Test or Production mode).")
        print("3. Go to Project Settings -> Service Accounts -> 'Generate New Private Key'.")
        print("4. Save the downloaded file as 'firebase-key.json' in this project root:")
        print(f"   {Path(__file__).parent / 'firebase-key.json'}")
        print("   (Or set FIREBASE_CREDENTIALS_JSON or FIREBASE_KEY_PATH in your .env)")
        return False

    client = firebase_db.get_firestore_client()
    if not client:
        print("[ERROR] Failed to connect to Cloud Firestore. Check service account key.")
        return False

    print("[OK] Successfully connected to Cloud Firestore!")
    try:
        catalog_count = len(list(client.collection("career_catalog").limit(10).stream()))
        users_count = len(list(client.collection("users").limit(10).stream()))
        print(f"[INFO] Cloud Documents sample: ~{catalog_count}+ careers, ~{users_count}+ users in Firestore")
        return True
    except Exception as e:
        print(f"[WARNING] Error querying Firestore: {e}")
        return False


def seed_catalog():
    print_banner()
    if not firebase_db.is_firebase_configured():
        print("[ERROR] Firebase is not configured. Place 'firebase-key.json' in project root.")
        return False

    data_file = Path(__file__).parent / "data" / "careers_data.json"
    if not data_file.exists():
        print(f"[ERROR] Catalog data file not found at {data_file}")
        return False

    print("[INFO] Seeding 34 careers across 22 categories into Cloud Firestore...")
    success = firebase_db.init_firestore(seed_file=data_file)
    if success:
        print("[OK] Successfully populated 'career_catalog' collection in Cloud Firestore!")
    else:
        print("[ERROR] Seeding encountered an error.")
    return success


def migrate_sqlite_data():
    print_banner()
    if not firebase_db.is_firebase_configured():
        print("[ERROR] Firebase is not configured. Place 'firebase-key.json' in project root.")
        return False

    db = firebase_db.get_firestore_client()
    if not db:
        print("[ERROR] Failed to obtain Firestore client.")
        return False

    # 1. Seed Catalog First
    seed_catalog()

    # 2. Migrate Users & Profiles from SQLite
    print("\n[INFO] Migrating users and profiles from local SQLite to Firestore...")
    conn = database.get_db()
    try:
        users = conn.execute("SELECT * FROM users").fetchall()
        migrated_users = 0
        for u in users:
            uid_str = str(u["id"])
            user_data = {
                "id": uid_str,
                "email": u["email"],
                "password_hash": u["password_hash"],
                "full_name": u["full_name"],
                "created_at": str(u["created_at"]),
            }
            db.collection("users").document(uid_str).set(user_data, merge=True)

            prof = conn.execute("SELECT * FROM student_profiles WHERE user_id = ?", (u["id"],)).fetchone()
            if prof:
                prof_data = {
                    "user_id": uid_str,
                    "degree": prof["degree"] or "",
                    "field_of_study": prof["field_of_study"] or "",
                    "current_year": prof["current_year"] or "",
                    "institution": prof["institution"] or "",
                    "country": prof["country"] or "",
                    "bio": prof["bio"] or "",
                    "updated_at": str(prof["updated_at"]),
                }
                db.collection("student_profiles").document(uid_str).set(prof_data, merge=True)
            migrated_users += 1
        print(f"[OK] Migrated {migrated_users} users and profiles to Cloud Firestore!")

        # 3. Migrate Saved Careers (Bookmarks)
        saved = conn.execute("SELECT * FROM saved_careers").fetchall()
        migrated_saved = 0
        for s in saved:
            doc_id = f"{s['user_id']}_{s['career_id']}"
            db.collection("saved_careers").document(doc_id).set({
                "user_id": str(s["user_id"]),
                "career_id": str(s["career_id"]),
                "notes": s["notes"] or "",
                "saved_at": str(s["saved_at"]),
            }, merge=True)
            migrated_saved += 1
        print(f"[OK] Migrated {migrated_saved} saved career bookmarks to Cloud Firestore!")

        # 4. Migrate Roadmaps
        roadmaps = conn.execute("SELECT * FROM learning_roadmaps").fetchall()
        migrated_roadmaps = 0
        for r in roadmaps:
            doc_id = f"{r['user_id']}_{r['career_id']}"
            stages = json.loads(r["stages_json"] or "[]")
            db.collection("learning_roadmaps").document(doc_id).set({
                "user_id": str(r["user_id"]),
                "career_id": str(r["career_id"]),
                "duration_months": int(r["duration_months"]),
                "stages": stages,
                "created_at": str(r["created_at"]),
            }, merge=True)
            migrated_roadmaps += 1
        print(f"[OK] Migrated {migrated_roadmaps} learning roadmaps to Cloud Firestore!")

        print("\n[SUCCESS] Full migration from local SQLite to Cloud Firestore complete!")
        return True
    except Exception as e:
        print(f"[ERROR] Migration error: {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Firebase Firestore Sync Utility")
    parser.add_argument("--status", action="store_true", help="Check Firebase configuration and connection")
    parser.add_argument("--seed-catalog", action="store_true", help="Seed 34 careers into Cloud Firestore")
    parser.add_argument("--migrate-all", action="store_true", help="Migrate SQLite data to Cloud Firestore")

    args = parser.parse_args()

    if args.seed_catalog:
        seed_catalog()
    elif args.migrate_all:
        migrate_sqlite_data()
    else:
        check_status()
