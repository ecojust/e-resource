"""Projected stone profiles, scrolls and perforated balcony balustrades."""
from math import cos, pi, sin
from shapely.geometry import LineString, Point

STONE = 'Bund granite'
TRIM = 'dressed pale granite'
DARK = 'recessed stone relief'


def plate(f, x, z, w, h, back, out, mat, label):
    f.box(x, z, w, h, out - back, (back + out) / 2, mat, label)


def ribbon(f, coords, radius, back, out, mat, label):
    cut = LineString(coords).buffer(radius, quad_segs=3, cap_style='round', join_style='round')
    f.prism(cut, back, out, mat, label)


def ellipse(f, x, z, rx, rz, back, out, mat, label, detail):
    pts = [(x + rx * cos(2*pi*j/detail), z + rz*sin(2*pi*j/detail)) for j in range(detail)]
    from shapely.geometry import Polygon
    f.prism(Polygon(pts), back, out, mat, label)


def spiral(f, x, z, r, sign, back, out, label, lod, mat=TRIM):
    steps = 16 if lod else 37
    a = [j/steps for j in range(steps+1)]
    pts = [(x+sign*r*(1-.84*t)*cos(2.8*pi*t), z+r*(1-.84*t)*sin(2.8*pi*t)) for t in a]
    ribbon(f, pts, r*.105, back, out, mat, label)


def ionic(f, x, bottom, top, radius, depth, lod, name, volutes=True):
    # Smooth shafts and stacked mouldings. Scale bases and capitals to each order.
    h = top-bottom
    n = 10 if lod else 28
    profile = [(bottom,1.38),(bottom+.045*h,1.38),(bottom+.049*h,1.28),
               (bottom+.061*h,1.33),(bottom+.074*h,1.08),(bottom+.09*h,1.02),
               (bottom+.20*h,1.01),(top-.105*h,.86),(top-.094*h,.91),
               (top-.080*h,1.04),(top-.060*h,1.18),(top-.040*h,1.24),(top,1.24)]
    f.builder.lathe(f.point(x,0,depth)[:2],[(z,r*radius) for z,r in profile],
                    STONE,n,f.label+'/'+name+' turned shaft')
    if volutes:
        for side in [-1,1]:
            cx=x+side*radius*.93; z=top-radius*.38
            ellipse(f,cx,z,.48*radius,.43*radius,depth+.55*radius,depth+.93*radius,DARK,name+' volute field',n)
            spiral(f,cx,z,.37*radius,side,depth+.93*radius,depth+1.05*radius,name+' Ionic scroll',lod)
    plate(f,x,top-.04*radius,2.88*radius,.18*radius,depth-radius,depth+radius,TRIM,name+' abacus')


def balcony(f, x, width, z, height, depth, lod, name):
    plate(f,x,z+.10*height,width,.20*height,depth-.22,depth+.22,TRIM,name+' plinth')
    plate(f,x,z+.91*height,width+.04,.18*height,depth-.20,depth+.20,TRIM,name+' handrail')
    for side in [-1,1]:
        plate(f,x+side*(width/2-.095),z+.51*height,.19,.80*height,depth-.15,depth+.16,STONE,name+' end pier')
    count=max(3,round((width-.4)/(.32 if lod else .27)))
    for j in range(count):
        u=x-width/2+.23+(j+.5)*(width-.46)/count
        profile=[(.18,.075),(.25,.078),(.34,.045),(.47,.060),(.58,.094),(.72,.066),(.79,.041),(.85,.075)]
        f.builder.lathe(f.point(u,0,depth)[:2],[(z+height*v,r)for v,r in profile],
                        TRIM,6 if lod else 10,f.label+'/'+name+' turned stone balusters')


def shell(f, x, z, rx, rz, base, lod, name):
    # Shallow radiating ribs in a blind semicircular head; keep its lower center visible.
    for i in range(1,8 if lod else 12):
        theta=pi*i/(8 if lod else 12)
        ribbon(f,[(x+.10*rx*cos(theta),z+.10*rz*sin(theta)),
                  (x+.78*rx*cos(theta),z+.78*rz*sin(theta))],.027,base,base+.037,TRIM,name+' radiating ribs')


def swag(f,x,z,width,lod):
    for side in [-1,1]:
        pts=[(x+side*(.12+width*.40*j/12),z-.12-.24*sin(pi*j/12)+.17*j/12)for j in range(13)]
        ribbon(f,pts,.057,.15,.24,TRIM,'attic carved garlands')
        for j in range(2,12,3 if lod else 2):
            u,h=pts[j]
            ellipse(f,u,h-.052,.068,.102,.19,.27,STONE,'attic leaf clusters',8 if lod else 12)
    ellipse(f,x,z-.035,.24,.29,.15,.24,TRIM,'attic medallion',12 if lod else 24)
    ellipse(f,x,z-.035,.15,.19,.24,.28,STONE,'attic medallion field',12 if lod else 20)
