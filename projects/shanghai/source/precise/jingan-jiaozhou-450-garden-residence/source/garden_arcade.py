"""The photographed garden arcade at 450 Jiaozhou Road, in local metres.

The three visible arch crowns have separate ellipses and measured joint rhythms.
The eastern end of the fourth span is an explicit estimate in the measurements.
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import box, Polygon
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
SECTIONS = json.loads((HERE.parent/'measurements/garden-arcade-sections.json').read_text())
ARCHES = SECTIONS['arcades']
FRONT_END = 16.95
REAR = 3.72
DEPTH = .45
FACE = 'Garden arcade | red masonry in running bond'
JOINT = 'Garden arcade | warm grey mortar in the arch joints'
SILL = 'Garden arcade | grey stone continuous landing'
CAP = 'Garden arcade | pale weathered terrace coping'
DRIP = 'Garden arcade | shadowed fascia drip'
SPINDLE = 'Garden arcade | pale turned baluster'
BASE = 'Garden arcade | squared stone bases and capitals'
RINGS = tuple(f'Garden arcade | fired radial brick {i+1}' for i in range(6))
def linear(rgb):
    c=np.array(rgb)/255.
    return np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4).tolist()
PALETTE = {k:{'color':linear(c),'roughness':r} for k,c,r in (
    (FACE,(255,255,255),.92),(JOINT,(127,109,95),.96),(SILL,(156,149,137),.91),
    (CAP,(177,168,149),.86),(DRIP,(121,110,93),.92),(SPINDLE,(201,192,173),.86),
    (BASE,(190,182,162),.89),
    *[(m,c,.93) for m,c in zip(RINGS,((133,87,67),(143,91,70),(152,99,77),
        (160,104,79),(169,115,89),(179,124,96)))])}
def texture():
    file=HERE/'arcade-running-bond.png'
    if not file.is_file():
        # One repeat is 12 stretcher lengths and 32 courses. Both dimensions
        # wrap without a broken course or alternating half-brick displacement.
        rng=np.random.default_rng(588);w,h=576,448
        im=Image.new('RGB',(w,h),(152,130,110));draw=ImageDraw.Draw(im)
        for row in range(32):
            top=row*14;shift=(row%2)*24
            for col in range(-1,13):
                x=col*48+shift
                color=np.array([149.,96.,74.])+rng.normal(0,6.8)*np.array([1,.86,.70])
                color+=rng.normal(0,2,3);rgb=tuple(np.clip(color,0,255).astype(int))
                draw.rectangle((x+1,top+1,x+46,top+12),fill=rgb)
                draw.line((x+1,top+12,x+46,top+12),fill=tuple(max(0,n-7) for n in rgb))
        rgb=np.array(im).astype(float)+rng.normal(0,3.5,(h,w,1))
        Image.fromarray(np.clip(rgb,0,255).astype('uint8')).quantize(144).save(file,optimize=True)
    PALETTE[FACE]['texture']=str(file)
def material_uv(part):
    # Give each triangle UVs in the plane of its actual face. Seam vertices
    # retain identical positions on the closed solid, including arch soffits.
    xyz=np.asarray(part['vertices']);verts=[];coords=[];inds=[];lookup={}
    for tri in part['triangles']:
        points=xyz[list(tri)];n=np.cross(points[1]-points[0],points[2]-points[0])
        n/=np.linalg.norm(n)
        if abs(n[1])>.995:
            uv=np.column_stack((points[:,0]/2.712,-points[:,2]/2.048))
        elif abs(n[2])>.995:
            uv=np.column_stack((points[:,0]/2.712,-points[:,1]/2.048))
        else:
            along=np.cross([0.,0.,1.],n);along/=np.linalg.norm(along)
            up=np.cross(n,along)
            uv=np.column_stack((points@along/2.712,-points@up/2.048))
        ids=[]
        for id0,tex in zip(tri,uv):
            key=(id0,*np.around(tex,8))
            if key not in lookup:lookup[key]=len(verts);verts.append(tuple(xyz[id0]));coords.append(tuple(tex))
            ids.append(lookup[key])
        inds.append(tuple(ids))
    part.update(vertices=verts,texcoords=coords,triangles=inds)
def front(x,z,d):return (x,-d,z)
def edge(a,t,width=0.):
    cx,sp,rx,rz=a['ellipse'];co=np.cos(t);si=np.sin(t)
    # The photographed first opening has a small asymmetry next to the west
    # spring. Interpolate continuously from each observed jamb into the crown.
    fix=(a['right']-cx-rx)*max(co,0.)**4+(a['left']-cx+rx)*min(co,0.)**4
    return (cx+(rx+width)*co+fix,sp+(rz+width)*si)
def clear_arch(a):
    ts=np.radians(a['joint_angles_degrees'])
    return Polygon([(a['left'],-.3),(a['right'],-.3),*[edge(a,t) for t in ts]])
def arch_band(a,t0,t1,inner,outer,steps):
    ts=np.linspace(t0,t1,steps+1)
    return Polygon([*[edge(a,t,outer) for t in ts],*[edge(a,t,inner) for t in ts[::-1]]])
def make_arch_wall(b,lod):
    clear=[clear_arch(a) for a in ARCHES]
    masonry=[]
    limits=[0.,*[(a['right']+b_['left'])/2 for a,b_ in zip(ARCHES,ARCHES[1:])],FRONT_END]
    for i,a in enumerate(ARCHES):
        ts=np.radians(a['joint_angles_degrees']);outer=a['band_width_m']
        band=Polygon([*[edge(a,t,outer) for t in ts],*[edge(a,t) for t in ts[::-1]]])
        masonry.append(band.intersection(box(limits[i],0.,limits[i+1],4.79)))
    shell=box(0.,0.,FRONT_END,4.79).difference(unary_union(clear+masonry))
    start=len(b.parts)
    b.prism(shell,-DEPTH,0.,front,FACE,'South arcade | four brick openings, piers and spandrels')
    for i,part in enumerate(b.parts[start:],1):
        part['label']+=f' {i}'
        material_uv(part)
    for a,support in zip(ARCHES,masonry):
        n=a['index'];ts=np.radians(a['joint_angles_degrees'])
        b.prism(support,-DEPTH,-.027,front,JOINT,f'Arch {n} | recessed mortar and intrados')
        for j,(left,right) in enumerate(zip(ts,ts[1:])):
            mid=(left+right)/2
            key=abs(mid-np.pi/2)<.073
            # Square-edged group of slightly proud bricks under each crown.
            width=a['band_width_m']+(.035 if key else 0.)
            gap=min(np.radians(.085),(right-left)*.13)
            section=arch_band(a,left+gap,right-gap,-.026 if key else -.004,width,1 if lod else 2)
            section=section.intersection(box(limits[n-1],0.,limits[n],4.79))
            b.prism(section,-DEPTH-.002,.036 if key else .009,front,RINGS[a['brick_tone'][j]],
                    f'Arch {n} | '+('crown brick ' if key else 'radial brick ')+str(j+1))
    for pi,(left,right) in enumerate([(0.,ARCHES[0]['left']),*[(a['right'],z['left']) for a,z in zip(ARCHES,ARCHES[1:])],
                                      (ARCHES[-1]['right'],FRONT_END)],1):
        b.box(((left+right)/2,DEPTH/2,.046),(right-left+.046,DEPTH+.085,.092),SILL,label=f'South arcade | low foot {pi}')
# The main front has seven visible shafts per complete bay. A short rail turns
# toward the west wall. Two winter 2020 street views resolve six shafts on
# the short return, including the area behind the lantern in the 2024 image.
PROFILE=[(5.106,.114),(5.146,.109),(5.200,.084),(5.264,.073),(5.305,.071),
         (5.340,.091),(5.365,.119),(5.392,.089),(5.455,.090),(5.515,.084),
         (5.618,.077),(5.720,.068),(5.809,.056),(5.910,.045),(5.993,.047),
         (6.041,.061),(6.073,.094),(6.103,.111),(6.148,.113)]
SHAFT_Y=.17
def turned(b,x,y,far,name):
    # The profile was measured on the plane of the visible parapet. Correct
    # for its physical offset from the arcade face in the original camera.
    eye_z=2.425;offset=SHAFT_Y/12.703
    z=lambda h:h+(h-eye_z)*offset
    d=.232
    for lo,hi,label in [(5.010,5.109,'square foot'),(6.145,6.225,'square capital')]:
        b.box((x,y,(z(lo)+z(hi))/2),(d,d,z(hi)-z(lo)),BASE,label=name+' | '+label)
    kept=[PROFILE[i] for i in (0,2,4,6,8,11,13,15,16,18)] if far else PROFILE
    b.lathe((x,y),[(z(h),r) for h,r in kept],SPINDLE,10 if far else 20,name+' | turned stem')
def add_terrace(b,lod):
    # The copings and cornices turn the same corner as the rail. Each section
    # is one L-shaped extrusion, avoiding intersecting mitres.
    for z0,z1,width,mat,title in [
        (4.735,4.827,.38,DRIP,'brick arcade to stone drip'),(4.827,4.898,.46,SILL,'lower stone band'),
        (4.898,5.060,.37,CAP,'balustrade sill'),(6.216,6.325,.32,CAP,'closed top rail'),
        (6.325,6.497,.39,CAP,'upper cap')]:
        t=width/2;cy=SHAFT_Y;cx=.17
        outline=box(cx-t,cy-t,FRONT_END+.035,cy+t).union(box(cx-t,cy-t,cx+t,REAR))
        b.plan_prism(outline,z0,z1,mat,'South and west terrace | '+title)
    groups=[];eye_x=-1.374
    for first in (.895,5.222,9.093,13.032):
        spacing=.431 if first>8 else .435
        ys=[(x+(x-eye_x)*SHAFT_Y/12.703) for x in [first+spacing*i for i in range(7)]]
        groups.append(ys)
    gaps=[(0.,groups[0][0]-.240),*[(last[-1]+.24,following[0]-.24) for last,following in zip(groups,groups[1:])],
          (groups[-1][-1]+.24,FRONT_END)]
    for n,(l,r) in enumerate(gaps,1):
        if r<=l:continue
        b.box(((l+r)/2,.185,5.645),(r-l,.43,1.195),FACE,label=f'South parapet | brick pier {n}')
        material_uv(b.parts[-1])
    for n,g in enumerate(groups,1):
        for j,x in enumerate(g,1):turned(b,x,SHAFT_Y,lod,f'South terrace {n} | baluster {j}')
    for i,y in enumerate(np.linspace(.84,3.20,6),1):turned(b,.17,y,lod,f'West terrace return | baluster {i}')
    b.box((.17,3.525,5.645),(.43,.391,1.195),FACE,label='West parapet | pier at rear wall')
    material_uv(b.parts[-1])
    b.box((FRONT_END/2,(REAR+DEPTH)/2,4.82),(FRONT_END,REAR-DEPTH,.24),SILL,label='Gallery terrace slab behind arches')
    b.box((FRONT_END/2,REAR/2,-.067),(FRONT_END,REAR+.08,.134),SILL,label='Garden gallery | exterior landing')
def add_arcade(b,lod=False):
    texture();b.palette.update({k:dict(v) for k,v in PALETTE.items()})
    make_arch_wall(b,lod);add_terrace(b,lod)
