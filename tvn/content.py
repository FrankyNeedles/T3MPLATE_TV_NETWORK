#!/usr/bin/env python3
"""Content tables -- Gary's cast, show presets, world lore, and the world-aware
fallback decision templates.

This replaces the old gary.py's content tables with a cast that maps to the real
curated sprite kit, and -- per RESEARCH_LIVING -- makes the fallback a *
parameterized-by-world-state* beat selector instead of `random.choice(templates)`.
"""
from __future__ import annotations

# --- The curated cast (name -> sprite kind + bio) -----------------------------
CAST = {
    "mario":  dict(kind="mario",  game="Super Mario World",
                   role="News Anchor", mood="cheerful",
                   bio="Former plumber turned anchor. Speaks in third person."),
    "luigi":  dict(kind="luigi",  game="Super Mario World",
                   role="Co-Anchor / Weather", mood="nervous",
                   bio="Mario's brother. Afraid of ghosts, great at forecasts."),
    "peach":  dict(kind="peach",  game="Super Mario World",
                   role="Morning Show Host", mood="gracious",
                   bio="Royalty with a background in diplomacy. Runs Mushroom Morning."),
    "toad":   dict(kind="toad",   game="Super Mario World",
                   role="Sports Desk", mood="bubbly",
                   bio="Keeper of the Sports Desk. Loud, tiny, enthusiastic."),
    "bowser": dict(kind="bowser", game="Super Mario World",
                   role="Talk Show Host", mood="booming",
                   bio="King of the Koopas. Also runs a rival late-night talk show."),
    "yoshi":  dict(kind="yoshi",  game="Super Mario World",
                   role="Sidekick / Contestant", mood="happy",
                   bio="Friendly dinosaur sidekick. Loves fruit. Hop-hops everywhere."),
    "wario":  dict(kind="wario",  game="Wario Land",
                   role="Late Night Host", mood="greedy",
                   bio="Self-appointed star of late night. Wants the money AND the fame."),
    "link":   dict(kind="link",   game="A Link to the Past",
                   role="Action Hero", mood="heroic",
                   bio="Hero of Hyrule. Stars in the big prime-time action drama."),
    "zelda":  dict(kind="zelda",  game="A Link to the Past",
                   role="Guest Host", mood="wise",
                   bio="Princess of Hyrule. Occasional guest; the audience adores her."),
}
SPRITE_KIND = {c["kind"] for c in CAST.values()}

# Classic on-air relationships (seeded into the world as friendships/feuds).
SEED_FRIENDSHIPS = [("mario", "luigi", 60), ("peach", "mario", 40),
                    ("yoshi", "mario", 50), ("link", "zelda", 65)]
SEED_FEUDS = [("mario", "bowser", -70), ("wario", "luigi", -35)]

# --- Show presets: format -> roles drawn from the cast -----------------------
SHOW_PRESETS = {
    "news":     dict(sets=["news_studio"], hosts=["mario", "luigi"],
                     ticker=True, mood="cheerful"),
    "morning":  dict(sets=["talk_show"], hosts=["peach", "mario"],
                     ticker=False, mood="gracious"),
    "talk":     dict(sets=["talk_show"], hosts=["bowser"],
                     ticker=False, mood="booming", has_guest=True),
    "game_show":dict(sets=["game_show"], hosts=["toad", "bowser"],
                     ticker=False, mood="excited", contestants=True),
    "soap":     dict(sets=["diner"], hosts=["luigi", "peach"],
                     ticker=False, mood="dramatic"),
    "late_night":dict(sets=["studio"], hosts=["wario"],
                     ticker=False, mood="greedy", has_guest=True),
    "cartoon":  dict(sets=["cartoon_house"], hosts=["yoshi", "toad"],
                     ticker=False, mood="happy"),
    "sitcom":   dict(sets=["cartoon_house"], hosts=["yoshi", "toad"],
                     ticker=False, mood="happy", comedy=True),
    "psa":      dict(sets=["studio"], hosts=["toad"],
                     ticker=False, mood="sincere", public_service=True),
    "sports":   dict(sets=["sports_arena"], hosts=["toad"],
                     ticker=True, mood="bubbly"),
    "action":   dict(sets=["city"], hosts=["link"],
                     ticker=True, mood="heroic"),
    "weather":  dict(sets=["news_studio"], hosts=["luigi"],
                     ticker=False, mood="nervous"),
    "infomercial": dict(sets=["studio"], hosts=["toad"],
                     ticker=False, mood="excited"),
    "rerun":    dict(sets=["cartoon_house"], hosts=["yoshi"],
                     ticker=False, mood="happy"),
}
DAYPART_FORMATS = {
    "overnight":     ["infomercial", "rerun"],
    "early_morning": ["news"],
    "morning":       ["morning", "news"],
    "daytime":       ["game_show", "soap", "talk"],
    "early_fringe":  ["talk", "sitcom"],
    "early_news":    ["news"],
    "access":        ["game_show"],
    "prime":         ["sitcom", "action", "drama"],
    "late_news":     ["news"],
    "late_night":    ["late_night", "talk"],
}

