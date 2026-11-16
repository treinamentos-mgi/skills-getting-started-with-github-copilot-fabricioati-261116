from copy import deepcopy

import pytest


ACTIVITY_NAME = "Test & Chess"
SIGNUP_URL = "/activities/Test%20%26%20Chess/signup"
STUDENT_EMAIL = "student+chess@mergington.edu"


def test_root_redirects_to_homepage(client):
    # Arrange
    url = "/"

    # Act
    response = client.get(url, follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_details_and_participants(client, activity_data):
    # Arrange
    expected = deepcopy(activity_data)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected


def test_signup_adds_participant_only_to_selected_activity(client, activity_data):
    # Arrange
    email = "new+student@mergington.edu"
    expected = deepcopy(activity_data)
    expected[ACTIVITY_NAME]["participants"].append(email)

    # Act
    response = client.post(SIGNUP_URL, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {ACTIVITY_NAME}"}
    assert client.get("/activities").json() == expected


def test_signup_rejects_duplicate_without_changing_activities(client, activity_data):
    # Arrange
    expected = deepcopy(activity_data)

    # Act
    response = client.post(SIGNUP_URL, params={"email": STUDENT_EMAIL})

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}
    assert client.get("/activities").json() == expected


def test_signup_rejects_unknown_activity(client, activity_data):
    # Arrange
    expected = deepcopy(activity_data)
    url = "/activities/Missing/signup"

    # Act
    response = client.post(url, params={"email": STUDENT_EMAIL})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert client.get("/activities").json() == expected


def test_unregister_removes_only_selected_participant(client, activity_data):
    # Arrange
    expected = deepcopy(activity_data)
    expected[ACTIVITY_NAME]["participants"].remove(STUDENT_EMAIL)

    # Act
    response = client.delete(SIGNUP_URL, params={"email": STUDENT_EMAIL})

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {STUDENT_EMAIL} from {ACTIVITY_NAME}"
    }
    assert client.get("/activities").json() == expected


def test_unregister_rejects_unknown_activity(client, activity_data):
    # Arrange
    expected = deepcopy(activity_data)
    url = "/activities/Missing/signup"

    # Act
    response = client.delete(url, params={"email": STUDENT_EMAIL})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert client.get("/activities").json() == expected


def test_unregister_rejects_missing_participant(client, activity_data):
    # Arrange
    expected = deepcopy(activity_data)
    email = "missing@mergington.edu"

    # Act
    response = client.delete(SIGNUP_URL, params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student is not signed up for this activity"}
    assert client.get("/activities").json() == expected


def test_unregister_last_participant_leaves_empty_list(client, activity_data):
    # Arrange
    url = "/activities/Other/signup"
    expected = deepcopy(activity_data)
    expected["Other"]["participants"] = []

    # Act
    response = client.delete(url, params={"email": STUDENT_EMAIL})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {STUDENT_EMAIL} from Other"}
    assert client.get("/activities").json() == expected


def test_unregister_repeated_cancellation_preserves_empty_list(client, activity_data):
    # Arrange
    url = "/activities/Other/signup"
    assert client.delete(url, params={"email": STUDENT_EMAIL}).status_code == 200
    expected = deepcopy(activity_data)

    # Act
    response = client.delete(url, params={"email": STUDENT_EMAIL})

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student is not signed up for this activity"}
    data = client.get("/activities").json()
    assert data["Other"]["participants"] == []
    assert data == expected


def test_signup_after_cancellation_adds_participant_once(client, activity_data):
    # Arrange
    assert client.delete(SIGNUP_URL, params={"email": STUDENT_EMAIL}).status_code == 200
    expected = deepcopy(activity_data)
    expected[ACTIVITY_NAME]["participants"].append(STUDENT_EMAIL)

    # Act
    response = client.post(SIGNUP_URL, params={"email": STUDENT_EMAIL})

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {STUDENT_EMAIL} for {ACTIVITY_NAME}"
    }
    data = client.get("/activities").json()
    assert data[ACTIVITY_NAME]["participants"].count(STUDENT_EMAIL) == 1
    assert data == expected


@pytest.mark.parametrize("method", ["POST", "DELETE"])
def test_signup_and_unregister_require_email(client, activity_data, method):
    # Arrange
    expected = deepcopy(activity_data)

    # Act
    response = client.request(method, SIGNUP_URL)

    # Assert
    assert response.status_code == 422
    assert any(
        error["loc"] == ["query", "email"] for error in response.json()["detail"]
    )
    assert client.get("/activities").json() == expected
