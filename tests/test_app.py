import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.app import activities, app


class UnregisterTests(unittest.TestCase):
    def setUp(self):
        self.email = "student+chess@mergington.edu"
        self.url = "/activities/Test%20%26%20Chess/signup"
        activity_patch = patch.dict(
            activities,
            {
                "Test & Chess": {
                    "description": "Test activity",
                    "schedule": "Friday",
                    "max_participants": 12,
                    "participants": [self.email, "other@mergington.edu"],
                },
                "Other": {"participants": [self.email]},
            },
            clear=True,
        )
        activity_patch.start()
        self.addCleanup(activity_patch.stop)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def test_unregister_updates_activity_and_allows_signup_again(self):
        response = self.client.delete(self.url, params={"email": self.email})

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.email, response.json()["message"])
        data = self.client.get("/activities").json()
        self.assertEqual(data["Test & Chess"]["participants"], ["other@mergington.edu"])
        self.assertEqual(data["Other"]["participants"], [self.email])

        response = self.client.post(self.url, params={"email": self.email})
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.email, self.client.get("/activities").json()["Test & Chess"]["participants"])

    def test_unregister_unknown_activity(self):
        response = self.client.delete("/activities/Missing/signup", params={"email": self.email})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Activity not found")
        self.assertEqual(len(activities["Test & Chess"]["participants"]), 2)

    def test_unregister_missing_participant_leaves_activity_unchanged(self):
        response = self.client.delete(self.url, params={"email": "missing@mergington.edu"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Student is not signed up for this activity")
        self.assertEqual(activities["Test & Chess"]["participants"], [self.email, "other@mergington.edu"])

    def test_unregister_last_participant_then_repeat(self):
        url = "/activities/Other/signup"
        response = self.client.delete(url, params={"email": self.email})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/activities").json()["Other"]["participants"], [])
        response = self.client.delete(url, params={"email": self.email})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(activities["Other"]["participants"], [])
