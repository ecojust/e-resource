"""Brick return cheeks and the change of direction into the rising upper flight."""
from math import cos,pi,sin
from shapely.geometry import Polygon
from materials import *
from joinery import door,plaque

def add_stair(f,lod=False):
    north=f.name=='1-2';number=2 if north else 4
    land=3.43 if north else 3.65;half=1.26 if north else 1.32
    left,right=(-6.50,-5.08) if north else (-6.09,-4.84)
    end=-1.27
    # Lower treads face the lane. The landing turns to the upper flight, which
    # follows the stepped wall and the inner rail seen in the two close views.
    first=7;lower_d=-1.47;back_d=.54
    for i in range(first):
        d=lower_d+(back_d-lower_d)*i/first;q=lower_d+(back_d-lower_d)*(i+1)/first
        f.rect(left+.15,right-.12,.008,half*(i+1)/first,-q,-d,STEP,'lower stair across the lane front '+str(i+1))
        if not lod:
            f.rect(left+.15,right-.12,half*(i+1)/first-.035,half*(i+1)/first+.004,-d-.035,-d+.017,SILL,'lower brick nosing')
    f.rect(left+.15,right,half-.15,half,-1.44,-back_d,STEP,'turning landing')
    upper=13
    for i in range(upper):
        u=right+(end-right)*i/upper;v=right+(end-right)*(i+1)/upper;top=half+(land-half)*(i+1)/upper
        f.rect(u,v,.015,top,-1.44,-.015,STEP,'upper flight along brick cheek '+str(i+1))
        if not lod:f.rect(u-.020,u+.029,top-.034,top+.003,-1.43,-.020,SILL,'upper stair nosing')
    f.rect(end,end+.55,land-.15,land,-1.44,-.01,STEP,'landing at the upper front door')
    # Top lines digitized on the large 2013 No.1 frame and on the separate
    # photograph by Shanghai Xinli Yangfang for No.4. Each terrace has a riser.
    cheek_end=-1.45 if north else -1.57
    heights=([(right,2.70),(-4.27,3.29),(-3.70,3.66),(-3.10,4.16),(-2.32,4.39),(cheek_end,4.39)] if north else
             [(right,2.91),(-4.00,3.44),(-3.39,3.91),(-2.74,4.35),(-1.69,4.63),(cheek_end,4.63)])
    top=[heights[0]]
    for (a,h),(b,k) in zip(heights,heights[1:]):
        top.extend([(b,h),(b,k)] if abs(k-h)>.002 else [(b,h)])
    wall=Polygon([(right,.01),(cheek_end,.01),*reversed(top)])
    f.solid(wall,.015,.235,BRICK,'stepped cheek of upper flight')
    for (a,h),(b,k) in zip(heights,heights[1:]):
        f.rect(a,b,h-.035,h+.018,.006,.253,SILL,'header course on each stair terrace')
    # The two outer cheeks turn at right angles to the upper flight. Each
    # descends in a hollow curve towards the mouth of the lower flight.
    for ux,tag in [(left,'left'),(right-.13,'right')]:
        g=f.face(ux,back_d,0,-1)
        ztop=(2.72 if north else 2.81) if tag=='left' else heights[0][1]
        curve=[(-.05,ztop),(.14,ztop),(.145,ztop-.29)]
        for i in range(1,12):
            t=i/11;curve.append((.145+1.26*(1-cos(t*pi/2)),ztop-.30-1.09*sin(t*pi/2)))
        curve.append((2.03,curve[-1][1]))
        g.solid(Polygon([(-.05,.014),(2.03,.014),*reversed(curve)]),-.158,.013,BRICK,tag+' concave brick return at stair mouth')
        g.band(curve,.076,-.177,.033,SILL,'radial brick coping on '+tag+' return')
    f.rail([(right+.05,1.39,half+.84),(end-.06,1.39,land+.88)],.034,OAK,'inclined dark timber handrail',6 if lod else 10)
    high=f.face(end+.55,-.025,0,1)
    high.rect(-.05,1.55,land,land+2.4,-.23,0,DARK,'upper door recess')
    door(high,.73,.89,land+.024,land+2.13,.09,0,'upper landing door',lod)
    if north:plaque(f,-5.02,3.162,2,-1.54)
    else:plaque(f,-3.91,2.562,4,.248)
