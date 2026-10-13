"""Find quests whose task items need ingredients or machines first unlocked by a quest that isn't a prerequisite.

Usage: python3 -I check_order.py --mods MODS_DIR
"""
import collections, io, json, os, re, runpy, sys, tempfile, zipfile

GEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generate.py")
MODS = sys.argv[sys.argv.index("--mods") + 1]
sys.argv = [GEN, "--mods", MODS, tempfile.mkdtemp()]
g = runpy.run_path(GEN)
Q, CHAPTERS = g["Q"], g["CHAPTERS"]

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
            outs = []
            if "result" in r:
                res = r["result"]
                outs.append(res.get("id") or res.get("item") if isinstance(res, dict) else res)
            for res in r.get("results", []) if isinstance(r.get("results"), list) else []:
                outs.append(res.get("id") or res.get("item") if isinstance(res, dict) else res)
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
}

key = lambda x: (x["group"], x["id"])
byk = {key(x): x for x in Q}


def deps(x):
    return [tuple(d.split("::")) if "::" in d else (x["group"], d) for d in x["deps"]]


anc = {}


def ancestors(k):
    if k not in anc:
        s = set()
        for d in deps(byk[k]):
            if d in byk:
                s |= {d} | ancestors(d)
        anc[k] = s
    return anc[k]


teaches = collections.defaultdict(set)   # item -> quests whose task asks for it
for x in Q:
    for t, _ in x["tasks"]:
        teaches[t].add(key(x))

findings = []
for x in Q:
    k = key(x)
    ok = ancestors(k) | {k}
    for t, _ in x["tasks"]:
        rs = recipes.get(t)
        if not rs:
            continue
        problems_per_recipe = []
        for typ, heat, ings in rs:
            p = []
            m = MACHINE.get(typ)
            if m and m in byk and m not in ok:
                p.append(f"needs {byk[m]['title']} ({typ.split(':')[1]})")
            if heat in ("heated", "superheated") and ("create", "blaze_burner") not in ok:
                p.append(f"needs Blaze Burner ({heat})")
            for ing in ings:
                opts = options(ing)
                gated = [teaches[o] for o in opts if teaches.get(o)]
                # Only a problem if every way to fill this slot is taught by a non-prerequisite quest.
                if opts and len(gated) == len(opts) and all(not (s & ok) for s in gated):
                    later = sorted({byk[q]["title"] for s in gated for q in s})
                    p.append(f"ingredient {'/'.join(sorted(opts))[:60]} from {later}")
            problems_per_recipe.append((typ, p))
        if all(p for _, p in problems_per_recipe):
            best = min(problems_per_recipe, key=lambda r: len(r[1]))
            findings.append((x["group"], x["title"], t, best[1]))

for f in findings:
    print(f"[{f[0]}] {f[1]}: {f[2]} -> {'; '.join(f[3])}")
print(len(findings), "findings;", sum(len(v) for v in recipes.values()), "recipes scanned")
