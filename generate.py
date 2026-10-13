"""Generate FTB Quests chapters for Create and its addons.

Usage: python3 -I generate.py --mods MODS_DIR [--profile PROFILE.json] [OUT_DIR]
Writes OUT_DIR/config/ftbquests/quests (default OUT_DIR: next to this script).
Every item id is checked against the jars in MODS_DIR, and chapters whose mods aren't there are skipped.
"""
import argparse, collections, hashlib, io, json, os, re, shutil, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--mods", required=True, help="folder of mod jars to validate against")
ap.add_argument("--profile", default=os.path.join(HERE, "profiles", "default.json"))
ap.add_argument("--minecraft-jar", default=os.path.expanduser(
    "~/Library/Application Support/PrismLauncher/libraries/com/mojang/minecraft/1.21.1/minecraft-1.21.1-client.jar"),
    help="vanilla client jar, used to check minecraft: item ids")
ap.add_argument("out", nargs="?", default=HERE)
args = ap.parse_args()
MODS, OUT = args.mods, args.out
PROFILE = json.load(open(args.profile))


# ---------------------------------------------------------------- item validation
def item_ids(z, ns):
    # Require an item model: lang keys exist for things that aren't plain items (create:small_bogey,
    # and create:package, which only has per-style models and shows as "?" in FTB Quests).
    s = set()
    for n in z.namelist():
        m = re.match(r"assets/" + ns + r"/models/item/([a-z0-9_/]+)\.json$", n)
        if m:
            s.add(f"{ns}:{m.group(1)}")
    return s


def scan(z):
    s = set()
    for n in z.namelist():
        m = re.match(r"assets/([^/]+)/lang/en_us\.json$", n)
        if m:
            s |= item_ids(z, m.group(1))
        if n.startswith("META-INF/jarjar/") and n.endswith(".jar"):
            s |= scan(zipfile.ZipFile(io.BytesIO(z.read(n))))
    return s


valid = set()
for jar in sorted(os.listdir(MODS)):
    if jar.endswith(".jar"):
        valid |= scan(zipfile.ZipFile(os.path.join(MODS, jar)))
check_vanilla = os.path.exists(args.minecraft_jar)
if check_vanilla:
    valid |= item_ids(zipfile.ZipFile(args.minecraft_jar), "minecraft")
else:
    print(f"no vanilla jar at {args.minecraft_jar}; minecraft: items are not checked")
present = {i.split(":")[0] for i in valid}


# ---------------------------------------------------------------- content
# Mod keys and quest ids feed the FTB ids, so never rename them. Titles, and which chapter a quest
# sits in (SUBCHAPTERS, below the content), can change freely without resetting progress.
CREATE, AERO, RAILS, FOUNDRY = "create", "aeronautics", "railways", "modern_foundry"
MODULES = {
    CREATE: dict(title="Create", requires={"create"}),
    AERO: dict(title="Aeronautics", requires={"create", "aeronautics", "simulated", "offroad"}),
    RAILS: dict(title="Steam 'n' Rails", requires={"create", "railways"}, group=CREATE),
    FOUNDRY: dict(title="Modern Foundry", requires={"modernfoundry"}),
}

Q = []


def q(group, qid, title, icon, deps, desc, tasks, check=False, needs=()):
    """group is the mod key; deps are quest ids from the same mod, or "mod::id" for another mod.
    needs lists extra mod namespaces this one quest requires; it is left out without them."""
    ns = lambda i: i if ":" in i else "create:" + i
    Q.append(dict(group=group, id=qid, title=title, icon=ns(icon), deps=deps, desc=desc,
                  tasks=[(ns(t), n) for t, n in tasks], check=check, needs=set(needs)))


# ---- Create --------------------------------------------------------------
q(CREATE, "welcome", "Welcome to Create", "wrench", [],
  ["Create is a mod about building machines out of spinning shafts, belts and pipes.",
   "Three habits will carry you: hold W over any item to open its Ponder (a short animated lesson), press R on an item in EMI to see how it is made, and wear Engineer's Goggles to read what a machine is doing.",
   "Click the checkmark when you are ready to start."],
  [], check=True)
q(CREATE, "andesite_alloy", "Andesite Alloy", "andesite_alloy", ["welcome"],
  ["Almost everything in Create starts here. Combine andesite with an iron nugget (or a zinc nugget) to craft Andesite Alloy.",
   "Craft a stack of it now; you will use it constantly."],
  [("andesite_alloy", 16)])
q(CREATE, "shaft", "Shafts", "shaft", ["andesite_alloy"],
  ["A Shaft carries rotation in a straight line. Place a Shaft next to a rotating block and it will spin too.",
   "Rotation has two numbers: speed (RPM) and stress. Keep both in mind."],
  [("shaft", 8)])
q(CREATE, "cogwheel", "Cogwheels", "cogwheel", ["shaft"],
  ["Cogwheels turn rotation around corners and change direction. A large cogwheel meshed with a small one doubles the speed and halves the strength, or the other way round.",
   "Try meshing two cogwheels on adjacent shafts and watch them reverse."],
  [("cogwheel", 4), ("large_cogwheel", 2)])
q(CREATE, "hand_crank", "Hand Crank", "hand_crank", ["cogwheel"],
  ["You need a power source. The Hand Crank is the simplest: hold right click to turn it one way, or sneak and hold right click to turn it the other.",
   "It is not automatic, but it is perfect for testing a build."],
  [("hand_crank", 1)])
q(CREATE, "water_wheel", "Water Wheel", "water_wheel", ["cogwheel"],
  ["Place a Water Wheel against flowing water for free, endless power.",
   "Water wheels spin slowly but provide steady stress. Use a larger cogwheel ratio to speed things up."],
  [("water_wheel", 1)])
q(CREATE, "windmill", "Windmill", "windmill_bearing", ["cogwheel"],
  ["Not near water? A Windmill Bearing turns a structure in front of it into a windmill. It needs at least 8 sail-like blocks; Windmill Sails stick to each other without glue.",
   "Right click the bearing to start it. More sails means more speed."],
  [("windmill_bearing", 1), ("white_sail", 8)])
q(CREATE, "goggles", "Engineer's Goggles", "goggles", ["press"],
  ["Goggles let you see speed and stress on any component you look at, and the Speedometer and Stressometer show them on a dial.",
   "If a machine will not move, the goggles will tell you why: usually overstress."],
  [("goggles", 1), ("speedometer", 1), ("stressometer", 1)])
q(CREATE, "casing", "Andesite Casing", "andesite_casing", ["andesite_alloy"],
  ["Casings are the frame for every machine. Right click a log with Andesite Alloy to make Andesite Casing.",
   "Casing also covers a shaft or cogwheel to make a neat, encased version."],
  [("andesite_casing", 8)])
q(CREATE, "gearbox", "Gearbox, Clutch, Gearshift", "gearbox", ["casing", "cogwheel"],
  ["A Gearbox splits rotation in several directions. A Clutch cuts power when it gets a redstone signal. A Gearshift reverses it.",
   "Together they let a single power source drive many different jobs."],
  [("gearbox", 1), ("clutch", 1), ("gearshift", 1)])
