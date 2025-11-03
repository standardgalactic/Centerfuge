import json, argparse, sys
def semantic_merge(a, b):
    out, conflicts = {}, []
    keys = set(a) | set(b)
    for k in sorted(keys):
        if k in a and k in b:
            if a[k]==b[k]: out[k]=a[k]
            else:
                # conflict: keep both with tags
                out[k] = {"left": a[k], "right": b[k]}
                conflicts.append(k)
        elif k in a: out[k]=a[k]
        else: out[k]=b[k]
    return out, conflicts
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("left"); ap.add_argument("right")
    ap.add_argument("-o","--out", default="-")
    args = ap.parse_args()
    with open(args.left,"r",encoding="utf-8") as f: A=json.load(f)
    with open(args.right,"r",encoding="utf-8") as f: B=json.load(f)
    merged, conflicts = semantic_merge(A,B)
    if args.out=="-": print(json.dumps({"merged":merged,"conflicts":conflicts}, indent=2))
    else:
        with open(args.out,"w",encoding="utf-8") as f: json.dump({"merged":merged,"conflicts":conflicts}, f, indent=2)
        print(f"Wrote {args.out}  conflicts={conflicts}")
if __name__=="__main__": main()
