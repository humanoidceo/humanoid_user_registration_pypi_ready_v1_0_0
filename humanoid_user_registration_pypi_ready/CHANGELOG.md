# Changelog

## 1.0.0 - 2026-07-05

Initial public release.

### Added

- `registration_view()` helper for creating a DRF registration endpoint from `views.py`.
- Field builder syntax: `field.phone_number(types.string, required=True)`.
- Source mapping syntax: `field.given_name(types.string, source="first_name")`.
- Optional non-model fields with `allow_non_model_fields=True`.
- Custom response fields.
- Password confirmation and Django password validation.
- Optional `post_register_hook` callback.
- Optional token response support for DRF TokenAuthentication.
- Optional `urls.py` for people who prefer `include()`.
