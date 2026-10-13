from collections import Counter

def counts(faces):
    """Return (V, E, F) for a mesh given as a list of vertex-index cycles."""
    verts = {v for f in faces for v in f}
    edges = {frozenset((f[i], f[(i + 1) % len(f)]))
             for f in faces for i in range(len(f))}
    return len(verts), len(edges), len(faces)

def euler_characteristic(faces):
    v, e, f = counts(faces)
    return v - e + f

def consistently_oriented(faces):
    """True if every directed edge occurs once and its reverse occurs once."""
    directed = Counter((f[i], f[(i + 1) % len(f)])
                       for f in faces for i in range(len(f)))
    return all(n == 1 and directed.get((b, a), 0) == 1
               for (a, b), n in directed.items())

def signed_volume(points, faces):
    """Signed volume by fan triangulation: (1/6) * sum of det(a, b, c)."""
    total = 0.0
    for f in faces:
        for i in range(1, len(f) - 1):
            a, b, c = points[f[0]], points[f[i]], points[f[i + 1]]
            cross = (b[1] * c[2] - b[2] * c[1],
                     b[2] * c[0] - b[0] * c[2],
                     b[0] * c[1] - b[1] * c[0])
            total += (a[0] * cross[0] + a[1] * cross[1] + a[2] * cross[2]) / 6.0
    return total

if __name__ == '__main__':
    pts = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    i = {p: n for n, p in enumerate(pts)}
    def q(*c): return [i[p] for p in c]
    cube = [q((-1,-1,-1), (-1,1,-1), (1,1,-1), (1,-1,-1)),
            q((-1,-1,1), (1,-1,1), (1,1,1), (-1,1,1)),
            q((-1,-1,-1), (1,-1,-1), (1,-1,1), (-1,-1,1)),
            q((-1,1,-1), (-1,1,1), (1,1,1), (1,1,-1)),
            q((-1,-1,-1), (-1,-1,1), (-1,1,1), (-1,1,-1)),
            q((1,-1,-1), (1,1,-1), (1,1,1), (1,-1,1))]
    print(counts(cube), euler_characteristic(cube))          # (8, 12, 6) 2
    print(consistently_oriented(cube), signed_volume(pts, cube))   # True 8.0
    flipped = [cube[0], cube[1][::-1]] + cube[2:]
    print(consistently_oriented(flipped), signed_volume(pts, flipped))  # False 5.33...
    open_box = cube[:1] + cube[2:]
    print(counts(open_box), euler_characteristic(open_box))  # (8, 12, 5) 1