# --- Commercial & promo content ----------------------------------------------
NATIONAL_SPOTS = [
    "Mushroom Cola", "Koopa Way", "Star Coin Bank", "Yoshi's Yarn",
    "Warp Pipe Travel", "1-Up Energy", "Feather Falls Airline",
    "Cape Feather Razors", "Koopa Troopa Insurance",
]
LOCAL_SPOTS = [
    "Toad Town Ford", "Kitchen Sink Emporium", "Tune in Tonight - T3TV",
    "Cape Town Diner", "Mushroom Mutual",
]
PSA_TOPICS = [
    ("Stay in School", "Council of Mushroom Kingdom"),
    ("Just Say No to Goombas", "Mushroom Department of Health"),
    ("Buckle Up at Warp Pipes", "Road Safety Koopaling Committee"),
    ("Eat Your Vegetables", "Sunflower Society"),
    ("Respect Your Elders", "Hyrule Elders Union"),
]

# --- Calendar/series flavor pools (drives SeasonState + episode titles) ------
SEASONS = {   # real calendar month -> (season, holiday/event driving programming)
    1: ("Winter", "New Year Tournament"),
    2: ("Winter", "Festival of Love"),
    3: ("Spring", "Mushroom Blossom Parade"),
    4: ("Spring", "Easter Egg Hunt"),
    5: ("Spring", "Star Festival"),
    6: ("Summer", "Beach Bash Week"),
    7: ("Summer", "Midsummer Sweeps"),
    8: ("Summer", "Harvest Kickoff"),
    9: ("Fall", "Back-to-School"),
    10: ("Fall", "Halloween Haunt"),
    11: ("Fall", "Thanksgiving Sweeps"),
    12: ("Winter", "Holiday Specials"),
}
# Per-genre episode title pools so each show's episodes have real, rotating titles.
EPISODE_TITLES = {
    "news":      ["The Pipe-Leak Scandal", "Storm Watch", "Mushroom Budget Crisis",
                  "Investigation at Toad Town", "Election Day", "The Arresting Update"],
    "morning":   ["Coffee at the Castle", "Guest Chef Yoshi", "Garden Party",
                  "Luigi's Forecast Surprise", "Morning Mailbag", "The Peach Parade"],
    "talk":      ["The Rival Returns", "Bowser Candid", "Late Confession",
                  "Feud or Fix?", "The Inconvenient Guest", "Bitter Apology"],
    "game_show": ["The Double-Down Round", "Return of the Champion", "Plumber vs Koopa",
                  "Lucky Star Bonus", "The Sudden Death Tie", "Winner Takes the Pipe"],
    "soap":      ["The Secret Heir", "Betrayal at the Diner", "Second Chance",
                  "The Long-Lost Letter", "A Storm At Sunrise", "The Reconciliation"],
    "late_night": ["The Crypt-Keeper's Grudge", "Starlight Monologue", "The Uninvited Guest",
                      "Midnight Confession", "Rooftop Fireside", "The Final Bow"],
    "sports":    ["Overtime Heartbreak", "The Comeback Drive", "Championship Finale",
                  "Rookie of the Year", "Snow Day Showdown", "The Free-Throw Faceoff"],
    "cartoon":   ["Yoshi's Big Snack", "The Great Garden Race", "Warp Pipe Mishap",
                  "Toad's Slipper Surprise", "The Song Contest", "Party at the Castle"],
    "sitcom":    ["Date Night Disaster", "The Misplaced Key", "Roommate Rumble",
                  "Bowser Babysits", "The Talent Show", "Neighborly Chaos"],
    "action":    ["The Shadow Fortress", "Raid on the Keep", "The Lost Relic",
                  "Siege of Hyrule", "The Phantom Step", "Escape from the Tower"],
}

