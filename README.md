# Create Quests

FTB Quests questlines for Create and its addons (Minecraft 1.21.1, NeoForge), written to walk a new player through each mod.

| Chapter | Quests | Needs | Covers |
|---|---|---|---|
| Create | 71 | Create | Rotation and power, copycat blocks, materials (sheets, kelp, casings, electron tubes) and what each unlocks, steam, equipment, build projects (farms and factories, each a checkbox plus a stack of output as proof), processing, brass, contraptions, fluids, precision mechanisms, logistics, trains |
| Aeronautics | 36 | Create Aeronautics | Simulated contraptions (diagrams, handles, springs), then four build paths: blimps, planes, helicopters (with keyboard flying and a mounted potato cannon) and cars |
| Steam 'n' Rails | 10 | Steam 'n' Rails | Track gauges, monorail, switches, couplers, semaphores, conductors, locometal |
| Crafts & Additions | 14 | Create Crafts & Additions | The rolling mill, wires and spools, alternators and electric motors, a power grid project, the Tesla Coil and electrum, accumulators, powered contraptions, liquid fuel |
| Modern Foundry | 14 | Modern Foundry | Tool parts, the smeltery, casting, the anvil, cobalt and the foundry |

Chapters for mods that aren't installed are left out when you generate, as are single quests for optional mods (the Automated Kitchen project needs Slice & Dice and Farmer's Delight).

Rewards are deliberately small: a level of XP per quest, survival basics (coal, torches, bread) early on, a few raw materials at milestones, and for parts you always need in sets (shafts, tires, track) you get back as many as the quest asked for.

## Using the quests

Requires FTB Quests, FTB Library and FTB Teams (FTB XMod Compat is recommended for recipe links).

Generate the chapters against your pack's mods folder, then copy `config/ftbquests/quests/` into your instance:

```sh
python3 -I generate.py --mods /path/to/instance/mods /path/to/instance
```

The `config/` folder in this repo is the output for all five mods with the default profile.

Quest ids are stable across regenerations, so updating keeps player progress.

## Chapters

Create and Aeronautics each get a chapter group with several chapters:

- **Create:** Create (the whole main progression on one hand-placed map), Equipment, Projects, plus Steam 'n' Rails and Crafts & Additions when installed
- **Aeronautics:** Basics, Blimps, Planes, Helicopters, Cars

Steam 'n' Rails, Crafts & Additions and Modern Foundry are single chapters. Prerequisites cross chapters where the recipes need them.

Quest ids come from the mod and the quest, not the chapter, so moving a quest between chapters keeps player progress.

The Create, Equipment, Crafts & Additions and Modern Foundry chapters are hand-placed (`POSITIONS` in `generate.py`); the rest are laid out automatically. To adjust a layout, move quests in FTB Quests' editor, quit the world, and copy the positions back:

```sh
python3 -I import_positions.py --mods /path/to/instance/mods --quests /path/to/instance/config/ftbquests/quests
```

Name a chapter file (e.g. `railways`) to start hand-placing it too.

## Profiles

A profile picks which mods' quests to include and whether to give item rewards. See `profiles/default.json`; pass another with `--profile`.

```json
{
  "mods": ["create", "aeronautics"],
  "item_rewards": true
}
```

## Checking quest order

`check_order.py` reads every recipe in the mods folder and reports quests whose items need an ingredient or machine that is only taught by a quest that isn't a prerequisite:

```sh
python3 -I check_order.py --mods /path/to/instance/mods
```

Tested with Create 6.0.10, Create Aeronautics 1.3.2, Steam 'n' Rails 0.3.0-beta.2 and Modern Foundry 4.1.8.

## License

MIT, see `LICENSE`.
