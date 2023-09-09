import unittest
from app import app, db
from models import Moodboard, User, Mood


class MoodboardTests(unittest.TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()

        self.client = app.test_client()

        # Disable CSRF for testing
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///moodboard_test"

        db.create_all()

        # Create sample data for tests
        user = User(
            name="Sample User", password="sample_password", email="sample@example.com"
        )
        mood = Mood(mood_name="Happy")
        db.session.add_all([user, mood])
        db.session.commit()

    def tearDown(self):
        db.session.close()
        db.drop_all()
        self.app_context.pop()

    def test_homepage(self):
        response = self.client.get("/")
        self.assertIn(b"<h1>Moodboard</h1>", response.data)


    def test_moodboard_creation(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1  # Use the sample user id from setup

        data = {
            "title": "New Moodboard",
            "description": "This is a test moodboard",
            "mood": "Happy",
        }

        response = self.client.post(
            "/create_moodboard", data=data, follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)

        moodboard = Moodboard.query.filter_by(title="New Moodboard").first()
        self.assertIsNotNone(moodboard)

    def test_sample_data_exists(self):
        user = User.query.filter_by(name="Sample User").first()
        mood = Mood.query.filter_by(mood_name="Happy").first()

        self.assertIsNotNone(user)
        self.assertIsNotNone(mood)


if __name__ == "__main__":
    unittest.main()