# --- Format coherence table (WEAK-1a): which beats a format may air ----------
# An infomercial / PSA / test-pattern / rerun may NEVER carry a feud or friendship
# skit -- it has a sales/announcement voice, not an interpersonal-drama one.
# A news/weather/sports/report format references the world but does not PERFORM it.
FORMAT_ALLOWED_BEATS = {
    "news":        ("ratings", "show_promo", "gag"),
    "morning":     ("friendship", "gag", "show_promo", "ratings"),
    "talk":        ("feud", "friendship", "gag", "show_promo", "ratings", "seeking_work"),
    "game_show":   ("feud", "friendship", "gag", "show_promo", "ratings"),
    "soap":        ("feud", "friendship", "show_promo", "ratings"),
    "late_night":  ("feud", "friendship", "gag", "show_promo", "ratings", "seeking_work"),
    "cartoon":     ("gag", "friendship", "show_promo", "ratings"),
    "sitcom":      ("gag", "friendship", "show_promo", "ratings"),
    "sports":      ("ratings", "show_promo"),
    "action":      ("show_promo", "ratings", "gag"),
    "weather":     ("ratings", "show_promo"),
    "psa":         ("show_promo", "ratings"),
    "infomercial": ("show_promo", "ratings"),      # NEVER feud/friendship
    "rerun":       ("show_promo", "ratings"),
}

