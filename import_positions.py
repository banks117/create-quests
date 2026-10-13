"""Copy quest positions you moved in FTB Quests' editor back into generate.py's POSITIONS.

Usage: python3 -I import_positions.py --mods MODS_DIR --quests INSTANCE/config/ftbquests/quests [CHAPTER ...]
With no chapters named, every chapter already in POSITIONS is updated; name a chapter (its file name,
e.g. railways) to start hand-placing it too. Quit the world first: FTB writes its edits on save.
"""
import argparse, contextlib, io, os, re, runpy, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--mods", required=True)
ap.add_argument("--quests", required=True, help="the instance's config/ftbquests/quests folder")
ap.add_argument("--profile", default=os.path.join(HERE, "profiles", "gears-and-gardens.json"))
ap.add_argument("chapters", nargs="*")
args = ap.parse_args()

GEN = os.path.join(HERE, "generate.py")
with tempfile.TemporaryDirectory() as out, contextlib.redirect_stdout(io.StringIO()):
    sys.argv = [GEN, "--mods", args.mods, "--profile", args.profile, out]
    g = runpy.run_path(GEN)
wanted = args.chapters or list(g["POSITIONS"])
src = open(GEN).read()
for mod, cid, fname, title, gid, items in g["chapters"]:
    if fname not in wanted:
        continue
    snbt = open(os.path.join(args.quests, "chapters", f"{fname}.snbt")).read()
    # FTB writes each quest as a tab-indented block; pull id, x and y out of each one.
    found = {}
    for blk in re.split(r"\n\t\t\}", snbt[snbt.index("quests: ["):]):
        qid = re.search(r'\n\t\t\tid: "([0-9A-F]+)"', blk)
        x = re.search(r"\n\t\t\tx: (-?[0-9.]+)d", blk)
        y = re.search(r"\n\t\t\ty: (-?[0-9.]+)d", blk)
        if qid and x and y:
            found[qid.group(1)] = (float(x.group(1)), float(y.group(1)))
    lines = []
    for x in items:
        p = found.get(g["fid"]("quest", mod, x["id"]))
        if p is None:
            print(f"{fname}: {x['id']} isn't in the instance's chapter, skipping it")
            continue
        lines.append(f"        {x['id']} {round(p[0], 2):g} {round(p[1], 2):g}")
    block = "\n".join(lines) + "\n    "
    pat = re.compile(rf'(    "{fname}": """\n)(.*?)(""",\n)', re.S)
    if pat.search(src):
        src = pat.sub(lambda m: m.group(1) + block + m.group(3), src, count=1)
    else:
        src = src.replace("POSITIONS = {\n", f'POSITIONS = {{\n    "{fname}": """\n{block}""",\n', 1)
    print(f"{fname}: {len(lines)} positions")
open(GEN, "w").write(src)
