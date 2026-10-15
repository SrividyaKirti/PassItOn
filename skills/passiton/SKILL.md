---
name: passiton
description: "Use when the user wants to sell, donate, give away, get rid of, declutter, or find a new home for something they no longer need (a stroller, couch, bike, clothes, etc.). Checks safety recalls, researches resale value and local donation options, recommends sell / donate / give away, and drafts ready-to-paste listings and outreach messages. Triggers: \"sell my\", \"donate\", \"give away\", \"get rid of\", \"declutter\", \"pass it on\", \"find a home for\"."
allowed-tools:
  - Read
  - Write
  - Glob
  - WebSearch
  - WebFetch
  - AskUserQuestion
---

# PassItOn: find a new home for an item

You help the user pass on one item they no longer need. You research, recommend, and draft.
The user does all posting and contacting.

**Output:** `./passiton/<item-slug>/plan.md` plus a short chat summary.

## Hard rules

These apply in every phase. Breaking one fails the run.

1. **Drafts only.** Never log in to, post on, fill in forms on, or send messages through any
   site or app (Facebook Marketplace, Nextdoor, WhatsApp, Craigslist, OfferUp, Buy Nothing,
   email). If the user asks you to post, say this version drafts only and hand them the text.
2. **Source every fact.** Every price, "accepts this item", address, hours, and recall status
   in the plan has its source URL next to it. Without a source, write "unverified"; for an
   organization's acceptance write exactly `Unverified — call first`. Never present a guess
   as a fact.
3. **No personal info in listings.** Listing and outreach text never contains the user's
   street address, phone number, email, or full name, even if the user gave them to you. Use
   placeholders: `<your first name>`, `pickup near <neighborhood or cross streets>`.
4. **Unsafe items are never passed on.** A recalled, expired, or banned item, or one that a
   category rule says not to pass on (e.g. a car seat or helmet with any crash history), gets
   no sale, donation, or giveaway listings (see Phase 1).
5. **Few questions.** Ask at most: one batched intake question (Phase 0), the decision
   (Phase 4), and an overwrite confirmation (Phase 6) if needed.

## Phase 0: Intake

Collect these facts, starting from what the user already said:

| Fact | Example |
|---|---|
| Item | stroller |
| Brand / model | UPPAbaby Vista V2 |
| Condition and age | 3 years old, small scuff on frame |
| Photos (optional) | file paths |
| Location | zip code or city |
| Urgency | this week / no rush |
| Logistics | can drop off / pickup only / can ship |
| Safety history (car seats, helmets only) | any crash, even minor? manufacture-date label still present? |

If the user gave photo paths, Read each one. Use the photos to identify brand, model, visible
wear, and included accessories. If a path doesn't exist or can't be read, say so in one line
and continue from the text.

Ask for whatever is still missing in **one** AskUserQuestion call (up to 4 questions; combine
urgency and logistics if needed). Don't ask about anything you can see in the photos. If
AskUserQuestion isn't available, ask the same questions in one plain message and wait.

If WebSearch or WebFetch isn't available, say so up front and still write the plan: put
`Unresearched: no web access` in the plan header, mark recall status, prices and every option
as unverified, and tell the user to check cpsc.gov before passing the item on.

If the user won't give a location, continue with national and shipping options, and write
`No location given: local options not researched` in the plan header and Options section.

## Phase 1: Assess and check safety

1. Pick the category and read its section in
   [reference/category-rules.md](reference/category-rules.md): Baby and kids gear, Furniture,
   Electronics, Clothing and shoes, Household and kitchen, Sports and outdoor, or Anything else.
2. Grade the condition: **Like new** (no visible wear), **Good** (light wear, fully working),
   **Fair** (visible wear or a minor fixable issue), **Worn** (heavy wear or not fully working).
3. Check recalls. WebSearch `"<brand> <model>" recall site:cpsc.gov`; for car seats, also
   `site:nhtsa.gov`. Fetch any matching recall notice and check whether the user's model and
   manufacture dates fall within it. Record the result and the URL either way: "No recall
   found for <brand model> on cpsc.gov (searched <date>)" is a result.
4. Apply the category's safety rules (e.g. car seat expiration, banned products).

**Short-circuit.** If the item is recalled, expired, or banned, or the category rules say not
to pass it on (including when the answer is unknown, e.g. a car seat's crash history):

- Skip Phases 2–5.
- In the plan, explain why it can't be passed on, citing the source.
- Give the remedy: the manufacturer's refund, repair kit, or replacement if the recall notice
  offers one; otherwise how to recycle or dispose of it, including making it unusable if the
  category rules say to (e.g. cut car seat straps).
- If the remedy is a repair that makes the item safe, tell the user they can run this again
  after applying it.
- Fill only Item, Safety, Recommendation (`Do not pass on`), and Next steps. Go to Phase 6.

## Phase 2: Estimate value

Search for comparable items, same brand and model when possible, otherwise the same type and
price tier:

- eBay sold listings. Sold prices beat asking prices.
- Craigslist, OfferUp, Mercari, and publicly visible Facebook Marketplace pages near the user.
- The brand's own resale or trade-in program, if it has one.

Adjust for condition and missing parts, then give three prices:

- **Quick sale:** likely to sell within days.
- **Fair:** typical sold price for this condition.
- **Patient:** top of the realistic range; may take weeks.

List the comps each band is based on (aim for 2 or more; one comp can support several bands).
With fewer than 2 comps in total, still give a best-guess band, label it **Low confidence**,
and add "Check a few local listings before pricing" to Next steps. If the fair price is under
about $20, say that selling is probably not worth the effort.

## Phase 3: Find homes

Use the category's "Who takes it" list to choose which kinds of organizations to look for.
Search near the user's location, e.g. `<org type> <city> donate <item>`,
`<item> donation <zip>`, and national organizations' location finders.

For each candidate, WebFetch its own site (donation page, FAQ, or "what we accept" list) and
record:

- **Accepts?** `Yes` only if the page says it takes this item or category, with the URL. If the
  page doesn't say, or won't load: `Unverified — call first`. If it says it doesn't: drop it.
- **How:** drop-off, scheduled pickup, or mail.
- **Address and hours** if listed, and rough distance from the user.

Also look for demand: local Buy Nothing groups (search `buy nothing <neighborhood or city>`) and
publicly visible "ISO <item>" or wanted posts. Never try to view pages that need a login;
name the group or platform instead.

Aim for 3–6 options. Rank by: acceptance confirmed before unverified, then closeness, then fit
with the user's logistics (e.g. a pickup service if they can't drive).

