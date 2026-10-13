
import unittest
from recommender import recommend_careers


class TestCareerRecommender(unittest.TestCase):

    def test_returns_three_careers(self):
        student = {
            "interests": ["Software", "AI", "Data"],
            "programming": ["Python"],
            "technical": ["SQL", "Git"],
            "work": "Coding",
        }

        results = recommend_careers(student)

        self.assertEqual(len(results), 3)

    def test_results_are_sorted_by_match(self):
        student = {
            "interests": ["Software", "AI", "Data"],
            "programming": ["Python"],
            "technical": ["SQL", "Git"],
            "work": "Coding",
        }

        results = recommend_careers(student)
        scores = [career["match"] for career in results]

        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_match_scores_are_valid(self):
        student = {
            "interests": ["Web"],
            "programming": ["JavaScript"],
            "technical": ["HTMLCSS"],
            "work": "Design",
        }

        results = recommend_careers(student)

        for career in results:
            self.assertGreaterEqual(career["match"], 0)
            self.assertLessEqual(career["match"], 100)

    def test_results_include_explanations(self):
        student = {
            "interests": ["Software"],
            "programming": ["Python"],
            "technical": ["SQL"],
            "work": "Coding",
        }

        results = recommend_careers(student)

        for career in results:
            self.assertIn("reasons", career)
            self.assertIn("matched_skills", career)
            self.assertIn("skills_to_learn", career)

    def test_empty_assessment_does_not_crash(self):
        results = recommend_careers({
            "interests": [],
            "programming": [],
            "technical": [],
            "work": "",
        })

        self.assertEqual(len(results), 3)

        for career in results:
            self.assertEqual(career["match"], 0)


if __name__ == "__main__":
    unittest.main()
