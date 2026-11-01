"""
Comprehensive automated test suite for EduMind AI.
Tests authentication, career catalog, multi-facet search, recommendations,
Gemini API fallback, and database persistence.
"""

import os
import unittest
import database
import careers_catalog
import recommender
import ai_service
from app import app


class TestEduMindAIFullSuite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Configure app for testing
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        database.init_db()

    def setUp(self):
        self.client = app.test_client()

    # ---------------- 1. AUTHENTICATION TESTS ----------------

    def test_01_user_registration_success(self):
        test_email = "alex.student@university.edu"
        # Ensure clean state for this test email
        conn = database.get_db()
        with conn:
            conn.execute("DELETE FROM users WHERE email = ?", (test_email,))
        conn.close()

        response = self.client.post("/register", data={
            "full_name": "Alex Student",
            "email": test_email,
            "password": "Password123!",
            "confirm_password": "Password123!",
            "degree": "B.Tech",
            "current_year": "3",
            "field_of_study": "Computer Science",
            "institution": "National Institute",
            "country": "India",
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome to EduMind AI", response.data)

        # Verify in database
        user = database.get_user_by_email(test_email) if hasattr(database, "get_user_by_email") else database.authenticate_user(test_email, "Password123!")
        self.assertIsNotNone(user)

    def test_02_registration_duplicate_email(self):
        test_email = "duplicate@university.edu"
        database.create_user(test_email, "Password123!", "First User", degree="BCA")

        response = self.client.post("/register", data={
            "full_name": "Second User",
            "email": test_email,
            "password": "Password123!",
            "confirm_password": "Password123!",
            "degree": "BCA",
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"already exists", response.data)

    def test_03_login_valid_credentials(self):
        test_email = "login.success@university.edu"
        database.create_user(test_email, "SecretPass99", "Login Tester", degree="B.Sc")

        response = self.client.post("/login", data={
            "email": test_email,
            "password": "SecretPass99",
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome, Login Tester", response.data)

    def test_04_login_invalid_password(self):
        test_email = "login.fail@university.edu"
        database.create_user(test_email, "CorrectPass1", "Fail Tester")

        response = self.client.post("/login", data={
            "email": test_email,
            "password": "WrongPassword",
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Invalid email or password", response.data)

    def test_05_protected_routes_require_login(self):
        # Without session, protected routes should redirect
        routes = ["/dashboard", "/profile", "/assessment"]
        for route in routes:
            response = self.client.get(route)
            self.assertEqual(response.status_code, 302)
            self.assertIn("/login", response.headers["Location"])

    def test_06_logout_clears_session(self):
        # Log in first
        test_email = "logout.test@university.edu"
        database.create_user(test_email, "Pass12345", "Logout User")
        self.client.post("/login", data={"email": test_email, "password": "Pass12345"})

        # Now logout
        response = self.client.get("/logout", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"signed out", response.data)

        # Check dashboard is now blocked
        dash_response = self.client.get("/dashboard")
        self.assertEqual(dash_response.status_code, 302)

    # ---------------- 2. CAREER CATALOG & SEARCH TESTS ----------------

    def test_07_catalog_loads_careers(self):
        careers = careers_catalog.get_all_careers()
        self.assertGreaterEqual(len(careers), 22)
        categories = careers_catalog.get_all_categories()
        self.assertGreaterEqual(len(categories), 20)

    def test_08_career_search_by_keyword(self):
        # Search by title keyword
        filtered, _, _, _ = careers_catalog.get_filtered_careers(query="Python")
        self.assertTrue(any("Python" in c["title"] for c in filtered))

        # Search by skill keyword
        filtered_sql, _, _, _ = careers_catalog.get_filtered_careers(query="SQL")
        self.assertGreater(len(filtered_sql), 0)

    def test_09_career_filter_by_category(self):
        filtered, _, _, _ = careers_catalog.get_filtered_careers(category="Medical and Healthcare")
        self.assertGreater(len(filtered), 0)
        for c in filtered:
            self.assertEqual(c["category"], "Medical and Healthcare")

    def test_10_career_detail_and_related(self):
        career = careers_catalog.get_career_by_id("python-developer")
        self.assertIsNotNone(career)
        self.assertEqual(career["title"], "Python Developer")
        self.assertTrue(len(career["technical_skills"]) > 0)
        self.assertTrue(len(career["responsibilities"]) > 0)

        # Related careers
        related = careers_catalog.get_related_careers(career["id"], limit=3)
        self.assertIsInstance(related, list)
        self.assertLessEqual(len(related), 3)

    # ---------------- 3. RECOMMENDATIONS & AI FALLBACK TESTS ----------------

    def test_11_global_recommendation_scoring(self):
        student = {
            "degree": "B.Tech",
            "year": "3",
            "interests": ["Software", "AI"],
            "programming": ["Python"],
            "technical": ["SQL", "Git"],
            "work": "Coding",
            "proficiency": "Intermediate",
        }

        recs = recommender.recommend_global_careers(student, top_k=5)
        self.assertEqual(len(recs), 5)

        # Check scores are sorted descending and valid
        scores = [r["match"] for r in recs]
        self.assertEqual(scores, sorted(scores, reverse=True))
        for s in scores:
            self.assertGreaterEqual(s, 0)
            self.assertLessEqual(s, 100)

    def test_12_non_cs_recommendations(self):
        commerce_student = {
            "degree": "B.Com",
            "year": "2",
            "interests": ["Finance"],
            "programming": [],
            "technical": ["Excel"],
            "work": "Finance",
            "proficiency": "Beginner",
        }

        recs = recommender.recommend_global_careers(commerce_student, top_k=5)
        top_titles = [r["name"] for r in recs]
        # Should include finance / accounting careers
        self.assertTrue(any("Accountant" in t or "Financial" in t for t in top_titles))

    def test_13_gemini_fallback_when_key_absent(self):
        # Test that without an API key, fallback returns cleanly without crashing
        orig_key = os.environ.get("GEMINI_API_KEY")
        try:
            if "GEMINI_API_KEY" in os.environ:
                del os.environ["GEMINI_API_KEY"]

            candidates = [{"id": "python-developer", "name": "Python Developer", "match": 80, "reasons": ["Test reason"]}]
            enhanced = ai_service.enhance_recommendations_with_gemini({}, candidates)
            self.assertEqual(len(enhanced), 1)
            self.assertFalse(enhanced[0]["ai_analyzed"])
            self.assertIn("ai_explanation", enhanced[0])
        finally:
            if orig_key:
                os.environ["GEMINI_API_KEY"] = orig_key

    # ---------------- 4. DATABASE PERSISTENCE TESTS ----------------

    def test_14_assessment_and_recommendation_persistence(self):
        # Create student user
        email = "persistence.student@university.edu"
        user = database.create_user(email, "Secret123!", "Persistent Student", degree="B.Tech") or database.get_user_by_email(email)

        input_data = {"degree": "B.Tech", "year": "3", "interests": ["AI"]}
        recs = [
            {"id": "python-developer", "name": "Python Developer", "match": 78, "reasons": ["Skill fit"], "matched_skills": ["Python"], "skills_to_learn": ["Docker"]},
            {"id": "data-analyst", "name": "Data Analyst", "match": 65, "reasons": ["Data fit"], "matched_skills": ["SQL"], "skills_to_learn": ["Power BI"]},
        ]

        # Save assessment
        assessment_id = database.save_assessment_record(user["id"], input_data, recs)
        self.assertIsNotNone(assessment_id)

        # Retrieve history
        history = database.get_user_assessments(user["id"])
        self.assertGreaterEqual(len(history), 1)
        self.assertEqual(history[0]["input_data"]["degree"], "B.Tech")
        self.assertEqual(len(history[0]["recommendations"]), 2)

    def test_15_saved_careers_bookmark_toggle(self):
        email = "bookmark.student@university.edu"
        user = database.create_user(email, "Pass1234!", "Bookmark Student") or database.get_user_by_email(email)

        # Save career
        saved = database.toggle_save_career(user["id"], "python-developer")
        self.assertTrue(saved)
        self.assertTrue(database.is_career_saved(user["id"], "python-developer"))

        # Fetch saved careers
        saved_list = database.get_user_saved_careers(user["id"])
        self.assertEqual(len(saved_list), 1)
        self.assertEqual(saved_list[0]["id"], "python-developer")

        # Toggle off
        unsaved = database.toggle_save_career(user["id"], "python-developer")
        self.assertFalse(unsaved)
        self.assertFalse(database.is_career_saved(user["id"], "python-developer"))

    def test_16_roadmap_generation_and_persistence(self):
        email = "roadmap.student@university.edu"
        user = database.create_user(email, "Pass1234!", "Roadmap Student") or database.get_user_by_email(email)

        # Dynamic roadmap for 3, 6, 12 months
        for dur in [3, 6, 12]:
            rm = careers_catalog.get_career_roadmap("python-developer", duration_months=dur)
            self.assertEqual(rm["duration_months"], dur)
            self.assertEqual(len(rm["stages"]), 3)

        # Persist roadmap
        rm_data = careers_catalog.get_career_roadmap("python-developer", duration_months=6)
        database.save_user_roadmap(user["id"], "python-developer", 6, rm_data["stages"])

        user_roadmaps = database.get_user_roadmaps(user["id"])
        self.assertEqual(len(user_roadmaps), 1)
        self.assertEqual(user_roadmaps[0]["career_id"], "python-developer")
        self.assertEqual(user_roadmaps[0]["duration_months"], 6)


if __name__ == "__main__":
    unittest.main()
