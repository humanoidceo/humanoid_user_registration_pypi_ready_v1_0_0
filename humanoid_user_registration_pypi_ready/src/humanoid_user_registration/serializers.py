"""Dynamic serializers used by humanoid_user_registration."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any

from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .fields import FieldSpec, normalize_fields

PostRegisterHook = Callable[[Any, Any], None]


MODEL_FIELD_BLACKLIST = {
    "id",
    "pk",
    "password",
    "last_login",
    "is_superuser",
    "is_staff",
    "is_active",
    "date_joined",
    "groups",
    "user_permissions",
}


class NonModelFieldError(ValueError):
    """Raised when a non-model field is not allowed."""


class UnknownFieldTypeError(ValueError):
    """Raised when the toolkit receives an unknown field type."""


class RegistrationConfigurationError(ValueError):
    """Raised when the registration view is configured incorrectly."""


def get_user_model_field_names(user_model: type | None = None) -> set[str]:
    """Return concrete field names from the active User model."""

    model = user_model or get_user_model()
    names: set[str] = set()
    for model_field in model._meta.get_fields():
        if getattr(model_field, "concrete", False) and not getattr(
            model_field, "many_to_many", False
        ):
            names.add(model_field.name)
    return names


def get_model_field(user_model: type, name: str) -> Any | None:
    """Return a Django model field, or None if it does not exist."""

    try:
        return user_model._meta.get_field(name)
    except Exception:  # noqa: BLE001 - Django raises FieldDoesNotExist
        return None


def is_savable_user_field(user_model: type, name: str) -> bool:
    """Return True if a value can safely be passed to create_user()."""

    if name in MODEL_FIELD_BLACKLIST:
        return False
    model_field = get_model_field(user_model, name)
    if model_field is None:
        return False
    if getattr(model_field, "many_to_many", False):
        return False
    if not getattr(model_field, "editable", True):
        return False
    return True


def build_drf_field(
    spec: FieldSpec,
    *,
    user_model: type,
    allow_non_model_fields: bool,
) -> serializers.Field:
    """Build a DRF serializer field from a FieldSpec."""

    target_name = spec.target_name
    model_field = get_model_field(user_model, target_name)
    target_exists = model_field is not None

    if not target_exists and not allow_non_model_fields:
        raise NonModelFieldError(
            f"'{spec.name}' targets '{target_name}', "
            f"but '{target_name}' does not exist "
            "on the active User model. Set allow_non_model_fields=True to accept "
            "it without saving it, or add the field to your User model."
        )

    field_kwargs: dict[str, Any] = {
        "required": spec.required,
        "write_only": spec.write_only,
        "read_only": spec.read_only,
        "allow_null": spec.allow_null,
    }

    if spec.source and spec.source != spec.name:
        field_kwargs["source"] = spec.source

    if spec.default is not None:
        field_kwargs["default"] = spec.default
        field_kwargs["required"] = False

    if spec.help_text is not None:
        field_kwargs["help_text"] = spec.help_text

    if spec.label is not None:
        field_kwargs["label"] = spec.label

    if spec.extra:
        field_kwargs.update(spec.extra)

    type_name = spec.type_name.lower()

    # If the target is a real model field and is unique, add DRF's UniqueValidator.
    if target_exists and getattr(model_field, "unique", False):
        validators = list(field_kwargs.pop("validators", []))
        validators.append(UniqueValidator(queryset=user_model.objects.all()))
        field_kwargs["validators"] = validators

    if type_name in {"string", "str"}:
        if spec.allow_blank is not None:
            field_kwargs["allow_blank"] = spec.allow_blank
        else:
            field_kwargs["allow_blank"] = not spec.required
        if spec.max_length is not None:
            field_kwargs["max_length"] = spec.max_length
        elif target_exists and getattr(model_field, "max_length", None):
            field_kwargs["max_length"] = model_field.max_length
        if spec.min_length is not None:
            field_kwargs["min_length"] = spec.min_length
        return serializers.CharField(**field_kwargs)

    if type_name == "text":
        if spec.allow_blank is not None:
            field_kwargs["allow_blank"] = spec.allow_blank
        else:
            field_kwargs["allow_blank"] = not spec.required
        if spec.max_length is not None:
            field_kwargs["max_length"] = spec.max_length
        if spec.min_length is not None:
            field_kwargs["min_length"] = spec.min_length
        return serializers.CharField(**field_kwargs)

    if type_name == "email":
        if spec.allow_blank is not None:
            field_kwargs["allow_blank"] = spec.allow_blank
        else:
            field_kwargs["allow_blank"] = not spec.required
        if spec.max_length is not None:
            field_kwargs["max_length"] = spec.max_length
        elif target_exists and getattr(model_field, "max_length", None):
            field_kwargs["max_length"] = model_field.max_length
        return serializers.EmailField(**field_kwargs)

    if type_name in {"integer", "int"}:
        return serializers.IntegerField(**field_kwargs)

    if type_name in {"boolean", "bool"}:
        return serializers.BooleanField(**field_kwargs)

    if type_name == "date":
        return serializers.DateField(**field_kwargs)

    if type_name in {"datetime", "date_time"}:
        return serializers.DateTimeField(**field_kwargs)

    if type_name == "float":
        return serializers.FloatField(**field_kwargs)

    if type_name == "decimal":
        decimal_kwargs = {
            "max_digits": 12,
            "decimal_places": 2,
        }
        decimal_kwargs.update(field_kwargs)
        return serializers.DecimalField(**decimal_kwargs)

    if type_name == "url":
        if spec.allow_blank is not None:
            field_kwargs["allow_blank"] = spec.allow_blank
        else:
            field_kwargs["allow_blank"] = not spec.required
        return serializers.URLField(**field_kwargs)

    if type_name == "uuid":
        return serializers.UUIDField(**field_kwargs)

    raise UnknownFieldTypeError(
        f"Unknown field type '{spec.type_name}' for field '{spec.name}'. "
        "Supported types: string, email, integer, boolean, date, datetime, "
        "float, decimal, url, uuid, text."
    )


def make_registration_serializer(
    *,
    fields: list[FieldSpec | str | dict[str, Any]],
    allow_non_model_fields: bool = False,
    response_fields: list[str] | None = None,
    require_password_confirmation: bool = True,
    validate_password_strength: bool = True,
    password_min_length: int | None = None,
    post_register_hook: PostRegisterHook | None = None,
    user_model: type | None = None,
) -> type[serializers.Serializer]:
    """Create a configured DRF serializer class for user registration."""

    normalized_fields = normalize_fields(fields)
    UserModel = user_model or get_user_model()

    # Validate early so configuration errors appear when Django imports views.py.
    for spec in normalized_fields:
        build_drf_field(
            spec,
            user_model=UserModel,
            allow_non_model_fields=allow_non_model_fields,
        )

    class HumanoidRegistrationSerializer(serializers.Serializer):
        password = serializers.CharField(
            write_only=True,
            required=True,
            min_length=password_min_length,
            style={"input_type": "password"},
        )
        if require_password_confirmation:
            password_confirm = serializers.CharField(
                write_only=True,
                required=True,
                style={"input_type": "password"},
            )

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            for item in normalized_fields:
                self.fields[item.name] = build_drf_field(
                    item,
                    user_model=UserModel,
                    allow_non_model_fields=allow_non_model_fields,
                )

        def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
            password = attrs.get("password")
            password_confirm = attrs.get("password_confirm")

            if require_password_confirmation and password != password_confirm:
                raise serializers.ValidationError(
                    {"password_confirm": "Password and password_confirm do not match."}
                )

            if validate_password_strength and password:
                # Build a temporary unsaved user so Django validators can inspect it.
                user_kwargs = self._build_user_kwargs(attrs)
                temp_user = UserModel(**user_kwargs)
                try:
                    password_validation.validate_password(password, temp_user)
                except DjangoValidationError as exc:
                    raise serializers.ValidationError(
                        {"password": list(exc.messages)}
                    ) from exc

            return attrs

        def _build_user_kwargs(self, attrs: dict[str, Any]) -> dict[str, Any]:
            user_kwargs: dict[str, Any] = {}
            for spec in normalized_fields:
                target_name = spec.target_name
                if target_name not in attrs:
                    continue
                if is_savable_user_field(UserModel, target_name):
                    user_kwargs[target_name] = attrs[target_name]
            return user_kwargs

        def _build_extra_payload(self, attrs: dict[str, Any]) -> dict[str, Any]:
            extra: dict[str, Any] = {}
            for spec in normalized_fields:
                target_name = spec.target_name
                value_key = target_name if spec.source else spec.name
                if value_key not in attrs:
                    continue
                if not is_savable_user_field(UserModel, target_name):
                    extra[spec.name] = attrs[value_key]
            return extra

        @transaction.atomic
        def create(self, validated_data: dict[str, Any]) -> Any:
            password = validated_data.pop("password")
            validated_data.pop("password_confirm", None)

            user_kwargs = self._build_user_kwargs(validated_data)

            try:
                user = UserModel.objects.create_user(password=password, **user_kwargs)
            except TypeError as exc:
                raise serializers.ValidationError(
                    {
                        "detail": (
                            "Could not create user. Check your configured fields. "
                            "Only real User model fields can be saved."
                        )
                    }
                ) from exc
            except IntegrityError as exc:
                raise serializers.ValidationError(
                    {"detail": "A user with these details already exists."}
                ) from exc

            extra_payload = self._build_extra_payload(validated_data)
            self.context["humanoid_extra_fields"] = extra_payload

            request = self.context.get("request")
            if post_register_hook:
                parameters = inspect.signature(post_register_hook).parameters
                if len(parameters) >= 3:
                    post_register_hook(user, request, extra_payload)
                else:
                    post_register_hook(user, request)

            return user

        def to_representation(self, instance: Any) -> dict[str, Any]:
            if response_fields is None:
                selected_fields = ["id"] + [item.name for item in normalized_fields]
            else:
                selected_fields = response_fields

            output: dict[str, Any] = {}
            extra_payload = self.context.get("humanoid_extra_fields", {})

            for name in selected_fields:
                if hasattr(instance, name):
                    output[name] = getattr(instance, name)
                    continue

                # Support API field names that are mapped through source.
                spec = next(
                    (item for item in normalized_fields if item.name == name),
                    None,
                )
                if spec and hasattr(instance, spec.target_name):
                    output[name] = getattr(instance, spec.target_name)
                    continue

                if name in extra_payload:
                    output[name] = extra_payload[name]

            return output

    return HumanoidRegistrationSerializer


__all__ = [
    "NonModelFieldError",
    "PostRegisterHook",
    "RegistrationConfigurationError",
    "UnknownFieldTypeError",
    "build_drf_field",
    "get_user_model_field_names",
    "is_savable_user_field",
    "make_registration_serializer",
]
