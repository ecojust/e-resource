"""Interlocking clay tiles across the garden slope and hip, fitted around both roof windows."""
from collections import defaultdict
from math import ceil,cos,floor,pi,sin
import numpy as np
from shapely import constrained_delaunay_triangles
from shapely.geometry import Polygon,box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from shapely.affinity import affine_transform
from frontage import finish,point
from roof_dormers import roof_openings
BED='Shanyin roof | dark tile bedding'
RIDGE='Shanyin roof | rounded hip tile'
ROLL='Shanyin roof | dark pitched rolls'
CLAYS=['Shanyin roof | fired clay '+v for v in ['gold','red','orange','dark','rose','umber']]
PALETTE={BED:finish((84,66,52)),RIDGE:finish((161,93,62)),ROLL:finish((78,65,56)),
         **{k:finish(v)for k,v in zip(CLAYS,[(179,109,78),(169,99,70),(184,117,83),
                                              (158,94,69),(177,106,76),(163,99,73)])}}

def pieces(shape):
    if shape.is_empty:return []
    if shape.geom_type=='Polygon':return [orient(shape,1.)]
    return [p for one in getattr(shape,'geoms',()) for p in pieces(one)]

def tile_part(poly,full,lo,hi,front,back,fn,lod):
    # The top is split along the raised water rib. Top/bottom share the same
    # subdivisions, so all boundary edges of clipped hip tiles match exactly.
    cuts=[0.,.13,.29,.75,1.] if not lod else [0.,.17,.45,1.]
    relief=[.006,.044,.013,.003,.009] if not lod else [.006,.033,.004,.009]
    ts=[];coords=[];lookup={}
    def vertex(x,y):
        key=(round(float(x),6),round(float(y),6))
        if key not in lookup:lookup[key]=len(coords);coords.append(key)
        return lookup[key]
    for a,c in zip(cuts,cuts[1:]):
        u=lo+(hi-lo)*a;v=lo+(hi-lo)*c
        if full:
            i,j,k,l=[vertex(s,t)for s,t in [(u,front),(v,front),(v,back),(u,back)]]
            ts.extend([(i,j,k),(i,k,l)])
        else:
            for part in pieces(poly.intersection(box(u,front,v,back))):
                if part.area<1e-7:continue
                for triangle in constrained_delaunay_triangles(part).geoms:
                    triple=tuple(vertex(*pt)for pt in list(orient(triangle,1).exterior.coords)[:3])
                    if len(set(triple))==3:ts.append(triple)
    verts=[]
    for upper in [False,True]:
        for x,y in coords:
            z=.018+float(np.interp((x-lo)/(hi-lo),cuts,relief))+.013*(back-y)/(back-front) if upper else .001
            verts.append(fn(x,y,z))
    n=len(coords);faces=[tuple(reversed(t))for t in ts]+[tuple(x+n for x in t)for t in ts]
    perimeter=set()
    for t in ts:
        for i,j in zip(t,(t[1],t[2],t[0])):
            if (j,i)in perimeter:perimeter.remove((j,i))
            else:perimeter.add((i,j))
    for i,j in perimeter:faces.append((i,j,j+n,i+n))
    return verts,faces

def cover(b,label,region,fn,lod):
    # fn maps (across, upslope, relief in Z) to the model; both roof mappings are right-handed.
    for piece in pieces(region):b.prism(piece,-.071,.001,fn,BED,label+' | backing with roof-window cuts')
    # The primary image gives 10–11 native pixels between exposed tile ribs in the clear front panel.
    width=.140;step=.397
    left,bot,right,top=region.bounds
    batches=defaultdict(lambda:[[],[]])
    for row in range(floor(bot/step),ceil(top/step)):
        front=row*step+.006;back=(row+1)*step-.002
        # The photographed tile side joints follow each course up the pitch.
        for column in range(floor(left/width),ceil(right/width)):
            lo=column*width+.003;hi=(column+1)*width-.002
            rect=box(lo,front,hi,back)
            if not region.intersects(rect):continue
            full=region.covers(rect);tile=rect if full else region.intersection(rect)
            if tile.area<.00012:continue
            group=(row,((column*29+row*17+column*row*7)%61)%len(CLAYS))
            v,f=tile_part(tile,full,lo,hi,front,back,fn,lod)
            if not f:continue
            xyz,faces=batches[group];base=len(xyz);xyz.extend(v);faces.extend([tuple(base+i for i in t)for t in f])
    for (row,k),(v,f)in batches.items():
        b.add(v,f,CLAYS[k],f'{label} | course {row+1:02} tone {k+1}')

