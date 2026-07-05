"""Optional built-in URLs.

Most users of this package only import `registration_view` in their own views.py.
This file exists only for simple demos or quick starts.
"""

from django.urls import path

from . import field, registration_view, types

app_name = "humanoid_user_registration"

register = registration_view(
    fields=[
        field.username,
        field.email(types.email, required=True),
        field.first_name(required=False),
        field.last_name(required=False),
    ]
)

urlpatterns = [
    path("register/", register, name="register"),
]
