# Contributing to SWISSINNO BLE

Thank you for helping improve the integration. Bug reports, verified Bluetooth
captures, translations, documentation and code contributions are welcome.

## Before opening an issue

- Update to the latest published integration version and restart Home Assistant.
- Search the existing issues and pull requests for the same problem.
- Use the appropriate issue form and complete all required fields.
- Report security vulnerabilities privately as described in
  [SECURITY.md](SECURITY.md).

When reporting Bluetooth decoding behavior, include the integration and Home
Assistant versions, trap family or model, connection method (local Bluetooth or
proxy), and complete manufacturer payloads where possible. Captures of the
known state before and after a transition are much more useful than a single
decoded value. Remove unrelated personal information and secrets from logs.

Never create a hazardous trap condition to collect test data. Do not touch or
short high-voltage plates, open energized electronics, or bypass manufacturer
safety features.

## Development

The validation workflow uses Python 3.12. Run the unit tests from the repository
root:

```text
python -m unittest discover -s tests -v
python -m compileall custom_components/swissinno_ble
```

For decoder changes, add regression tests covering every affected observed
frame and its Ready/Caught/unknown behavior. Protocol values must be supported
by documentation or repeatable captures; do not guess mappings for unobserved
status bytes.

For translation changes, keep the same key structure as `translations/en.json`
and preserve Home Assistant placeholders exactly.

## Pull requests

- Keep each pull request focused on one change.
- Explain the user-visible behavior and how it was verified.
- Add or update tests for behavioral changes.
- Update the README and changelog when users need to know about the change.
- Do not change the integration version unless a maintainer requests it.
- Confirm that HACS, Hassfest and unit-test checks pass.

By participating, you agree to follow the project
[Code of Conduct](CODE_OF_CONDUCT.md).
