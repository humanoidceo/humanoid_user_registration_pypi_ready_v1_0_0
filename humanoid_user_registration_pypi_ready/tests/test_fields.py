from humanoid_user_registration import field, types
from humanoid_user_registration.fields import normalize_field


def test_field_builder_simple_field():
    spec = field.username
    assert spec.name == "username"
    assert spec.type_name == "string"
    assert spec.required is True


def test_field_builder_typed_field():
    spec = field.age(types.integer, required=False)
    assert spec.name == "age"
    assert spec.type_name == "integer"
    assert spec.required is False


def test_field_source_mapping():
    spec = field.given_name(types.string, source="first_name")
    assert spec.name == "given_name"
    assert spec.target_name == "first_name"


def test_normalize_string_field():
    spec = normalize_field("email")
    assert spec.name == "email"


def test_normalize_dict_field():
    spec = normalize_field({"name": "age", "type": "integer", "required": False})
    assert spec.name == "age"
    assert spec.type_name == "integer"
    assert spec.required is False
