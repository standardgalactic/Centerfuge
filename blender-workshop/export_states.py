import json
import numpy as np
from netsim import arrangement_graph, incidence, run

pos, edges = arrangement_graph()
n = len(pos)
B = incidence(n, edges)
north, south = int(np.argmax(pos[:, 2])), int(np.argmin(pos[:, 2]))
kappa, lam, sigma, dt, steps, every = 1.0, 0.5, 1.0, 0.1, 1200, 10

_, _, traj = run(np.zeros(n), [sigma] * steps, dt, B, kappa, lam, north, south, record=True)
saved = traj[::every]

with open('network_states.json', 'w') as f:
    json.dump({'radius': 10.0, 'dt': dt, 'every': every,
               'params': {'kappa': kappa, 'lam': lam, 'sigma': sigma},
               'north': north, 'south': south,
               'pos': pos.round(9).tolist(), 'edges': [list(e) for e in edges],
               'states': saved.round(9).tolist()}, f)
print(len(saved), 'saved states of', n, 'nodes; max stock', round(float(saved.max()), 4))
