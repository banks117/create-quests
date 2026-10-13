# Gears and Gardens Quests

FTB Quests questlines for the **Create: Gears and Gardens** modpack (Minecraft 1.21.1, NeoForge), written to walk a new player through Create and its addons.

| Chapter | Quests | Covers |
|---|---|---|
| Create Basics | 45 | Rotation and power, processing, brass, contraptions, fluids, precision mechanisms, logistics, trains |
| Aeronautics | 25 | Simulated contraptions, then three build paths: blimps, planes and cars |
| Steam 'n' Rails | 10 | Track gauges, monorail, switches, couplers, semaphores, conductors, locometal |
| Modern Foundry | 14 | Tool parts, the smeltery, casting, the anvil, cobalt and the foundry |

Rewards are deliberately small: a level of XP per quest, survival basics (coal, torches, bread) early on, a few raw materials at milestones, and for parts you always need in sets (shafts, tires, track) you get back as many as the quest asked for.

## Using the quests

Requires FTB Quests, FTB Library and FTB Teams (FTB XMod Compat is recommended for recipe links).

Copy `config/ftbquests/quests/` into your instance's `config/ftbquests/quests/`. Quest ids are stable across regenerations, so updating the files keeps player progress.

## Regenerating

The chapters are generated from `generate.py`, which checks every item id against the mod jars:

```sh
python3 -I generate.py
```

By default it reads jars from the Prism instance's mods folder; set `GG_MODS` to point elsewhere.

Expected mods: Create 6.0.10, Create Aeronautics 1.3.2 (bundled), Steam 'n' Rails 0.3.0-beta.2, Modern Foundry 4.1.8.
