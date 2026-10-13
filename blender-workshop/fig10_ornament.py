"""Figure 10.1: a tonal plinth (1.45 x the floor colour) under floor ornament of amplitude 0, 0.2, 0.35, with the nearest-colour reading."""
import os, tempfile
import numpy as np
from PIL import Image
from ornament import *
prgb = PLINTHS['tonal 1.45']
refs = {'plinth': prgb, 'floor': FLOOR, 'wall': WALL, 'background': BACK}
truth = identity_mask(prgb)
top, bot = [], []
for amp in (0.0, 0.2, 0.35):
    sc, objs = setup(lambda: noisy_floor_material(amp), prgb, size=(480, 360))
    img = to_srgb8(render_exr(sc, os.path.join(tempfile.mkdtemp(), 'o')))
    pred = read(img, refs) == 'plinth'
    vis = np.zeros(img.shape, dtype=np.uint8) + 30
    vis[pred & truth] = (255, 255, 255)            # found
    vis[pred & ~truth] = (213, 94, 0)              # false alarm
    vis[~pred & truth] = (0, 114, 178)             # missed
    top.append(img.astype(np.uint8)); bot.append(vis)
rows = [np.concatenate(top, axis=1), np.concatenate(bot, axis=1)]
Image.fromarray(np.concatenate(rows, axis=0)).save('figs/fig10_ornament.png')
