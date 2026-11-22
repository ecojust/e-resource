"""Individually edged clay interlocking pans clipped to the valleys and dormer opening."""
from collections import defaultdict
import math
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, box
from shapely.geometry.polygon import orient
from lawn import BASE, MEASURE, N, ROOF, SLOPE, T, pitched, roof_z, roofcut

CLAY='Ochre roof pans with mineral speckle';PALE='Fired orange pan';RED='Weathered russet pan';JOINT='Dark upper roof joints';RIDGE='Orange clay at the ridge'
CLAY_SET=(CLAY,PALE,RED)
REPEAT=.59

def roof_xyz(x,y,lift=0):
    return np.asarray([x,y,roof_z(y)])+N*lift

def pieces(shape):
    if isinstance(shape,Polygon) and shape.area>1.e-9:yield shape
    elif isinstance(shape,MultiPolygon):
        for sub in shape.geoms:yield from pieces(sub)

def add_roof(b,lod):
    face=ROOF.difference(roofcut())
    mapper=lambda x,y,h:roof_xyz(x,y,h)
    b.prism(face,-.096,-.009,mapper,JOINT,'Principal roof/dark bed around dormer')
    source=MEASURE['samples'][2]['measured_centers'];ref=source[len(source)//2]['surface_yz'][0]
    left,low,right,high=face.bounds
    pitch_x=.222
    high_profile=np.array([.000,.080,.17,.30,.63,.79,.91,1.0])
    rise=np.array([.006,.040,.067,.043,.012,.006,.016,.013])
    far_profile=np.array([.0,.18,.54,1.0]);far_rise=np.array([.006,.051,.008,.013])
    prof,ht=(far_profile,far_rise) if lod else (high_profile,rise)
    for row in range(math.floor((low-ref)/T),math.ceil((high-ref)/T)):
        y0=ref+row*T;y1=y0+T*.970
        batches=defaultdict(lambda:([],[]))
        for col in range(math.floor(left/pitch_x)-1,math.ceil(right/pitch_x)+1):
            x0=(col+.45*(row%2))*pitch_x
            color=CLAY_SET[(col*29+row*23+(col*row)%9)%7%3]
            # Each sliver is convex: cut the cell to the outline and the dormer sides.
            for k in range(len(prof)-1):
                ax=x0+prof[k]*pitch_x*.98;bx=x0+prof[k+1]*pitch_x*.98
                clipped=face.intersection(box(ax,y0,bx,y1))
                for sub in pieces(clipped):
                    poly=np.array(orient(sub,sign=1).exterior.coords[:-1])
                    if len(poly)<3:continue
                    v,f=batches[color];start=len(v)
                    subrise=np.interp(poly[:,0],[ax,bx],ht[k:k+2])+.014-(poly[:,1]-y0)/T*.012
                    for (x,y),z in zip(poly,subrise):v.append(roof_xyz(x,y,z))
                    # Cell strips are bounded by straight valleys/cheeks. Split any concave corner
                    # using ear clipping rather than a fan across the dormer mouth.
                    if sub.equals(sub.convex_hull):f.extend((start,start+n,start+n+1)for n in range(1,len(poly)-1))
                    else:
                        from shapely import constrained_delaunay_triangles
                        for triangle in constrained_delaunay_triangles(sub).geoms:
                            indices=[int(np.argmin(np.abs(poly-q).sum(axis=1))) for q in orient(triangle,sign=1).exterior.coords[:-1]]
                            f.append(tuple(start+n for n in indices))
                    for i,(p,q) in enumerate(zip(poly,np.roll(poly,-1,axis=0))):
                        if abs(p[1]-y0)+abs(q[1]-y0)>.00001:continue
                        lower_v,lower_f=batches[JOINT];k0=len(lower_v)
                        j=(i+1)%len(poly);lower_v.extend((roof_xyz(*p,subrise[i]),roof_xyz(*q,subrise[j]),roof_xyz(*q,-.010),roof_xyz(*p,-.010)));lower_f.append((k0,k0+3,k0+2,k0+1))
        for color,(verts,faces)in batches.items():
            if verts:
                label={CLAY:'ochre',PALE:'orange',RED:'russet',JOINT:'overlaps'}[color]
                b.add(verts,faces,color,'Principal roof/course '+str(row+20)+' '+label)
    # Separate cap units sit astride the observed high edge. Model only the section in view.
    a,c=pitched([[405,173.6],[581,150.7]]);ends=[roof_xyz(*point,.031)for point in (a,c)]
    distance=np.linalg.norm(ends[1]-ends[0]);axis=(ends[1]-ends[0])/distance;side=np.cross(axis,N);side/=np.linalg.norm(side)
    count=round(distance/.46);segments=5 if lod else 10
    for i in range(count):
        start=ends[0]+axis*(distance*i/count);end=ends[0]+axis*min(distance,distance*(i+1.08)/count)
        rings=[]
        for p,rad in [(start,.109),(end,.094)]:
            rings.extend([p+rad*(np.cos(t)*side+np.sin(t)*N)for t in np.linspace(0,np.pi,segments+1)])
        step=segments+1
        b.add(rings,[(k,k+1,k+1+step,k+step)for k in range(segments)],RIDGE,'Principal roof/ridge cap '+str(i+1))

def apply_roof_uv(b):
    along=np.array([0.,1.,SLOPE])/np.hypot(1.,SLOPE)
    for part in b.parts:
        if part['material']!=CLAY:continue
        points=np.asarray(part['vertices'],dtype=np.float32).astype(float)
        part['texcoords']=np.column_stack([points[:,0]/REPEAT,1-(points@along)/REPEAT]).tolist()
