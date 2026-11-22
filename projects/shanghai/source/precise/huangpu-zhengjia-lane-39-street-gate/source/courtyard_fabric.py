"""Visible north-facing plaster facade and roofs at the end of Lane 39."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import box,Polygon
from courtyard_photo_plane import on_end,EYE
from material_names import MATERIAL

BASE=Path(__file__).resolve().parents[1]/'measurements'
F=json.loads((BASE/'courtyard-fabric-observations.json').read_bytes())
SIGN=json.loads((BASE/'housekeeping-paint.json').read_bytes())

def paint(rgb,r=.91,metal=0.):
    v=np.array(rgb)/255
    return dict(color=np.where(v<=.04045,v/12.92,((v+.055)/1.055)**2.4).tolist(),roughness=r,metallic=metal)
PLINTH='Courtyard front | cool grey plinth'
EAVE='Courtyard front | dark fascia and downpipes'
BOARD='Courtyard front | lime-painted soffit'
TERRAS=['Courtyard roof | muted red pantile '+str(i+1) for i in range(5)]
RIDGE='Courtyard roof | weathered ridge mortar'
COURT='Courtyard ground | warm grey concrete'
HOLLOW='Courtyard front | shadow inside the small gable'
STEEL='Courtyard front | ironwork and wall brackets'
GREEN='Courtyard sign | green enamel'
YELLOW='Courtyard sign | golden yellow lettering'
CLIPS='Courtyard sign | grey fixing plates'
UNIT='2015 courtyard | air-conditioner casing'
FAN='2015 courtyard | fan behind grille'
BARS='2015 courtyard | alloy grille'
PALETTE={COURT:paint([167,161,146]),PLINTH:paint([119,116,106]),EAVE:paint([58,52,45]),BOARD:paint([194,183,157]),RIDGE:paint([149,125,102]),HOLLOW:paint([66,54,43]),STEEL:paint([74,69,59],.74,.12),GREEN:paint([19,72,54],.72),YELLOW:paint([174,148,45],.81),CLIPS:paint([177,173,157],.67,.13),UNIT:paint([184,183,170],.82),FAN:paint([83,82,74],.76),BARS:paint([156,152,139],.69,.17)}
PALETTE.update({k:paint(rgb)for k,rgb in zip(TERRAS,[[131,77,57],[142,87,66],[123,75,60],[145,95,75],[117,70,52]])})

def face(b,shape,y0,y1,mat,label):
    b.prism(shape,-y1,-y0,lambda x,z,d:(x,-d,z),mat,label)

def pixshape(uv,y=0.):
    return Polygon([(x,z)for x,_,z in [on_end(u,v,y)for u,v in uv]])

def rect(b,x0,x1,y0,y1,z0,z1,mat,label):
    b.box([(x1+x0)/2,(y1+y0)/2,(z1+z0)/2],[x1-x0,y1-y0,z1-z0],mat,label=label)

def solid(b,vertices,faces,mat,label):
    v=np.array(vertices,float);m=v.mean(0);vol=0.
    for ring in faces:
        for i in range(1,len(ring)-1):
            a,c,d=v[[ring[0],ring[i],ring[i+1]]]-m;vol+=a@np.cross(c,d)
    b.add(v,[list(f) for f in faces]if vol>0 else [list(reversed(f))for f in faces],mat,label)

def flat_tile(b,points,h,mat,label):
    p=np.asarray(points);v=np.vstack([p,p-[0,0,h]]);n=len(p)
    solid(b,v,[list(range(n)),list(reversed(range(n,2*n))),*[[i,(i+1)%n,(i+1)%n+n,i+n]for i in range(n)]],mat,label)

def tiled_strip(b,front,back,lod,label,nx,ny):
    f=np.asarray(front);r=np.asarray(back);count=f.shape[0]
    def point(u,t):
        s=min(count-1.0000001,max(0,u*(count-1)));k=int(s);q=s-k
        return (1-t)*((1-q)*f[k]+q*f[k+1])+t*((1-q)*r[k]+q*r[k+1])
    for row in range(ny):
        t0=max(0,(row-.13)/ny);t1=(row+1)/ny
        for col in range(nx):
            uv=np.linspace(col/nx,(col+1)/nx,5 if lod else 9)
            vert=[]
            for t in (t0,t1):
                for i,u in enumerate(uv):
                    p=point(u,t);p[2]+=.014*np.cos(i*np.pi*2/(len(uv)-1))+.006*(row%2)
                    vert.append(p)
            top=np.array(vert);n=len(uv);vertices=np.vstack([top,top-[0,0,.030]])
            faces=[]
            for k in range(n-1):
                a,c,d,e=k,k+1,n+k+1,n+k
                faces.extend([[a,c,d,e],[2*n+e,2*n+d,2*n+c,2*n+a],[a,2*n+a,2*n+c,c],[e,d,2*n+d,2*n+e]])
            faces += [[0,n,3*n,2*n],[n-1,3*n-1,4*n-1,2*n-1]]
            solid(b,vertices,faces,TERRAS[(5*row+col*7+row*col)%5],f'{label} course {row+1:02d} tile {col+1:02d}')

def sign(b,lod):
    front=-.066
    face(b,pixshape(SIGN['green_board'],front),front,-.012,GREEN,'Green housekeeping sign backing')
    for r in SIGN['pigment']:
        def loop(points):return [(x,z)for x,_,z in [on_end(*p,front-.004)for p in points]]
        geom=Polygon(loop(r['shell']),[loop(o)for o in r['holes']])
        face(b,geom,front-.004,front+.001,YELLOW,'Enamel '+r['mark'])
    for i,uv in enumerate(SIGN['fasteners']):
        x,_,z=on_end(*uv,front-.007);rect(b,x-.026,x+.026,front-.010,front+.002,z-.026,z+.026,CLIPS,f'Housekeeping sign fixing plate {i+1}')

def services(b,lod):
    for j,a in enumerate(F['cooling_units']):
        surf=-.249
        shape=pixshape(a['corners'],surf);x0,z0,x1,z1=shape.bounds
        face(b,shape,surf,-.015,UNIT,f'Air conditioner {j+1} metal cabinet')
        x,_,z=on_end(*a['fan'],surf-.009);radius=(z1-z0)*.366
        b.tube([[x,surf+.003,z],[x,surf-.008,z]],radius,FAN,sides=24 if lod else 44,label=f'Air conditioner {j+1} fan')
        for k in range(-4,5):
            dx=radius*k/5;dz=(radius**2-dx**2)**.5
            rect(b,x+dx-.004,x+dx+.004,surf-.019,surf-.006,z-dz,z+dz,BARS,f'Air conditioner {j+1} grille {k+5}')
        for k,px in enumerate([x0+.05,x1-.05]):
            rect(b,px-.013,px+.013,-.258,.018,z0-.024,z0+.001,STEEL,f'Air conditioner {j+1} shelf bracket {k+1}')
    for j,axis in enumerate(F['drainpipe_axes']):
        pts=[on_end(*uv,-.075)for uv in axis]
        b.tube(pts,.043,EAVE,sides=9 if lod else 16,label=f'Wall drainpipe {j+1}')
    sign(b,lod)

def end_roof(b,lod):
    outer=[np.array(on_end(*uv,F['roof_front_y']))for uv in F['roof_front_edge']]
    edge=[outer[0]+t*(outer[1]-outer[0])for t in [0.,1/3,2/3,1.]]
    ridge=[np.array(on_end(*uv,y))for uv,y in zip(F['roof_upper_profile'],F['roof_upper_depth'])]
    tiled_strip(b,edge,ridge,lod,'Main roof',50,7)
    for i in range(3):
        b.tube([ridge[i]+[0,0,.024],ridge[i+1]+[0,0,.024]],.048,TERRAS[3],sides=8 if lod else 14,label=f'Visible ridge cap section {i+1}')
    feet=[np.array(on_end(*uv,F['roof_front_y']+.015))for uv in F['bottom_edge_of_eave']]
    face(b,Polygon([(x,z)for x,_,z in [outer[0],outer[1],feet[1],feet[0]]]),-.326,-.252,EAVE,'Black outer fascia at tiled eave')
    flat_tile(b,[feet[0],feet[1],feet[1]+[0,.63,.015],feet[0]+[0,.63,.015]],.039,BOARD,'Light painted projecting soffit')
    # The photographed lower ends of the stack disappear behind the front pitch.
    # Continue the masonry into the volume under those tiles so it also sits
    # correctly in an elevated inspection view.
    cheek=pixshape(F['chimney_face'],.022)
    x0,z0,x1,z1=cheek.bounds
    chimney=cheek.union(box(x0+.01,8.86,x1-.013,z0+.07))
    face(b,chimney,.022,.35,MATERIAL,'Roughcast rectangular chimney')
    face(b,pixshape(F['chimney_cap'],-.012),-.012,.387,PLINTH,'Stone projecting chimney cap')
    for j,uv in enumerate(F['roof_vents']):
        x,y,z=on_end(*uv,1.85)
        b.tube([[x,y,z-.252],[x,y,z]],.041,BOARD,sides=10 if lod else 16,label=f'Short roof vent {j+1}')

def low_east_wing(b,lod):
    # Preserve the visible portion of the right-hand wing as a cut section.
    obs=F['annex'];y=.1
    wall=pixshape(obs['front'],y)
    opening=pixshape(obs['opening_visible'],y)
    face(b,wall.difference(opening),y,y+.24,MATERIAL,'East low wing cut section')
    x0,z0,x1,z1=opening.bounds
    face(b,opening,y+.152,y+.17,HOLLOW,'East wing shaded window recess')
    for i in range(4):
        px=x0+(i+.35)*(x1-x0)/3.65
        rect(b,px-.008,px+.008,y+.04,y+.061,z0,z1,STEEL,f'East wing window grille {i+1}')
    rect(b,x0,x1,y+.03,y+.053,z0+(z1-z0)*.61-.012,z0+(z1-z0)*.61+.012,STEEL,'East wing grille transom')
    low=[on_end(*uv,y-.01)for uv in obs['plinth']]
    poly=Polygon([(low[0][0],-.15),(low[1][0],-.15),(low[1][0],low[1][2]),(low[0][0],low[0][2])])
    face(b,poly,y-.011,y+.002,PLINTH,'East wing plaster plinth')
    e=[np.array(on_end(*uv,y-.23))for uv in obs['main_eave']]
    upper=[np.array(on_end(*uv,depth)) for uv,depth in zip(obs['front_roof_head'],obs['front_roof_head_y'])]
    along=np.array(obs['front_roof_head'])[:,0]
    fraction=(along-along[0])/(along[-1]-along[0])
    eave=[e[0]+(e[1]-e[0])*value for value in fraction]
    tiled_strip(b,eave,upper,lod,'Low roof',29,5)
    lip=[np.array(on_end(*uv,depth)) for *uv,depth in obs['left_slope_lower']]
    crest=[np.array(on_end(*uv,depth)) for *uv,depth in obs['left_slope_upper']]
    tiled_strip(b,lip,crest,lod,'Low wing side pitch',17,7)
    b.tube(crest,.052,BOARD,sides=8 if lod else 14,label='Weathered capping tile over annex far roof edge')
    hip=[np.array(on_end(*uv,depth))for *uv,depth in obs['ridge_cap_right']]
    b.tube(hip,.055,BOARD,sides=8 if lod else 14,label='Annex south return pale hip tiles')
    at_gable=.713
    profile=pixshape(obs['gable_upper']+obs['gable_lower'],at_gable)
    face(b,profile,at_gable,at_gable+.12,BOARD,'East wing gable bargeboard')
    face(b,pixshape(obs['gable_inner'],at_gable+.090),at_gable+.090,at_gable+.131,HOLLOW,'Dark triangular reveal of east wing')
    face(b,pixshape(obs['awning'],y-.11),y-.11,y+.062,TERRAS[2],'East wing small red window hood')

def add_courtyard_fabric(b,lod=False):
    from courtyard_windows import openings
    feet=[on_end(*uv)for uv in F['wall_foot']]
    eave=[on_end(*uv,-.31)for uv in F['bottom_edge_of_eave']]
    left,right=[p[0]for p in feet]
    z0=min(p[2]for p in feet)
    boundary=Polygon([(left,z0-.03),(right,z0-.03),(right,eave[1][2]+.025),(left,eave[0][2]+.025)])
    for op in openings():
        boundary=boundary.difference(box(op['left'],op['bottom'],op['right'],op['top']))
    face(b,boundary,.0,.34,MATERIAL,'House north wall with eight measured openings')
    base=[on_end(*uv,-.015)for uv in F['wall_plinth_top']]
    face(b,Polygon([(left,z0-.029),(right,z0-.029),(right,base[1][2]),(left,base[0][2])]),-.015,.001,PLINTH,'Main house grey rendered plinth')
    end_roof(b,lod)
    services(b,lod)
    low_east_wing(b,lod)
    # The CC image shows paving immediately in front of the transverse house.
    # Only this photographed section is drawn; its far edge is a model cut.
    ground=Polygon([(left-.08,-3.40),(right+2.10,-3.40),(right+2.10,.29),(left-.08,.29)])
    b.prism(ground,-.105,-.030,lambda x,y,z:(x,y,z),COURT,'Photographed paving in front of courtyard facade')

