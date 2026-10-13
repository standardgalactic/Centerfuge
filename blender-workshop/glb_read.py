"""Minimal independent reader for binary glTF (.glb): no Blender needed. Used to check what an exporter wrote."""
import json, struct
import numpy as np

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def read(path):
    data = open(path, 'rb').read()
    magic, version, length = struct.unpack('<4sII', data[:12])
    assert magic == b'glTF' and version == 2 and length == len(data)
    off = 12; js = None; bn = b''
    while off < length:
        clen, ctype = struct.unpack('<II', data[off:off + 8]); chunk = data[off + 8:off + 8 + clen]; off += 8 + clen
        if ctype == 0x4E4F534A:
            js = json.loads(chunk.decode())
        elif ctype == 0x004E4942:
            bn = chunk
    return js, bn


def accessor(js, bn, i):
    a = js['accessors'][i]; bv = js['bufferViews'][a['bufferView']]
    n, k = a['count'], NC[a['type']]; dt = np.dtype(CT[a['componentType']])
    start = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = bv.get('byteStride', k * dt.itemsize)
    if stride == k * dt.itemsize:
        arr = np.frombuffer(bn, dtype=dt, count=n * k, offset=start).reshape(n, k)
    else:
        arr = np.stack([np.frombuffer(bn, dtype=dt, count=k, offset=start + j * stride) for j in range(n)])
    return arr.copy()
