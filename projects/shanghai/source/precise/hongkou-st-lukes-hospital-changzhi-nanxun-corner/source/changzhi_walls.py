"""Five photographed street faces, a recessed gable wall, and the traced roof boundary."""
import json
from math import hypot
from pathlib import Path
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from changzhi_finish import STUCCO,TEXTURE
from changzhi_roof_crown import gable_street_span
import changzhi_sashes,changzhi_entrances
import changzhi_ground_panels

SOURCE=Path(__file__).parent
PANEL='Changzhi | slightly shaded plaster panels'
CAP='Changzhi | warm cast stone cornice'
SHADE='Changzhi | underside of plaster mouldings'
PLINTH='Changzhi | grey street base'
MEMBRANE='Changzhi | weathered grey roof finish'
PIPE='Changzhi | painted rainwater goods'
def paint(rgb,roughness,metallic=0.0):
    return dict(color=[((v/255+.055)/1.055)**2.4 for v in rgb],roughness=roughness,metallic=metallic)
PALETTE={STUCCO:dict(color=[1.,1.,1.],texture=str(TEXTURE),roughness=.96),
        PANEL:paint((184,179,173),.94),CAP:paint((206,201,193),.9),SHADE:paint((161,154,147),.95),
        PLINTH:paint((172,166,161),.97),MEMBRANE:paint((120,117,110),.97),PIPE:paint((78,77,72),.78,.12)}

def mapper(face):
    start,end=face['a'],face['b']
    dx,dy=end[0]-start[0],end[1]-start[1];length=hypot(dx,dy)
    tx,ty=dx/length,dy/length;nx,ny=face['out']
    def place(s,z,d):
        return start[0]+tx*s+nx*d,start[1]+ty*s+ny*d,z
    return place

def add_skin(b,face,shape,inner,outer,material,label):
    if not shape.is_empty and shape.area>1e-7:
        b.prism(shape,inner,outer,mapper(face),material,face['id']+' | '+label)

def moulding(b,face,a,e,z,sections,label):
    for index,(bottom,top,depth,material) in enumerate(sections):
        add_skin(b,face,box(a,z+bottom,e,z+top),-.015,depth,material,label+' '+str(index+1))

def add_walls(b,lod,layout):
    faces=layout['faces'];roof_heights=layout['eaves'];gable=gable_street_span(layout)
    ground=changzhi_entrances.opening_profiles(layout);upper=changzhi_sashes.opening_profiles(layout)
    rows=json.loads((SOURCE/'upper-window-layout.json').read_bytes())['rows']
    for face in faces:
        key=face['id'];length=face['length'];height=roof_heights[key]
        skin=box(0,0,length,height)
        if key=='changzhi':
            # The pediment module supplies its own perforated triangle and real oculus.
            skin=skin.difference(box(gable['s0'],gable['base_z'],gable['s1'],height+10.))
        shallow=changzhi_ground_panels.inset_faces(layout) if key=='nanxun' else []
        holes=unary_union([*ground.get(key,[]),*upper.get(key,[]),*shallow])
        if shallow:
            changzhi_ground_panels.add_sealed_panels(b,face,layout,add_skin,STUCCO,CAP)
        add_skin(b,face,skin.difference(holes),-.39,0.,STUCCO,'single perforated street wall')
        base=box(0,.015,length,.22).difference(holes)
        add_skin(b,face,base,-.012,.025,PLINTH,'pavement plinth')
        # Ground cornice is continuous around the visible chamfer. Its three distinct drops
        # are visible even where the newly repaired street photography displays obscure doors.
        moulding(b,face,0,length,layout['low_fascia'],[(-.12,0,.061,SHADE),(0,.085,.135,CAP),(.085,.156,.196,CAP),(.156,.202,.163,PANEL)],'ground cornice')
        belt=layout['intermediate'][key]
        if key=='changzhi':
            # The pediment has its own lower rake course, independent of the six arched bays.
            bands=[(0,gable['s0'],belt),(gable['s1'],length,gable['base_z']-.15)]
            eaves=[(0,gable['s0'],height),(gable['s1'],length,height)]
        else:bands=[(0,length,belt)];eaves=[(0,length,height)]
        for a,e,z in bands:
            if e-a>.04 and key=='changzhi':
                moulding(b,face,a,e,z,[(-.06,.09,.066,SHADE),(.09,.21,.113,PANEL),(.21,.30,.166,CAP),(.30,.39,.204,SHADE),(.39,.47,.235,CAP),(.47,.58,.262,CAP),(.58,.77,.284,PANEL)],'upper sill string')
        for a,e,z in eaves:
            if e-a>.04:
                moulding(b,face,a,e,z,[(-.17,-.11,.046,PANEL),(-.11,-.018,.10,SHADE),(-.018,.075,.14,CAP)],'eaves edge')
        if key=='changzhi':
            table={r['id']:r for r in rows if r['face']==key}
            for axis in range(1,7):
                r=table[f'changzhi/{axis}/3'];low=table[f'changzhi/{axis}/2']
                s0=r['center_fraction']*length;w=r['width_fraction']*length
                if axis<=3:
                    apron=box(s0-w*.57,low['crown']+.39,s0+w*.57,r['sill']-.045)
                    add_skin(b,face,apron.difference(holes),-.009,.026,PANEL,'drop apron below window '+str(axis))
                if axis==4:
                    trio=[table[f'changzhi/{j}/2'] for j in (4,5,6)]
                    left=(trio[0]['center_fraction']-trio[0]['width_fraction']*.60)*length
                    right=(trio[-1]['center_fraction']+trio[-1]['width_fraction']*.60)*length
                    z=sum(x['crown']for x in trio)/3.
                    add_skin(b,face,box(left,z+.35,right,z+.51),-.014,.092,CAP,'continuous lintel on three grouped windows')
                    for j,opening in enumerate(trio):
                        u=opening['center_fraction']*length
                        key_shape=Polygon([(u-.065,z+.005),(u+.065,z+.005),(u+.103,z+.39),(u-.103,z+.39)])
                        add_skin(b,face,key_shape,-.014,.094,CAP,'triple bay dropped key '+str(j+1))
        face_rows=[r for r in rows if r['face']==key]
        for r in face_rows:
            center=r['center_fraction']*length
            trim=bounds_for_trim(r,center,length)
            if not trim:continue
            for mat,shape,name in trim:
                add_skin(b,face,shape,-.009,.075 if name=='keystone' else .049,mat,name+' '+r['id'])
    # The three chamfer sections share both cornices with the Nanxun street side.
    # Buffer a single polyline to miter all the returns, including the centre projection.
    path=LineString([faces[1]['a']]+[f['b']for f in faces[1:]])
    z=layout['upper_fascia']
    for j,(a,e,d,material) in enumerate([(-.10,.04,.055,SHADE),(.04,.18,.105,PANEL),(.18,.27,.149,CAP),(.27,.34,.174,SHADE),(.34,.43,.211,CAP),(.43,.50,.226,SHADE),(.50,.61,.260,CAP),(.61,.82,.278,PANEL)]):
        strip=path.buffer(-d,single_sided=True,join_style='mitre').union(path.buffer(.012,single_sided=True,join_style='mitre'))
        b.plan_prism(strip,z+a,z+e,material,'Turning upper cornice | mitered course '+str(j+1))
    add_back_and_roof(b,layout,gable,lod)