q(CREATE, "millstone", "Millstone", "millstone", ["casing", "cogwheel"],
  ["The Millstone grinds items: wheat into flour, ores into crushed ore, and more. Power it from the side with cogwheels.",
   "Throw items in the top, then right click it to take the result, or pull it out with a hopper or funnel."],
  [("millstone", 1), ("wheat_flour", 4)])
q(CREATE, "crushing_wheel", "Crushing Wheels", "crushing_wheel", ["crafter", "millstone"],
  ["Two Crushing Wheels placed side by side crush ore into more crushed ore than a furnace could ever give you.",
   "Make them spin into each other, then drop items in the top."],
  [("crushing_wheel", 2), ("crushed_raw_iron", 4)])
q(CREATE, "fan", "Encased Fan", "encased_fan", ["gearbox", "press"],
  ["A Fan blowing through a block processes items in its path: through lava it smelts, through fire it smokes food, through water it washes.",
   "Fan speed changes the range, not how fast items are processed. It works on belts and depots too."],
  [("encased_fan", 1), ("propeller", 1)])
q(CREATE, "belt", "Mechanical Belt", "belt_connector", ["gearbox"],
  ["Belts carry items between machines. Right click two shafts in a line with Belt Connectors to link them.",
   "Items on belts can be processed along the way by a Press, a Saw, or a Fan."],
  [("belt_connector", 4), ("depot", 1)])
q(CREATE, "funnels", "Funnels and Chutes", "andesite_funnel", ["press"],
  ["Funnels move items on and off belts and into inventories. Chutes carry them up and down.",
   "A funnel with a filter will only pass the item you set."],
  [("andesite_funnel", 2), ("chute", 2), ("filter", 1)])
q(CREATE, "press", "Mechanical Press", "mechanical_press", ["belt", "casing"],
  ["Place the Press over a belt or depot and feed it ingots to make sheets. Sheets unlock nearly every mid-game recipe.",
   "Powered by rotation from the side."],
  [("mechanical_press", 1), ("iron_sheet", 4), ("copper_sheet", 4)])
q(CREATE, "wrench", "Wrench", "wrench", ["press"],
  ["Now that you can press gold sheets, make a Wrench. It rotates blocks, picks machines back up instantly, and configures many components.",
   "Sneak and right click with it to pick a block up."],
  [("wrench", 1)])
q(CREATE, "basin", "Basin and Mixer", "mechanical_mixer", ["press"],
  ["Put a Basin on the ground and a Mechanical Mixer above it, and it will automate shapeless crafting recipes and a few special ones.",
   "Some recipes only run when the basin is heated from below. That comes later."],
  [("basin", 1), ("mechanical_mixer", 1)])
q(CREATE, "zinc", "Zinc", "zinc_ingot", ["andesite_alloy"],
  ["Zinc is a new ore that spawns underground. Smelt it or wash crushed ore with a Fan to make ingots.",
   "You will need it for brass."],
  [("zinc_ingot", 4)])
q(CREATE, "blaze_burner", "Blaze Burner", "blaze_burner", ["basin"],
  ["A Blaze Burner under a basin supplies the heat many recipes need. Find a Blaze in the Nether and right click it with an empty Blaze Burner to capture it.",
   "Feed it flammable items to keep it hot. A Blaze Cake makes it burn even hotter."],
  [("blaze_burner", 1)])
q(CREATE, "brass", "Brass", "brass_ingot", ["zinc", "blaze_burner"],
  ["Mix copper and zinc ingots in a heated basin to make brass. Press it into sheets.",
   "Brass opens a new tier of machines."],
  [("brass_ingot", 8), ("brass_sheet", 4)])
q(CREATE, "brass_casing", "Brass Casing", "brass_casing", ["brass"],
  ["Craft brass casing the same way as andesite casing: right click a log with a sheet of brass.",
   "Brass casing is the frame for the stronger machines."],
  [("brass_casing", 8)])
q(CREATE, "deployer", "Deployer", "deployer", ["brass_casing"],
  ["A Deployer acts like a player: it places blocks, uses items, activates blocks, harvests and even attacks.",
   "Put one next to a depot and you can combine items automatically."],
  [("deployer", 1)])
q(CREATE, "saw", "Mechanical Saw", "mechanical_saw", ["brass_casing"],
  ["The Saw cuts logs into planks, chops trees down, and stonecuts items for you.",
   "Placed on a belt line it is an automatic carpentry station."],
  [("mechanical_saw", 1)])
q(CREATE, "drill", "Mechanical Drill", "mechanical_drill", ["brass_casing"],
  ["The Drill breaks whatever it faces. Put it on a contraption and you have an automatic miner.",
   "Remember the stress cost: bigger machines need more power."],
  [("mechanical_drill", 1)])
q(CREATE, "harvester", "Harvester and Plough", "mechanical_harvester", ["brass_casing"],
  ["Mounted on a contraption, the Harvester reaps crops and the Plough tills the soil. Perfect for a farm.",
   "Combine them with a Mechanical Bearing for a moving farm."],
  [("mechanical_harvester", 2), ("mechanical_plough", 2)])
q(CREATE, "glue", "Super Glue", "super_glue", ["press"],
  ["Contraptions only move what is connected. Super Glue groups blocks together: click two corners to glue the area between them.",
   "Punch a glued area with the glue in hand to remove it."],
  [("super_glue", 1)])
q(CREATE, "bearing", "Mechanical Bearing", "mechanical_bearing", ["glue", "brass_casing"],
  ["The Bearing spins everything attached to its face as a contraption: windmills, drills, a rotating arm of farm equipment.",
   "Build on its face, glue the structure, and give the bearing rotation to assemble it."],
  [("mechanical_bearing", 1)])
q(CREATE, "piston", "Mechanical Piston", "mechanical_piston", ["glue", "brass_casing"],
  ["A Piston pushes a structure in a line. Add Piston Extension Poles behind it to make the stroke longer.",
   "Use it for doors, elevators and anything that needs to slide."],
  [("mechanical_piston", 1), ("piston_extension_pole", 4)])
q(CREATE, "pulley", "Rope Pulley", "rope_pulley", ["glue", "brass_casing"],
  ["The Rope Pulley raises and lowers a contraption on a rope. It is the basis of elevators and cranes.",
   "A Gantry Carriage lets you do the same sideways."],
  [("rope_pulley", 1), ("gantry_carriage", 1), ("gantry_shaft", 2)])
q(CREATE, "fluids", "Fluid Pipes", "fluid_pipe", ["brass_casing"],
  ["Pipes move liquids. A Mechanical Pump pushes fluid through a pipe in the direction you set.",
   "Fluid Tanks store liquid and can be stacked into bigger ones."],
  [("fluid_pipe", 8), ("mechanical_pump", 1), ("fluid_tank", 1)])
q(CREATE, "spout", "Spout and Item Drain", "spout", ["fluids", "belt"],
  ["A Spout fills items with liquid as they pass beneath it. An Item Drain empties them again.",
   "Use them to make potions, fill buckets, or bottle honey."],
  [("spout", 1), ("item_drain", 1)])
