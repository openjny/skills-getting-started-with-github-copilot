"""Tests for the Mergington High School Activities API."""
import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to their original state before each test."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


# --- GET / ---

class TestRoot:
    def test_root_redirects_to_index(self, client):
        # Arrange & Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


# --- GET /activities ---

class TestGetActivities:
    def test_get_activities_returns_all(self, client):
        # Arrange (nothing extra needed)

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) >= 3

    def test_get_activities_contains_expected_keys(self, client):
        # Arrange & Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        for name, details in data.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details


# --- POST /activities/{activity_name}/signup ---

class TestSignup:
    def test_signup_success(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "testuser@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        assert email in activities[activity_name]["participants"]

    def test_signup_activity_not_found(self, client):
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "testuser@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # already registered

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is already signed up"


# --- DELETE /activities/{activity_name}/unregister ---

class TestUnregister:
    def test_unregister_success(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # already registered

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
        assert email not in activities[activity_name]["participants"]

    def test_unregister_activity_not_found(self, client):
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "testuser@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_not_registered(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "nobody@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is not registered for this activity"
