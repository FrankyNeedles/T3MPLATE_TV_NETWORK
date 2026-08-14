# RESEARCH: The Real 90s Broadcast Day — A Buildable Spec for the SNES Network

> **Purpose:** Turn "the SNES world as a living 90s network TV broadcast" from a vibe into a
> codeable broadcast architecture. This report describes how a real American 1990s broadcast
> television network actually operated, then gives a concrete, slot-by-slot 24-hour schedule
> template and rotation rules a builder can implement directly.
>
> **Audience:** the engineer building the broadcast engine. Every timing, duration, and naming
> below is deliberately explicit so you can code without further research.
>
> **Alignment note:** This report aligns to the existing `app/program_90s.py` and `FULL_VISION.md`
> and explicitly calls out where the existing attempt diverges from real 90s TV. Ranked at the end.

---

## 0. TL;DR — The five things that most create the "90s TV" feel

If you implement only a handful of things, implement these (ranked):

1. **A real, fixed daily grid** with the correct *blocks* and *times* (local news at 6/11pm,
   network prime 8–11, late-night 11:35). A viewer who flips in must instantly recognize "it's
   7:30pm — this is access." Format mismatch (a game show at 10pm) breaks the illusion worse than
   any pixel issue. **This is what the original project got wrong** — it felt random because it had
   no believable grid.
2. **Commercial breaks structured like real TV**: 22 min of content per 30-min slot, ~4 ad pods in
   an hour, every break an *ordered sequence* (promo → national spot → local spot → station ID),
   not a random fill. The *grammar* of the break is what feels real.
3. **The "hand-off" moments** — show-end tag → local break → station ID → next-show bumper →
   "coming up" tease. These 10–20 seconds between shows are the connective tissue of real TV.
4. **The overnight/sign-off behavior** — infomercials, classic reruns, color bars, "technical
   difficulties," and sign-off. Authenticity lives in the *dead air* as much as the marquee.
5. **90s graphics grammar** — corner station bug, lower-thirds, chrome/bevel typography, digital
   wipes, test patterns. These are cheap to fake and instantly read as "the 90s."

---

## 1. The Broadcast Day Taxonomy

A real 90s network affiliate's day is divided into **dayparts** — each with its own format rules,
target demo, ad load, and sales value. These are the industry-standard names and *real* Eastern
times (Central shifted ~1hr). Affiliates of the Big 3 (ABC/NBC/CBS) and FOX follow this shape;
independents fill it differently. **SNES Network should model a Big-3-style affiliate** because that
grid is what people's muscle memory of "90s TV" is built from.

| Daypart (industry name) | Wall clock (ET) | Typical programming | Ad load | Notes |
|---|---|---|---|---|
| **Sign-on / Overnight** | ~4:00–6:00 AM | Sign-on: color bars, test pattern, National Anthem, station ID → **overnight paid programming (infomercials)**, classic reruns | Heavy (infomercials = 100% ads) | Some stations ran 24h (no sign-off); many small independents signed off with color bars + National Anthem + "We now begin our broadcast day" |
| **Early morning** | 6:00–7:00 AM | Local news (4:30–6 or 6–7) and/or network early show | Local break at :25/:55 | **Early local news** ("Eyewitness News at 6") — this slot is gold for authenticity |
| **Morning news/talk** | 7:00–9:00 AM | Network morning show (Today / GMA / CBS This Morning) with local news cut-ins every :30 | Network pods ~3–4 min, local cut-in pods ~1–2 min | Local anchor inserts "good morning" segments on the :25/:55 |
| **AM kids (Sat only)** | 7:00–11:00 AM Sat | Network/affiliate cartoon blocks (Saturday morning cartoons) | Kid ads (cereal, toys) | Big-3 ran action/adventure toons 7–10/11 Sat; Fox Kids was weekday+Sat by 1992. SNES can run this Sat-only |
| **Daytime** | 9:00 AM–4:30 PM | Game shows, talk shows, soap operas | **Heaviest ad load** (~9–11 min per 30-min slot) | Advertiser-heavy (household products); soaps had more ads than prime because content was cheap |
| **Early fringe** | 4:30–6:00/6:30 PM | Syndicated sitcom reruns, talk shows (Oprah/Jerry Springer), court shows | Local+syndicated pods | Locally sold time — high value |
| **Early local news** | 5:00, 5:30, 6:00 PM | Half-hour or hour local news blocks | Local breaks between segments | 2–3 news blocks stacked; "Eyewitness News at 5 and 6" |
| **Access / Prime access** | 6:30/7:00–8:00 PM | Syndicated game/magazine (Wheel of Fortune, Jeopardy!, Entertainment Tonight, Inside Edition) | **Highest-priced local ad slots in the day** | "Access" because it *leads into* prime; a distinct, scripted feel |
| **Prime time** | 8:00–11:00 PM (Sun 7–11; FOX 8–10) | Network sitcoms/dramas; night-blocks (Must-See TV, TGIF) | ~8 min per 30-min slot (~16 min/hr) | The marquee. Every network night has an identity |
| **Late news / Late fringe** | 11:00–11:35 PM | Local late news (the "11 o'clock news") | Local pods | Distinctly different tone from evening news ("news at 11") |
| **Late-night network** | 11:35 PM–1:00/1:35 AM | Network late-night talk (Leno 11:35, Letterman 11:35, Conan 12:35) | Network pods | Tonight/Late Show ~60 min; Conan/Late Late ~60 min |
| **Overnight network** | 1:00/1:35–4:00/5:00 AM | ABC *World News Now* (2–4:30), CBS *Up to the Minute* (2–4), infomercials, rebroadcasts | Infomercial-heavy | Then hand back to sign-on |