q(CREATE, "steam_engine", "Steam Engine", "steam_engine", ["fluids", "blaze_burner"],
  ["Steam is Create's big power source. Build a boiler from at least 4 Fluid Tanks, fill it with water, heat it from below, and attach Steam Engines to its sides.",
   "Blaze Burners raise the boiler's power level, and each level lets one more engine run at full strength. Bigger levels need more water, size and heat; goggles show the current level."],
  [("steam_engine", 1), ("fluid_tank", 4)])
q(CREATE, "hose", "Hose Pulley", "hose_pulley", ["fluids"],
  ["The Hose Pulley sucks up (or pours out) large bodies of fluid. Lower it into a lava lake and it will drain it.",
   "It is the right way to supply a big lava setup."],
  [("hose_pulley", 1)])
q(CREATE, "precision", "Precision Mechanism", "precision_mechanism", ["deployer", "brass"],
  ["The gate to the advanced machines. It needs a sequenced assembly: a gold sheet on a belt passes under deployers and a press in a set order.",
   "Check the recipe in EMI (R) to see each step."],
  [("precision_mechanism", 2)])
q(CREATE, "arm", "Mechanical Arm", "mechanical_arm", ["precision"],
  ["The Arm picks up items from one place and puts them in another. Select its inputs and outputs before placing it, and it will run your factory.",
   "It is the heart of compact automation."],
  [("mechanical_arm", 1)])
q(CREATE, "crafter", "Mechanical Crafter", "mechanical_crafter", ["precision"],
  ["Arrange Mechanical Crafters in the shape of a crafting grid and they will assemble any recipe you feed them.",
   "Use a Wrench to set the direction items are passed."],
  [("mechanical_crafter", 4)])
q(CREATE, "sequenced", "Sequenced Gearshift", "sequenced_gearshift", ["precision", "gearbox"],
  ["A Sequenced Gearshift runs a rotation program: turn this much, wait, then turn that much.",
   "Great for pistons and doors that need exact timing."],
  [("sequenced_gearshift", 1), ("rotation_speed_controller", 1)])
q(CREATE, "redstone", "Redstone Link", "redstone_link", ["precision"],
  ["Redstone Links send signals wirelessly. Set a frequency with two items, and every link with the same items shares the signal.",
   "Pulse Repeaters and Timers help you shape the signal."],
  [("redstone_link", 2), ("pulse_repeater", 1), ("pulse_timer", 1)])
q(CREATE, "display", "Display Boards", "display_board", ["redstone"],
  ["Display Links turn any value into text: a train schedule, a fluid level, an item count.",
   "Show it on Display Boards or Nixie Tubes."],
  [("display_link", 1), ("display_board", 1), ("nixie_tube", 2)])
q(CREATE, "schematic", "Schematics", "schematic_table", ["precision"],
  ["Save a build as a schematic, then print it elsewhere. The Schematicannon builds it for you from your inventory and gunpowder.",
   "Use the Schematic and Quill to select an area."],
  [("schematic_and_quill", 1), ("schematic_table", 1), ("schematicannon", 1)])
q(CREATE, "vault", "Item Vaults", "item_vault", ["precision"],
  ["Vaults are huge storage blocks and they connect, unlike chests. Use one as the heart of a base.",
   "Pair them with funnels and arms for automatic sorting."],
  [("item_vault", 4)])
q(CREATE, "packages", "Packages and Logistics", "packager", ["vault", "redstone"],
  ["Create 6 adds a logistics network. A Stock Link on a vault joins it, a Stock Ticker orders from it, and Packagers wrap items into Packages for delivery.",
   "Factory Gauges let machines request their own supplies."],
  [("stock_link", 1), ("stock_ticker", 1), ("packager", 1), ("factory_gauge", 1)])
q(CREATE, "train_track", "Train Tracks", "track", ["precision"],
  ["Create has a full railway system. To lay track in bulk, click an existing track, then a second spot: Create fills in the run, including turns and slopes.",
   "Hold sprint while connecting for the longest possible bend, and keep blocks in your off-hand to pave under the track automatically."],
  [("track", 16)])
q(CREATE, "train_station", "Train Station", "track_station", ["train_track"],
  ["Stations are the stops on your network. Select a track, then place the Station beside it.",
   "Open its menu and switch to Assembly Mode to build a train there. Trains can only be taken apart again at a station.",
   "Stations are crafted from Train Casing; make a couple of extra casings for your bogeys."],
  [("track_station", 1), ("railway_casing", 2)])
q(CREATE, "first_train", "Your First Train", "controls", ["train_station", "glue"],
  ["With the station in Assembly Mode, use Train Casing on the track to place bogeys (click again to change their design). Build your train on top and Super Glue it together.",
   "Every train needs Train Controls on board; a second set lets it leave stations in both directions. Confirm assembly in the station menu, then take it for a ride and tick the box.",
   "Trains run faster if they find fuel in a chest or barrel on board."],
  [("controls", 1)], check=True)
q(CREATE, "train_signal", "Signals and Schedules", "track_signal", ["first_train"],
  ["Signals split the track into sections so more than one train can run safely. A Schedule tells a train where to go and when.",
   "Put a station at each stop, then write a schedule that visits them in turn."],
  [("track_signal", 2), ("schedule", 1), ("train_door", 1)])
q(CREATE, "radiance", "Refined Radiance", "chromatic_compound", ["precision", "blaze_burner"],
  ["The end of the tree. Chromatic Compound is made in a heated basin and, after absorbing enough light, becomes Refined Radiance.",
   "Check EMI for the exact recipe."],
  [("chromatic_compound", 1)])

q(CREATE, "backtank", "Copper Backtank", "copper_backtank", ["hand_crank"],
  ["A Backtank is a wearable tank of pressurised air. Place it and give it rotation to fill it; the faster it spins, the faster it fills.",
   "Wear it on your back and other Create gear draws on it: diving helmets, the Extendo Grip and the Potato Cannon."],
  [("copper_backtank", 1)])
q(CREATE, "diving", "Diving Gear", "copper_diving_helmet", ["backtank"],
  ["With a Backtank, the Diving Helmet lets you breathe underwater, slowly using up the tank's air. Diving Boots let you sink quickly and walk and jump on the sea floor.",
   "The boots also stop Mechanical Belts carrying you along. Handy for underwater builds, harbours and shipwrecks."],
  [("copper_diving_helmet", 1), ("copper_diving_boots", 1)])
q(CREATE, "extendo_grip", "Extendo Grip", "extendo_grip", ["backtank", "crafter"],
  ["Held in your off-hand, the Extendo Grip greatly increases your reach. It is a Mechanical Crafter recipe.",
   "While you wear a Backtank it uses air instead of durability, so it never wears out. Perfect for tall machines."],
  [("extendo_grip", 1)])
q(CREATE, "potato_cannon", "Potato Cannon", "potato_cannon", ["backtank", "crafter", "fluids"],
  ["Launch your home-grown vegetables at enemies. It fires suitable items from your inventory, and different crops hit differently.",
   "With a Backtank on, it runs on air instead of durability."],
  [("potato_cannon", 1)])
q(CREATE, "netherite_diving", "Netherite Diving Gear", "netherite_diving_helmet", ["diving"],
  ["Upgrade your Backtank, Diving Helmet and Diving Boots with netherite at a smithing table. With netherite leggings too, the full set makes you immune to fire and lava and lets you see in it.",
   "Walk the floor of the Nether's lava seas."],
  [("netherite_backtank", 1), ("netherite_diving_helmet", 1), ("netherite_diving_boots", 1)])

