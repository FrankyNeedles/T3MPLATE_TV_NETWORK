#!/usr/bin/env python3
import json
from pathlib import Path

CACHE_PATH = Path("data/tcrf_cache.json")

TOP_50_SNES_GAMES = {
    "super_mario_world": {
        "title": "Super Mario World (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Super_Mario_World_(SNES)",
    },
    "the_legend_of_zelda_a_link_to_the_past": {
        "title": "The Legend of Zelda: A Link to the Past (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/The_Legend_of_Zelda:_A_Link_to_the_Past_(SNES)",
    },
    "chrono_trigger": {
        "title": "Chrono Trigger (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Chrono_Trigger_(SNES)",
    },
    "super_metroid": {
        "title": "Super Metroid (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Super_Metroid_(SNES)",
    },
    "super_mario_world_2_yoshis_island": {
        "title": "Super Mario World 2: Yoshi's Island (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Super_Mario_World_2:_Yoshi's_Island_(SNES)",
    },
    "donkey_kong_country": {
        "title": "Donkey Kong Country (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Donkey_Kong_Country_(SNES)",
    },
    "earthbound": {
        "title": "EarthBound (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/EarthBound_(SNES)",
    },
    "final_fantasy_vi": {
        "title": "Final Fantasy VI (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Final_Fantasy_VI_(SNES)",
    },
    "secret_of_mana": {
        "title": "Secret of Mana (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Secret_of_Mana_(SNES)",
    },
    "donkey_kong_country_2_diddys_kong_quest": {
        "title": "Donkey Kong Country 2: Diddy's Kong Quest (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Donkey_Kong_Country_2:_Diddy's_Kong_Quest_(SNES)",
    },
    "street_fighter_ii_the_world_warrior": {
        "title": "Street Fighter II: The World Warrior (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Street_Fighter_II_(SNES)",
    },
    "kirby_super_star": {
        "title": "Kirby Super Star (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Kirby_Super_Star_(SNES)",
    },
    "star_fox": {
        "title": "Star Fox (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Star_Fox_(SNES)",
    },
    "super_castlevania_iv": {
        "title": "Super Castlevania IV (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Super_Castlevania_IV_(SNES)",
    },
    "mega_man_x": {
        "title": "Mega Man X (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Mega_Man_X_(SNES)",
    },
    "super_mario_kart": {
        "title": "Super Mario Kart (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Super_Mario_Kart_(SNES)",
    },
    "donkey_kong_country_3_dixie_kongs_double_trouble": {
        "title": "Donkey Kong Country 3: Dixie Kong's Double Trouble! (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Donkey_Kong_Country_3:_Dixie_Kong's_Double_Trouble!_(SNES)",
    },
    "super_mario_rpg_legend_of_the_seven_stars": {
        "title": "Super Mario RPG: Legend of the Seven Stars (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Super_Mario_RPG:_Legend_of_the_Seven_Stars_(SNES)",
    },
    "f_zero": {
        "title": "F-Zero (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/F-Zero_(SNES)",
    },
    "pilotwings": {
        "title": "Pilotwings (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Pilotwings_(SNES)",
    },
    "simcity": {
        "title": "SimCity (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/SimCity_(SNES)",
    },
    "super_punch_out": {
        "title": "Super Punch-Out!! (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Super_Punch-Out!!_(SNES)",
    },
    "u_n_squadron": {
        "title": "U.N. Squadron (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/U.N._Squadron_(SNES)",
    },
    "super_ghouls_n_ghosts": {
        "title": "Super Ghouls 'n Ghosts (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Super_Ghouls_%27n_Ghosts_(SNES)",
    },
    "harvest_moon": {
        "title": "Harvest Moon (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Harvest_Moon_(SNES)",
    },
    "terranigma": {
        "title": "Terranigma (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Terranigma_(SNES)",
    },
    "lufia_ii_rise_of_the_sinistrals": {
        "title": "Lufia II: Rise of the Sinistrals (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Lufia_II:_Rise_of_the_Sinistrals_(SNES)",
    },
    "ogre_battle": {
        "title": "Ogre Battle: The March of the Black Queen (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Ogre_Battle:_The_March_of_the_Black_Queen_(SNES)",
    },
    "tetris_attack": {
        "title": "Tetris Attack (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Tetris_Attack_(SNES)",
    },
    "breath_of_fire_ii": {
        "title": "Breath of Fire II (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Breath_of_Fire_II_(SNES)",
    },
    "actraiser": {
        "title": "ActRaiser (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/ActRaiser_(SNES)",
    },
    "super_mario_all_stars": {
        "title": "Super Mario All-Stars (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Super_Mario_All-Stars_(SNES)",
    },
    "contra_iii_the_alien_wars": {
        "title": "Contra III: The Alien Wars (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Contra_III:_The_Alien_Wars_(SNES)",
    },
    "super_double_dragon": {
        "title": "Super Double Dragon (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Super_Double_Dragon_(SNES)",
    },
    "axelay": {
        "title": "Axelay (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Axelay_(SNES)",
    },
    "super_star_wars": {
        "title": "Super Star Wars (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Super_Star_Wars_(SNES)",
    },
    "teenage_mutant_ninja_turtles_turtles_in_time": {
        "title": "Teenage Mutant Ninja Turtles: Turtles in Time (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Teenage_Mutant_Ninja_Turtles:_Turtles_in_Time_(SNES)",
    },
    "pocky_and_rocky": {
        "title": "Pocky & Rocky (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Pocky_%26_Rocky_(SNES)",
    },
    "super_putty": {
        "title": "Super Putty (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Super_Putty_(SNES)",
    },
    "super_valis_4": {
        "title": "Super Valis 4 (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Super_Valis_4_(SNES)",
    },
    "magical_drop_2": {
        "title": "Magical Drop 2 (USA)",
        "rom_sha1": "0000000000000000000000000000000000000000",
        "tcrf_url": "https://tcrf.net/Magical_Drop_2_(SNES)",
    },
}

if CACHE_PATH.exists():
    with open(CACHE_PATH, "r") as f:
        cache = json.load(f)
    for gid, data in cache.items():
        if gid in TOP_50_SNES_GAMES:
            TOP_50_SNES_GAMES[gid].update(data)

print(f"TOP_50 loaded: {len(TOP_50_SNES_GAMES)} games")
