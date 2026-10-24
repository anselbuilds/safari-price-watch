# Safari Price Watch

[繁體中文](README.zh-Hant.md)

This repository is archived. The skill is now maintained at [anselbuilds/agent-skills](https://github.com/anselbuilds/agent-skills/tree/main/skills/price-watch).

**Experimental v0.1.0 prerelease.** Created and maintained by Ansel under [MIT](LICENSE).

[Download v0.1.0](https://github.com/anselbuilds/safari-price-watch/archive/refs/tags/v0.1.0.zip) · [Release notes](https://github.com/anselbuilds/safari-price-watch/releases/tag/v0.1.0) · [Install and use](#install-and-use)

## Requirements

- Python 3.9+ with SQLite and system IANA timezone data; standard library only. Tested here with Python 3.9.6 on macOS arm64. No API key or package install is required.
- For actual monitoring: a Mac/Safari with Notify Me available, Apple Intelligence eligibility and Safari system notifications. Apple's current [Notify Me guide](https://support.apple.com/en-in/guide/safari/ak35p2kk9h5r/mac) describes macOS 27 support, language/region limits and the setup interface. Check availability on your device; this package does not enable system features or accept terms for you.
- Local list, show, prompt and handoff operations need neither Safari nor Computer Use. Native setup/edit/stop needs manual action or an agent with a supported Computer Use tool.

The skill instructions and generated Safari condition cards are currently in Traditional Chinese. This English README explains the workflow; it is not a claim of fully localized output.

## First use without installation

From the extracted repository root, run this synthetic demonstration with an explicit disposable database:

```sh
python3 skills/price-watch/scripts/watchlist.py --db runtime/demo/watchlist.sqlite3 add demo-ssd --file skills/price-watch/examples/demo-contract.json
python3 skills/price-watch/scripts/watchlist.py --db runtime/demo/watchlist.sqlite3 handoff demo-ssd
python3 skills/price-watch/scripts/watchlist.py --db runtime/demo/watchlist.sqlite3 show demo-ssd
```

Expected: `status` remains `draft`; handoff has `action: setup` and `native_action_performed: false`. Repeating `add` with the same id fails rather than replacing it. This example uses example.com and is not a real product. Do not create a native Safari watch from it. The helper initializes its database even for list/show commands.

Ask an agent: “Read `skills/price-watch/SKILL.md`, then explain this demo handoff. Do not operate Safari or mark it active.”

## Install and use

Copy the complete `skills/price-watch` folder to the skill directory supported by your agent. Codex's documented project location is `.agents/skills/price-watch`; personal installation may use `~/.agents/skills/price-watch` under the [current skill guide](https://learn.chatgpt.com/docs/build-skills). Some existing environments use `~/.codex/skills/price-watch`; honor that host's configuration. Preserve an existing installation before replacing it. The final path must end in `price-watch/SKILL.md`. Host-native discovery has not been tested in this release.

Set `PRICE_WATCH_DB` to an explicit location outside the installed skill for personal/global installs, or pass `--db` before the command. The helper auto-detects `.agents/skills` as a project layout; a personal installation in that layout should therefore use an explicit database path. Other layouts use the user state directory. See [registry commands](skills/price-watch/references/registry.md) and [skill README](skills/price-watch/README.md).

Use `$price-watch` or your host's skill picker:

> Prepare a price watch for this product URL, exact model and seller. Use a listed price at or below USD 80, in stock, daily at 09:00 in Etc/UTC. Generate a setup card; I will configure Safari myself. Read the product page for the baseline first; do not invent a price if it cannot be read.

Then configure Safari from the card. Reopen its Edit view and verify the actual conditions and time. Record `active` only after an agent observes that verification or the user explicitly confirms the checked settings. A vague “done” is insufficient. For a change, revise the local contract and then edit the existing native watch. For a stop, request-stop locally, remove the native watch, verify removal, then record stopped.

| Local state | Meaning |
| --- | --- |
| draft | Saved locally; no native setup verified |
| needs_attention | Conditions changed or native state uncertain; Safari may still use old conditions |
| active | Native setup last verified, not proof of future delivery |
| stop_pending | Stop requested but native removal not verified |
| stopped | Native removal verified; history retained |

Notification delivery is recorded separately, only with actual observed delivery or explicit user confirmation. Expiry is a local warning, not an automatic stop. `list` is the last known registry, not a live Safari inventory. Do not alter a real watch's threshold merely to test notifications.

## Tests and limits

```sh
python3 -m unittest discover -s tests -v
```

Tests use synthetic data and disposable directories beneath the checkout; they do not access Safari, network services or real watchlists. See [VALIDATION.md](VALIDATION.md). Actual notification delivery has not been observed. There is no headless Safari management API integration, independent scraper, scheduler or alert backend. Safari's price interpretation, timing and deduplication are not guaranteed by this skill.

## Privacy and reporting

SQLite stores URLs, conditions and evidence in plaintext. Keep it outside the installable skill and do not publish runtime files, browser profiles or personal evidence. An agent may send read content to its model provider; local SQLite does not make the full workflow offline. Use public product URLs without credentials or session parameters. See [SECURITY.md](SECURITY.md).
