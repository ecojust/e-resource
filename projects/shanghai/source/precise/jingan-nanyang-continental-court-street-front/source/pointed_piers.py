"""Contemporary evidence for the exposed aggregate street piers on Continental Court.
Local t follows the numbered northern-to-southern street edge; d increases inwards
from the highest central arris. World coordinates use true east, north and height.
"""
import json
import math
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, box

STONE = 'Pier | grey exposed aggregate'
RECESS = 'Pier | sheltered stone'
SEAM = 'Pier | dark joint bed'
EDGE = 'Pier | weathered stone edge'
BOWL = 'Pier | weathered dark relief'
LEAF = 'Pier | raised foliate edges'


def finish(rgb):
    c = np.array(rgb) / 255.
    return {'color': np.where(c <= .04045, c / 12.92, ((c + .055)/1.055)**2.4).tolist(),
            'roughness': .89, 'metallic': 0.}


PALETTE = {key:finish(rgb) for key,rgb in [(STONE,(156,152,142)),(RECESS,(138,132,120)),
          (SEAM,(112,107,97)),(EDGE,(163,158,145)),(BOWL,(76,74,62)),(LEAF,(94,91,73))]}


for key in (STONE, EDGE, RECESS):
    PALETTE[key]['texture'] = str(Path(__file__).with_name('pier-aggregate.jpg'))
    PALETTE[key]['color'] = [min(1.,v/.833) for v in PALETTE[key]['color']]


def pointed(radius, spring, tip, feet, steps):
    rise = tip - spring
    offset = (rise*rise-radius*radius)/(2*radius)
    arc = radius+offset
    right=[(x,spring+math.sqrt(max(0.,arc*arc-(x+offset)**2))) for x in np.linspace(radius,0,steps+1)]
    return Polygon([(-radius,feet),(radius,feet)]+right+[(-x,z) for x,z in right[-2::-1]])


# Absolute levels from real pixel rays, on the final common street datum.
# Each row is (outer tip, arch spring, sill top, bottom fillet, clear half-width).
# The eastern shopfronts screen most of the level of the lancets.
LOWER={0:None,1:None,2:(4.98,4.61,3.18,2.86,.223),3:None,
       4:(5.05,4.66,3.21,2.90,.218),5:(5.04,4.66,3.18,2.88,.218),
       6:(5.02,4.65,3.16,2.84,.218),7:(5.07,4.70,2.90,2.33,.235),
       8:(5.04,4.66,2.86,2.36,.235),9:(5.01,4.64,2.84,2.41,.229),
       10:(5.28,4.93,3.20,2.70,.204),11:(5.33,4.95,3.18,2.66,.207)}


def course_levels(station):
    # Adjacent faces share the banding. Two long faces give independent runs of joints.
    if station <= 6:
        measured = [3.170,3.540,3.912,4.286,4.660,5.038,5.412,5.784,6.152,6.527,
                    6.889,7.299,7.694,8.084,8.446,8.857,9.264,9.678,10.089,10.454,
                    10.911,11.328,11.729,12.132,12.522,12.966,13.342,13.737,14.131,
                    14.525,14.917,15.309,15.704,16.103,16.497,16.872]
    else:
        measured = [3.178,3.552,3.927,4.298,4.682,5.046,5.422,5.786,6.156,6.526,
                    6.896,7.276,7.648,8.064,8.445,8.886,9.294,9.704,10.112,10.518,
                    10.920,11.342,11.734,12.150,12.540,12.952,13.305,13.685,14.068,
                    14.459,14.837,15.223,15.610,15.994,16.384,16.766]
    pitch = (measured[4]-measured[0])/4
    lower = [measured[0] - n*pitch for n in range(8,0,-1)]
    return [0., *lower, *measured, 17.12]