**Why this matters for authenticity:** the *labels and clock times* ARE the simulation's skeleton.
Your daypart detector (`get_current_daypart`) should return these exact blocks. A viewer should be
able to guess the clock from what's on screen.

---

## 2. Commercial Architecture

### 2.1 The math of a broadcast hour (the single most important spec)

A 60-minute prime-time hour does **NOT** contain 60 minutes of content. It contains roughly:

- **~44 minutes of program content**
- **~16 minutes of commercial time** (network + local + promos combined)

A 30-minute sitcom = **~22 min content / ~8 min ads** (this is the famous "22 minutes" — already
correct in `program_90s.py`). A 30-min soap/game show = **~20 min content / ~10 min ads** (daytime
is heavier).

> **Spec:** `CONTENT_PER_HALF_HOUR = 22*60` (already in code — keep it). For daytime, use
> `20*60`. Add `ADS_PER_HALF_HOUR = 8*60` prime / `10*60` daytime. **Fix `BREAK_INTERVAL`: the
> current `6*60` (a break every 6 min) is wrong — that's ~10 breaks/hour. Real prime has ~4.**

### 2.2 Ad pods (break structure)

Commercials are not dumped in one block — they're split into **pods** placed at scripted points in
the program. Real prime placement (a 60-min drama):

| Pod | Approx. clock position | Contents |
|---|---|---|
| **Lead-in / pre-show** | just after :00 | Network promo + "brought to you by" + 2–4 national spots |
| **Break 1** | ~:08–:10 | 4–6 spots |
| **Break 2 (mid)** | ~:20–:22 | 4–6 spots (the "coming up" tease sits right before this in the show) |
| **Break 3** | ~:36–:38 | 4–6 spots |
| **Break 4** | ~:48–:50 | 4–6 spots |
| **Post-show / lead-out** | just before :00/:30 | Network promo for next show + "next on" tease |

A 30-min sitcom: ~2 pods + the lead-in and a post-show "next week" tease.

> **Spec:** each pod is a **sequence**, not a random fill. Order matters:
> `show-exit tag → [promo → national spot ×N → local spot ×1–2 → station ID] → next-show bumper`.

### 2.3 Network vs. local

