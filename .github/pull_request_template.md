## Summary

Describe the change and the user-visible result.

## Verification

List the tests run and, for Bluetooth behavior, the hardware or captured frames
used for verification.

## Checklist

- [ ] The change is focused and does not include unrelated modifications.
- [ ] Unit tests were added or updated for behavioral changes.
- [ ] `python -m unittest discover -s tests -v` passes.
- [ ] `python -m compileall custom_components/swissinno_ble` passes.
- [ ] Decoder mappings are supported by documentation or repeatable captures.
- [ ] Translation keys match `translations/en.json`, if translations changed.
- [ ] User-facing documentation and `CHANGELOG.md` were updated when needed.
- [ ] I did not change the integration version unless requested by a maintainer.
