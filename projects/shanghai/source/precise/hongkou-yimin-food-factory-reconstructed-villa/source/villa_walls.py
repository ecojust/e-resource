"""Visible front courtyard of the relocated, reduced villa at the Yimin Food Factory display."""
from pathlib import Path
import json
import math
import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import LineString, Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
PARAM=json.loads((HERE.parent/'measurements/villa-three-cameras.json').read_bytes())['parameters']
LAYOUT=json.loads((HERE.parent/'measurements/villa-roof-interface.json').read_bytes())
BRICK='Villa | running-bond red brick'
JOINT='Villa | arch lime mortar'
KEYS=['Villa | radial brick '+str(i+1) for i in range(6)]
CAST='Villa | warm grey concrete'
SILL='Villa | smooth grey sill'
TERR='Villa | oriel terracotta jambs'
DARK='Villa | dark stained frame'
GLASS='Villa | window glass'
ORIEL='Villa | window glass, warm reflections at right oriel'
SHADE='Villa | interior shadow'
METAL='Villa | brushed ramp railing'
FLOOR='Villa | entrance paving'
INLAY='Villa | narrow dark paving inlay'
HIGHLIGHT='Villa | recessed light face in spandrel'
SMOKE='Villa | portico smoked door glass'
SKY='Villa | pale glazing in upper oriel'
BLIND='Villa | dark horizontal blind slat'
HANDLE='Villa | aged metal window fastener'
def linear(rgb):
    t=np.asarray(rgb)/255.
    return np.where(t<=.04045,t/12.92,((t+.055)/1.055)**2.4).tolist()
PALETTE={n:{'color':linear(rgb),'roughness':rough} for n,rgb,rough in [
 (BRICK,(254,252,246),.91),(JOINT,(136,110,96),.94),(CAST,(162,149,141),.89),
 (SILL,(156,150,144),.78),(TERR,(135,73,57),.9),(DARK,(57,47,43),.53),
 (GLASS,(77,65,62),.32),(ORIEL,(117,94,78),.32),(SHADE,(56,48,45),.94),(METAL,(170,171,161),.39),
 (SMOKE,(51,54,53),.26),(SKY,(181,184,199),.37),(BLIND,(67,57,54),.90),(HANDLE,(133,115,94),.47),(INLAY,(145,139,137),.82),(FLOOR,(201,195,186),.88),(HIGHLIGHT,(167,160,149),.70),
 *[(m,c,.87) for m,c in zip(KEYS,[(137,68,54),(148,73,56),(155,82,61),(139,73,56),(163,83,62),(151,78,59)])]]}
PALETTE[GLASS].update(alpha=.70,metallic=.07)
PALETTE[ORIEL].update(alpha=.71,metallic=.06)
PALETTE[SMOKE].update(alpha=.84,metallic=.09)
PALETTE[SKY].update(alpha=.94,metallic=.06)
PALETTE[METAL]['metallic']=.47

def texture():
    """Original running bond with one 0.23 m stretcher and a 0.063 m course."""
    f=HERE/'replica-running-bond.png'
    if not f.is_file():
        w,h=1800,1024;im=Image.new('RGB',(w,h),(106,75,65));draw=ImageDraw.Draw(im)
        rng=np.random.default_rng(1940);cw,ch=18,5.25
        for row in range(math.ceil(h/ch)):
            y=round(row*ch)
            for col in range(-1,101):
                x=round(col*cw+(row%2)*cw/2)
                c=np.array((152,79,61))+rng.normal(0,3.3)+[rng.normal(0,3.5),0,0]
                rgb=tuple(np.clip(c,0,255).astype(int))
                draw.rectangle((x+1,y+1,x+int(cw)-1,round((row+1)*ch)-1),fill=rgb)
        im.quantize(80).save(f,optimize=True)
    PALETTE[BRICK]['texture']=str(f)