def capping(b,a,c,lod,label):
    a=np.asarray(a,float);c=np.asarray(c,float);v=c-a;length=np.linalg.norm(v)
    axis=v/length
    width=np.cross(axis,[0.,0.,1.]);width/=np.linalg.norm(width)
    up=np.cross(width,axis);up/=np.linalg.norm(up)
    slices=5 if lod else 8
    profile=[(cos(k*pi/slices)*.104,sin(k*pi/slices)*.083+.019)for k in range(slices+1)]
    # For this mapper the (side, up, axis) basis must be right-handed.
    if np.linalg.det(np.stack([width,up,axis]))<0:width*=-1
    mapper=lambda x,z,t: tuple(a+width*x+up*z+axis*t)
    count=ceil(length/.31)
    for t in range(count):
        b.prism(Polygon([*profile,(-.104,.000),(.104,.000)]),t*length/count+.002,
                (t+1)*length/count,mapper,RIDGE,label+' | segmented caps')

def add_roof(b,lod,layout):
    e=layout['eave_y'];ze=layout['eave_z'];hx,hr,hz=layout['hip_end'];slope=(hz-ze)/(hr-e)
    xmin=point(layout,layout['front_u'][0],800)[0]-.20;xmax=point(layout,layout['front_u'][1],800)[0]
    base=Polygon([(xmin,e),(xmax,e),(xmax,hr),(hx,hr)])
    holes=unary_union([Polygon(q)for q in roof_openings(layout)])
    cover(b,'Front roof',base.difference(holes),lambda x,y,d:(x,y,ze+slope*(y-e)+d),lod)
    side=Polygon([(xmin,e),(hx,hr),(xmin,hr)])
    # Across = -Y, up the hip = +X. The original cap runs from the projecting eaves to the main ridge.
    local=affine_transform(side,[0,-1,1,0,0,0])
    cover(b,'West hip',local,lambda u,t,d:(t,-u,ze+(t-xmin)*(hz-ze)/(hx-xmin)+d),lod)
    capping(b,[xmin,e,ze+.021],[hx,hr,hz+.021],lod,'Garden hip')
    # Follow the three longitudinal dark rolls visible between the clay ribs and the dormer walls.
    P=np.asarray(layout['camera_P'])
    def on_pitch(u,v):
        m=P[:2]-np.array([u,v])[:,None]*P[2]
        intercept=ze-slope*e
        x,y=np.linalg.solve(np.column_stack([m[:,0],m[:,1]+m[:,2]*slope]),-m[:,3]-m[:,2]*intercept)
        return (x,y,intercept+slope*y+.070)
    for i,(lower,upper) in enumerate([((550,424),(623,306)),((750,425),(792,292)),((819,425),(856,260))],1):
        b.tube([on_pitch(*lower),on_pitch(*upper)],.045,ROLL,8 if lod else 12,f'Garden roof | dark pitched roll {i}')
    back=layout['back_roof'];bx,by,bz=back['back_left'];fx,fy,fz=back['front_left']
    high=Polygon([(fx,fy),(xmax,fy),(xmax,by),(bx,by)])
    cover(b,'Rear upper roof',high,lambda x,y,d:(x,y,fz+(bz-fz)*(y-fy)/(by-fy)+d),lod)
    capping(b,[bx,by,bz+.014],[xmax,by,bz+.014],lod,'Upper ridge')
