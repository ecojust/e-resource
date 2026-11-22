"""The clay tile slope, rooftop rods, single condenser and the visible drainpipe."""
import math
import numpy as np
from shapely.geometry import box,Point

TILE='Weathered terracotta pan';TILE2='Rose clay pan';DARK_TILE='Dark tile bed'
PIPE='Ivory painted pipe';IRON='Aged dark iron';UNIT='Faded condenser case';FAN='Condenser fan in shade'

def tile_slope(builder,lod):
    xmin,xmax=.005,3.38;ystart,yend=.28,4.88;zbase=-.22;slope=.329
    def p(x,y,d=0):
        return np.array([x,y,zbase+slope*(y-ystart)+d])
    roof=[p(xmin,ystart),p(xmax,ystart),p(xmax,yend),p(xmin,yend)]
    builder.add([*roof,*[v-[0,0,.095]for v in roof]],[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],DARK_TILE,'Lower roof/tile bed')
    # The section closes immediately under the roof bed, including the right-hand cut face.
    bottom=[np.array([v[0],v[1],-.72])for v in roof]
    soffit=[v-[0,0,.095]for v in roof]
    builder.add([*bottom,*soffit],[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],
                'Neutral cut in plaster','Lower roof/cut beneath sloping roof')
    rows=12 if lod else 18;cols=12 if lod else 19
    for r in range(rows):
        y=ystart+(yend-ystart)*r/rows;back=ystart+(yend-ystart)*(r+1)/rows+.012
        cuts=[xmin,*[xmin+(xmax-xmin)*(k+(.50 if r%2 else 0))/cols for k in range(cols) if .001<(k+(.50 if r%2 else 0))/cols<.999],xmax]
        for j,(l,t)in enumerate(zip(cuts,cuts[1:])):
            if t-l<.025:continue
            l+=.002;t-=.002;m=(l+t)/2
            top=[p(l,y,.014),p(m,y,.037),p(t,y,.014),p(l,back,.007),p(m,back,.023),p(t,back,.007)]
            lower=[v-np.array([0,0,.018])for v in top]
            faces=[(0,1,4,3),(1,2,5,4),(6,9,10,7),(7,10,11,8),(0,6,7,1),(1,7,8,2),
                   (2,8,11,5),(5,11,10,4),(4,10,9,3),(3,9,6,0)]
            builder.add([*top,*lower],faces,TILE2 if (r*3+j)%6==0 else TILE,'Lower roof/pan course '+str(r+1))
    for j in range(cols):
        x=xmin+(j+.5)*(xmax-xmin)/cols
        builder.tube([p(x,yend-.06,.051),p(x,yend+.018,.052)],.031,DARK_TILE,6 if lod else 12,label='Lower roof/ridge ends')

def external_fittings(builder,wall,lod):
    sides=10 if lod else 20
    for j,(x,y,z,rise,radius)in enumerate([(-2.18,.035,2.17,.72,.012),(-.012,.11,2.17,.57,.026)]):
        builder.tube([(x,y,z),(x,y,z+rise)],radius,IRON,sides,label='Upper roof/upright rod '+str(j+1))
    # The wall pipe turns away immediately beneath the cornice.
    pts=[wall.point(.52,-.08,.077),wall.point(.52,1.70,.077),wall.point(.55,1.755,.077),wall.point(.83,1.755,.065)]
    builder.tube(pts,.034,PIPE,sides,label='Return/vertical drain and elbow')
    for z in [.16,.65,1.40]:
        wall.box(.52,z,.092,.027,.088,.03,PIPE,'pipe strap')
    base=.97;top=1.58;near=2.08;far=3.24;cy=2.85;cz=1.28
    wall.prism(box(near,base,far,top),.115,.494,UNIT,'metal condenser casing')
    n=12 if lod else 34
    outer=Point(cy,cz).buffer(.258,quad_segs=n//4)
    inner=Point(cy,cz).buffer(.213,quad_segs=n//4)
    wall.prism(outer,.493,.510,FAN,'fan recess')
    wall.prism(outer.difference(inner),.509,.535,'Weathered fan ring','round fan guard')
    for k in range(6 if lod else 10):
        a=k*math.pi/(6 if lod else 10);u=.19*math.cos(a);v=.19*math.sin(a)
        builder.tube([wall.point(cy-u,cz-v,.527),wall.point(cy+u,cz+v,.527)],.0045,FAN,5 if lod else 8,label='Return/fan spokes')
    wall.prism(Point(cy,cz).buffer(.073,quad_segs=5 if lod else 10),.524,.545,UNIT,'round fan hub')
    for y in [near+.16,far-.17]:
        builder.tube([wall.point(y,base-.01,.05),wall.point(y,base-.01,.48),wall.point(y,base-.27,.055)],.016,IRON,6 if lod else 10,label='Return/condenser bracket')
    for k in range(3 if lod else 6):
        z=base+.15+k*(top-base-.27)/(2 if lod else 5)
        builder.tube([wall.point(near-.01,z,.19),wall.point(near-.01,z,.36)],.009,FAN,5 if lod else 8,label='Return/case side grille')
