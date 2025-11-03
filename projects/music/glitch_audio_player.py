import numpy as np, pygame as pg, sys, math
pg.init()
rate=44100; dur=2.0
t = np.linspace(0,dur,int(rate*dur),endpoint=False)
wave = (0.5*np.sin(2*np.pi*220*t) + 0.25*np.sign(np.sin(2*np.pi*110*t))).astype(np.float32)
pg.mixer.init(frequency=rate, size=-16, channels=1)
surf = pg.display.set_mode((800,300)); clock=pg.time.Clock()
sound = pg.sndarray.make_sound((wave*32767).astype(np.int16))
sound.play()
running=True; idx=0; step=max(1,len(wave)//800)
while running:
    for e in pg.event.get():
        if e.type==pg.QUIT: running=False
        if e.type==pg.KEYDOWN and e.key==pg.K_q: running=False
    surf.fill((10,10,15))
    for x in range(800):
        j = min(len(wave)-1, x*step)
        y = int(150 - wave[j]*120)
        pg.draw.line(surf, (120,255,200), (x,150), (x,y), 1)
    pg.display.flip(); clock.tick(60)
pg.quit()
