from vortex_port import *
p = dict(rot=30, intake=55, turb=100, t1=90, t2=115)
print('settings', p)
for noise in ('linear', 'sqrt'):
    for dt in (1/120, 1/60, 1/30, 0.05):
        tab = outcome_table(dt, noise, 3000, 11, **p)
        print(noise, round(dt, 4), {k: (round(v[0], 3), round(v[1], 2)) for k, v in tab.items()}, flush=True)
