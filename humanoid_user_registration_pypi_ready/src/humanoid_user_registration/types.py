"""Public field types for humanoid_user_registration.

Use from views.py like:

    from humanoid_user_registration import types
    field.age(types.integer)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FieldType:
    """A small typed value used by the public field builder API."""

    name: str

    def __str__(self) -> str:  # pragma: no cover - tiny convenience method
        return self.name


class Types:
    """Supported serializer field types.

    These are attributes so users do not need to write raw strings:

        field.age(types.integer)
        field.email(types.email)
    """

    string = FieldType("string")
    email = FieldType("email")
    integer = FieldType("integer")
    boolean = FieldType("boolean")
    date = FieldType("date")
    datetime = FieldType("datetime")
    float = FieldType("float")
    decimal = FieldType("decimal")
    url = FieldType("url")
    uuid = FieldType("uuid")
    text = FieldType("text")


# Main public object.
types = Types()

# Optional alias requested by some users. `types` is recommended because `type`
# is a Python built-in, but this alias is supported intentionally.
type = types


__all__ = ["FieldType", "Types", "types", "type"]
