"""Find quests whose task items need ingredients or machines first unlocked by a quest that isn't a prerequisite.

Usage: python3 -I check_order.py --mods MODS_DIR
"""
import argparse, collections, io, json, os, re, runpy, sys, tempfile, zipfile

ap = argparse.ArgumentParser()
ap.add_argument("--mods", required=True)
MODS = ap.parse_args().mods
GEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generate.py")
with tempfile.TemporaryDirectory() as out:
    sys.argv = [GEN, "--mods", MODS, out]
    g = runpy.run_path(GEN)
Q, dep_key = g["Q"], g["dep_key"]

recipes = collections.defaultdict(list)   # output item -> [(type, heated, [ingredient alternatives])]
tags = collections.defaultdict(set)


def walk(z):
    for n in z.namelist():
        if n.startswith("META-INF/jarjar/") and n.endswith(".jar"):
            walk(zipfile.ZipFile(io.BytesIO(z.read(n))))
            continue
        m = re.match(r"data/([^/]+)/tags/items?/(.+)\.json$", n)
        if m:
            try:
                for v in json.loads(z.read(n)).get("values", []):
                    tags[f"{m.group(1)}:{m.group(2)}"].add(v["id"] if isinstance(v, dict) else v)
            except Exception:
                pass
            continue
        if re.match(r"data/[^/]+/recipes?/.+\.json$", n):
            try:
                r = json.loads(z.read(n))
            except Exception:
                continue
            t = r.get("type", "")
            results = ([r["result"]] if "result" in r else []) + (r["results"] if isinstance(r.get("results"), list) else [])
            outs = [res.get("id") or res.get("item") if isinstance(res, dict) else res for res in results]
            ings = []
            if "key" in r:
                ings = list(r["key"].values())
            ings += r.get("ingredients", [])
            if "ingredient" in r:
                ings.append(r["ingredient"])
            if "base" in r:
                ings.append(r["base"])
            for o in (o for o in outs if isinstance(o, str)):
                recipes[o].append((t, r.get("heat_requirement"), ings))


for j in os.listdir(MODS):
    if j.endswith(".jar"):
        walk(zipfile.ZipFile(os.path.join(MODS, j)))


def expand(tag, seen=None):
    seen = seen or set()
    out = set()
    for v in tags.get(tag, ()):
        if v.startswith("#"):
            if v[1:] not in seen:
                seen.add(v[1:])
                out |= expand(v[1:], seen)
        else:
            out.add(v)
    return out


def options(ing):
    """Items that satisfy one ingredient slot."""
    if isinstance(ing, list):
        return set().union(*(options(i) for i in ing)) if ing else set()
    if isinstance(ing, str):
        return expand(ing[1:]) if ing.startswith("#") else {ing}
    if "tag" in ing:
        return expand(ing["tag"])
    if "item" in ing:
        return {ing["item"]}
    if "id" in ing:
        return {ing["id"]}
    return set()


MACHINE = {  # recipe type -> quest that teaches the machine
    "create:pressing": ("create", "press"), "create:mixing": ("create", "basin"),
    "create:compacting": ("create", "basin"), "create:crushing": ("create", "crushing_wheel"),
    "create:milling": ("create", "millstone"), "create:splashing": ("create", "fan"),
    "create:filling": ("create", "spout"), "create:emptying": ("create", "spout"),
    "create:deploying": ("create", "deployer"), "create:sequenced_assembly": ("create", "precision"),
    "create:mechanical_crafting": ("create", "crafter"), "create:cutting": ("create", "saw"),
    "createaddition:rolling": ("createaddition", "rolling_mill"), "createaddition:charging": ("createaddition", "tesla_coil"),
}

key = lambda x: (x["group"], x["id"])
byk = {key(x): x for x in Q}
anc = {}


def ancestors(k):
    if k not in anc:
        s = set()
        for d in byk[k]["deps"]:
            p = dep_key(byk[k], d)
            if p in byk:
                s |= {p} | ancestors(p)
        anc[k] = s
    return anc[k]


teaches = collections.defaultdict(set)   # item -> quests whose task asks for it
for x in Q:
    for t, _ in x["tasks"]:
        # Vanilla items are always obtainable by hand, whatever quest happens to ask for them.
        if not t.startswith("minecraft:"):
            teaches[t].add(key(x))

# The starting parts count as known once a player has Andesite Alloy:
# each is one craft away from it, so later quests needn't list Shafts or Cogwheels to use them.
BASICS = {"create:shaft", "create:cogwheel", "create:large_cogwheel", "create:andesite_casing"}
ALLOY = ("create", "andesite_alloy")

findings = []
for x in Q:
    k = key(x)
    ok = ancestors(k) | {k}
    basics = ALLOY in ok
    for t, _ in x["tasks"]:
        if t.startswith("minecraft:"):
            continue  # obtainable in vanilla ways the mod recipes don't show (mining, smelting, drops)
        rs = recipes.get(t)
        if not rs:
            continue
        problems = []
        for typ, heat, ings in rs:
            p = []
            m = MACHINE.get(typ)
            if m and m in byk and m not in ok:
                p.append(f"needs {byk[m]['title']} ({typ.split(':')[1]})")
            if heat in ("heated", "superheated") and ("create", "blaze_burner") not in ok:
                p.append(f"needs Blaze Burner ({heat})")
            for ing in ings:
                opts = options(ing)
                if basics and opts & BASICS:
                    continue
                gated = [teaches[o] for o in opts if teaches.get(o)]
                # Only a problem if every way to fill this slot is taught by a non-prerequisite quest.
                if opts and len(gated) == len(opts) and all(not (s & ok) for s in gated):
                    later = sorted({byk[q]["title"] for s in gated for q in s})
                    p.append(f"ingredient {'/'.join(sorted(opts))[:60]} from {later}")
            problems.append(p)
        if all(problems):
            findings.append((x["group"], x["title"], t, min(problems, key=len)))

for f in findings:
    print(f"[{f[0]}] {f[1]}: {f[2]} -> {'; '.join(f[3])}")
print(len(findings), "findings;", sum(len(v) for v in recipes.values()), "recipes scanned")
