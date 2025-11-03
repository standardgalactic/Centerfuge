import pygame as pg, math, random, sys
W,H = 900, 650
pg.init(); screen = pg.display.set_mode((W,H)); clock = pg.time.Clock()
font = pg.font.SysFont("Courier", 18)
reticle_a = 0.0
asteroids = []
shots = []
def spawn():
    r = random.uniform(260, 320)
    ang = random.uniform(0, 2*math.pi)
    x, y = W/2 + r*math.cos(ang), H/2 + r*math.sin(ang)
    vx, vy = -0.7*math.cos(ang), -0.7*math.sin(ang)
    size = random.randint(10, 30)
    asteroids.append([x,y,vx,vy,size])
for _ in range(18): spawn()
score = 0
while True:
    for e in pg.event.get():
        if e.type == pg.QUIT: sys.exit(0)
        if e.type == pg.KEYDOWN and e.key == pg.K_q: sys.exit(0)
        if e.type == pg.KEYDOWN and e.key == pg.K_SPACE:
            shots.append([W/2, H/2, math.cos(reticle_a)*8, math.sin(reticle_a)*8])
    keys = pg.key.get_pressed()
    if keys[pg.K_LEFT]:  reticle_a -= 0.06
    if keys[pg.K_RIGHT]: reticle_a += 0.06
    # update
    for a in asteroids:
        a[0]+=a[2]; a[1]+=a[3]
    for s in shots:
        s[0]+=s[2]; s[1]+=s[3]
    shots[:] = [s for s in shots if 0<=s[0]<=W and 0<=s[1]<=H]
    # collisions
    rem=[]
    for i,a in enumerate(asteroids):
        ax,ay,_,_,sz=a
        for s in shots:
            if (ax-s[0])**2 + (ay-s[1])**2 <= (sz+2)**2:
                score+=1; rem.append(i); break
    for i in sorted(set(rem), reverse=True): asteroids.pop(i); spawn()
    # draw
    screen.fill((5,10,10))
    # cockpit rings
    for r in (120,180,240):
        pg.draw.circle(screen,(10,180,150),(W//2,H//2),r,1)
    # asteroids
    for x,y,_,_,sz in asteroids:
        pg.draw.circle(screen,(0,255,140),(int(x),int(y)),sz,1)
    # reticle
    cx,cy=W//2,H//2
    rx,ry = cx+int(140*math.cos(reticle_a)), cy+int(140*math.sin(reticle_a))
    pg.draw.circle(screen,(140,255,200),(rx,ry),8,1)
    pg.draw.line(screen,(140,255,200),(rx-12,ry),(rx+12,ry),1)
    pg.draw.line(screen,(140,255,200),(rx,ry-12),(rx,ry+12),1)
    # HUD
    txt = font.render(f"BLASTOIDS  score={score}  SPACE=fire  Q=quit", True,(140,255,200))
    screen.blit(txt,(20,20))
    pg.display.flip(); clock.tick(60)
