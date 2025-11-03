import sys, json
stack = []
def push(name, val): stack.append({"name":name,"value":float(val)})
def merge():
    b=stack.pop(); a=stack.pop()
    stack.append({"name":a["name"]+"+"+b["name"], "value":a["value"]+b["value"]})
def split(r):
    b = stack.pop()
    a = {"name": b["name"]+"A", "value": b["value"]*r}
    c = {"name": b["name"]+"B", "value": b["value"]*(1-r)}
    stack.extend([a,c])
def run(lines):
    for ln in lines:
        ln=ln.strip()
        if not ln or ln.startswith("#"): continue
        t=ln.split()
        op=t[0].upper()
        if op=="PUSH": push(t[1], t[2])
        elif op=="MERGE": merge()
        elif op=="SPLIT": split(float(t[1]))
        elif op=="PRINT": print(json.dumps(stack, indent=2))
        else: raise SystemExit(f"Unknown op: {op}")
if __name__=="__main__":
    if len(sys.argv)<2:
        print("Usage: python spherepop.py <program.sp>"); sys.exit(1)
    with open(sys.argv[1],"r",encoding="utf-8") as f:
        run(f.readlines())
