"""Photographic street section of Denis Apartments, Nanjing West Road at Shimen Second Road."""
from pathlib import Path
import json
import math
import sys
import numpy as np
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from photo_architecture import Facade

P=json.loads((HERE/'parameters.json').read_bytes())
META={
    'id':P['id'],'name':P['name'],'status':'photo-informed-exterior','scope':P['scope'],
    'audit_directory':'data/audit/denis-apartments-v1/','viewer_page':'denis-apartments.html',
    'model_scope_zh':'德义大楼面向南京西路、石门二路的褐砖临街带，含商铺开间、转角二层石带、错色砖纹、竖向凸肋、窄钢窗及收分冠饰。未进入模型的背街部分与附近同孚大楼保留。原有四尊立像、历史招牌与住宅入口具体开间待查。',
    'coordinate_convention':P['source_frame'],'interiors_modeled':False,
}
COLORS={'umber face brick':(.469,.321,.211),'buff brick':(.586,.437,.290),'ochre brick':(.534,.379,.232),
    'dark firebrick':(.365,.246,.177),'maroon soldier brick':(.352,.219,.170),
    'incised granite band':(.575,.493,.418),'charcoal mortar':(.358,.302,.257),
    'grey green glass':(.210,.261,.258),'shaded glass':(.155,.187,.174),'dark steel casement':(.205,.202,.181),
    'light sash':(.445,.438,.377),'shop glass':(.169,.220,.211),'stone sill':(.552,.495,.402),
    'cream crown ornament':(.773,.692,.565),'weathered dark roof':(.350,.349,.317),
    'service metal':(.578,.581,.525),'fan shadow':(.289,.295,.272),'grey stone shop pier':(.466,.428,.365)}
PALETTE={name:dict(color=list(rgb),roughness=.30 if 'glass'in name else .82) for name,rgb in COLORS.items()}
CURVE=np.array(P['street_path_xy'])
DIST=np.linalg.norm(np.diff(CURVE,axis=0),axis=1)
STA=np.r_[0.,DIST.cumsum()]
# Straight runs and the returning corner are divided independently. The old tenant fascias
# do not determine the position of the apartment windows above them.
RUNS=[(0,12,'Nanjing'),(1,2,'Turn'),(2,1,'Turn'),(3,1,'Turn'),(4,1,'Turn'),(5,7,'Shimen')]
LEVELS=np.array([5.18,9.16,12.82,16.49,20.15,23.82,27.48,31.14,34.80])
PARAPET=38.42
TOWER=39.70


def panes(face,opening,depth,low,shop=False):
    xmin,zmin,xmax,zmax=opening.bounds
    w=xmax-xmin;h=zmax-zmin
    face.prism(opening.buffer(.005,join_style='mitre'),-depth-.026,-depth,'shop glass' if shop else 'grey green glass','recess glazing')
    frame=opening.difference(opening.buffer(-(.063 if shop else .048),join_style='mitre'))
    bars=[frame];columns=2 if low else (3 if shop else 4)
    for i in range(1,columns):
        x=xmin+i*w/columns;bars.append(box(x-.021,zmin,x+.021,zmax))
    for f in ([.70] if shop else ([.60] if low else [.32,.64])):
        z=zmin+h*f;bars.append(box(xmin,z-.022,xmax,z+.022))
    face.prism(unary_union(bars),-depth+.006,-depth+.058,'dark steel casement','window sash grid')
    if not shop:
        face.box(0,zmin-.063,w+.13,.091,.22,-.028,'stone sill','thin projecting sill')


def ornament(f,u,base,h):
    w=.16
    v=[(u-.045,base),(u-.045,base+h*.34),(u-w,base+h*.41),(u-.071,base+h*.48),
       (u-.068,base+h*.74),(u-.13,base+h*.78),(u,base+h),(u+.13,base+h*.78),
       (u+.068,base+h*.74),(u+.071,base+h*.48),(u+w,base+h*.41),(u+.045,base+h*.34),(u+.045,base)]
    f.prism(Polygon(v),.23,.267,'cream crown ornament','slender crown relief')


def variegated_tiles(face,wall,section,bay,low):
    """Raised selected headers and stretchers on the second floor and pier shafts."""
    if low:return
    rng=np.random.default_rng(3700+section*23+bay)
    w=face.length
    rows=range(0,30)
    by_material={name:[] for name in ('buff brick','ochre brick','dark firebrick')}
    for ri in rows:
        z=4.62+ri*.095
        for ci in range(math.ceil(w/.26)+1):
            u=-w/2+(ci+.5*(ri%2))*.26
            if rng.random()>.31:continue
            s=box(u,z,u+.223,z+.078).intersection(wall)
            if not s.is_empty and s.area>.002:
                name=list(by_material)[(ci+2*ri+bay)%3];by_material[name].append(s)
    for ri in range(45):
        z=8.76+ri*.62
        for side in (-1,1):
            u=side*(w/2-.32)
            if abs(u) + .15>w/2 or rng.random()>.66:continue
            by_material['ochre brick' if ri%3 else 'dark firebrick'].append(box(u-.098,z,u+.098,z+.066))
    for mat,patches in by_material.items():
        if patches:
            face.prism(unary_union(patches),.002,.016,mat,'mottled header courses')