# Projects: a checkbox for "I built it" plus a stack of its output as proof.
q(CREATE, "cobble_gen", "Project: Cobblestone Generator", "minecraft:cobblestone", ["drill"],
  ["Put machines together for the first time. Build a lava and water cobblestone generator and point a Mechanical Drill at it, feeding the drops into a chest.",
   "Endless stone is the raw material for the next few projects. Tick the box and hand in a few stacks."],
  [("minecraft:cobblestone", 256)], check=True)
q(CREATE, "iron_farm", "Project: Iron Farm", "minecraft:iron_nugget", ["cobble_gen", "millstone", "fan"],
  ["Mill your cobblestone into gravel, then wash the gravel with an Encased Fan blowing through water.",
   "Each gravel gives a 12.5% chance of an iron nugget and a 25% chance of flint. Keep the flint: the Andesite Factory needs it.",
   "The same washing trick works on other blocks: red sand (mill it from granite) gives gold nuggets, and soul sand gives quartz."],
  [("minecraft:iron_nugget", 64)], check=True)
q(CREATE, "andesite_factory", "Project: Andesite Factory", "andesite_alloy", ["iron_farm", "basin"],
  ["Andesite is renewable in Create: a Mechanical Press over a Basin compacts 2 flint, 1 gravel and some lava into andesite. Your iron farm already makes the flint and gravel.",
   "Then mix that andesite with iron nuggets from the same farm to make Andesite Alloy, automatically."],
  [("andesite_alloy", 64)], check=True)
q(CREATE, "kelp_farm", "Project: Kelp Farm", "minecraft:dried_kelp", ["saw", "fan"],
  ["Belts are made from dried kelp, and big factories need a lot of belts. Grow kelp underwater, cut it with Mechanical Saws, and blow it through fire with an Encased Fan to dry it.",
   "Dried kelp blocks also make good furnace fuel."],
  [("minecraft:dried_kelp", 64)], check=True)
q(CREATE, "crop_farm", "Project: Crop Farm", "minecraft:wheat", ["harvester", "bearing"],
  ["Mount Harvesters and Ploughs on a moving contraption, a bearing arm or a piston sweep, and let it reap and till your fields.",
   "Harvesters replant as they go. Collect the drops with funnels or a chest on the contraption."],
  [("minecraft:wheat", 256)], check=True)
q(CREATE, "tree_farm", "Project: Tree Farm", "minecraft:oak_log", ["saw", "deployer"],
  ["A Mechanical Saw fells a whole tree at once. Add a Deployer holding saplings to replant, and bone meal to speed it up.",
   "Wood for every casing you will ever need."],
  [("minecraft:oak_log", 128)], check=True)
q(CREATE, "ore_processing", "Project: Ore Processing", "crushed_raw_iron", ["crushing_wheel", "fan"],
  ["Unlike your iron farm, this handles the ore you mine, and gets extra out of every trip. Run your raw ore through Crushing Wheels, then wash it with a fan. Raw iron crushes into crushed iron with a chance of experience, and washing it gives 9 nuggets with a chance of redstone.",
   "Gold gives quartz the same way. Belt it all together so your mining trips process themselves."],
  [("crushed_raw_iron", 64)], check=True)
q(CREATE, "brass_factory", "Project: Brass Factory", "brass_ingot", ["brass"],
  ["Feed copper and zinc into a heated mixer automatically and belt the brass away. Keep the Blaze Burner fed.",
   "Brass goes into almost every advanced machine, so it pays to have plenty."],
  [("brass_ingot", 128)], check=True)
q(CREATE, "kitchen", "Project: Automated Kitchen", "sliceanddice:slicer", ["deployer"],
  ["Slice & Dice automates Farmer's Delight. A Slicer holding a knife does the cutting board's work, and it can work over a Basin too. Sprinklers water your crops.",
   "Grow cabbages and turn them into leaves without lifting a knife."],
  [("sliceanddice:slicer", 1), ("farmersdelight:cabbage_leaf", 64)], check=True, needs=("sliceanddice", "farmersdelight"))
q(CREATE, "cargo_train", "Project: Cargo Train", "track_station", ["train_signal"],
  ["Connect two bases with track and run a scheduled train between them, loading and unloading cargo at each station.",
   "Send your farm output home without lifting a finger, then tick the box."],
  [], check=True)

# ---- Aeronautics ---------------------------------------------------------
q(AERO, "physics", "Physics Assembler", "simulated:physics_assembler", [f"{CREATE}::casing"],
  ["Sable gives contraptions real physics: weight, lift, thrust and drag. The Physics Assembler turns a glued build into a Simulated Contraption.",
   "Glue the build with Super Glue or Honey Glue, then hold right click and pull the lever.",
   "Here is a pot of Honey Glue to start. It wears out, so make more with a Spout by filling an iron sheet with honey (see the Create chapter)."],
  [("simulated:physics_assembler", 1)])
q(AERO, "honey_glue", "Honey Glue", "simulated:honey_glue", ["physics", f"{CREATE}::spout"],
  ["Honey Glue only sticks to Simulated Contraptions, so it won't catch blocks you didn't mean to. Click two corners, then Ctrl-scroll to resize the area; hold Alt to place a corner in mid-air.",
   "If a contraption splits apart, a Slime Ball merges two contraptions back together."],
  [("simulated:honey_glue", 4), ("minecraft:slime_ball", 1)])
q(AERO, "steering", "Steering Wheel", "simulated:steering_wheel", ["physics", f"{CREATE}::cogwheel"],
  ["Hold right click on a Steering Wheel and move the mouse to turn it; sneak to snap to 45 degrees.",
   "It outputs precise rotation, and you can set its maximum angle on its value panel."],
  [("simulated:steering_wheel", 1)])
q(AERO, "throttle", "Throttle Lever", "simulated:throttle_lever", ["steering", f"{CREATE}::brass_casing"],
  ["A Throttle Lever is a precise redstone dial: right click and drag to set its strength, and use a wrench to invert it.",
   "Use it to control engines, burners and transmissions."],
  [("simulated:throttle_lever", 1)])
q(AERO, "engine", "Portable Engine", "simulated:white_portable_engine", ["physics"],
  ["A Portable Engine burns fuel to make rotation, right on board your vehicle. It can run in either direction and be refuelled automatically.",
   "Feed it a Blaze Cake to superheat it for extra power."],
  [("simulated:white_portable_engine", 1)])
q(AERO, "propeller", "Propellers", "aeronautics:wooden_propeller", ["engine", f"{CREATE}::brass_casing", f"{CREATE}::fan"],
  ["A Propeller Bearing attaches to the block in front of it and spins it as a propeller. Any structure with at least 2 sail-like blocks works, and more sails push harder.",
   "Reverse the rotation, or use a wrench, to reverse the thrust. Goggles show thrust and airflow.",
   "Wooden and Andesite Propellers are the same part in two styles; craft one to swap to the other."],
  [("aeronautics:propeller_bearing", 1), ("aeronautics:wooden_propeller", 2)])

