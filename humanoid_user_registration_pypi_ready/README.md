# Humanoid User Registration

**Humanoid User Registration** is a tiny toolkit on top of **Django REST Framework** that helps you create a flexible user registration API from `views.py` in only a few lines.

It is designed for developers who do not want to write a new serializer every time they need user registration.

```python
from humanoid_user_registration import registration_view, field, types

register = registration_view(
    fields=[
        field.username,
        field.email(types.email, required=True),
        field.given_name(types.string, source="first_name"),
        field.family_name(types.string, source="last_name"),
        field.phone_number(types.string, required=True),
    ],
    allow_non_model_fields=True,
)
```

---

## Main idea

You configure registration directly inside your Django `views.py`.

You do **not** need to add package settings like this:

```python
HUMANOID_USER_REGISTRATION = {...}
```

You do **not** need to create a custom registration serializer manually.

You do **not** need to add this package to `INSTALLED_APPS` unless you want to use optional features from your own project.

You only import the toolkit and create a DRF view.

---

## Installation

```bash
pip install humanoid-user-registration
```

Development install from local source:

```bash
pip install -e .
```

---

## Requirements

- Python 3.9+
- Django 4.2+
- Django REST Framework 3.14+

---

## Quick start

### 1. Create your registration view in `views.py`

```python
from humanoid_user_registration import registration_view, field, types

register = registration_view(
    fields=[
        field.username,
        field.email(types.email, required=True),
        field.first_name(required=False),
        field.last_name(required=False),
    ]
)
```

### 2. Connect your URL

Your Django project still needs a URL route. This is a Django rule: a request cannot reach a view unless some URL points to it.

Example in `urls.py`:

```python
from django.urls import path
from .views import register

urlpatterns = [
    path("api/auth/register/", register, name="register"),
]
```

If your project already routes to this `views.py`, then you only work in `views.py`.

### 3. Send a POST request

```json
{
  "username": "hekmat",
  "email": "hekmat@example.com",
  "first_name": "Hekmat",
  "last_name": "Rahimi",
  "password": "StrongPass123!",
  "password_confirm": "StrongPass123!"
}
```

Example success response:

```json
{
  "message": "Registration successful.",
  "user": {
    "id": 1,
    "username": "hekmat",
    "email": "hekmat@example.com",
    "first_name": "Hekmat",
    "last_name": "Rahimi"
  }
}
```

---

## Important: JSON keys need quotation marks

In JSON, keys must use quotation marks:

```json
{
  "username": "hekmat"
}
```

This is invalid JSON:

```json
{
  username: "hekmat"
}
```

But inside Python `views.py`, the toolkit lets you avoid raw string dictionaries by using this clean style:

```python
field.age(types.integer)
field.phone_number(types.string)
field.given_name(types.string, source="first_name")
```

---

## Field syntax

### Simple model fields

```python
from humanoid_user_registration import registration_view, field, types

register = registration_view(
    fields=[
        field.username,
        field.email(types.email),
        field.first_name,
        field.last_name,
    ]
)
```

### Required and optional fields

```python
register = registration_view(
    fields=[
        field.username,
        field.email(types.email, required=True),
        field.first_name(required=False),
        field.last_name(required=False),
    ]
)
```

### More field types

```python
register = registration_view(
    fields=[
        field.username,
        field.email(types.email),
        field.age(types.integer, required=False),
        field.is_student(types.boolean, required=False),
        field.date_of_birth(types.date, required=False),
        field.website(types.url, required=False),
    ],
    allow_non_model_fields=True,
)
```

---

## Supported field types

Use these inside `views.py`:

```python
types.string
types.email
types.integer
types.boolean
types.date
types.datetime
types.float
types.decimal
types.url
types.uuid
types.text
```

There is also a `type` alias:

```python
from humanoid_user_registration import registration_view, field, type

register = registration_view(
    fields=[
        field.username,
        field.age(type.integer),
    ]
)
```

But `types.integer` is recommended because `type` is already a Python built-in name.

---

## Rename API fields with `source`

Sometimes your frontend field name is different from your Django User model field name.

Example: frontend sends `given_name`, but Django User model has `first_name`.

```python
register = registration_view(
    fields=[
        field.username,
        field.email(types.email),
        field.given_name(types.string, source="first_name"),
        field.family_name(types.string, source="last_name"),
    ]
)
```

Frontend request:

```json
{
  "username": "hekmat",
  "email": "hekmat@example.com",
  "given_name": "Hekmat",
  "family_name": "Rahimi",
  "password": "StrongPass123!",
  "password_confirm": "StrongPass123!"
}
```

Saved in Django:

```text
given_name  -> User.first_name
family_name -> User.last_name
```

---

## Add non-model fields

A **model field** is a real database/User model field. For Django's default User model, common fields are:

```text
username
email
first_name
last_name
password
```

A **non-model field** is a field that does not exist in your User model, for example:

```text
phone_number
address
nid_number
age
```

To accept non-model fields:

```python
register = registration_view(
    fields=[
        field.username,
        field.email(types.email),
        field.phone_number(types.string, required=True),
        field.address(types.string, required=False),
        field.age(types.integer, required=False),
    ],
    allow_non_model_fields=True,
)
```

Request:

```json
{
  "username": "hekmat",
  "email": "hekmat@example.com",
  "phone_number": "0700000000",
  "address": "Kabul",
  "age": 22,
  "password": "StrongPass123!",
  "password_confirm": "StrongPass123!"
}
```

What happens:

```text
username      saved if User.username exists
email         saved if User.email exists
phone_number  accepted and returned, but not permanently saved unless User.phone_number exists
address       accepted and returned, but not permanently saved unless User.address exists
age           accepted and returned, but not permanently saved unless User.age exists
```

