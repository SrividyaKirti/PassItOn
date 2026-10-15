# PassItOn

An open-source AI agent toolkit that helps you find new homes for things you no longer need.
Discover local donation centers, match with people in need, and simplify community giveaways.

## The `passiton` skill

Tell your agent about something you want to get rid of, like "I want to give away or sell my
stroller, I'm in 94107". The skill:

1. Checks safety recalls (and stops if the item shouldn't be passed on).
2. Estimates resale value from comparable sold listings.
3. Finds local donation organizations that actually accept that item, with sources.
4. Recommends sell, donate, or give away, and lets you choose.
5. Drafts ready-to-paste posts for Facebook Marketplace, Nextdoor, Craigslist, OfferUp, Buy
   Nothing and WhatsApp groups, plus emails to donation centers.

It writes everything to `./passiton/<item>/plan.md`. It never posts or messages anyone for you.

## Install (Claude Code)

From a clone:

```bash
git clone https://github.com/SrividyaKirti/PassItOn.git
mkdir -p ~/.claude/skills
ln -s "$PWD/PassItOn/skills/passiton" ~/.claude/skills/passiton
```

Or download `passiton-skill-<version>.zip` from the
[latest release](https://github.com/SrividyaKirti/PassItOn/releases/latest) and unzip it into
`~/.claude/skills/`.

Then ask Claude Code something like "help me get rid of my old couch", or run `/passiton`.

## Contributing

- Work on a branch and open a pull request to `main`; direct pushes to `main` are blocked.
- CI runs the skill validator and its tests, markdownlint, and a link check.
- Locally:

  ```bash
  python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
  .venv/bin/pytest -q
  .venv/bin/python scripts/validate-skills.py
  ```

- Agent behavior is tested by hand with the scenarios in `tests/scenarios.md` before each release.

## Releasing

Merge to `main`, then tag: `git tag v1.0.0 && git push origin v1.0.0`. The release workflow
checks that the tag is on `main`, re-runs CI, and publishes the skill zip.

## License

See [LICENSE](LICENSE).
