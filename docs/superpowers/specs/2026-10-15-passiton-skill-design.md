# PassItOn Skill — Design Spec

Date: 2026-10-15
Status: Draft for review

## Goal

A single agent skill (`/passiton`) that takes something you no longer need — e.g. a baby
stroller — and produces a sourced "pass-it-on plan": whether to sell, donate, or give it away,
where specifically (named local orgs / platforms), at what price, and ready-to-paste listings
and outreach messages. It replaces manually browsing Facebook Marketplace, Nextdoor, WhatsApp
groups and donation-center websites.

Modeled on gstack skills (e.g. `design-review/SKILL.md`): one `SKILL.md` with frontmatter and a
phased playbook the agent follows, using only built-in agent tools.

## Decisions (agreed)

| Topic | Decision |
|---|---|
| Autonomy (v1) | Research + drafts only. The agent never logs in, posts, or messages anyone. |
| Sell vs donate | Agent evaluates and recommends; the user makes the final choice. |
| Input | Chat description + optional photo paths. |
| Output | Markdown plan file at `./passiton/<item-slug>/plan.md` plus a short chat summary. |
| Architecture | Option A: one self-contained `SKILL.md` + one reference file. No scripts, no APIs. |

## Non-goals (v1)

- Posting to, scraping behind login on, or messaging via any platform (Marketplace, Nextdoor,
  WhatsApp, OfferUp, Craigslist). These lack public posting APIs and prohibit automation.
- Monitoring replies, negotiating, or scheduling pickups.
- Batch/inventory processing of many items.
- Helper scripts or price-scraping code.

## Repo layout

```
skills/passiton/SKILL.md                      # the skill
skills/passiton/reference/category-rules.md   # per-category donation fit + safety rules
tests/scenarios.md                            # baseline + with-skill test scenarios
scripts/validate-skills.py                    # CI: frontmatter + referenced-file checks
.github/workflows/ci.yml                      # CI on PRs to main
.github/workflows/release.yml                 # tag → GitHub Release with skill zip
.markdownlint.jsonc, .lycheeignore            # lint/link-check config
README.md                                     # what it is + install instructions
docs/superpowers/specs/2026-10-15-passiton-skill-design.md
```

Install: copy or symlink `skills/passiton` into `~/.claude/skills/` (or a project's
`.claude/skills/`).

## SKILL.md frontmatter

```yaml
name: passiton
description: Use when the user wants to get rid of, sell, donate, give away, or find a new home
  for an item they no longer need (e.g. stroller, couch, bike, clothes). Researches value,
  safety recalls, and local donation options, recommends sell/donate/give-away, and drafts
  ready-to-paste listings.
allowed-tools: [Read, Write, Glob, WebSearch, WebFetch, AskUserQuestion]
```

Triggers (in description): "sell my", "donate", "give away", "get rid of", "declutter",
"pass it on", "find a home for".

## Phases

### Phase 0 — Intake

Collect: item (what it is), brand/model if known, condition, photos (optional file paths),
location (zip or city), urgency (this week / no rush), logistics (can drive / can ship /
pickup only). Read any photos to infer brand, model, condition and visible wear. Ask for
anything missing in **one** AskUserQuestion call (max 4 questions). Location: ask once; if
declined, proceed with national/shipping options and state that in the plan.

### Phase 1 — Assess & safety

- Identify item category and grade condition: Like new / Good / Fair / Worn.
- Consult `reference/category-rules.md` for the category.
- Recall check: WebSearch CPSC (cpsc.gov/Recalls), and NHTSA for car seats, by brand + model.
- If recalled, expired (car seats past expiration date), or banned (drop-side cribs, inclined
  infant sleepers): **short-circuit** — skip Phases 2–5 sale/donation content; the plan
  recommends the manufacturer remedy (refund/repair kit) if available, otherwise recycle or
  dispose, with source links.

### Phase 2 — Value

- WebSearch/WebFetch comparable listings: eBay sold listings, Craigslist, OfferUp, Mercari,
  publicly visible Marketplace pages; brand resale programs if they exist.
- Produce a price band: **Quick sale / Fair / Patient**, each with 2+ comp links.
- If fewer than 2 comps found, mark the band "low confidence" and add a "check comps
  yourself" next step.

### Phase 3 — Find homes

- Donation orgs near the location that accept **this category**, guided by
  `category-rules.md` (e.g. stroller → pregnancy resource centers, family shelters,
  diaper banks / baby-gear nonprofits, Goodwill / Salvation Army; also Buy Nothing groups).
- For each candidate, WebFetch its site to confirm: accepts this item, drop-off vs pickup,
  hours/address. If acceptance isn't stated, label **"Unverified — call first"**; never list as
  accepted without a source.
- Demand signals: publicly visible "ISO <item>" posts or wanted listings, if any.
- Target 3–6 ranked options.

### Phase 4 — Recommend

Weigh resale value vs effort vs speed vs impact (and urgency/logistics from intake).
Present a decision via AskUserQuestion: Sell / Donate / Give away (Buy Nothing / free
listing), with the recommended option first and marked "(Recommended)", each with a one-line
reason. The user's choice determines emphasis in Phase 5 (the other paths stay in the plan as
alternatives).

### Phase 5 — Drafts

- One ready-to-paste block per relevant platform: Facebook Marketplace, Nextdoor, Craigslist,
  OfferUp, Buy Nothing, and a short WhatsApp/community-group blurb. Each: title, price (or
  "Free"), body tailored to the platform's norms/length, tags/category.