- **Network time:** national ads the network sold (Sears, Coke, McDonald's, car ads) plus network
  **promos** for its own upcoming shows.
- **Local time:** the affiliate sells its own local spots (car dealers, local furniture, "Tune in
  tonight"). Local spots are inserted at the *start or end* of the pod, and local news blocks are
  all-local.
- **Split:** in a pod, roughly `promo + 2/3 national + 1/3 local`.

For SNES: model **network = "The Mushroom Network" national ads** (the celebrity-parody spots from
FULL_VISION) and **local = "T3TV" spots** (station-specific). The callsign is the *affiliate*; the
network content is national. This matches the dual identity already in the code (T3TV + SNES-1).

### 2.4 Spot length units

- Base unit = **30 seconds** (the standard, and how ad time is sold).
- 15s and 60s exist but are minority.
- **Infomercials = 30 minutes** (full paid program), a different thing entirely.

### 2.5 The "glue" elements (these make it feel real)

| Element | Duration | Where |
|---|---|---|
| **Station ID** | 5–10s | Top of hour (:00/:30) — "This is T3TV, an affiliate of the Mushroom Network." |
| **Show bumper** | 5–8s | Opening title card of a show (music sting + logo). |
| **"Coming up" bump** | 10–15s | Mid-show, right before a pod — teases the next segment. |
| **Network promo** | 10–30s | "Next week on…" / "Tonight on Must-See TV." |
| **PSA** | 15–30s | Public service announcement (AD Council): Smokey Bear, "Just Say No," McGruff. Usually late-night/access/overnight. |
| **Logo bug** | persistent | Corner network/station logo overlaid whole program. |
| **TV rating card** | 3–5s | TV-G / TV-PG / TV-14 shown at program start (V-chip era, post-1997). |
| **"Brought to you by" / sponsor billboard** | 5s | Sponsor ID at show open/close. |

> **Spec:** build every commercial break as an **ordered list** of these elements, not as one
> undifferentiated "commercial break" card (which is what the current code does).

### 2.6 Hand-off moments (the connective tissue)

Real TV has a predictable **transition sequence** between shows. This is 15–30 seconds and it's the
part most simulators skip. Canonical sequence:

```
[SHOW A ends] → end credits / "tag" scene → "Next on Show A" teaser
    → [LOCAL BREAK: local ad + station ID]
    → [SHOW B bumper: title card + theme sting] → [TV rating card] → Show B content
```

Between *network* shows there's often a network "promo for the next show" and the affiliate does its
station ID at the top of the hour. **Program your hand-offs as first-class objects** (a
`HandOff`/`Transition` segment) — not as an afterthought.

---

## 3. Program & Network Conventions

### 3.1 News format (local news / network morning news)

Anatomy of a 30-min local newscast (structure holds for 30- or 60-min):

- **Open:** graphics sting + theme music, anchor quick-tease of top 3 stories (15–20s).
- **Segment 1 — Top stories:** anchor reads lead, toss to field reporter (a "package" = pre-taped
  60–90s piece with reporter stand-up + sound bites). ~8–10 min.
- **Break** (local pod).
- **Segment 2 — Other news / human interest:** ~4–5 min.
- **Weather:** meteorologist at the weather wall, ~2–3 min, uses green-screen or a weather bug.
- **Sports:** sports anchor, ~2–3 min, highlights + scores ticker.
- **Close:** anchor "that's our broadcast," "have a great night," tease "coming up at 6" or
  "more at 11," roll credits over next-show tease. ~1 min.

**Conventions:** two anchors at a desk (the famous "happy talk" banter), a corner **news bug** with
the station logo + "NEWS 6", **lower-thirds** identifying reporters ("REPORTER: Name"), a scrolling
**ticker** (later 90s), **"breaking news"** banners. The 11pm news is sharper/more serious than the
6pm; the 6pm has more human interest and "news you can use."

> **SNES spec:** Mario = anchor, Luigi = co-anchor/weather, Toad = sports. Reuse the existing
> `create_news_broadcast`, `NewsTicker`, `LowerThird`, `BreakingNewsBanner`. Good foundation — keep.

### 3.2 Game show format

A 30-min syndicated game show (Wheel/Jeopardy) or network (Price is Right is 60 min):

- **Open:** host enters, theme music, product/prize montage, audience applause.
- **Rounds:** scripted rounds with escalating stakes, buzzer/lights, host patter, prize plugs.
- **Commercial pod** after round 1, another mid-way.
- **Final round / bonus:** high-stakes, dramatic.
- **Close:** host sign-off, plug for tomorrow's show, roll credits over the "come on down" bit.

**Conventions:** audience, product placement (prizes), host catchphrases, "you're our next
contestant." The **host + game board** is the set; everything is in-studio.

### 3.3 Sitcom format

- **~22 min.** Structure: cold open → title credits (theme song) → Act 1 → [pod] → Act 2 →
  [pod] → tag scene → credits.
- **Conventions:** laugh track (canned audience), studio-bound sets, recurring catchphrases,
  episode title cards, "created by" credit, TV-PG rating. ~22 episodes/season, new episodes
  fall–spring, **reruns** in summer and in syndication.
- **90s sitcom look:** 4:3 studio, bright practical sets, big laugh-reactions, the "freeze + laugh"
  on a punchline.

### 3.4 Late-night talk format

- **~60 min (Leno/Letterman).** Structure:
  - **Cold open** tease → title/band intro.
  - **Monologue** (5–8 min of topical jokes) → 
  - **Desk bit / correspondence gag** (Letterman: "Top Ten") →
  - **Guest 1** (comedian/actor, ~8–10 min interview) →
  - **[pod]** → 
  - **Guest 2** + **musical/comedy act** (~6 min) →
  - **Close / thank-you / promo of tomorrow's guests.**
- **Conventions:** host + band + sidekick, guest couch, opening monologue, "we'll be right back"
  bumps before every pod, "LIVE" bug (often actually taped earlier that day), intro cards with
  guest names (those famous blue/green font cards).

### 3.5 Soap opera format (daytime drama)

- **30 min** (Y&R, Days) — content ~20 min, ad load ~10 min (heaviest of the day).
- **Structure:** no laugh track, cliffhangers at every pod, ~6–8 scenes with overlapping dialogue,
  **"previously on [show]"** recap open, dramatic stingers between scenes, weekly story arcs.
- This is a great SNES fit for the daytime block (character-driven drama between SNES characters).

### 3.6 Show lifecycle, syndication, reruns, sweeps, seasonality

- **Season:** the TV year runs **September–May** (new episodes) with **summer reruns** and
  **season premieres in mid/late September** (the "fall season").
- **Sweeps:** rating measurement periods that set ad rates: **February, May, November** (and July
  by the late 90s). During sweeps, networks air **stunt programming**: cliffhangers, crossovers,
  guest stars, specials, series finales. `program_90s.py` already handles Feb/May/Nov — correct.
- **Syndication:** after a show accumulates ~100 episodes (≈4–5 seasons), it's sold into
  syndication and **stripped** (aired 5 days/week in access/early fringe as reruns). This is why
  early fringe and access are full of sitcom reruns.
- **Cancellation/pilot lifecycle:** pilot → series order (fall/spring) → full season → renewal →
  cancellation → revival. **Premiere weeks** (Sept) and **finales** (May) are special events.
- **Seasonality:** Christmas specials (Dec), holiday episodes (Halloween, Thanksgiving),
  **summer blocks** (reruns, movie nights), **new year's eve specials**.
- **Nielsen ratings:** reported as a **rating** (share of all TV households) and **share** (share of
  TVs in use). A hit = ~20+ share; top show ~15–20 rating. The code's `RatingsContext` models the
  right concepts — good.

---

## 4. On-Air Look & Feel (90s graphics grammar)

These are cheap to fake and instantly read as "the 90s":

### 4.1 Graphics & typography
- **Faux-3D chrome / bevel:** logos with metallic gradients, beveled edges, drop shadows — the
  "flying toaster / silver chrome" look.
- **Condensed bold sans-serif** titles (Arial Black / Helvetica Black / condensed type), often
  **italic-slanted** with a **gradient fill**.
- **Computer-graphics aesthetic:** glossy sphere logos, 3D wireframe fly-throughs, spinning logo
  reveals (the "CGI logo" — think the spinning silver orb of a 90s station ID).
- **Color palette:** strong primaries + chrome; news used blue/red/gold; sports used yellow/blue.

### 4.2 Standard on-screen furniture
- **Station/network bug:** persistent small logo in a corner (usually lower-right or upper-left)
  the whole program.
- **Lower-third:** name + title box in lower-left for speakers/reporters (existing `LowerThird`).
- **Ticker:** scrolling headlines at the bottom (existing `NewsTicker`).
- **Weather bug:** small temp + condition box.
- **TV rating** card at program start (TV-G/PG/14) — post-1997 V-chip era.

### 4.3 Transitions
- **Digital wipes:** star wipe, circle wipe, page-curl wipe, split-screen sweep, the iconic
  **"digital clock/glitch" wipe** of the era.
- **Fades** to/from black between segments; **dissolves**.
- **Flash frames** on dramatic stingers.
- **3D logo fly-through** at show open/close.

### 4.4 Test patterns / emergency / sign-off (the "dead air" realism)
- **SMPTE color bars** with 1kHz tone (existing `ColorBars`) — shown before sign-on, after
  sign-off, and during maintenance.
- **Test pattern:** the classic **Indian-head test pattern** (NBC) or **SMPTE bars with clock
  circle** — usually an on-screen generated pattern, often with a tone and a clock.
- **"Technical difficulties" / "Please stand by":** color bars + tone + message card, or a static
  "We are experiencing technical difficulties" card (existing `create_station_signoff` covers some
  of this).
- **National Anthem** at sign-off (for affiliates that signed off).
- **Sign-on:** bars → test pattern → National Anthem → station ID → first program.

> **Spec:** give the overnight/sign-off a *real* sequence. Do NOT just fade to black for 7 hours
> (the current FULL_VISION schedule's fatal flaw — see §6).

---

## 5. CONCRETE 24-HOUR SNES NETWORK SCHEDULE TEMPLATE

This is the implementable grid. Modeled on a Big-3 affiliate (national "Mushroom Network" content +
local "T3TV" affiliate inserts). Times = Eastern. Format + duration + rotation rule per slot.

| Clock | Block | Show (SNES) | Format | Dur | Rotation / notes |
|---|---|---|---|---|---|
| 4:00–4:30 | **Overnight 1** | *Infomercial* — "The Power-Up 9000 Exercise Machine" (Toad) | Infomercial | 30m | Rotate among 4 paid-programming parodies |
| 4:30–5:00 | **Overnight 2** | *Infomercial* — "Mushroom Fade Mastery" (magic set) | Infomercial | 30m | |
| 5:00–6:00 | **Overnight 3** | *Classic rerun* — "Zelda: Adventures in Hyrule" (rerun) | 60m drama rerun | 60m | Rotate classic drama reruns |
| 6:00–6:30 | **Early news** | *T3TV Morning Update* | Local news (short) | 30m | Mario + Luigi quick headlines/weather |
| 6:30–7:00 | **Early morning** | *Infomercial / farm-and-home* | Infomercial | 30m | |
| 7:00–9:00 | **Morning news/talk** | *Mushroom Morning* (Mario, Peach, Toad) | Network morning show | 120m | Local cut-in at :25/:55 |
| 9:00–10:00 | **Daytime A** | *Super Playhouse* (kids' block) | Kids' variety | 60m | Mon–Fri; cartoon reruns |
| 10:00–11:00 | **Daytime B** | *The Price is Right-ish* — "Name That Mushroom" | Game show | 60m | |
| 11:00–12:00 | **Daytime C** | *Koopa & Chill* (talk show) | Daytime talk | 60m | Heavy ad load |
| 12:00–12:30 | **Daytime D** | *Midday News* | Network midday news | 30m | |
| 12:30–2:00 | **Daytime E** | *Soap: "The Rings of Hyrule"* | Soap opera | 90m | Heaviest ad load (20min/30m) |
| 2:00–3:00 | **Daytime F** | *Soap: "Bowser's Bitter Heir"* | Soap opera | 60m | |
| 3:00–4:30 | **Daytime G** | *Afternoon Talk* — "The Peach Report" | Daytime talk | 90m | |
| 4:30–6:00 | **Early fringe** | *Sitcom reruns* — "Luigi & Company" | Sitcom rerun | 90m | Stripped (5×/wk) reruns |
| 6:00–6:30 | **Early news** | *Eyewitness News at 6* | Local news | 30m | News bug, ticker |
| 6:30–7:00 | **Early news 2** | *Eyewitness News at 6:30* | Local news | 30m | |
| 7:00–7:30 | **Access** | *Wheel-of-Fortune-like* — "The Coin Block" | Game show | 30m | **Highest-value local slot** |
| 7:30–8:00 | **Access** | *Jeopardy-like* — "Final Fantasy Facts" | Game show | 30m | Magazine/game identity |
| 8:00–9:00 | **Prime (night block)** | *Comedy* — "Super Mario Bros. Show" | Sitcom | 60m | Night-identity slot (see rotations) |
| 9:00–11:00 | **Prime** | *Drama* — "Chrono: A Link to the Present" | Drama | 120m | Or action/event per night block |
| 11:00–11:35 | **Late news** | *News at 11* (sharp, serious) | Local late news | 35m | Ticker + breaking news |
| 11:35–12:35 | **Late-night** | *The Late Show with Wario* | Late-night talk | 60m | Monologue + guests |
| 12:35–1:35 | **Late-night 2** | *Late Night with Waluigi* | Late-night talk | 60m | Younger/sillier |
| 1:35–2:00 | **Late fringe** | *PSA block + station ID* | PSA stack | 25m | McGruff/AD Council-style PSAs |
| 2:00–3:00 | **Overnight** | *Classic rerun* — "EarthBound: The Broadcast" | Rerun | 60m | |
| 3:00–4:00 | **Overnight** | *Infomercial* — rotating | Infomercial | 60m | → loops to 4:00 top |

### Night-identity rotations (the "block programming" that makes a week feel real)
Real networks give each night an identity. Rotate **prime 8–11** on a weekly pattern (SNES-flavored
analogues of the famous blocks):

- **Monday:** *Movie night* — 2hr event film + 1hr drama. 
- **Tuesday:** *Comedy night* — 3× sitcoms.
- **Wednesday:** *Action/adventure* — Street Fighter / Donkey Kong action hour + drama.
- **Thursday:** *"Must-See SNES"* — 3× flagship sitcoms (Friends/Seinfeld analogue) + ER-analogue
  drama → the "watercooler" night.
- **Friday:** *"TGIF SNES"* — family sitcoms 8–10 + comedy 10–11 (young-skewing).
- **Saturday:** *Morning cartoons 7–11* + *evening variety/sports* + action movies 8–11.
- **Sunday:** *Early-anchor drama 7–8* + *"60-Minutes-like" magazine* + *prestige drama* 9–11.

### Rotation & repeat rules
- **Stripped reruns** (early fringe): same show Mon–Fri, different episodes.
- **Sweeps weeks** (Feb/May/Nov): replace regular rotation with **stunt episodes** (cliffhangers,
  crossovers, guest stars, "two-hour specials"). Max production budget + cross-promotion.
- **Premiere week** (mid/late Sept): all-new, heavy promos.
- **Finale week** (May): series finales, retrospective specials.
- **Holidays:** Christmas specials (Dec 1–26), Halloween episodes (late Oct), New Year's Eve
  special.
- **Summer:** more reruns + movie nights + "best of" clip shows.

### Commercial/bumper rotation rules
- Every break is an ordered pod: `promo → national×N → local×1–2 → station ID`.
- **Ad pool:** maintain a pool of N national spots (celebrity-parody: Mario-as-Elon, Bowser-as-The
  Rock, Toad-as-Zuckerberg from FULL_VISION) + M local spots (T3TV: car dealer, furniture, "Tune in
  tonight"). **Never repeat the same spot twice in a row**; shuffle pool; weight local vs national
  by daypart (local-heavy in news/access, national-heavy in prime).
- **Station ID** at every :00 and :30 top.
- **PSAs** clustered in late-night/overnight and during daytime talk.
- **Bug** + **TV rating** persistent per show.

---

## 6. Gaps in the existing attempt → how this report fixes them

| Existing (`program_90s.py` / FULL_VISION) | Problem | Fix (from this report) |
|---|---|---|
| `BREAK_INTERVAL = 6*60` | A break every 6 min = ~10 breaks/hr — unrealistically dense | Pods at ~:08/:20/:36/:48; 22/8 split; daytime 20/10 |
| Daypart mapping `MORNING=7–9`, `DAYTIME=9–16`, `PRIME=19–23`, `OVERNIGHT=1–7` | No sign-on, no access block, no separate early/late news, overnight too long | Full 12-daypart grid in §1 + §5 table |
| FULL_VISION schedule: `11PM–6AM = Test Pattern/Music` | 7 straight hours of test pattern is NOT 90s-authentic (affiliates ran infomercials/reruns/overnight news, and many were 24h) | Real overnight: infomercials, classic reruns, overnight news, PSA block, sign-on sequence |
| FULL_VISION: `5–7 Evening News`, `9–11 Late Night Talk` | Evening news starting at 5 is right, but 9–11 as "late night talk" collides with prime (prime is 8–11); late-night is post-11:35 | Corrected blocks: prime 8–11, late news 11, late-night 11:35+ |
| Commercials as single `CommercialBreakCard` | No pod ordering, no network/local split, no hand-off | Ordered pod grammar + hand-off objects (§2.5–2.6) |
| No `HandOff`/transition concept | Misses the connective tissue | Model show-to-show transition as first-class segment |
| **Daypart block shows lists** (`MORNING: ["game_show","talk","news"]`) are reasonable but not a fixed grid | Random selection of show *type* per daypart still feels random — the original failure | Lock to a **fixed grid** (§5); daypart picks *within* the slot, not the slot itself |

**The core failure diagnosis:** the original project had the *ingredients* (bumpers, lower-thirds,
commercial cards, color bars) but no **fixed daily grid** and no **commercial grammar**. It treated
programming as "pick a random show type for the current daypart" — which produces random-feeling TV.
Real 90s TV is *predictable*: same show at 6pm, same at 7:30, prime 8–11. **Fix the skeleton first
(the grid + the pod grammar), then decorate with all the existing good assets.**

---

## 7. Ranked: what most creates the authentic 90s-TV feel

1. **The fixed daily grid + correct clock blocks** (viewer can guess the time from the format).
2. **Commercial pod grammar** — ordered break sequences, correct 22/8 math, network/local split.
3. **Hand-off/transition moments** between shows (the connective tissue).
4. **Overnight/sign-off realism** — infomercials, reruns, color bars, "technical difficulties,"
   sign-on. The dead air is where authenticity lives.
5. **90s graphics grammar** — corner bug, lower-thirds, chrome/bevel type, digital wipes, test
   patterns. Cheap, instant 90s signal.
6. **Night-identity block programming** (Must-See TV / TGIF analogues) + sweeps stunting.
7. **Late-night talk format** (monologue → guests → band) — very recognizable.

---

## 8. Best next action for the builder

**Rebuild the scheduler around a fixed grid, not around daypart-random selection.** Concretely, in
`app/program_90s.py`:

1. Replace the loose `DAYPART_SHOWS` type-lists with a **fixed 24-slot schedule table** (the §5
   grid) — each slot = `(daypart, show, format, duration, rotation_pool)`. `get_current_daypart`
   returns the §1 blocks; the grid, not daypart, decides what's on.
2. Fix the commercial math: set `CONTENT_PER_HALF_HOUR=22*60`, add `ADS=8*60` (prime) / `10*60`
   (daytime), and replace the `6*60` `BREAK_INTERVAL` with the **pod clock** `[8, 20, 36, 48]`
   minutes for hours (and `[:10, :20]` for half-hours).
3. Add a **`HandOff`/transition segment type** and a **pod builder** that emits the ordered
   `promo → national → local → station ID` sequence — extend the existing `CommercialBreakCard`
   into a list-of-elements rather than one card.
4. Wire the §5 **rotation rules** (stripped reruns, night-identity week, sweeps/premiere/finale/
   holiday overrides) onto the grid.
5. Keep ALL the existing asset layers (bumpers, lower-thirds, ticker, color bars, PSAs) — they are
   good; they were just being driven by the wrong skeleton.

Once the grid + pod grammar are in, the SNES network will read as a *real* 90s broadcast day, and
the existing living-world/Gary/authentic-asset layers can be layered back on top without the
"random filler" failure.
