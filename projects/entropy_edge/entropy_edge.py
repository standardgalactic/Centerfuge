import json, random, sys
state = {
    "turn": 0, "energy": 10, "entropy": 0.0, "tiles": {"(0,0)": {"scan":"home"}},
    "buildings": []
}
def end_turn():
    state["turn"] += 1
    prod = sum(2 if b=="factory" else 0 for b in state["buildings"])
    science = sum(1 if b=="lab" else 0 for b in state["buildings"])
    state["energy"] += 1 + prod
    state["entropy"] += 0.1*prod + 0.05*science
    print(f"End turn {state['turn']}  +energy={1+prod}  ΔS={0.1*prod+0.05*science:.2f}")
def build(kind):
    cost = 5 if kind=="factory" else 4 if kind=="lab" else 999
    if state["energy"]<cost: print("Not enough energy."); return
    state["energy"]-=cost; state["buildings"].append(kind); print(f"Built {kind}.")
def scan():
    x = random.randint(-2,2); y = random.randint(-2,2)
    key = f"({x},{y})"
    state["tiles"][key] = {"scan": random.choice(["mineral","oasis","void"])}
    print(f"Scanned tile {key}: {state['tiles'][key]['scan']}")
def status():
    print(json.dumps(state, indent=2))
def main():
    print("Entropy's Edge :: type 'help'")
    while True:
        try:
            cmd = input("> ").strip().split()
        except (EOFError, KeyboardInterrupt):
            print(); break
        if not cmd: continue
        op = cmd[0]
        if op=="help": print("end | build <factory|lab> | scan | status | quit")
        elif op=="end": end_turn()
        elif op=="build" and len(cmd)>1: build(cmd[1])
        elif op=="scan": scan()
        elif op in ("status","s"): status()
        elif op in ("quit","q","exit"): break
        else: print("Unknown command.")
if __name__=="__main__": main()
