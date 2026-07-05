"""Public view helpers for humanoid_user_registration."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .serializers import make_registration_serializer


def _maybe_create_token(user: Any) -> str | None:
    """Create or return a DRF token if rest_framework.authtoken is installed."""

    try:
        from rest_framework.authtoken.models import Token
    except Exception:  # noqa: BLE001 - optional dependency path
        return None

    token, _created = Token.objects.get_or_create(user=user)
    return token.key


def registration_view(
    *,
    fields: list[Any],
    allow_non_model_fields: bool = False,
    response_fields: list[str] | None = None,
    require_password_confirmation: bool = True,
    validate_password_strength: bool = True,
    password_min_length: int | None = None,
    post_register_hook: Callable[[Any, Any], None] | None = None,
    success_message: str = "Registration successful.",
    status_code: int = status.HTTP_201_CREATED,
    permission_classes: list[type] | tuple[type, ...] | None = None,
    authentication_classes: list[type] | tuple[type, ...] | None = None,
    throttle_classes: list[type] | tuple[type, ...] | None = None,
    include_token: bool = False,
) -> Callable[..., Any]:
    """Return a ready-to-use DRF registration view.

    This is the main API. Use it in `views.py`:

        from humanoid_user_registration import registration_view, field, types

        register = registration_view(
            fields=[
                field.username,
                field.email(types.email),
                field.given_name(types.string, source="first_name"),
            ],
        )

    Then connect your existing project URL to `register`.
    """

    SerializerClass = make_registration_serializer(
        fields=fields,
        allow_non_model_fields=allow_non_model_fields,
        response_fields=response_fields,
        require_password_confirmation=require_password_confirmation,
        validate_password_strength=validate_password_strength,
        password_min_length=password_min_length,
        post_register_hook=post_register_hook,
    )

    PermissionClasses = list(permission_classes or [permissions.AllowAny])
    AuthenticationClasses = (
        list(authentication_classes) if authentication_classes is not None else None
    )
    ThrottleClasses = list(throttle_classes) if throttle_classes is not None else None

    class HumanoidRegistrationView(generics.CreateAPIView):
        serializer_class = SerializerClass
        permission_classes = PermissionClasses

        if AuthenticationClasses is not None:
            authentication_classes = AuthenticationClasses
        if ThrottleClasses is not None:
            throttle_classes = ThrottleClasses

        def create(self, request: Any, *args: Any, **kwargs: Any) -> Response:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            data: dict[str, Any] = {
                "message": success_message,
                "user": serializer.to_representation(user),
            }
            if include_token:
                token = _maybe_create_token(user)
                if token is not None:
                    data["token"] = token
            headers = self.get_success_headers(serializer.data)
            return Response(data, status=status_code, headers=headers)

    return HumanoidRegistrationView.as_view()


__all__ = ["registration_view"]