# blimps
q(AERO, "envelope", "Envelope", "aeronautics:white_envelope", ["physics"],
  ["Envelope blocks make a balloon. They enclose a space that lifts when filled with hot air, so the balloon must be airtight.",
   "Blocks inside take up volume. Encase shafts in envelope to run them through the balloon airtight."],
  [("aeronautics:white_envelope", 16)])
q(AERO, "burner", "Hot Air Burner", "aeronautics:adjustable_burner", ["envelope", f"{CREATE}::press"],
  ["Place a Hot Air Burner under the balloon. Powered with redstone, it fills the balloon from the top down.",
   "Its panel sets the maximum output and the redstone strength scales it. Several burners can feed one balloon."],
  [("aeronautics:adjustable_burner", 1)])
q(AERO, "altitude", "Altitude Sensor", "simulated:altitude_sensor", ["burner"],
  ["Lift weakens as you climb. A balloon settles where lift equals weight, so changing the burner output changes your altitude.",
   "An Altitude Sensor turns height into a redstone signal: wire it to the burner for a blimp that holds its height."],
  [("simulated:altitude_sensor", 1)])
q(AERO, "steam_vent", "Steam Vent", "aeronautics:steam_vent", ["burner", f"{CREATE}::steam_engine"],
  ["A Steam Vent lifts a balloon with steam instead of hot air. Like a Steam Engine, it needs heat, water and boiler space.",
   "Bigger airships with several vents need a stronger boiler."],
  [("aeronautics:steam_vent", 1)])
q(AERO, "levitite", "Levitite", "aeronautics:levitite", ["physics"],
  ["Enough Levitite keeps a contraption afloat, but it cannot climb on its own; you still need lift or thrust. It also resists slow movement.",
   "Levitite Blend crystallises into Levitite when heated, and the crystal spreads through the whole pool. Blocks used as a mould may break."],
  [("aeronautics:levitite_blend_bucket", 1), ("aeronautics:levitite", 4)])
q(AERO, "first_blimp", "Build a Blimp", "aeronautics:white_envelope", ["burner", "propeller", "steering"],
  ["Put it together: a sealed balloon with a Hot Air Burner, a Portable Engine driving a Propeller, and a Steering Wheel to turn.",
   "Fly it, land it, and tick the box when you're done."],
  [], check=True)

# planes
q(AERO, "sails", "Wings", "simulated:white_symmetric_sail", ["propeller"],
  ["Regular Sails on a moving contraption make lift, at right angles to their surface; the faster you go, the more lift. Enough lift and you fly.",
   "Symmetric Sails only make drag. Angle them away from your direction of travel to turn or stabilise."],
  [("white_sail", 8), ("simulated:white_symmetric_sail", 4)])
q(AERO, "controls", "Control Surfaces", "simulated:torsion_spring", ["sails", "steering"],
  ["A Swivel Bearing turns a glued part of your craft. A Torsion Spring passes rotation within a set angle and springs back when you let go: ideal for flaps and rudders.",
   "Bearings driven like this have to be told not to disassemble."],
  [("simulated:swivel_bearing", 1), ("simulated:torsion_spring", 2)])
q(AERO, "first_plane", "Build a Plane", "simulated:white_symmetric_sail", ["controls"],
  ["A propeller for thrust, wings for lift, and control surfaces to steer. Take off, fly a loop of your base, and land.",
   "Tick the box when you're done."],
  [], check=True)
q(AERO, "gyro", "Gyroscopic Propeller Bearing", "aeronautics:gyroscopic_propeller_bearing", ["propeller"],
  ["Normal propeller bearings make poor helicopters: the rotor tips with the craft. A Gyroscopic Propeller Bearing tries to keep its propeller upright.",
   "A redstone signal resets its tilt to zero when you don't want it leaning."],
  [("aeronautics:gyroscopic_propeller_bearing", 1)])
q(AERO, "first_heli", "Build a Helicopter", "aeronautics:gyroscopic_propeller_bearing", ["gyro", "throttle"],
  ["Mount a Gyroscopic Propeller Bearing facing up with a rotor on top, power it from a Portable Engine, and use a Throttle Lever to climb and descend.",
   "Lift fades as the air thins, so you'll hover where thrust and weight balance. Take off, hover, land, and tick the box."],
  [], check=True)
q(AERO, "heli_stability", "Steady Flying", "aeronautics:gyroscopic_propeller_bearing", ["first_heli"],
  ["Gyroscopic Propeller Bearings facing downwards can hold a top-heavy craft level.",
   "Add a second rotor or a tail to stop the craft spinning, and tune it until it flies straight. Tick the box when it does."],
  [], check=True)
q(AERO, "flight_sensors", "Flight Sensors", "simulated:gimbal_sensor", ["first_plane"],
  ["The Gimbal Sensor outputs redstone based on how the craft is tilted, and the Velocity Sensor based on its speed.",
   "Wire them to your control surfaces and you have an autopilot."],
  [("simulated:gimbal_sensor", 1), ("simulated:velocity_sensor", 1)])

# cars
q(AERO, "wheels", "Wheels and Tires", "offroad:tire", ["physics", f"{CREATE}::press"],
  ["Mount a Tire on a Wheel Mount to give your contraption wheels.",
   "Bigger tires roll over rougher ground."],
  [("offroad:wheel_mount", 2), ("offroad:tire", 2)])
q(AERO, "drivetrain", "Drivetrain", "simulated:directional_gearshift", ["wheels", "engine", f"{CREATE}::brass_casing"],
  ["A Directional Gearshift gives you forward and reverse: power one side to drive, the other to back up, both to stop.",
   "An Analog Transmission slows the wheels with redstone, like a gearbox. A Throttle Lever drives both nicely."],
  [("simulated:directional_gearshift", 1), ("simulated:analog_transmission", 1)])
q(AERO, "first_car", "Build a Car", "offroad:large_tire", ["drivetrain", "steering"],
  ["Four wheels, a Portable Engine, a drivetrain and a Steering Wheel. Drive it out of your base and back.",
   "Tick the box when you're done."],
  [], check=True)
q(AERO, "big_tires", "Bigger Tires", "offroad:monstrous_tire", ["first_car"],
  ["Large and Monstrous Tires climb over almost anything.",
   "Time for a monster truck."],
  [("offroad:large_tire", 2), ("offroad:monstrous_tire", 1)])
q(AERO, "borehead", "Borehead Miner", "offroad:borehead_bearing", ["first_car", f"{CREATE}::crushing_wheel"],
  ["A Borehead Bearing with Rock Cutting Wheels and a storage container is a drill that breaks blocks all around it. The wheels attach without glue.",
   "It spins at a quarter of its input speed and slows down when cutting lots of blocks; use several to keep up."],
  [("offroad:borehead_bearing", 1), ("offroad:rockcutting_wheel", 2)])

# extras
q(AERO, "ropes", "Ropes and Docking", "simulated:rope_winch", ["first_blimp", f"{CREATE}::crafter", f"{CREATE}::funnels"],
  ["Right click a Rope Winch and a Rope Connector with a Rope Coupling to tie them together; the winch reels the rope with rotation. Shears cut it.",
   "Docking Connectors lock two crafts together rigidly and pass items and fluids across."],
  [("simulated:rope_winch", 1), ("simulated:rope_connector", 1), ("simulated:docking_connector", 2)])
