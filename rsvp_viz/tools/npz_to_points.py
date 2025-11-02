# tools/npz_to_points.py
# Usage: python npz_to_points.py input_fields.npz out.ply --from phi --th 0.2 --voxel 1.0
import argparse, numpy as np

def write_ply_xyz(path, pts):
    with open(path,"w") as f:
        f.write("ply\nformat ascii 1.0\n")
        f.write(f"element vertex {len(pts)}\nproperty float x\nproperty float y\nproperty float z\nend_header\n")
        for x,y,z in pts: f.write(f"{x} {y} {z}\n")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("npz"); ap.add_argument("out_ply")
    ap.add_argument("--from", dest="src", default="phi")
    ap.add_argument("--th", type=float, default=0.2)
    ap.add_argument("--voxel", type=float, default=1.0)
    ap.add_argument("--transpose", action="store_true")
    args=ap.parse_args()
    data=np.load(args.npz)
    arr=np.asarray(data[args.src], dtype=np.float32)
    if args.transpose: arr=np.transpose(arr,(2,1,0))
    idx=np.argwhere(arr>=args.th)
    pts=idx[:, ::-1].astype(np.float32)*args.voxel
    write_ply_xyz(args.out_ply, pts)
    print(f"Wrote {args.out_ply} with {len(pts)} points")
if __name__=="__main__":
    main()