Important: `allow_non_model_fields=True` does not create database columns. It only allows the API to accept extra fields without crashing.

If you want non-model fields to be saved permanently, use one of these professional options:

1. Add the fields to your custom User model.
2. Create a separate Profile model.
3. Save the extra values in a `post_register_hook`.

---

## Use `post_register_hook`

You can run custom logic after the user is created.

```python
from humanoid_user_registration import registration_view, field, types


def after_register(user, request):
    phone_number = request.data.get("phone_number")
    print("New user:", user.username)
    print("Phone:", phone_number)


register = registration_view(
    fields=[
        field.username,
        field.email(types.email),
        field.phone_number(types.string, required=True),
    ],
    allow_non_model_fields=True,
    post_register_hook=after_register,
)
```

You can also define a hook with three parameters:

```python
def after_register(user, request, extra_fields):
    print(extra_fields)
```

The toolkit will pass non-model fields to `extra_fields`.

---

## Custom response fields

By default, the response includes `id` and the configured fields.

You can control the response:

```python
register = registration_view(
    fields=[
        field.username,
        field.email(types.email),
        field.given_name(types.string, source="first_name"),
    ],
    response_fields=["id", "username", "email", "given_name"],
)
```

---

## Disable password confirmation

Default request requires both:

```json
{
  "password": "StrongPass123!",
  "password_confirm": "StrongPass123!"
}
```

To use only `password`:

```python
register = registration_view(
    fields=[field.username, field.email(types.email)],
    require_password_confirmation=False,
)
```

---

## Password validation

By default, the toolkit calls Django's password validators.

To disable password strength validation:

```python
register = registration_view(
    fields=[field.username, field.email(types.email)],
    validate_password_strength=False,
)
```

To add a minimum length at serializer level:

```python
register = registration_view(
    fields=[field.username, field.email(types.email)],
    password_min_length=8,
)
```

---

## Include DRF token in response

If your project uses DRF TokenAuthentication and has `rest_framework.authtoken` installed, you can return a token after registration.

```python
register = registration_view(
    fields=[field.username, field.email(types.email)],
    include_token=True,
)
```

Response:

```json
{
  "message": "Registration successful.",
  "user": {
    "id": 1,
    "username": "hekmat",
    "email": "hekmat@example.com"
  },
  "token": "abc123..."
}
```

If `rest_framework.authtoken` is not installed, the user is still created, but no token is returned.

---

## Custom permissions, authentication, and throttling

```python
from rest_framework.throttling import AnonRateThrottle

register = registration_view(
    fields=[field.username, field.email(types.email)],
    throttle_classes=[AnonRateThrottle],
)
```

By default, registration uses `AllowAny` permission.

---

## Full realistic example

```python
# views.py
from humanoid_user_registration import registration_view, field, types


def after_register(user, request, extra_fields):
    # Example: save phone_number to a Profile table in your own project.
    # Profile.objects.create(user=user, phone_number=extra_fields.get("phone_number"))
    pass


register = registration_view(
    fields=[
        field.username,
        field.email(types.email, required=True),
        field.given_name(types.string, source="first_name", required=True),
        field.family_name(types.string, source="last_name", required=False),
        field.phone_number(types.string, required=True),
        field.age(types.integer, required=False),
        field.date_of_birth(types.date, required=False),
    ],
    allow_non_model_fields=True,
    response_fields=[
        "id",
        "username",
        "email",
        "given_name",
        "family_name",
        "phone_number",
        "age",
        "date_of_birth",
    ],
    post_register_hook=after_register,
)
```

Request:

```json
{
  "username": "hekmat",
  "email": "hekmat@example.com",
  "given_name": "Hekmat",
  "family_name": "Rahimi",
  "phone_number": "0700000000",
  "age": 22,
  "date_of_birth": "2004-01-01",
  "password": "StrongPass123!",
  "password_confirm": "StrongPass123!"
}
```

---

## Older supported styles

The recommended style is:

```python
field.age(types.integer, required=False)
```

But these also work:

```python
"username"
```

```python
{"name": "age", "type": "integer", "required": False}
```

This keeps the toolkit flexible.

---

## Optional built-in URL

The package includes an optional default URL:

```python
from django.urls import include, path

urlpatterns = [
    path("api/auth/", include("humanoid_user_registration.urls")),
]
```

This creates:

```text
POST /api/auth/register/
```

But the main goal of this package is still the `views.py` style.

---

## Development

Clone the project:

```bash
git clone https://github.com/your-username/humanoid-user-registration.git
cd humanoid-user-registration
```

Install dev dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Run linting:

```bash
ruff check .
```

Build package:

```bash
python -m build
```

Check package:

```bash
python -m twine check dist/*
```

Upload to TestPyPI:

```bash
python -m twine upload --repository testpypi dist/*
```

Upload to PyPI:

```bash
python -m twine upload dist/*
```

---

## GitHub Actions publishing

This package includes `.github/workflows/publish.yml` for PyPI Trusted Publishing.

Recommended flow:

1. Push your code to GitHub.
2. Create the project on PyPI.
3. Configure Trusted Publisher on PyPI for your GitHub repository.
4. Create a GitHub release.
5. GitHub Actions builds and publishes the package.

---

## Security notes

- This toolkit uses Django's active User model through `get_user_model()`.
- Passwords are saved through Django's `create_user()` method.
- Django password validators are enabled by default.
- Non-model fields are not saved unless you save them yourself through a hook or your own model.
- Always use HTTPS in production.
- Add throttling/rate limiting to public registration endpoints.

---

## License

MIT License.