q(AERO, "delivery_airship", "Project: Delivery Airship", "simulated:docking_connector", ["ropes"],
  ["Build an airship that docks at two bases and carries cargo between them, passing items across its Docking Connectors.",
   "Tick the box when it has made a delivery."],
  [], check=True)
q(AERO, "navigation", "Navigation Table", "simulated:navigation_table", ["altitude", f"{CREATE}::precision"],
  ["A Navigation Table holds a navigation item and sends a redstone signal towards its destination, weaker when you're facing away.",
   "Steer by it on long flights."],
  [("simulated:navigation_table", 1)])
q(AERO, "goggles", "Aviator's Goggles", "aeronautics:aviators_goggles", ["propeller", f"{CREATE}::goggles"],
  ["Look the part. Aviator's Goggles are goggles for pilots.",
   "They also show what Engineer's Goggles do."],
  [("aeronautics:aviators_goggles", 1)])

# ---- Steam 'n' Rails -----------------------------------------------------
q(RAILS, "welcome", "Steam 'n' Rails", "railways:semaphore", [f"{CREATE}::first_train"],
  ["Steam 'n' Rails adds more to Create trains: new track gauges, switches, couplers, semaphores and a whole set of locomotive building blocks.",
   "You will need a working Create train first. Click the checkmark to start."],
  [], check=True)
q(RAILS, "gauges", "Narrow and Wide Gauge", "railways:track_oak_wide", ["welcome"],
  ["Narrow and wide gauge tracks come in every wood type. Each gauge needs its own bogeys.",
   "Narrow gauge is great for tight mine railways; wide gauge for big mainline trains."],
  [("railways:track_oak_narrow", 16), ("railways:track_oak_wide", 16)])
q(RAILS, "monorail", "Monorail", "railways:track_monorail", ["welcome"],
  ["Monorail track has its own bogeys and hangs a train off a single rail.",
   "Try one for a skyline line between bases."],
  [("railways:track_monorail", 16)])
q(RAILS, "switches", "Track Switches", "railways:track_switch_andesite", ["welcome"],
  ["Select a track, then place a Switch nearby. It sends trains passing its marker left, straight or right.",
   "Use it to cycle right, sneak-use to cycle left, or set it with redstone. Power the bottom to lock it."],
  [("railways:track_switch_andesite", 1), ("railways:track_switch_brass", 1)])
q(RAILS, "coupler", "Train Coupler", "railways:track_coupler", ["switches"],
  ["Select a track, then place a Coupler nearby. It couples and decouples trains without taking them apart.",
   "Scroll with a wrench to set the gap, and click with a wrench to choose couple, decouple or both. Power it to act."],
  [("railways:track_coupler", 1)])
q(RAILS, "semaphore", "Semaphores", "railways:semaphore", ["welcome", f"{CREATE}::train_signal"],
  ["Semaphores go on a pole above a Train Signal and show its state.",
   "On a brass signal with several exits, a second semaphore above the first shows whether any or all paths are blocked."],
  [("railways:semaphore", 2)])
q(RAILS, "conductor", "Conductors", "railways:white_conductor_cap", ["welcome"],
  ["Put a Conductor Cap on Andesite Casing to build a Conductor: a little helper that rides your trains.",
   "Conductors press buttons and flip levers they look at, and can carry a toolbox. Match cap colours to control which conductors respond."],
  [("railways:white_conductor_cap", 1), ("andesite_casing", 1)])
q(RAILS, "handcar", "Handcar", "railways:handcar", ["welcome"],
  ["A small, simple rail cart for getting around before you have a full train.",
   "Pick it up again with a wrench."],
  [("railways:handcar", 1)])
q(RAILS, "locometal", "Locometal", "railways:riveted_locometal", ["welcome"],
  ["Locometal blocks, boilers and smokeboxes make your locomotive look the part. Paint them with a Paint Brush.",
   "Smokestacks puff smoke from the top of your engine."],
  [("railways:riveted_locometal", 16), ("railways:smokestack_coalburner", 1)])
q(RAILS, "buffers", "Buffers and Headstocks", "railways:small_buffer", ["locometal"],
  ["Buffers stop trains at the end of the line. Headstocks and couplers finish off the ends of your carriages.",
   "They are decorative, but no train looks right without them."],
  [("railways:small_buffer", 2), ("railways:copycat_headstock", 2)])

# ---- Modern Foundry ------------------------------------------------------
q(FOUNDRY, "book", "Materials and You", "modernfoundry:materials_and_you", [],
  ["Modern Foundry is a port of Tinkers' Construct: you build tools from parts, and every material changes a tool's stats.",
   "Materials and You is your guide to all of it, and new players usually start with a copy. If you don't have one, craft a Pattern from planks and sticks and combine it with a book.",
   "Give it a read, then click the checkmark when you're ready."],
  [], check=True)
q(FOUNDRY, "pattern", "Part Builder", "modernfoundry:part_builder", ["book"],
  ["A Pattern is the template for a tool part. The Part Builder turns a pattern and a material into that part.",
   "Make a stack of Patterns; each part you build uses one."],
  [("modernfoundry:part_builder", 1)])
q(FOUNDRY, "tinker_station", "Tinker Station", "modernfoundry:tinker_station", ["pattern"],
  ["The Tinker Station assembles finished tools from parts and lets you swap them later.",
   "Combine a head, a handle and a binding."],
  [("modernfoundry:tinker_station", 1)])
q(FOUNDRY, "first_tool", "First Tool", "modernfoundry:pickaxe", ["tinker_station"],
  ["Build a pickaxe: a pick head, a tool handle and a tool binding.",
   "Different materials give different durability, speed and traits."],
  [("modernfoundry:pickaxe", 1)])
q(FOUNDRY, "seared", "Seared Bricks", "modernfoundry:seared_stone", ["tinker_station"],
  ["Seared Stone is the building material for the smeltery. Make it the way the book shows.",
   "You need a lot, so start early."],
  [("modernfoundry:seared_stone", 16)])
q(FOUNDRY, "melter", "Seared Melter", "modernfoundry:seared_melter", ["seared"],
  ["A Melter turns solid items into molten metal. It needs a fuel tank or a heater underneath it.",
   "It is the small version of the smeltery."],
  [("modernfoundry:seared_melter", 1), ("modernfoundry:seared_heater", 1)])
q(FOUNDRY, "casting", "Casting", "modernfoundry:seared_table", ["melter"],
  ["Pour molten metal from a Seared Faucet into a Casting Table or Basin to make parts, ingots and blocks.",
   "Place a cast in the table first, then fill it."],
  [("modernfoundry:seared_table", 1), ("modernfoundry:seared_basin", 1), ("modernfoundry:seared_faucet", 1)])
q(FOUNDRY, "smeltery", "Smeltery", "modernfoundry:smeltery_controller", ["casting"],
  ["Build a hollow box of Seared Stone, place the Controller on one side, and you have a full smeltery.",
   "It melts ores and alloys metals. Add tanks and fuel as you grow."],
  [("modernfoundry:smeltery_controller", 1), ("modernfoundry:seared_fuel_tank", 1)])