# --- World-aware beat templates (fallback, parameterized by digest) ----------
# Placeholders are filled from the living-world digest (top friendships/feuds,
# active shows, running gags, seeking-work guests) so the feed is CAUSED by the
# world, not random. `{a}`/`{b}` are the RELATIONSHIP pair (real feud/friendship
# actors -- WEAK-1b); `{score}` their live bond. `{c1}`/`{c2}` are the hosts.
# Each beat carries MULTIPLE dialogue variants (rotated per airing via a seed ->
# GAP-3) AND per-format voice overrides so every format sounds like itself
# (WEAK-1c).
FALLBACK_BEATS = {
    "friendship": {
        "story": "{a} and {b} co-host today -- their friendship is at {score}.",
        "variants": [
            [("{a}", "Now folks, {b} and I -- we're as tight as a warp-pipe seal."),
             ("{b}", "You and me, {a}. Mushrooms for life.")],
            [("{a}", "The best part of this job is sharing the desk with {b}."),
             ("{b}", "Aw {a}, you'll make me blush. To the viewers -- look at us!")],
            [("{a}", "Folks ask how we stay so close through all this. {b}, you first."),
                         ("{b}", "Toadstools don't lie, {a}. That's the whole secret.")],
                        [("{a}", "One for the record books -- {b} and I, partners again."),
                         ("{b}", "And the best team on T3TV says hi, {a}.")],
                    ],
        "formats": {
            "morning": [
                [("{a}", "A perfect morning to have {b} dropping by the studio!"),
                 ("{b}", "Your coffee's already here, {a}. I never miss it.")],
                [("{a}", "{b}, you bring such sunshine to our early set."),
                                 ("{b}", "Only because you make the welcome, {a}.")],
                                [("{a}", "Morning viewers -- {b}'s here, so today is already off to a win."),
                                 ("{b}", "Save a seat for me, {a}. I'm not leaving.")],
                            ],
            "talk": [
                [("{a}", "We've got {b} on the couch -- and you know that's family."),
                 ("{b}", "When {a} calls, I come running. Warts and all.")],
            ],
        },
        "motion": "talk",
    },
    "feud": {
        "story": "Viewers, {a} and {b} are feuding again (score {score}). Drama is guaranteed.",
        "variants": [
            [("{a}", "{b}, we are NOT going to rehash last week."),
             ("{b}", "Oh, we absolutely are, {a}.")],
            [("{a}", "I won't take the high road and pretend, {b}, that this is fine."),
             ("{b}", "Fine is for places without {a}. This is a battlefield.")],
            [("{a}", "For the record, {b} started this. The viewers know."),
             ("{b}", "The viewers know {a} finished nothing. That's the record.")],
        ],
        "formats": {
            "soap": [
                [("{a}", "Every time I think we've buried the hatchet, {b}, you dig it up."),
                 ("{b}", "Some wounds never heal, {a}. Ours is favorite.")],
            ],
            "late_night": [
                [("{a}", "Big feud energy tonight -- {b} and I have unfinished business."),
                 ("{b}", "Lights, camera, and a grudge, {a}. Perfect late-night TV.")],
            ],
            "game_show": [
                [("{a}", "Round two, {b} -- let's settle this thing on the buzzer."),
                 ("{b}", "Your buzzer, {a}. My sweep. Deal.")],
            ],
        },
        "motion": "talk",
    },
    "gag": {
        "story": "And once again the fans loved {gag} -- that's {count} times now.",
        "variants": [
            [("{c1}", "Did you see it? {gag}, right here on air!"),
             ("{c2}", "That's number {count}, and the viewers can't get enough.")],
            [("{c1}", "I thought we'd seen the last of it. Nope -- {gag}!"),
             ("{c2}", "Number {count} and counting. It's a tradition now.")],
        ],
        "formats": {
            "cartoon": [
                [("{c1}", "Here we go again -- {gag}! Who wrote that in?"),
                 ("{c2}", "The audience, {c1}. They're the writers now.")],
            ],
            "morning": [
                [("{c1}", "A fond little {gag} to open the show -- the fans adore it."),
                 ("{c2}", "It's back for number {count}. We love you for it.")],
            ],
        },
        "motion": "happy",
    },
    "seeking_work": {
        "story": "{guest} is looking for work after their last show wrapped. Welcome as today's guest!",
        "variants": [
            [("{host}", "Everyone, welcome {guest} to the show!"),
             ("{guest}", "Thanks, {host}. I'm really looking for the next big thing.")],
            [("{host}", "The very talented {guest} joins us. They're between shows, folks."),
             ("{guest}", "And I'm ready for my close-up, {host}. Here's hoping.")],
        ],
        "formats": {
            "talk": [
                [("{host}", "We've got {guest} hot off a wrap -- let's put them to work!"),
                 ("{guest}", "Point me at the mic, {host}. I'm all yours.")],
            ],
        },
        "motion": "wave",
    },
    "show_promo": {
        "story": "Tonight on {show}: a must-see episode. Don't touch that dial!",
        "variants": [
            [("{c1}", "Coming up next, {show} -- you will not want to miss this."),
             ("{c2}", "Stay right there, viewers.")],
            [("{c1}", "Clear your schedule -- {show} is next and it's huge."),
                         ("{c2}", "You heard it first on T3TV.")],
                        [("{c1}", "You won't want to touch that dial -- {show} is coming up."),
                         ("{c2}", "Right here on T3TV, right after this break.")],
                    ],
        "formats": {
            "infomercial": [
                [("{c1}", "But wait, there's more -- right after this, {show} on T3TV."),
                 ("{c2}", "Keep your dial tuned. It's the offer of the year.")],
                [("{c1}", "Operators are standing by -- and so is {show}, next."),
                 ("{c2}", "Don't miss the deal these viewers are calling about.")],
            ],
            "psa": [
                [("{c1}", "A public announcement from all of us -- and {show} is next."),
                 ("{c2}", "Stay informed, stay kind, stay tuned to T3TV.")],
            ],
            "news": [
                [("{c1}", "Up next on {show}: the story everyone's whispering about."),
                 ("{c2}", "Straight ahead after this break.")],
            ],
        },
        "motion": "idle",
    },
    "ratings": {
        "story": "{show} is pulling strong ratings this week. The whole station is buzzing.",
        "variants": [
            [("{c1}", "Word is {show} hit its best numbers yet!"),
             ("{c2}", "Must be something in the warp pipe water.")],
            [("{c1}", "The overnight numbers came in -- {show} is on fire."),
             ("{c2}", "The viewers have spoken, and they love it.")],
        ],
        "formats": {
            "news": [
                            [("{c1}", "Ratings are in and {show} owns its slot this week."),
                             ("{c2}", "A sweep-worthy performance across the board.")],
                        ],
                        "infomercial": [
                            [("{c1}", "The numbers don't lie, and tonight {show} tops them all."),
                             ("{c2}", "Call the numbers you see -- this is the hour to tune in.")],
                        ],
                        "sports": [
                            [("{c1}", "The numbers are in, and {show} is winning its demo tonight."),
                             ("{c2}", "A ratings drive the whole arena can cheer.")],
                        ],
        },
        "motion": "happy",
    },
}