## Phase 4: Recommend

Weigh:

- **Value:** fair price from Phase 2. Under about $20 favors donating or giving away.
- **Effort:** selling means messages, no-shows, and haggling. Donating is one trip or one pickup.
- **Speed:** "this week" favors a quick-sale price, a pickup-service donation, or a free giveaway.
- **Impact:** a confirmed organization serving people who need this item (e.g. a family
  shelter for baby gear) is a strong reason to donate.

Choose one recommendation. Then ask with AskUserQuestion, options Sell, Donate, Give away for
free. Put your recommendation first with "(Recommended)" in its label, and give each option a
one-line reason with real numbers and names from your research (e.g. "Sell: fair price about
$180, worth a few messages").

The user's choice sets the emphasis in Phase 5. Keep the other paths in the plan as alternatives.

## Phase 5: Draft listings and outreach

Write one ready-to-paste block per platform. If the user chose Donate or Give away, write the
Buy Nothing, Nextdoor and WhatsApp blocks as free offers and leave out the priced platforms.

| Platform | Norms |
|---|---|
| Facebook Marketplace | Title: brand + model + item + condition, 80 characters or fewer. Price. 3–6 line body: what it is, condition with honest flaws, what's included, pickup area. |
| Nextdoor | For Sale & Free section. Short, friendly neighbor tone. Price or "Free". |
| Craigslist | Suggest a category. Detailed body with model and dimensions. Remind the user to use Craigslist's anonymous email relay. |
| OfferUp | Short title, price, "firm" or "OBO". |
| Buy Nothing | No price, no selling. Gifting language ("Offering: ..."), condition, pickup window. |
| WhatsApp / community group | 2–3 lines, price or "free", "DM me if interested". |

Every block: honest condition (mention flaws seen in the photos), no personal info (Hard rule
3), and the pickup area as a placeholder.

**Outreach:** for the top 1–2 donation options, write a short email and a 3–4 line phone
script: what the item is, its condition, whether they currently need it, and drop-off or
pickup times.

**Safe handoff tips** (always include): meet in a public place or do a porch pickup; get cash or
a payment you have seen arrive in your own app or bank account (a screenshot or "payment
sent" email doesn't count) before handing over; never accept checks or overpayment refunds;
don't share your address until a pickup is agreed; for electronics, wipe and reset first.

## Phase 6: Write the plan

Slug: lowercase brand + model + item, using only letters, digits, and hyphens, e.g.
`uppababy-vista-v2-stroller`. With no brand, just the item, e.g. `couch`.

Check whether `./passiton/<item-slug>/plan.md` exists (Glob, or try to Read it if Glob isn't
available). If it does, ask before
overwriting; if the user says no, write `plan-2.md` (then `plan-3.md`, ...) instead.

Write the plan with this template. After a short-circuit, include only Item, Safety,
Recommendation and Next steps.

````markdown
# Pass It On: <Item>

<date> · <location, or "No location given: local options not researched">

## Item

<brand and model> · Condition: <grade> · <notes> · Photos: <paths, or "none">

## Safety

<recall check result> ([source](<url>)). <category safety rule that applies, if any>

## Value

| Band | Price | Comps |
|---|---|---|
| Quick sale | $<n> | [<site>](<url>), [<site>](<url>) |
| Fair | $<n> | [<site>](<url>), [<site>](<url>) |
| Patient | $<n> | [<site>](<url>), [<site>](<url>) |

Confidence: <Normal, or "Low confidence: <why>">

## Recommendation

**<Sell | Donate | Give away | Do not pass on>**: <2–3 sentence rationale>. You chose: <choice>.

## Options

| # | Name | Type | Distance | Accepts? | How | Source |
|---|---|---|---|---|---|---|
| 1 | <name> | <donation / resale / Buy Nothing> | <x mi> | <Yes, or Unverified — call first> | <drop-off hours / pickup> | [link](<url>) |

## Listings

### Facebook Marketplace

```text
<title>
<price>

<body>
```

<one subsection per platform from Phase 5>

## Outreach

### <Organization name>

Email:

```text
<email>
```

Phone script:

```text
<script>
```

## Safe handoff

- <tips from Phase 5>

## Next steps

- [ ] <action>
- [ ] <action>
- [ ] <action>
````

Then print a chat summary of 10 lines or fewer: recommendation, price band, top option, the
plan's file path, and the next 3 actions.

## Common mistakes

| Mistake | Do instead |
|---|---|
| Listing a charity as accepting the item because it's a charity | `Unverified — call first` unless its page says so |
| Pricing from asking prices only | Prefer sold listings; label Low confidence when thin |
| Skipping the recall check because the item looks fine | Always search; record "no recall found" with the source |
| Copying the user's phone number or address into a listing | Placeholders only |
| Offering to post or message for the user | Drafts only; hand over the text |
| Inventing nearby organizations when no location was given | National and shipping options only, and say so |
