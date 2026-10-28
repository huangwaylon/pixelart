"""mvariants.py (M, round 3): timing / length variants per action -> motion/variants/<name>.json
walk 6/8/10/12 frames, run 6/8/10, idle 8/12/16, each x {snappy holds, even}; jump: anticipation short/long x hang short/long."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mbuild

VARS = []
for n in (6, 8, 10, 12):
    for feel in ("snappy", "even"): VARS.append(("walk", dict(name=f"walk_{n}{feel[0]}", n=n, feel=feel, T=0.84, head_hold=(n >= 10))))
for n in (6, 8, 10):
    for feel in ("snappy", "even"): VARS.append(("run", dict(name=f"run_{n}{feel[0]}", n=n, feel=feel, T=0.56)))
for n in (8, 12, 16):
    for feel in ("holds", "even"): VARS.append(("idle", dict(name=f"idle_{n}{feel[0]}", n=n, feel=feel, T=2.4, head_hold=True)))
for an, a in (("as", 0.5), ("al", 2.5)):
    for hn, h in (("hs", 0.6), ("hl", 1.8)): VARS.append(("jump", dict(name=f"jump_{an}_{hn}", antic=a, hang=h)))

if __name__ == "__main__":
    only = sys.argv[1].split(",") if len(sys.argv) > 1 else None
    for act, v in VARS:
        if only and act not in only and v["name"] not in only: continue
        print(v["name"], mbuild.build(act, var=v))
