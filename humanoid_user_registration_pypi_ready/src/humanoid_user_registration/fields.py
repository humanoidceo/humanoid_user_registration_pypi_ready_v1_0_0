"""Field builder API for humanoid_user_registration.

Example:

    from humanoid_user_registration import field, types

    fields=[
        field.username,
        field.email(types.email, required=True),
        field.given_name(types.string, source="first_name"),
        field.age(types.integer, required=False),
    ]
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Any

from .types import FieldType, types


@dataclass(frozen=True)
class FieldSpec:
    """Definition of one incoming registration field.

    Parameters
    ----------
    name:
        The field name used by the API request body.
    field_type:
        One of the public field types, for example `types.string`.
    required:
        Whether this field is required in the incoming request.
    source:
        Optional model/user field name where this value should be saved.
        Example: `field.given_name(types.string, source="first_name")` means
        the API receives `given_name`, but the User model receives `first_name`.
    write_only:
        Hide the field from the API response.
    read_only:
        Accept no input for the field. Usually not needed for registration.
    allow_blank:
        Allow empty string values for string-like fields.
    allow_null:
        Allow null values.
    default:
        Optional default value.
    max_length/min_length:
        Validation helpers for string-like fields.
    help_text/label:
        Optional DRF metadata.
    extra:
        Additional keyword arguments passed to the DRF serializer field.
    """

    name: str
    field_type: FieldType | str = types.string
    required: bool = True
    source: str | None = None
    write_only: bool = False
    read_only: bool = False
    allow_blank: bool | None = None
    allow_null: bool = False
    default: Any = None
    max_length: int | None = None
    min_length: int | None = None
    help_text: str | None = None
    label: str | None = None
    extra: Mapping[str, Any] | None = None

    def __call__(
        self,
        field_type: FieldType | str | None = None,
        *,
        required: bool | None = None,
        source: str | None = None,
        write_only: bool | None = None,
        read_only: bool | None = None,
        allow_blank: bool | None = None,
        allow_null: bool | None = None,
        default: Any = None,
        max_length: int | None = None,
        min_length: int | None = None,
        help_text: str | None = None,
        label: str | None = None,
        **extra: Any,
    ) -> FieldSpec:
        """Return a copied field with new options.

        This makes `field.age(types.integer, required=False)` possible.
        """

        updates: dict[str, Any] = {}
        if field_type is not None:
            updates["field_type"] = field_type
        if required is not None:
            updates["required"] = required
        if source is not None:
            updates["source"] = source
        if write_only is not None:
            updates["write_only"] = write_only
        if read_only is not None:
            updates["read_only"] = read_only
        if allow_blank is not None:
            updates["allow_blank"] = allow_blank
        if allow_null is not None:
            updates["allow_null"] = allow_null
        if default is not None:
            updates["default"] = default
        if max_length is not None:
            updates["max_length"] = max_length
        if min_length is not None:
            updates["min_length"] = min_length
        if help_text is not None:
            updates["help_text"] = help_text
        if label is not None:
            updates["label"] = label
        if extra:
            current_extra = dict(self.extra or {})
            current_extra.update(extra)
            updates["extra"] = current_extra
        return replace(self, **updates)

    @property
    def target_name(self) -> str:
        """The User model field that receives this value."""

        return self.source or self.name

    @property
    def type_name(self) -> str:
        """Return the serializer type as a simple string."""

        if isinstance(self.field_type, FieldType):
            return self.field_type.name
        return str(self.field_type)

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation of the field spec."""

        return {
            "name": self.name,
            "type": self.type_name,
            "required": self.required,
            "source": self.source,
            "write_only": self.write_only,
            "read_only": self.read_only,
            "allow_blank": self.allow_blank,
            "allow_null": self.allow_null,
            "default": self.default,
            "max_length": self.max_length,
            "min_length": self.min_length,
            "help_text": self.help_text,
            "label": self.label,
            "extra": dict(self.extra or {}),
        }


class FieldBuilder:
    """Dynamic field builder.

    Any attribute becomes a FieldSpec:

        field.username
        field.phone_number(types.string)
        field.age(types.integer)
    """

    def __getattr__(self, name: str) -> FieldSpec:
        if name.startswith("_"):
            raise AttributeError(name)
        return FieldSpec(name=name)

    def custom(
        self,
        name: str,
        field_type: FieldType | str = types.string,
        **options: Any,
    ) -> FieldSpec:
        """Create a field whose name is only known at runtime."""

        return FieldSpec(name=name, field_type=field_type)(**options)


field = FieldBuilder()


def normalize_field(spec: FieldSpec | str | Mapping[str, Any]) -> FieldSpec:
    """Normalize all supported field styles into FieldSpec.

    Supported inputs:

    - `field.username`
    - `"username"`
    - `{ "name": "age", "type": "integer", "required": False }`
    """

    if isinstance(spec, FieldSpec):
        return spec

    if isinstance(spec, str):
        return FieldSpec(name=spec)

    if isinstance(spec, Mapping):
        data = dict(spec)
        name = data.pop("name", None)
        if not name:
            raise ValueError("Field dictionaries must include a 'name' key.")
        field_type = data.pop("type", data.pop("field_type", types.string))
        return FieldSpec(name=name, field_type=field_type)(**data)

    raise TypeError(
        "Fields must be FieldSpec objects, strings, or dictionaries. "
        f"Received: {spec!r}"
    )


def normalize_fields(
    specs: list[FieldSpec | str | Mapping[str, Any]],
) -> list[FieldSpec]:
    """Normalize and validate a list of field definitions."""

    normalized = [normalize_field(item) for item in specs]
    seen: set[str] = set()
    duplicates: set[str] = set()
    for item in normalized:
        if item.name in seen:
            duplicates.add(item.name)
        seen.add(item.name)
    if duplicates:
        duplicate_list = ", ".join(sorted(duplicates))
        raise ValueError(f"Duplicate API field names are not allowed: {duplicate_list}")
    return normalized


__all__ = [
    "FieldSpec",
    "FieldBuilder",
    "field",
    "normalize_field",
    "normalize_fields",
]
