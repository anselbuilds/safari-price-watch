# Experimental v0.1.0 validation

## Reproducible local checks

On macOS arm64 with Python 3.9.6, all 18 CLI/state regression tests passed, with no skips. Run `python3 -m unittest discover -s tests -v` from the repo root. The test suite uses synthetic example.com data and isolated disposable directories under this checkout. It does not open Safari, call a network service, or read a real watchlist.

The tests cover draft-only creation; handoff without state/event mutation; revisions preserving prior conditions while clearing verification; stop-pending boundaries; duplicate identity rollback; reuse after verified stop; separate setup/delivery evidence; expiry warnings; invalid money/timezone/URL/baseline rejection; text remaining data; explicit/env database paths; global-install storage; and POSIX permissions.

The supplied `SKILL.md` passed the skill-creator frontmatter validator. The Python helper and skill instructions are byte-identical to the handed-over portable source; packaging added bilingual documentation, a synthetic fixture and reproducible tests. Python 3.9.0 itself, other Python releases and Windows/Linux execution were not tested.

## Native Safari evidence

The source handoff reports that one native Notify Me setup was created and its conditions and frequency were reopened and checked in Edit. That is prior setup evidence, not a new verification in this package-preparation run. No personal product, price, account or receipt is included here.

Actual notification delivery has not been observed. No production watch or threshold was changed to force a notification. The `record-delivery` test only verifies local state logic; its synthetic evidence is not a real Safari notification. Future end-to-end delivery testing needs an explicitly agreed separate test watch, a real qualifying page change and an observed notification.

Host-native skill discovery, Safari on other devices/regions/languages, automatic stopping at expiry, price interpretation accuracy, notification timing and deduplication remain unverified. Local test success does not prove these properties.