- Outreach: email + phone script for the top 1–2 donation orgs.
- Safe handoff tips: meet in public / porch pickup, no address or phone in listing text,
  cash/verified payment only.

### Phase 6 — Write plan

Write `./passiton/<item-slug>/plan.md` (slug: lowercase brand-model-item, e.g.
`uppababy-vista-stroller`). If it exists, ask before overwriting. Then print a ≤10-line chat
summary: recommendation, price band, top option, file path, next 3 actions.

## Plan file format

```markdown
# Pass It On: <Item>
<date> · <location>

## Item
Brand/model, condition grade, notes, photos used.

## Safety
Recall check result + source link(s); any category rule that applies.

## Value
| Band | Price | Comps |
|---|---|---|
| Quick sale | $ | links |
| Fair | $ | links |
| Patient | $ | links |
(confidence note)

## Recommendation
Sell | Donate | Give away — 2–3 sentence rationale. User chose: <choice>.

## Options
| # | Name | Type | Distance | Accepts? | How | Source |
|---|---|---|---|---|---|---|

## Listings
### Facebook Marketplace
...
### Nextdoor
...
(one per platform)

## Outreach
Email + call script for top org(s).

## Next steps
- [ ] ...
- [ ] ...
- [ ] ...
```

## reference/category-rules.md

Covers, per category: donation fit (which org types take it), common refusals, safety/recall
rules, and listing tips. v1 categories: **baby & kids gear** (strollers, car seats, cribs,
high chairs, toys), **furniture** (incl. upholstered-item and mattress restrictions),
**electronics** (data wipe, e-waste recycling), **clothing & shoes**, **household & kitchen**,
**sports & outdoor** (bikes, helmets — helmets not resold after impact). Unknown categories
fall back to general rules (Goodwill/Salvation Army/Buy Nothing + general comps).

## Rules the skill enforces

1. Every factual claim (price, acceptance, hours, recall status) cites a source URL.
2. Never post, log in, or send messages; output is drafts only.
3. Never include the user's address, phone, or full name in listing text.
4. Unsafe/recalled items are never listed for sale or donation.
5. Ask at most one batched intake question round plus the Phase 4 decision (and an overwrite
   confirmation if needed).

## Error handling

| Situation | Behavior |
|---|---|
| No location | Ask once; else national/shipping options, noted in plan. |
| Photos missing/unreadable | Continue from text; ask condition in intake. |
| < 2 price comps | "Low confidence" band + manual-check next step. |
| Org acceptance not confirmable | "Unverified — call first". |
| Recalled/unsafe | Short-circuit to remedy/recycle/dispose. |
| WebSearch/WebFetch unavailable | Say so; produce drafts + generic options, clearly labeled unresearched. |
| plan.md exists | Ask before overwriting. |

## Testing

Following the superpowers `writing-skills` approach (baseline before skill, then with skill),
documented in `tests/scenarios.md`:

1. **Stroller, 94107, good condition** — expect full plan, price band with comps, ≥3 local
   options with sources, all platform listings.
2. **Recalled inclined infant sleeper** — expect short-circuit: no sale/donation listings,
   recall source cited.
3. **Old couch, no location given, user declines** — expect national fallback noted,
   furniture restrictions (upholstery) surfaced.

Pass criteria for each with-skill run: plan file exists with all sections, sources cited for
claims, no posting/login attempted, no personal info in listings, correct short-circuit for
scenario 2. Baseline runs (without the skill) are recorded to show what the skill adds.

These scenarios need a live agent with web access, so they are run manually before a release
and are **not** part of CI.

## CI/CD

### Branching

- `main` is protected: no direct pushes; changes land only via pull request with passing CI.
- Work happens on feature/release branches (v1 work on `v1.0`), merged to `main` by PR.

### CI — `.github/workflows/ci.yml`

Runs on `pull_request` to `main` and on `push` to `main`. Jobs:

1. **Skill frontmatter validation** — a small script (`scripts/validate-skills.py`, stdlib
   only + PyYAML) checks every `skills/*/SKILL.md`:
   - YAML frontmatter parses;
   - `name` present, kebab-case, and matches its directory name;
   - `description` present, starts with "Use when", ≤ 1024 chars;
   - `allowed-tools` present and a non-empty list.
2. **Referenced files exist** — the same script checks that every relative path referenced
   from a `SKILL.md` (e.g. `reference/category-rules.md`) exists in the skill directory.
3. **Markdown lint** — `markdownlint-cli2` over `**/*.md` with a repo `.markdownlint.jsonc`
   (line length rule disabled; plan/listing templates need long lines).
4. **Link check** — `lychee` over `README.md`, `skills/**/*.md`, and `docs/**/*.md`; external
   link failures are reported but retried, with a `.lycheeignore` for known-flaky hosts.

### CD — `.github/workflows/release.yml`

- Triggered by pushing a tag matching `v*.*.*` (e.g. `v1.0.0`) on a commit already on `main`.
- Re-runs the CI checks, then packages `skills/passiton/` as `passiton-skill-<version>.zip`
  and publishes a GitHub Release with the zip attached and auto-generated notes.
- The README install section points to the latest release zip as an alternative to cloning.

### Branch protection (repo setting, not code)

After `ci.yml` exists on `main`, configure a ruleset on `main` via `gh`/GitHub UI: require a
pull request, require the CI status checks to pass, block force-pushes and deletions. This
changes GitHub repo settings and is applied only with the owner's explicit confirmation.

### Bootstrapping order

Because `main` currently has no CI, the first PR (`v1.0` → `main`) introduces the workflows;
branch protection is enabled immediately after that PR merges.