q(FOUNDRY, "channels", "Channels and Drains", "modernfoundry:seared_channel", ["smeltery"],
  ["Channels carry molten metal. Drains and Ducts connect the smeltery to the rest of your setup.",
   "Use them to fill many tables at once."],
  [("modernfoundry:seared_channel", 4), ("modernfoundry:seared_drain", 1), ("modernfoundry:seared_duct", 1)])
q(FOUNDRY, "forge", "Tinkers' Anvil", "modernfoundry:tinkers_anvil", ["first_tool", "smeltery"],
  ["The Tinkers' Anvil builds large tools such as hammers and broad axes, and is where you apply modifiers.",
   "It is cast from a block of metal; check the book for which metals work."],
  [("modernfoundry:tinkers_anvil", 1)])
q(FOUNDRY, "anvil", "Modifier Worktable", "modernfoundry:modifier_worktable", ["forge"],
  ["The Modifier Worktable handles the finer modifier work, such as removing or extracting modifiers.",
   "Repair Kits patch tools up wherever you are."],
  [("modernfoundry:modifier_worktable", 1)])
q(FOUNDRY, "slime", "Slime Islands", "modernfoundry:sky_slime_ball", ["smeltery"],
  ["Travel to a slime island to find slime balls and slime trees. They are the base of the slimy materials.",
   "Use them for slime boots and slimy chestplates."],
  [("modernfoundry:sky_slime_ball", 4)])
q(FOUNDRY, "cobalt", "Cobalt", "modernfoundry:raw_cobalt", ["slime", "anvil"],
  ["Cobalt is found in the Nether and is the next big material tier.",
   "Melt it in the smeltery for better tools."],
  [("modernfoundry:raw_cobalt", 4)])
q(FOUNDRY, "scorched", "The Foundry", "modernfoundry:foundry_controller", ["cobalt"],
  ["The Foundry is the late-game cousin of the smeltery, built from Scorched Stone.",
   "Read Fantastic Foundry for the details."],
  [("modernfoundry:foundry_controller", 1), ("modernfoundry:scorched_stone", 16)])


# ---------------------------------------------------------------- rewards
# Rewards stay small so players still have to progress and gather: a level of XP per quest,
# survival basics early on, and a few raw materials at milestones. No machines or tools.
MILESTONES = {
    (CREATE, "andesite_alloy"): [("minecraft:torch", 8)],
    (CREATE, "shaft"): [("minecraft:coal", 4)],
    (CREATE, "cogwheel"): [("minecraft:bread", 3)],
    (CREATE, "hand_crank"): [("minecraft:torch", 8)],
    (CREATE, "casing"): [("minecraft:coal", 4)],
    (CREATE, "water_wheel"): [("create:andesite_alloy", 4), ("minecraft:bread", 3)],
    (CREATE, "millstone"): [("minecraft:torch", 8)],
    (CREATE, "press"): [("create:iron_sheet", 2)],
    (CREATE, "zinc"): [("create:zinc_nugget", 4)],
    (CREATE, "brass"): [("create:brass_nugget", 4)],
    (CREATE, "precision"): [("create:electron_tube", 1)],
    (AERO, "physics"): [("simulated:honey_glue", 1)],
    (FOUNDRY, "pattern"): [("minecraft:torch", 8), ("minecraft:coal", 4)],
    (FOUNDRY, "smeltery"): [("modernfoundry:seared_stone", 4)],
}
# Parts you always need in sets: make N, get N more, so the first build is within reach.
MATCH = {
    (CREATE, "shaft"): ["create:shaft"],
    (CREATE, "cogwheel"): ["create:cogwheel"],
    (CREATE, "windmill"): ["create:white_sail"],
    (CREATE, "belt"): ["create:belt_connector"],
    (CREATE, "piston"): ["create:piston_extension_pole"],
    (CREATE, "fluids"): ["create:fluid_pipe"],
    (CREATE, "train_track"): ["create:track"],
    (AERO, "wheels"): ["offroad:tire", "offroad:wheel_mount"],
    (AERO, "propeller"): ["aeronautics:wooden_propeller"],
    (AERO, "envelope"): ["aeronautics:white_envelope"],
    (AERO, "sails"): ["create:white_sail"],
    (AERO, "ropes"): ["simulated:docking_connector"],
    (RAILS, "gauges"): ["railways:track_oak_narrow", "railways:track_oak_wide"],
    (RAILS, "monorail"): ["railways:track_monorail"],
}
for x in Q:
    key = (x["group"], x["id"])
    x["rewards"] = MILESTONES.get(key, []) + [(i, n) for i, n in x["tasks"] if i in MATCH.get(key, [])] \
        if PROFILE.get("item_rewards", True) else []
    x["xp"] = not x["check"] or x["deps"] != []
# Projects are bigger builds, so they pay a little more XP; still no free machines.
XP_LEVELS = {(CREATE, p): 3 for p in "cobble_gen iron_farm andesite_factory kelp_farm crop_farm tree_farm "
             "ore_processing brass_factory kitchen cargo_train".split()}
XP_LEVELS[(AERO, "delivery_airship")] = 3


# ---------------------------------------------------------------- chapters
# Every chapter sits in a group (named after a mod), in MODULES order: FTB Quests lists ungrouped
# chapters above all groups, and opens the first chapter for new players, so Create has to come first.
SUBCHAPTERS = {
    CREATE: [
        ("getting_started", "Getting Started", "welcome andesite_alloy shaft cogwheel hand_crank water_wheel windmill casing gearbox"),
        ("processing", "Processing", "millstone belt funnels press wrench goggles fan basin"),
        ("brass", "Brass", "zinc blaze_burner brass brass_casing deployer saw drill harvester"),
        ("projects", "Projects", "cobble_gen iron_farm andesite_factory kelp_farm crop_farm tree_farm ore_processing brass_factory kitchen"),
        ("contraptions", "Contraptions", "glue bearing piston pulley"),
        ("fluids", "Fluids and Steam", "fluids spout hose steam_engine"),
        ("equipment", "Equipment", "backtank diving extendo_grip potato_cannon netherite_diving"),
        ("precision", "Precision and Automation", "precision arm crafter crushing_wheel sequenced radiance"),
        ("logistics", "Logistics", "redstone display schematic vault packages"),
        ("trains", "Trains", "train_track train_station first_train train_signal cargo_train"),
    ],
    AERO: [
        ("basics", "Basics", "physics honey_glue steering throttle engine propeller goggles"),
        ("blimps", "Blimps", "envelope burner altitude steam_vent levitite first_blimp ropes delivery_airship navigation"),
        ("planes", "Planes", "sails controls first_plane flight_sensors"),
        ("helicopters", "Helicopters", "gyro first_heli heli_stability"),
        ("cars", "Cars", "wheels drivetrain first_car big_tires borehead"),
    ],
}
# A chapter shows its first quest's icon unless set here (keyed by chapter file name).
# The backtank draws an empty air gauge under its icon, so Equipment uses the diving helmet.
CHAPTER_ICONS = {"create_equipment": "create:copper_diving_helmet"}

for mod in MODULES:
    ids = [x["id"] for x in Q if x["group"] == mod]
    placed = [i for _, _, s in SUBCHAPTERS.get(mod, []) for i in s.split()]
    if mod in SUBCHAPTERS and sorted(placed) != sorted(ids):
        sys.exit(f"{mod}: quests not placed in exactly one chapter: {sorted(set(ids) ^ set(placed))}")