def add_pier(b,index,center,tangent,top=18.35526679941441,lod=False):
    coarse=lod is True or lod=='lod'
    scale=top/18.35526679941441
    tx,ty=np.array(tangent,dtype=float)/np.linalg.norm(tangent)
    prefix=f'Pier {index:02d} | '
    begin=len(b.parts)
    body=.26
    back=.51
    width=1.04
    observed=LOWER[index]
    point,spring,shelf,underside,radius=observed or (5.02,4.66,3.18,2.86,.218)
    point-=.054
    low=4.35 if index<=3 else 0.

    def xyz(t,d,z):
        return (center[0]+scale*(tx*t-ty*d),center[1]+scale*(ty*t+tx*d),z*scale)
    def prism(poly,front,rear,material,name):
        if not poly.is_empty and poly.area>1e-8:
            pieces = list(poly.geoms) if poly.geom_type == 'MultiPolygon' else [poly]
            for piece in pieces:
                label = name
                if len(pieces) == 2:
                    label += ' left' if piece.centroid.x < 0 else ' right'
                b.prism(piece,-rear,-front,lambda t,z,out:xyz(t,-out,z),material,prefix+label)
    def add_local(v,f,material,name):
        verts=np.asarray([xyz(*p) for p in v])
        v0=verts-verts.mean(axis=0)
        vol=sum(np.dot(v0[a[0]],np.cross(v0[a[i]],v0[a[i+1]])) for a in f for i in range(1,len(a)-1))
        b.add(verts,f if vol>0 else [a[::-1] for a in f],material,prefix+name)
    def rings(sections,material,name):
        count=len(sections[0]); verts=[p for sec in sections for p in sec]
        faces=[]
        for i in range(len(sections)-1):
            for j in range(count):
                k=(j+1)%count
                faces.append((i*count+j,i*count+k,(i+1)*count+k,(i+1)*count+j))
        for i,rev in [(0,True),(len(sections)-1,False)]:
            cent=len(verts);verts.append(np.mean(sections[i],axis=0))
            for j in range(count):
                edge=(cent,i*count+j,i*count+(j+1)%count)
                faces.append(edge[::-1] if rev else edge)
        add_local(verts,faces,material,name)

    # The photographed pointed slot is a blind recess, with a continuous rear face.
    steps=5 if coarse else 12
    outer=pointed(radius+.045,spring+.012,point+.054,shelf,steps)
    inner=(pointed(radius,spring,point,shelf-.004,steps) if observed else Polygon())
    extent=box(-width/2,low,width/2,17.12)
    skin=extent.difference(inner)
    prism(extent,body+.135,back,SEAM,'continuous backing and recessed joints')
    prism(skin,body+.018,body+.141,SEAM,'joint bed and niche returns')
    levels = course_levels(index)
    for row, (bottom, top_z) in enumerate(zip(levels, levels[1:])):
        lo=max(low,bottom+.003)
        hi=min(17.12,top_z-.003)
        if hi>lo:
            prism(skin.intersection(box(-width,lo,width,hi)),body,body+.020,STONE,f'washed stone course {row+1:02d}')
    if observed:
        # The clear floor of the niche has its own sheltered face; a narrow incised
        # joint remains between its courses. These marks are visible behind the lamp.
        seams = [3.176,3.542,3.918,4.290,4.665] if index<=6 else [3.178,3.564,3.944,4.326,4.707]
        edges = [low-.02, *[z for z in seams if low < z < point], point+.01]
        for row, (z0,z1) in enumerate(zip(edges,edges[1:])):
            section=inner.intersection(box(-radius,z0+.004,radius,z1-.004))
            prism(section,body+.128,body+.137,RECESS,f'lancet recessed course {row+1:02d}')
    if observed:
        prism(outer.difference(inner).intersection(extent),body-.030,body+.021,EDGE,'blind lancet edge')
    if index>=4:
        # Pointed cap and shaft rise over a tiered sill with two visible lower fillets.
        profile=[(2.15,.155,.228),(2.18,.190,.197),(2.225,.210,.168),(2.245,.230,.145),
                 (2.310,.240,.134),(2.335,.244,.153),(2.350,.246,.164),(2.590,.322,.073),
                 (2.640,.356,.036),(2.685,.364,.026),(2.720,.370,.029),
                 (2.750,.359,.050),(2.786,.330,.077)]
        profile=[(underside+(z-2.15)*(shelf-underside)/.636,half,front) for z,half,front in profile]
        rings([[(-half,front,z),(half,front,z),(half,body+.05,z),(-half,body+.05,z)]
               for z,half,front in profile],EDGE,'projecting sill and lower roll')
    crown=[(-.52,17.105),(.52,17.105),(.52,17.19),(.475,17.23),(.458,17.39),
           (.498,17.47),(.172,17.86),(.13,17.98),(-.13,17.98),(-.171,17.86),
           (-.497,17.47),(-.458,17.39),(-.475,17.23),(-.52,17.19)]
    prism(Polygon(crown),body-.018,back,STONE,'two sloping shoulders and small notches')
    # Surveyed pointed tip, gently swept transition to the side folds, long central ridge.
    crest=[(-.286,.199,17.69),(-.180,.141,17.88),(-.149,.095,17.97),(-.092,.053,18.013),
           (-.047,.024,18.09),(0.,0.,18.35526679941441),(.047,.024,18.09),(.092,.053,18.013),
           (.149,.095,17.97),(.180,.141,17.88),(.286,.199,17.69)]
    sections=[[(x,d,10.52),(x,body+.034,10.52),(x,body+.034,z),(x,d,z)] for x,d,z in crest]
    rings(sections,STONE,'folded shaft and finial')
    profile=[(10.13,.038,.048),(10.157,.090,.099),(10.225,.119,.137),(10.29,.206,.194),
             (10.40,.255,.237),(10.46,.279,.284),(10.48,.307,.310),
             (10.51,.313,.319),(10.541,.305,.314)]
    def bowl(z,half,throw):
        pts=[(half*math.cos(a),body+.012-throw*math.sin(a),z) for a in np.linspace(0,math.pi,11 if coarse else 23)]
        return pts+[(-half,body+.024,z),(half,body+.024,z)]
    rings([bowl(*p) for p in profile],BOWL,'half-bowl terminal and rim')
    def surface(x,z):
        rad=np.interp(z,[p[0] for p in profile],[p[1] for p in profile])
        throw=np.interp(z,[p[0] for p in profile],[p[2] for p in profile])
        return body+.011-throw*math.sqrt(max(0,1-(x/rad)**2))
    def relief(x,z,rx,rz,angle,depth,material,label):
        ring=[]
        for a in np.linspace(0,math.tau,8 if coarse else 14,endpoint=False):
            h=rx*math.cos(a);v=rz*math.sin(a)
            t=x+h*math.cos(angle)-v*math.sin(angle);zz=z+h*math.sin(angle)+v*math.cos(angle)
            ring.append((t,surface(t,zz),zz))
        verts=[(x,surface(x,z)-depth,z),(x,surface(x,z)+.012,z)]+ring
        n=len(ring)
        faces=[(0,2+i,2+(i+1)%n) for i in range(n)]+[(1,2+(i+1)%n,2+i) for i in range(n)]
        add_local(verts,faces,material,label)
    lobes=[(-.066,10.399,.052,.076,-1.05),(-.030,10.422,.046,.070,-.35),
           (.041,10.421,.050,.077,.35),(.073,10.386,.046,.064,.98),(.004,10.333,.036,.064,.05)]
    for i,entry in enumerate(lobes):
        relief(*entry,.020,LEAF,f'central foliate lobe {i+1}')
    berries=[(.182,10.411),(.157,10.443),(.205,10.424),(.147,10.389),(.175,10.366),(.133,10.341)]
    for side in (-1,1):
        for i,(t,z) in enumerate(berries[::2] if coarse else berries):
            relief(side*t,z,.023,.026,side*.35,.018,BOWL,f'round relief {side:+d} group {i+1}')

    for part in b.parts[begin:]:
        if part['material'] not in (STONE,EDGE,RECESS):
            continue
        uv=[]
        for east,north,z in part['vertices']:
            t=(east-center[0])*tx+(north-center[1])*ty
            d=-(east-center[0])*ty+(north-center[1])*tx
            # The mineral aggregate has no directional pattern. The oblique terms
            # keep the side, top, and bottom triangles mapped as well as the face.
            uv.append([(t+.813*d)/.32,(z-.273*d+.093*t)/.32])
        part['texcoords']=uv


def add_pointed_piers(b,lod=False,plan=None,height=None):
    if plan is None:
        j=json.loads((Path(__file__).resolve().parents[1]/'measurements/street-frontage-layout.json').read_text())
        plan=j['pier_tip_axes_m'];height=j['height_m']['tip']
    if len(plan)!=12 or not height:
        raise ValueError('Twelve pier centres and the fitted crown elevation are required.')
    for i,p in enumerate(plan):
        tangent=np.array(plan[min(i+1,11)])-plan[max(i-1,0)]
        add_pier(b,i,p,tangent,height,lod)
