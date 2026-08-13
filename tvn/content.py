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

# --- World-aware beat templates (fallback, parameterized by digest) ----------
# Placeholders are filled from the living-world digest (top friendships/feuds,
# active shows, running gags, seeking-work guests) so the feed is CAUSED by the
# world, not random.
FALLBACK_BEATS = {
    "friendship": {
        "story": "{c1} and {c2} co-host today -- their friendship is at {score}.",
        "dialogue": [
            ("{c1}", "Great to have {c2} back on the show today!"),
            ("{c2}", "The pleasure's mine, {c1}."),
        ],
        "motion": "talk",
    },
    "feud": {
        "story": "Viewers, {c1} and {c2} are feuding again (score {score}). Drama is guaranteed.",
        "dialogue": [
            ("{c1}", "{c2}, we are NOT going to rehash last week."),
            ("{c2}", "Oh, we absolutely are."),
        ],
        "motion": "talk",
    },
    "gag": {
        "story": "And once again the fans loved {gag} -- that's {count} times now.",
        "dialogue": [
            ("{c1}", "Did you see it? {gag}, right on air!"),
            ("{c2}", "The viewers can't get enough."),
        ],
        "motion": "happy",
    },
    "seeking_work": {
        "story": "{guest} is looking for work after their last show wrapped. Welcome as today's guest!",
        "dialogue": [
            ("{host}", "Everyone, welcome {guest} to the show!"),
            ("{guest}", "Thanks for having me. I'm really looking for the next big thing."),
        ],
        "motion": "wave",
    },
    "show_promo": {
        "story": "Tonight on {show}: a must-see episode. Don't touch that dial!",
        "dialogue": [
            ("{c1}", "Coming up next, {show} -- you will not want to miss this."),
            ("{c2}", "Stay right there, viewers."),
        ],
        "motion": "idle",
    },
    "ratings": {
        "story": "{show} is pulling strong ratings this week. The whole station is buzzing.",
        "dialogue": [
            ("{c1}", "Word is {show} hit its best numbers yet!"),
            ("{c2}", "Must be something in the warp pipe water."),
        ],
        "motion": "happy",
    },
}