wanted = PROFILE.get("mods") or list(MODULES)
included = [c for c in wanted if MODULES[c]["requires"] <= present]
for c in wanted:
    if c not in included:
        print(f"skipping {c}: missing mods {sorted(MODULES[c]['requires'] - present)}")
all_keys = {(x["group"], x["id"]) for x in Q}
Q = [x for x in Q if x["group"] in included and x["needs"] <= present]


# ---------------------------------------------------------------- validation
def dep_key(x, d):
    return tuple(d.split("::")) if "::" in d else (x["group"], d)


for x in Q:
    # A prerequisite that was left out (its mod isn't installed) just doesn't apply.
    kept = {(y["group"], y["id"]) for y in Q}
    x["deps"] = [d for d in x["deps"] if dep_key(x, d) in kept or dep_key(x, d) not in all_keys]
keys = {(x["group"], x["id"]) for x in Q}
bad = []
for x in Q:
    for i in [x["icon"]] + [t for t, _ in x["tasks"]] + [r for r, _ in x["rewards"]]:
        if i not in valid and (check_vanilla or not i.startswith("minecraft:")):
            bad.append((x["group"], x["id"], i))
    for d in x["deps"]:
        if dep_key(x, d) not in keys:
            bad.append((x["group"], x["id"], "dep:" + d))
if bad:
    sys.exit(f"unknown items / deps: {bad}")


# ---------------------------------------------------------------- FTB Quests output
def fid(*parts):
    # Stable ids keep player progress intact when the files are regenerated.
    # FTB Quests ids are signed longs; it silently reassigns any id with the top bit set.
    h = int(hashlib.sha1("/".join(parts).encode()).hexdigest()[:16], 16) & 0x7FFFFFFFFFFFFFFF
    return f"{h:016X}"


class Long(int):
    pass


def snbt(v, ind=0):
    pad, inner = "\t" * ind, "\t" * (ind + 1)
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, Long):
        return f"{int(v)}L"
    if isinstance(v, float):
        return f"{v}d"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        return json.dumps(v)
    if isinstance(v, list):
        if not v:
            return "[ ]"
        if all(isinstance(x, str) for x in v):
            return "[" + ", ".join(json.dumps(x) for x in v) + "]"
        return "[\n" + "\n".join(inner + snbt(x, ind + 1) for x in v) + "\n" + pad + "]"
    return "{\n" + "\n".join(f"{inner}{k}: {snbt(x, ind + 1)}" for k, x in sorted(v.items())) + "\n" + pad + "}"


def local_deps(x, ids):
    return [p for p in x["deps"] if "::" not in p and p in ids]


def layout(items):
    """Column = dependency depth within the chapter; rows spread around 0."""
    byid = {x["id"]: x for x in items}
    depth = {}

    def d(i):
        if i not in depth:
            local = local_deps(byid[i], byid)
            depth[i] = 0 if not local else 1 + max(d(p) for p in local)
        return depth[i]
    cols = collections.defaultdict(list)
    for x in items:
        cols[d(x["id"])].append(x)
    return {x["id"]: (col, n - (len(xs) - 1) / 2) for col, xs in cols.items() for n, x in enumerate(xs)}


FTB = f"{OUT}/config/ftbquests/quests"
if os.path.exists(FTB):
    shutil.rmtree(FTB)
os.makedirs(f"{FTB}/chapters")
os.makedirs(f"{FTB}/lang")
lang = {}
group_ids = {}
chapters = []   # (mod, chapter id, file name, title, group id, quests)
for g in included:
    home = MODULES[g].get("group", g)
    if home not in group_ids:
        group_ids[home] = fid("group", home)
        lang[f"chapter_group.{group_ids[home]}.title"] = MODULES[home]["title"]
    mine = {x["id"]: x for x in Q if x["group"] == g}
    if g in SUBCHAPTERS:
        for key, title, ids in SUBCHAPTERS[g]:
            chapters.append((g, fid("chapter", g, key), f"{g}_{key}", title, group_ids[home], [mine[i] for i in ids.split() if i in mine]))
    else:
        chapters.append((g, fid("chapter", g), g, MODULES[g]["title"], group_ids[home], list(mine.values())))
# FTB Quests numbers chapters within each group, and rewrites the files that way on load.
order_in_group = collections.Counter()
for g, cid, fname, title, gid, items in chapters:
    order = order_in_group[gid]
    order_in_group[gid] += 1
    lang[f"chapter.{cid}.title"] = title
    ids = {x["id"] for x in items}
    pos = layout(items)
    quests = []
    for x in items:
        qid = fid("quest", g, x["id"])
        lang[f"quest.{qid}.title"] = x["title"]
        lang[f"quest.{qid}.quest_desc"] = [p for d in x["desc"] for p in (d, "")][:-1]
        tasks = [{"id": fid("task", g, x["id"], "check"), "type": "checkmark"}] if x["check"] else []
        for i, (item, cnt) in enumerate(x["tasks"]):
            t = {"id": fid("task", g, x["id"], str(i)), "type": "item", "item": {"count": 1, "id": item}}
            if cnt > 1:
                t["count"] = Long(cnt)
            tasks.append(t)
        rewards = [{"id": fid("reward", g, x["id"], str(i)), "type": "item", "count": cnt,
                    "item": {"count": 1, "id": item}} for i, (item, cnt) in enumerate(x["rewards"])]
        if x["xp"]:
            levels = XP_LEVELS.get((g, x["id"]), 1)
            rewards.append({"id": fid("reward", g, x["id"], "xp"), "type": "xp_levels", "xp_levels": levels})
        col, row = pos[x["id"]]
        qd = {"id": qid, "x": float(col * 2), "y": float(row * 1.5),
              "tasks": tasks, "rewards": rewards, "icon": {"id": x["icon"]}}
        if x["deps"]:
            qd["dependencies"] = [fid("quest", *dep_key(x, d)) for d in x["deps"]]
        if not local_deps(x, ids):
            qd["shape"] = "gear"
            qd["size"] = 1.5
        elif x["check"]:
            qd["shape"] = "hexagon"
            qd["size"] = 1.25
        quests.append(qd)
    chapter = {"default_hide_dependency_lines": False, "default_quest_shape": "", "filename": fname,
               "group": gid, "icon": {"id": CHAPTER_ICONS.get(fname, items[0]["icon"])}, "id": cid,
               "order_index": order, "quest_links": [], "quests": quests}
    open(f"{FTB}/chapters/{fname}.snbt", "w").write(snbt(chapter) + "\n")
open(f"{FTB}/chapter_groups.snbt", "w").write(snbt({"chapter_groups": [{"id": i} for i in group_ids.values()]}) + "\n")
open(f"{FTB}/data.snbt", "w").write(snbt({"version": 13, "default_consume_items": False,
                                          "default_autoclaim_rewards": "disabled", "fallback_locale": "en_us"}) + "\n")
open(f"{FTB}/lang/en_us.snbt", "w").write(snbt(lang) + "\n")
print({g: len([x for x in Q if x["group"] == g]) for g in included}, "|", len(chapters), "chapters,", len(Q), "quests")
