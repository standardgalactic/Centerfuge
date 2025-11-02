# tools/npz_to_vdb.py
# Usage: python npz_to_vdb.py input_fields.npz out.vdb --grid density --from phi
import argparse, numpy as np
import pyopenvdb as vdb

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("npz"); ap.add_argument("out_vdb")
    ap.add_argument("--grid", default="density")
    ap.add_argument("--from", dest="src", default="phi")
    ap.add_argument("--voxel_size", type=float, default=1.0)
    ap.add_argument("--transpose", action="store_true", help="Use if NPZ is xyz; converts to zyx")
    args=ap.parse_args()
    data=np.load(args.npz)
    if args.src not in data: raise KeyError(f"{args.src} not in {list(data.keys())}")
    arr=np.asarray(data[args.src], dtype=np.float32)
    if args.transpose:
        arr=np.transpose(arr,(2,1,0))
    grid=vdb.FloatGrid(); grid.name=args.grid
    grid.transform=vdb.createLinearTransform(voxelSize=args.voxel_size)
    vdb.tools.copyFromArray(grid, arr)
    vdb.write(args.out_vdb, grids=[grid])
    print(f"Wrote {args.out_vdb} grid={grid.name} shape={arr.shape}")
if __name__=="__main__":
    main()
