"""Humanoid User Registration.

A small DRF toolkit for user registration in a few lines from views.py.
"""

from .fields import FieldBuilder, FieldSpec, field
from .serializers import make_registration_serializer
from .types import FieldType, Types, type, types
from .views import registration_view

__version__ = "1.0.0"

__all__ = [
    "FieldBuilder",
    "FieldSpec",
    "FieldType",
    "Types",
    "field",
    "make_registration_serializer",
    "registration_view",
    "type",
    "types",
]