def bounds_for_trim(r,s,length):
    level=r['level'];key=r['face'];axis=r['axis']
    # Both 2023 street faces show shallow keyed heads, with a visible separation
    # between the paired wings on the broad middle panel of the corner.
    if key=='changzhi' and (axis>6 or level==2 and axis>=4):return []
    w=r.get('width',r.get('width_fraction',0.)*length)
    if not w:return []
    top=r['crown']
    if level==4:
        return [(CAP,Polygon([(s-.11,top-.006),(s+.11,top-.006),(s+.16,top+.25),(s-.16,top+.25)]),'keystone')]
    left,right=s-w*.67,s+w*.67
    if key.startswith('corner'):rise=.055;low=.20;high=.33
    else:rise=.095;low=.23;high=.405
    if key=='changzhi' and level==2:
        return [(CAP,Polygon([(s-.065,top+.01),(s+.065,top+.01),(s+.12,top+.405),(s-.12,top+.405)]),'drop key')]
    # A shallow ogee in each arm is visible in both the 2016 sunny photograph and
    # the municipal 2023 plate. It stops short of the separately projecting key.
    def arm(start,end,flip):
        t=[0.,.16,.36,.70,1.]
        y=[-.65*rise,-.95*rise,-.40*rise,.08*rise,0.]
        if flip:y.reverse()
        edge=[(start+f*(end-start),top+low+v) for f,v in zip(t,y)]
        return Polygon(edge+[(u,v+high-low)for u,v in reversed(edge)])
    wing=arm(left,s-.09,False)
    other=arm(s+.09,right,True)
    stone=Polygon([(s-.075,top+.046),(s+.075,top+.046),(s+.12,top+high),(s-.12,top+high)])
    return [(CAP,wing,'left hood'),(CAP,other,'right hood'),(CAP,stone,'keystone')]

def add_back_and_roof(b,layout,gable,lod):
    faces=layout['faces'];ring=[f['a'] for f in faces]+[faces[-1]['b']]+layout['back_points']
    outline=Polygon(ring);front_height=layout['eaves']['changzhi'];upper=layout['eaves']['nanxun']
    b.plan_prism(outline,-.061,.001,PLINTH,'Sole | traced existing footprint')
    # The roof field sits below the street parapets and the round opening. The concealed
    # side of the gable remains clear. Roof finish and rear wall heights are estimates.
    deck_z=layout['roof_deck']
    deck=outline.buffer(-.34,join_style='mitre')
    b.plan_prism(deck,deck_z-.15,deck_z,MEMBRANE,'Roof | set-back roof field')
    for i,(a,e)in enumerate(zip(ring[len(faces):],ring[len(faces)+1:]+[ring[0]])):
        dx,dy=e[0]-a[0],e[1]-a[1];length=hypot(dx,dy)
        face=dict(id='return '+str(i+1),a=a,b=e,out=[dy/length,-dx/length])
        h=upper-.3 if i<7 else (upper+front_height)*.5-.32 if i==7 else front_height-.31
        add_skin(b,face,box(0,0,length,h),-.34,0,PANEL,'plain footprint closure')
        moulding(b,face,0,length,h,[(-.07,.04,.055,SHADE)],'roof weathering')
