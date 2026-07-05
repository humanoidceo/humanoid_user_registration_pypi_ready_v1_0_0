import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from humanoid_user_registration import field, types
from humanoid_user_registration.serializers import make_registration_serializer


@pytest.mark.django_db
def test_registration_serializer_creates_user_with_source_mapping():
    Serializer = make_registration_serializer(
        fields=[
            field.username,
            field.email(types.email),
            field.given_name(types.string, source="first_name"),
        ],
        validate_password_strength=False,
    )
    serializer = Serializer(
        data={
            "username": "hekmat",
            "email": "hekmat@example.com",
            "given_name": "Hekmat",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }
    )
    assert serializer.is_valid(), serializer.errors
    user = serializer.save()
    assert user.username == "hekmat"
    assert user.email == "hekmat@example.com"
    assert user.first_name == "Hekmat"
    assert user.check_password("StrongPass123!")


@pytest.mark.django_db
def test_registration_serializer_accepts_non_model_fields_when_allowed():
    Serializer = make_registration_serializer(
        fields=[
            field.username,
            field.phone_number(types.string, required=True),
        ],
        allow_non_model_fields=True,
        validate_password_strength=False,
    )
    serializer = Serializer(
        data={
            "username": "hekmat2",
            "phone_number": "0700000000",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }
    )
    assert serializer.is_valid(), serializer.errors
    user = serializer.save()
    assert user.username == "hekmat2"
    assert "phone_number" in serializer.context["humanoid_extra_fields"]


@pytest.mark.django_db
def test_registration_api_view():
    client = APIClient()
    response = client.post(
        "/register/",
        {
            "username": "apiuser",
            "email": "apiuser@example.com",
            "given_name": "API",
            "phone_number": "0700000000",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        },
        format="json",
    )
    assert response.status_code == 201, response.data
    assert response.data["user"]["username"] == "apiuser"
    assert response.data["user"]["given_name"] == "API"
    assert response.data["user"]["phone_number"] == "0700000000"
    assert get_user_model().objects.filter(username="apiuser").exists()
