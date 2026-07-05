from django.urls import path

from humanoid_user_registration import field, registration_view, types

urlpatterns = [
    path(
        "register/",
        registration_view(
            fields=[
                field.username,
                field.email(types.email),
                field.given_name(types.string, source="first_name"),
                field.phone_number(types.string, required=False),
            ],
            allow_non_model_fields=True,
            validate_password_strength=False,
        ),
        name="register",
    )
]
