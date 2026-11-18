import sys
from PIL import Image, ImageDraw, ImageFont
S = 2  # supersample
N = 31
X0, CELL, SL = 375, 47.5, 7
ROW0, RSTEP, H = 160, 85, 50
def sig(segs):  # list of (start_cell, value) -> per-cell list
    v = [None]*N
    for i,(s,val) in enumerate(segs):
        e = segs[i+1][0] if i+1 < len(segs) else N
        for k in range(s, e): v[k] = val
    return v
def pulses(cells):
    return [1 if k in cells else 0 for k in range(N)]
rows = [
 ("CLK", "clk", None),
 ("CSN pad", "bit", sig([(0,1),(2,0),(28,1)])),
 ("i_csn_frame", "bit", sig([(0,1),(2,0),(25,1)])),
 ("i_sclk_en", "bit", sig([(0,0),(5,1),(23,0)])),
 ("State", "bus", sig([(0,"IDLE"),(6,"S"),(7,"ACTIVE"),(26,"H"),(27,"IDLE")])),
 ("o_sclk", "bit", sig([(0,0),(9,1),(11,0),(13,1),(15,0),(17,1),(19,0),(21,1),(23,0)])),
 ("o_sample", "bit", pulses(range(8,23,2))),
 ("o_launch", "bit", pulses(range(9,22,2))),
 ("IO out (pad)", "bus", sig([(0,None),(5,"D0"),(10,"D1"),(12,"D2"),(14,"D3"),(16,"D4"),(18,"D5"),(20,"D6"),(22,"D7"),(24,None)])),
 ("o_csn_hold", "bit", sig([(0,0),(6,1),(27,0)])),
 ("o_csn_idle", "bit", [0]*N),
]
W = 1898; Ht = ROW0 + RSTEP*len(rows) - 10
img = Image.new("RGB", (W*S, Ht*S), "white"); d = ImageDraw.Draw(img)
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
ft = ImageFont.truetype(F, 34*S); fl = ImageFont.truetype(F, 34*S); fn = ImageFont.truetype(F, 22*S); fb = ImageFont.truetype(F, 27*S)
BLUE, GR, BLK = (31,64,160), (128,128,128), (17,17,17)
def P(x,y): return (x*S, y*S)
def line(pts, w=2.2): d.line([P(*p) for p in pts], fill=BLK, width=int(w*S), joint="curve")
x = lambda k: X0 + k*CELL
title = "Clock Manager: PRESCALER = 2, DDR, CKMODE = 0, DLY = 0, launch at half-period midpoint"
d.text(P(W/2, 42), title, font=ft, fill=BLK, anchor="mm")
yb = ROW0 + RSTEP*len(rows) - 50
for k in range(N+1):
    for yy in range(125, yb, 10):
        d.line([P(x(k), yy), P(x(k), yy+4)], fill=(200,200,200), width=2*S)
    if k < N: d.text(P(x(k)+CELL/2, 106), str(k), font=fn, fill=GR, anchor="mm")
for r,(name,kind,v) in enumerate(rows):
    top = ROW0 + r*RSTEP; bot = top + H; mid = (top+bot)/2
    d.text(P(345, mid), name, font=fl, fill=BLUE, anchor="rm")
    if kind == "clk":
        pts = [(x(0), bot)]
        for k in range(N):
            pts += [(x(k), top), (x(k)+CELL/2, top), (x(k)+CELL/2, bot), (x(k+1), bot)]
        line(pts)
    elif kind == "bit":
        y = lambda b: top if b else bot
        pts = [(x(0), y(v[0]))]
        for k in range(1, N):
            if v[k] != v[k-1]:
                pts += [(x(k), y(v[k-1])), (x(k)+SL, y(v[k]))]
        pts.append((x(N), y(v[-1])))
        line(pts)
    else:
        k = 0
        while k < N:
            e = k
            while e < N and v[e] == v[k]: e += 1
            xs, xe = x(k), x(e)
            ls = SL if k > 0 else 0; le = SL if e < N else 0
            if v[k] is None:
                poly = [P(xs+ls,top),P(xe-le,top),P(xe,mid),P(xe-le,bot),P(xs+ls,bot),P(xs,mid)]
                d.polygon(poly, fill=(221,221,221))
                for hx in range(int(xs), int(xe), 12):
                    pass
                line([(xs,mid),(xs+ls,top),(xe-le,top),(xe,mid),(xe-le,bot),(xs+ls,bot),(xs,mid)])
            else:
                poly = [P(xs+ls,top),P(xe-le,top),P(xe,mid),P(xe-le,bot),P(xs+ls,bot),P(xs,mid)]
                d.polygon(poly, fill=(244,246,251))
                line([(xs,mid),(xs+ls,top),(xe-le,top),(xe,mid),(xe-le,bot),(xs+ls,bot),(xs,mid)])
                if k == 0: line([(xs,top),(xs,bot)])
                if e == N: line([(xe,top),(xe,bot)])
                d.text(P((xs+xe)/2, mid), v[k], font=fb if len(v[k])>1 else fb, fill=BLK, anchor="mm")
            k = e
img = img.resize((W, Ht), Image.LANCZOS)
img.save(sys.argv[1])
