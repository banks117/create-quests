# Create Quests

FTB Quests questlines for Create and its addons (Minecraft 1.21.1, NeoForge), written to walk a new player through each mod.

| Chapter | Quests | Needs | Covers |
|---|---|---|---|
| Create | 48 | Create | Rotation and power, steam, processing, brass, contraptions, fluids, precision mechanisms, logistics, trains |
| Aeronautics | 27 | Create Aeronautics | Simulated contraptions, then four build paths: blimps, planes, helicopters and cars |
| Steam 'n' Rails | 10 | Steam 'n' Rails | Track gauges, monorail, switches, couplers, semaphores, conductors, locometal |
| Modern Foundry | 14 | Modern Foundry | Tool parts, the smeltery, casting, the anvil, cobalt and the foundry |

Chapters for mods that aren't installed are left out when you generate.

Rewards are deliberately small: a level of XP per quest, survival basics (coal, torches, bread) early on, a few raw materials at milestones, and for parts you always need in sets (shafts, tires, track) you get back as many as the quest asked for.

## Using the quests

Requires FTB Quests, FTB Library and FTB Teams (FTB XMod Compat is recommended for recipe links).

Generate the chapters against your pack's mods folder, then copy `config/ftbquests/quests/` into your instance:

```sh
python3 -I generate.py --mods /path/to/instance/mods /path/to/instance
```

The `config/` folder in this repo is the output for all four chapters with the default profile.

Quest ids are stable across regenerations, so updating keeps player progress.

## Profiles

A profile picks the chapter group title, which chapters to include, and whether to give item rewards. See `profiles/default.json`; pass another with `--profile`.

```json
{
  "group_key": "create-quests",
  "group_title": "Create Quests",
  "chapters": ["create", "aeronautics"],
  "item_rewards": true
}
```

`group_key` feeds the group id; keep it fixed once players are using it.

## Checking quest order

`check_order.py` reads every recipe in the mods folder and reports quests whose items need an ingredient or machine that is only taught by a quest that isn't a prerequisite:

```sh
python3 -I check_order.py --mods /path/to/instance/mods
```

Tested with Create 6.0.10, Create Aeronautics 1.3.2, Steam 'n' Rails 0.3.0-beta.2 and Modern Foundry 4.1.8.

## License

MIT, see `LICENSE`.
