"""The visible garden front of the gable at 27 Aomen Lane 660.

Model coordinates are metres. Survey points are expressed in the front photograph
to keep the established door, window and cornice measurements on the same grid.
"""
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade

SCALE=.018
def x(u): return (u-267.)*SCALE
def z(v): return (358.-v)*SCALE
def poly(points): return Polygon([(x(u),z(v)) for u,v in points])
def rect(l,t,r,b): return poly([(l,t),(r,t),(r,b),(l,b)])
def band(left,right,low,high):
    return Polygon([left[0],left[1],right[1],right[0]])
FIELD='Warm ochre garden roughcast'
WOOD='Dark olive timber casement'
LINTEL='Pale lintel and sill'
IRON='Oxblood balcony wood'
SUPPORT='Weathered ledge brackets'
GLASS=['Grey garden window reflection','Green garden window reflection','Blue smoke garden window']
TIMBER='Dark roof board underside'
PORTLAND='Ochre window reveal'
PLINTH='Red brick basement pointing'
BRICKS=['Warm row-house clinker','Faded red row-house clinker','Rose row-house clinker']
UPPER=[[(177.4,99.1),(221.5,94.4),(223.6,163.9),(178.6,167.8)],
       [(300.1,87.3),(348.5,83.7),(352.9,150.8),(302.4,157.1)]]
# End the study at the two corners of the projecting gable, before adjacent houses.
FACADE=[(127.,358),(129.,103.),(206.,10.),(306.,2.),(402.,78.),(414.,358.)]

def bilinear(points,a,b):
    ul,ur,lr,ll=np.asarray(points,dtype=float)
    return tuple((1-b)*((1-a)*ul+a*ur)+b*((1-a)*ll+a*lr))
def pane(points,a0,a1,b0,b1):
    return poly([bilinear(points,a,b) for a,b in [(a0,b0),(a1,b0),(a1,b1),(a0,b1)]])
def cap(face,points,tag):
    shape=poly(points)
    face.prism(shape,-.006,.095,LINTEL,tag)
def sash(face,i,quad):
    tag='Left' if not i else 'Right'
    intervals=[(.044,.476),(.524,.956)]
    heights=[.04,.271,.486,.702,.963]
    openings=[]
    for j,(l,r) in enumerate(intervals):
        for k,(top,bottom) in enumerate(zip(heights,heights[1:])):
            low=top if k==0 else top+.011
            high=bottom if k==len(heights)-2 else bottom-.011
            shape=pane(quad,l,r,low,high)
            openings.append(shape)
            face.prism(shape,-.147,-.134,GLASS[(j+k+i)%len(GLASS)],tag+' glass '+str(j+1)+'-'+str(k+1))
    frame=poly(quad).difference(unary_union(openings))
    face.prism(frame,-.138,-.076,WOOD,tag+' casement frame and glazing bars')
    face.prism(poly(quad).buffer(.038,join_style=2).difference(poly(quad)), -.180,-.015,PORTLAND,tag+' ochre reveal')
    if i==0:
        cap(face,[(168,88),(230,82),(230,87),(169,94)],tag+' lintel')
    else:
        cap(face,[(291,77),(357,71),(358,77),(292,84)],tag+' lintel')

def guard(b,face,i):
    """Two shallow timber Juliette guards, with square posts and three corbels apiece."""
    left,right,top_left,top_right,low_left,low_right=[153,239,147,142,168,163] if not i else [286,373,136,130,157,151]
    label=('Left' if not i else 'Right')+' timber guard/'
    def pos(t,base,d):
        u=left+(right-left)*t
        h=(low_left+(low_right-low_left)*t) if base else (top_left+(top_right-top_left)*t)
        return np.array([x(u),-d,z(h)])
    def rail(a,c,width,height,material,tag):
        a,c=np.array(a),np.array(c);direction=c-a
        along=direction/np.linalg.norm(direction)
        perp=np.cross(along,[0,0,1.])
        if np.linalg.norm(perp)<1e-8:perp=np.array([1.,0.,0.])
        else:perp/=np.linalg.norm(perp)
        up=np.cross(perp,along)
        b.box((a+c)/2,[np.linalg.norm(direction),width,height],material,[along,perp,up],label+tag)
    for base,d,thick,depth in [(False,.377,.061,.089),(True,.37,.07,.09)]:
        rail(pos(-.012,base,d),pos(1.012,base,d),depth,thick,IRON,('top rail' if not base else 'lower rail'))
        for e in (0,1):
            rail(pos(e,base,.03),pos(e,base,d),depth,thick,IRON,('left' if not e else 'right')+(' foot return' if base else ' hand return'))
    for n,a in enumerate((.034,.19,.35,.51,.67,.83,.964)):
        rail(pos(a,True,.37),pos(a,False,.37),.044,.049,IRON,'square upright '+str(n+1))
    # Continuous projecting ledge is visible at the foot of each rail.
    for d1,d2 in [(.003,.424)]:
        lo=pos(0,True,d1);hi=pos(1,True,d1)
        verts=[]
        for h in [-.108,-.025]:
            for d in [d1,d2]:
                for q in [lo,hi]: verts.append((q[0],-d,q[2]+h))
        b.add(verts,[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)],SUPPORT,label+'projecting ledge')
    for n,a in enumerate((.14,.5,.866)):
        q=pos(a,True,.0); profile=[(.012,-.1),(.39,-.1),(.34,-.18),(.21,-.235),(.13,-.35),(.022,-.35)]
        verts=[(q[0]+offset,-d,q[2]+h) for offset in (-.054,.054) for d,h in profile]
        lim=len(profile); sides=[(k,(k+1)%lim,(k+1)%lim+lim,k+lim) for k in range(lim)]
        b.add(verts,[tuple(range(lim-1,-1,-1)),tuple(range(lim,2*lim)),*sides],SUPPORT,label+'tapered bracket '+str(n+1))

def add_gable(b,lod,holes):
    face=Facade(b,[-.5,0],[.5,0],'Number 27 garden front')
    outline=poly(FACADE); cut=unary_union([poly(q) for q in UPPER]+list(holes))
    face.prism(outline.difference(cut),-.245,0.,FIELD,'roughcast with four openings')
    foot=outline.intersection(rect(124,310,422,359)).difference(cut)
    face.prism(foot,-.014,.015,PLINTH,'plinth mortar bed')
    for row in range(11):
        for j in range(-1,29):
            l=126+j*11.+(row%2)*5.5; top=311+row*4.25
            shape=foot.intersection(rect(l,top,l+10.45,top+3.70))
            if shape.area>.0003:
                face.prism(shape,.014,.022,BRICKS[(j*j+row+abs(j))%3],'plinth brick course '+str(row+1))
    for i,q in enumerate(UPPER):
        sash(face,i,q);guard(b,face,i)
