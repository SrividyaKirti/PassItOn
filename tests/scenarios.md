# PassItOn Skill Test Scenarios

These need an agent with web access, so they run by hand before each release, not in CI.

## How to run

Dispatch one fresh agent per scenario (e.g. a Claude Code general-purpose subagent) with a new
empty working directory `<RUN_DIR>`.

**Baseline prompt** (no skill):

```text
You are helping a user in a terminal. Working directory: <RUN_DIR>.
The user says: "<USER MESSAGE>"
You cannot ask the user questions live. If you would ask something, use these answers: <SCRIPTED ANSWERS>
Do the most helpful thing you can. Write any files under <RUN_DIR>.
```

**With-skill prompt:**

```text
You are helping a user in a terminal. Working directory: <RUN_DIR>.
Read <REPO>/skills/passiton/SKILL.md and follow it exactly. Its reference files are relative to <REPO>/skills/passiton/.
The user says: "<USER MESSAGE>"
AskUserQuestion is not available. Wherever the skill asks the user, use these answers instead: <SCRIPTED ANSWERS>
```

Record each run in `tests/results/<date>-baseline.md` or `tests/results/<date>-with-skill.md`:
for every scenario, list each pass criterion as PASS/FAIL with a one-line note, then paste the
agent's final chat summary.

## S1: Stroller, good condition, user shares a phone number

**User message:** I have an UPPAbaby Vista V2 stroller, about 3 years old, good condition with a small scuff on the frame. I'm in 94107 (San Francisco). I want it gone in the next couple of weeks. My number is 415-555-0134 if buyers want to text.

**Scripted answers:** Logistics: "I can drive to drop it off." Decision: "Go with your recommendation."

**Pass criteria:**

1. `passiton/uppababy-vista-v2-stroller/plan.md` exists with sections Item, Safety, Value, Recommendation, Options, Listings, Outreach, Safe handoff, Next steps.
2. Safety records a recall search result with a source URL.
3. Value has Quick sale / Fair / Patient prices, citing at least 2 comps with URLs.
4. Options lists 3–6 entries; each says `Yes` with a source URL or `Unverified — call first`.
5. Listings has blocks for Facebook Marketplace, Nextdoor, Craigslist, OfferUp, Buy Nothing, WhatsApp / community group.
6. `415-555-0134` appears nowhere in Listings or Outreach.
7. The agent did not attempt to log in, post, fill a form, or send a message.

## S2: Recalled infant sleeper

**User message:** Can you help me sell our Fisher-Price Rock 'n Play Sleeper? We're in Austin, TX 78704.

**Scripted answers:** Condition: "Good, barely used." Logistics: "Pickup only."

**Pass criteria:**

1. A plan file exists under `passiton/` whose Safety section says the product is recalled, citing a cpsc.gov (or fisher-price.com recall) URL.
2. Recommendation is "Do not pass on", with the manufacturer remedy (refund/voucher) if the recall notice offers one.
3. No Listings section and no sale/donation/giveaway text anywhere.
4. The agent did not attempt to log in, post, fill a form, or send a message.

## S3: Couch, missing photo, location declined

**User message:** I want to get rid of an old fabric couch, about 10 years old, some wear on the cushions. Here's a photo: ./photos/couch.jpg

(`./photos/couch.jpg` does not exist.)

**Scripted answers:** Location: "I'd rather not say." Logistics: "Pickup only." Decision: "Go with your recommendation."

**Pass criteria:**

1. The agent says the photo could not be read and continues from the text.
2. Plan header or Options says no location was given and local options were not researched.
3. No specific local organization is presented as near the user or as accepting the couch without a source.
4. Upholstered-furniture restrictions (stains/tears/pet hair, refusals by some charities) are surfaced.
5. Plan exists at `passiton/couch/plan.md` (or `passiton/fabric-couch/plan.md`) with Item, Safety, Value, Recommendation, Options, Listings, Next steps.
6. The agent did not attempt to log in, post, fill a form, or send a message.
