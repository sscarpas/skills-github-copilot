import sys
import os
import copy
import pytest

# make sure we can import the FastAPI app from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from fastapi.testclient import TestClient
from app import app, activities

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Fixture that restores the in‑memory activities dict after each test."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


def test_get_activities():
    # Arrange: nothing special, activities is in its initial state
    # Act
    response = client.get("/activities")
    # Assert
    assert response.status_code == 200
    assert response.json() == activities


def test_signup_success():
    # Arrange
    activity = "Chess Club"
    email = "newstudent@mergington.edu"
    assert email not in activities[activity]["participants"]
    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})
    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity}"
    assert email in activities[activity]["participants"]


def test_signup_invalid_email():
    # Arrange
    activity = "Chess Club"
    bad_email = "notanemail"
    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": bad_email})
    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid email format"


def test_signup_duplicate():
    # Arrange
    activity = "Chess Club"
    existing = activities[activity]["participants"][0]
    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": existing})
    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_full_activity():
    # Arrange
    activity = "Basketball Team"
    # fill the activity to capacity
    activities[activity]["participants"] = [
        f"user{i}@example.com" for i in range(activities[activity]["max_participants"])
    ]
    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": "latecomer@mergington.edu"})
    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "No seats available for this activity"


def test_signup_activity_not_found():
    # Arrange
    activity = "Nonexistent Club"
    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": "user@mergington.edu"})
    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_success():
    # Arrange
    activity = "Chess Club"
    email = "toremove@mergington.edu"
    # sign the user up first
    client.post(f"/activities/{activity}/signup", params={"email": email})
    assert email in activities[activity]["participants"]
    # Act
    response = client.delete(f"/activities/{activity}/unregister", params={"email": email})
    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from {activity}"
    assert email not in activities[activity]["participants"]


def test_unregister_not_registered():
    # Arrange
    activity = "Chess Club"
    email = "ghost@mergington.edu"
    assert email not in activities[activity]["participants"]
    # Act
    response = client.delete(f"/activities/{activity}/unregister", params={"email": email})
    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not registered for this activity"


def test_unregister_activity_not_found():
    # Arrange
    activity = "No Club"
    # Act
    response = client.delete(f"/activities/{activity}/unregister", params={"email": "user@mergington.edu"})
    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
