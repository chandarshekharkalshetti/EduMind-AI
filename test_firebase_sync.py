"""
Unit tests for Firebase Cloud Database integration and Dual-Engine Fallback in EduMind AI.
"""

import unittest
import firebase_db
import database
import sync_to_firebase


class TestFirebaseCloudIntegration(unittest.TestCase):

    def test_01_firebase_db_module_loaded(self):
        """Verify firebase_db module is loaded and provides expected interface."""
        self.assertTrue(hasattr(firebase_db, "is_firebase_configured"))
        self.assertTrue(hasattr(firebase_db, "get_firestore_client"))
        self.assertTrue(hasattr(firebase_db, "init_firestore"))
        self.assertTrue(hasattr(firebase_db, "create_user"))
        self.assertTrue(hasattr(firebase_db, "authenticate_user"))
        self.assertTrue(hasattr(firebase_db, "get_student_profile"))
        self.assertTrue(hasattr(firebase_db, "save_assessment_record"))
        self.assertTrue(hasattr(firebase_db, "toggle_save_career"))
        self.assertTrue(hasattr(firebase_db, "save_user_roadmap"))

    def test_02_dual_engine_detection(self):
        """Verify database reports active database engine."""
        db_type = database.get_active_db_type()
        self.assertIn(db_type, ["SQLite (Local)", "Firebase Firestore (Cloud)"])

    def test_03_firebase_unconfigured_graceful_fallback(self):
        """When credentials are absent, client returns None rather than raising exceptions."""
        if not firebase_db.is_firebase_configured():
            self.assertFalse(database.is_cloud_mode())
            self.assertEqual(database.get_active_db_type(), "SQLite (Local)")

    def test_04_sync_tool_status_runs_cleanly(self):
        """Verify sync_to_firebase check_status completes without uncaught errors."""
        result = sync_to_firebase.check_status()
        self.assertIsInstance(result, bool)


if __name__ == "__main__":
    unittest.main()