def brick_facing(face, windows, shop, section, bay, low):
    """Model the contrasting fired headers, including brick colours above the shop course."""
    if low:return
    rng=np.random.default_rng(5800+section*41+bay)
    width=face.length
    exclusions=[w.bounds for w in [shop,*windows]]
    vertices={m:[] for m in ('buff brick','ochre brick','dark firebrick')}
    faces={m:[] for m in vertices}
    for row in range(292):
        z=8.36+row*.103
        if z>37.71:break
        for col in range(math.ceil(width/.252)+1):
            u=-width/2+(col+(row%2)*.5)*.252
            if not (-width/2+.005<=u and u+.219<=width/2-.005):continue
            if rng.random()>.23:continue
            if any(u<r+.045 and u+.219>l-.045 and z<t+.045 and z+.078>b-.045 for l,b,r,t in exclusions):continue
            material=rng.choice(('buff brick','ochre brick','dark firebrick'),p=(.29,.34,.37))
            verts=vertices[material];offset=len(verts)
            verts.extend([face.point(u,z,.008),face.point(u+.219,z,.008),face.point(u+.219,z+.078,.008),face.point(u,z+.078,.008)])
            faces[material].extend([(offset,offset+1,offset+2),(offset,offset+2,offset+3)])
    for material,verts in vertices.items():
        if verts:face.builder.add(verts,faces[material],material,face.label+'/upper brick facing')


def fan(face,u,z,low):
    face.box(u,z,.68,.49,.38,.18,'service metal','window air unit')
    if low:return
    face.box(u,z,.55,.36,.014,.377,'fan shadow','recessed unit grille')
    for j in range(6):face.box(u,z-.14+j*.055,.53,.014,.014,.389,'service metal','metal grille slat')


def bay_geometry(face,section,index,ordinal,low):
    w=face.length
    corner=section in (1,2,3,4);wider=section==0 and index in (3,8)
    shop=box(-w*.365,.14,w*.365,3.78);holes=[shop];windows=[]
    for floor,z in enumerate(LEVELS):
        width=min(w*.60,2.16 if floor==0 else 1.74)
        high=1.83 if floor in (0,7,8) else 1.67
        if corner and floor>=7:width*=.89
        win=box(-width/2,z,width/2,z+high);holes.append(win);windows.append(win)
    top=PARAPET
    wall=box(-w/2,.05,w/2,top).difference(unary_union(holes))
    face.prism(wall,-.48,0,'umber face brick','brick wall cut openings')
    panes(face,shop,.45,low,True)
    for i,window in enumerate(windows):panes(face,window,.24 if i<7 else .35,low)
    face.box(0,4.04,w,.43,.29,.025,'incised granite band','shop fascia and sill')
    face.box(0,4.37,w,.10,.45,.10,'stone sill','lower drip course')
    face.box(0,7.92,w,.43,.58,.12,'incised granite band','second floor stone band')
    face.box(0,8.20,w,.12,.61,.14,'stone sill','stone cap')
    if corner:
        face.box(0,30.89,w,.21,.14,.035,'incised granite band','upper corner string')
        face.box(0,34.55,w,.17,.18,.042,'stone sill','attic corner string')
        if section in (1,3) and index==0:ornament(face,w*.36,35.14,2.86)
    variegated_tiles(face,wall,section,index,low)
    brick_facing(face,windows,shop,section,index,low)
    for sign in (-1,1):
        u=sign*(w/2-.16)
        face.box(u,2.0,.306,3.92,.54,.028,'grey stone shop pier','retail stone pier')
        face.box(u,23.39,.34,30.24,.30,.063,'umber face brick','raised full height pier')
        face.box(u,31.48,.25,15.13,.40,.079,'ochre brick','stepped pier head')
        face.box(u,38.20,.27,1.02,.45,.10,'umber face brick','parapet upstand')
    if wider:
        face.box(0,38.21,w-.37,1.09,.42,.014,'umber face brick','raised street crest')
        face.box(0,39.51,w+.25,.36,1.15,.10,'stone sill','overhanging central canopy')
        for side in (-1,1):face.box(side*.77,38.79,.36,1.73,.59,.00,'dark firebrick','raised crest pier')
    if not low:
        for i,z in enumerate(LEVELS):
            if (ordinal*3+i*11)%13 in (1,3,5,9):fan(face,.22 if i%2 else -.21,z-.40,low)


def assemble(b,low=False):
    suffix={0:'South',1:'Arc A',2:'Arc B',3:'Arc C',4:'Arc D',5:'East'}
    n=0
    for section,num,_ in RUNS:
        start,end=CURVE[section],CURVE[section+1]
        for i in range(num):
            f=Facade(b,start+(end-start)*(i/num),start+(end-start)*((i+1)/num),suffix[section])
            bay_geometry(f,section,i,n,low);n+=1
    strip=Polygon(P['strip_xy'])
    b.plan_prism(strip,-.02,.13,'grey stone shop pier','Section/footing')
    b.plan_prism(strip,PARAPET-.58,PARAPET-.41,'weathered dark roof','Section/estimated roof')
    street=LineString(CURVE)
    for a,c in zip(P['strip_xy'],P['strip_xy'][1:]):
        mid=np.mean([a,c],axis=0)
        if street.distance(Point(mid))<.07:continue
        f=Facade(b,a,c,'Section rear')
        f.prism(box(-f.length/2,.09,f.length/2,PARAPET-.46),-.18,0,'dark firebrick','estimated closure')
    assert all(len(q['label'].encode())<60 for q in b.parts)


if __name__=='__main__':
    from final_preview import package
    package(build,HERE,META,PALETTE,assemble)