def texture_faces(part):
    """Project each face onto a plane with physical UV scale, including each jamb."""
    vv=np.asarray(part['vertices']);out=[];uv=[];ff=[];li={}
    for tri in part['triangles']:
        t=vv[list(tri)];normal=np.cross(t[1]-t[0],t[2]-t[0]);a=np.argmax(abs(normal));new=[]
        for index in tri:
            key=(a,index)
            if key not in li:
                li[key]=len(out);x,y,z=vv[index]
                if a==0:u,v=(y+8)/23.,(11.95-z)/12.288
                elif a==1:u,v=(x+11.5)/23.,(11.95-z)/12.288
                else:u,v=(x+11.5)/23.,(9-y)/12.288
                out.append(vv[index].tolist());uv.append((u,v))
            new.append(li[key])
        ff.append(tuple(new))
    part.update(vertices=out,triangles=ff,texcoords=uv)

def add_walls(b,lod=False,layout=None):
    """Build two projecting gables and the recessed three-bay portico in local metres."""
    low=lod in (True,'lod'); L=layout or LAYOUT;P=PARAM
    texture();b.palette.update(PALETTE)
    def prism(shape,plane,back,front,material,label):
        polygons = [shape] if shape.geom_type == 'Polygon' else shape.geoms
        for polygon in polygons:
            # Boolean subtraction can leave zero-area rings where two glazing bars meet.
            if polygon.geom_type != 'Polygon' or polygon.area < 1e-9:
                continue
            start = len(b.parts)
            b.prism(orient(polygon, sign=1.), back, front, plane, material, label)
            if material == BRICK:
                for part in b.parts[start:]:
                    texture_faces(part)
    def face(y):return lambda x,z,d:(x,y-d,z)
    def side(x):return lambda y,z,d:(x+d,y,z)
    def shell(x0,x1,bottom,top,cuts,plane,material,label):
        shape=box(x0,bottom,x1,top).difference(unary_union(cuts))
        prism(shape,plane,-.245,0,material,label)
    def beam(x0,x1,y0,y1,z0,z1,material,label):
        b.box([(x0+x1)/2,(y0+y1)/2,(z0+z1)/2],[x1-x0,y1-y0,z1-z0],material,label=label)
    def opening(center,a,level,rad,height,N):
        th=np.linspace(0,np.pi,N+1)
        return Polygon([(center-a,level),(center+a,level),*[(center+a*np.cos(t),height+rad*np.sin(t)) for t in th]])
    def pieces_glass(polygon,plane,columns,rows,label,*,depth=-.09,extra=(),glass_material=GLASS,back_material=SHADE):
        x0,z0,x1,z1=polygon.bounds
        rim=polygon.difference(polygon.buffer(-.045,join_style=2))
        vertical=[box(x-.022,z0-.1,x+.022,z1+.1)for x in columns]
        horizontal=[box(x0-.1,z-.024,x1+.1,z+.024)for z in rows]
        frame=polygon.intersection(unary_union([rim,*vertical,*horizontal,*extra]))
        prism(frame,plane,depth-.063,depth,DARK,label+' | timber frame and glazing bars')
        glass=polygon.difference(frame)
        prism(glass,plane,depth-.061,depth-.049,glass_material,label+' | recessed glazing')
        prism(polygon,plane,depth-.118,depth-.101,back_material,label+' | shadow behind glass')

    left=L['left'];right=L['right'];mid=L['arcade'];spring=P['spring'];rise=P['arch_rise']
    base=-P['deck'];arch_centers=[i*P['pitch']for i in (-1,0,1)];N=12 if low else 32
    cuts=[opening(cx,.875,0,rise,spring,N)for cx in arch_centers]
    spandrels=[]
    for cx in arch_centers:
        for direction in (-1,1):
            x=cx+direction*.84
            spandrels.append(Polygon([(x-.145,spring+rise+.128),(x+.145,spring+rise+.128),(x+direction*.145,spring+rise-.105)]))
    shell(mid['x_left'],mid['x_right'],0,mid['z_arcade_top']+.12,cuts+spandrels,face(0),BRICK,'Three-bay arcade | openings and triangular recesses')
    for j,shape in enumerate(spandrels):
        prism(shape,face(0),-.082,-.074,HIGHLIGHT,f'Arcade | triangular recessed backing {j+1}')
        lo,bot,hi,top=shape.bounds
        dark=shape.intersection(box(lo,top-.083,hi,top))
        prism(dark,face(0),-.074,-.069,SHADE,f'Arcade | recessed upper lip {j+1}')
    # The rear glazing is read through the arcade. Its setback is an estimate from
    # the visible lateral reveals. The tilt and divisions follow the 2018 photograph.
    setback=.78
    rear=[opening(cx,.82,.012,rise-.03,spring-.04,N)for cx in arch_centers]
    shell(mid['x_left'],mid['x_right'],0,mid['z_arcade_top']+.08,rear,face(setback),BRICK,'Portico | short back wall with three glazed openings')
    for j,(cx,ap) in enumerate(zip(arch_centers,rear),1):
        fan=[]
        for theta in np.radians([41,90,139]):
            fan.append(LineString([(cx,spring-.15),(cx+.90*np.cos(theta),spring-.15+.89*np.sin(theta))]).buffer(.013,cap_style=2))
        pieces_glass(ap,face(setback),[cx],[spring-.21,.86,.12],f'Portico | glazed door {j}',depth=-.038,extra=fan,glass_material=SMOKE)
        for k in (-1,1):
            beam(cx+k*.11-.014,cx+k*.11+.014,setback-.045,setback-.009,.79,1.06,METAL,f'Portico door {j} | pull handle')
        # Cast stone clads the vertical reveals on the front face only.
        for sign in (-1,1):
            x=cx+sign*.875
            lo,hi=sorted((x-sign*.009,x+sign*.074))
            beam(lo,hi,-.018,.244,0,spring,SILL,f'Arcade {j} | jamb lining {sign}')
        angles=np.linspace(0,np.pi,13 if low else 28)
        def band(t0,t1,dr,steps):
            aa=np.linspace(t0,t1,steps)
            return [(cx+(.875+dr)*math.cos(t),spring+(rise+dr)*math.sin(t)) for t in aa]
        prism(Polygon(band(0,np.pi,.164,N+1)+band(np.pi,0,0,N+1)),face(0),-.005,.020,JOINT,f'Arcade {j} | curved backing')
        for i,(u,v) in enumerate(zip(angles,angles[1:])):
            joint=.005
            prism(Polygon(band(u+joint,v-joint,.163,4)+band(v-joint,u+joint,.008,4)),face(0),.019,.031,
                  KEYS[(i*3+j+i//3)%len(KEYS)],f'Arcade {j} | radial brick {i+1:02d}')
    beam(mid['x_left'],mid['x_right'],-.37,setback+.16,-.092,0,FLOOR,'Paved portico landing')
    center_left=mid['x_left']+1.27
    for j in range(2):
        front=-.37-(j+1)*.32
        beam(center_left,mid['x_right'],front,front+.345,base-.05,-P['deck']*(j+1)/3,CAST,f'Approach | step {j+1}')
    ramp_left=mid['x_left']+.06;ramp_right=center_left-.06;front=-3.04
    mapping=lambda y,z,d:(ramp_right+d,y,z)
    prism(Polygon([(front,base-.095),(-.35,base-.095),(-.35,0),(front,base)]),mapping,ramp_left-ramp_right,0,CAST,'Approach | gently sloping ramp')
    for side_i,x in enumerate([ramp_right-.035,ramp_left+.04]):
        for q in [0,.52,1.]:
            y=front*(1-q)-.36*q;z=base*(1-q)
            b.tube([[x,y,z],[x,y,z+.80]],.021,METAL,6 if low else 10,f'Ramp | handrail {side_i+1} upright')
        for z in [.48,.81]:
            b.tube([[x,front,base+z],[x,-.36,z]],.021,METAL,6 if low else 10,f'Ramp | sloped handrail {side_i+1}')
    # Front gables have different width, projection, roof shoulder and window height.
    for is_left,wg in [(True,left),(False,right)]:
        plane=face(wg['y_face']);x0=wg['x_left'];x1=wg['x_right'];label='Left gable'if is_left else'Right gable'
        coords=[(x0,base),(x1,base),(x1,wg['z_inner_toe']),((x0+x1)/2,wg['z_ridge']),(x0,wg['z_inner_toe'])]
        cx=wg['oriel_center'];width=wg['oriel_glazing_width'];z0=wg['oriel_glazing_bottom'];z1=wg['oriel_glazing_top']
        front_y=wg['oriel_y'];y=wg['y_face'];offset=y-front_y
        cuts=[box(cx-width*.74,z0-.04,cx+width*.74,z1+.03)];other=[]
        if is_left:
            a=x1+P['left_window_center'];width0=P['left_window_w']
            # The second frame is visible at the left edge of Fig. 03. Its sill
            # and head align with the fully visible right-hand opening.
            for i,x in enumerate([a-2.43,a]):
                zlo=P['left_window_sill'];zhi=P['left_window_head']
                op=box(x-width0*.5,zlo,x+width0*.5,zhi);cuts.append(op);other.append((i,x,op,zlo,zhi))
        prism(Polygon(coords).difference(unary_union(cuts)),plane,-.245,0,BRICK,label+' | pierced red-brick front')
        shell(x0,x1,base,.045,[],face(y-.012),CAST,label+' | plinth course')
        for i,x,op,zlo,zhi in other:
            dz=zhi-zlo;extra=[box(x+off*width0-.012,zlo,x+off*width0+.012,zlo+.32*dz) for off in (-.25,.25)]
            pieces_glass(op,plane,[x],[zlo+dz*s for s in (.32,.68)],label+f' | front casement {i+1}',extra=extra)
            for block in (-1,1):
                xa=x+(.029 if block==1 else -width0*.5+.053);xb=x+(width0*.5-.053 if block==1 else -.029)
                for num,z in enumerate(np.arange(zlo+.045,zhi-.04,.081 if low else .041)):
                    beam(xa,xb,y+.152,y+.159,z,z+.009,BLIND,f'Front window {i+1} | horizontal blind course')
                fh=zlo+dz*.32
                beam(x+block*width0*.36-.009,x+block*width0*.36+.009,y+.047,y+.061,fh-.14,fh+.007,HANDLE,f'Front window {i+1} | lower catch')
            xlo,_,xhi,_=op.bounds
            prism(Polygon([(xlo-.10,zhi+.23),(xhi+.10,zhi+.23),(xhi+.04,zhi),(xlo-.04,zhi)]),
                  plane,-.01,.035,SILL,label+f' | tapered lintel {i+1}')
            beam(xlo-.067,xhi+.067,y-.105,y+.115,zlo-.081,zlo,SILL,label+f' | projecting sill {i+1}')
        # Front facet and its short splayed side lights are distinct panes.
        a=width*.5
        back=width*.79
        edges=[((cx-back,y-.012),(cx-a,front_y)),((cx-a,front_y),(cx+a,front_y)),((cx+a,front_y),(cx+back,y-.012))]
        plan=Polygon([(cx-back,y+.025),(cx-a,front_y),(cx+a,front_y),(cx+back,y+.025)])
        b.plan_prism(orient(plan,sign=1.),z0-.264,z0-.012,SILL,label+' | oriel sill block')
        b.plan_prism(orient(plan.buffer(.035,join_style=2),sign=1.),z0-.032,z0+.012,CAST,label+' | oriel sill lip')
        if is_left:
            for idx,x in enumerate([cx-a*.92,cx+a*.92]):
                beam(x-.071,x+.071,front_y+.027,y+.032,z0-.54,z0-.255,TERR,f'Upper oriel | sill bracket {idx+1}')
        else:
            b.plan_prism(orient(plan,sign=1.),base,z0-.26,CAST,'Right oriel | masonry base')
        for i,((xa,ya),(xb,yb)) in enumerate(edges):
            dx,dy=xb-xa,yb-ya;span=math.hypot(dx,dy);tx,ty=dx/span,dy/span
            mapper=lambda u,z,d,xa=xa,ya=ya,tx=tx,ty=ty:(xa+tx*u+ty*d,ya+ty*u-tx*d,z)
            full=box(0,z0,span,z1);rim=.058 if i==1 else .055
            sash=box(rim,z0+.035,span-rim,z1-.033)
            prism(full.difference(sash),mapper,-.085,.012,TERR,label+f' | oriel facet {i+1} surround')
            if is_left:cols=[span/2] if i==1 else [];levels=[]
            else:cols=[span/2] if i==1 else [];levels=[z0+(z1-z0)*v for v in (.44,.72)]
            if not is_left and i==1:
                extras=[box(span*v-.012,z0+(z1-z0)*.44,span*v+.012,z1) for v in (.33,.67)]
            else:extras=[]
            pieces_glass(sash,mapper,cols,levels,label+f' | oriel facet {i+1}',depth=-.006,extra=extras,glass_material=(SKY if i==1 else GLASS) if is_left else ORIEL)
        b.plan_prism(orient(plan.buffer(.025,join_style=2),sign=1.),z1-.002,z1+.11,TERR,label+' | top casing')
    # The inner face of the left wing has two independently visible ground-floor windows.
    sideplane=side(left['x_right']);ys=[P['side_near'],P['side_far']];half=P['side_width']/2
    apertures=[box(v-half,P['side_sill'],v+half,P['side_head']) for v in ys]
    shell(left['y_face']+.245,1.20,base,left['z_eave']+.12,apertures,sideplane,BRICK,'Left return | courtyard side with two cut windows')
    for i,(v,op)in enumerate(zip(ys,apertures)):
        pieces_glass(op,sideplane,[v],[P['side_sill']+(P['side_head']-P['side_sill'])*s for s in (.34,.73)],f'Courtyard | side window {i+1}')
        prism(box(v-half-.045,P['side_sill']-.075,v+half+.045,P['side_sill']),sideplane,-.09,.105,SILL,f'Courtyard | side sill {i+1}')
    # Right inner return is shortened by the observed much shallower right wing.
    inward=lambda u,z,d:(right['x_left']-d,-u,z)
    shell(-1.20,-right['y_face']-.245,base,right['z_eave']+.12,[],inward,BRICK,'Right return | visible courtyard wall')
    # Plain cut faces close the portion of the exterior shell visible in the photographs.
    rear=8.5
    shell(-rear+.245,-left['y_face']-.245,base,left['z_eave'],[],lambda u,z,d:(left['x_left']-d,-u,z),BRICK,'Left wing | outer return')
    shell(right['y_face']+.245,rear-.245,base,right['z_eave'],[],side(right['x_right']),BRICK,'Right wing | outer return')

    shell(-right['x_right'],-left['x_left'],base,min(left['z_eave'],right['z_eave']),[],
          lambda u,z,d:(-u,rear+d,z),BRICK,'Rear | plain cutoff at the aerial envelope')
    # The primary courtyard photograph shows grey parallel borders set into light paving.
    court=box(left['x_right'],left['y_face']-.28,right['x_left'],-.38)
    b.plan_prism(orient(court,sign=1.),base-.13,base-.025,FLOOR,'Courtyard | visible pavement between wings')
    for i,y in enumerate([-1.19,-1.31,-3.44,-3.56]):
        beam(center_left+.12,right['x_left']-.11,y,y+.036,base-.025,base-.019,INLAY,f'Courtyard | transverse stone inlay {i+1}')
    for i,x in enumerate([center_left+.13,center_left+.25,right['x_left']-.26,right['x_left']-.14]):
        beam(x,x+.034,left['y_face']-.27,-.45,base-.025,base-.018,INLAY,f'Courtyard | longitudinal stone inlay {i+1}')
