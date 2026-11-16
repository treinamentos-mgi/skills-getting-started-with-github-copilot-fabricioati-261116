from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def activity_data(monkeypatch: pytest.MonkeyPatch):
    data = {
        "Test & Chess": {
            "description": "Test chess activity",
            "schedule": "Friday",
            "max_participants": 12,
            "participants": ["student+chess@mergington.edu", "other@mergington.edu"],
        },
        "Other": {
            "description": "Another test activity",
            "schedule": "Monday",
            "max_participants": 10,
            "participants": ["student+chess@mergington.edu"],
        },
    }
    monkeypatch.setattr(app_module, "activities", data)
    return data


@pytest.fixture
def client(activity_data) -> Iterator[TestClient]:
    with TestClient(app_module.app) as test_client:
        yield test_client
