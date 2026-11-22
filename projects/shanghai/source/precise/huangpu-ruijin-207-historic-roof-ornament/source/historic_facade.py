"""The long columned elevation and its two-bay return recorded in the 1930s photographs."""
import json
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from scipy.optimize import brentq
from rosholt_front_plane import on_face,pixel
from material_names import MATERIAL

ROOT=Path(__file__).resolve().parents[1]/'measurements'
F=json.loads((ROOT/'historic-front-windows.json').read_bytes())
SIDE=json.loads((ROOT/'historic-two-view-registration.json').read_bytes())
secondary=np.asarray(SIDE['secondary_camera_matrix'])
hom=np.asarray(F['rectification']['homography_rectified_to_print'])
COLUMN='1930s exterior | smooth light round piers'
RAIL='1930s exterior | painted glazing bars'
SOFFIT='1930s exterior | shaded concrete reveals'
GLASS='1930s exterior | smoky glass in period photograph'
FROST='1930s exterior | mottled translucent glass units'
FROSTED='1930s exterior | lighter pressed glass units'
VOID='1930s exterior | dark inner recess'
VENT='1930s exterior | dark slots in spandrels'
CAP='1930s exterior | roof vent hoods'
METAL='1930s exterior | metal and fixing straps'
OPEN='1930s exterior | tilted projecting sash'
def grey(c,rough,metal=0):
    return dict(color=[((c/255+.055)/1.055)**2.4]*3,roughness=rough,metallic=metal)
PALETTE={COLUMN:grey(200,.85),RAIL:grey(188,.64,.10),SOFFIT:grey(133,.91),GLASS:grey(77,.33,.20),FROST:grey(134,.46,.14),FROSTED:grey(153,.48,.13),VOID:grey(48,.94),VENT:grey(61,.85),CAP:grey(129,.80),METAL:grey(96,.61,.30),OPEN:grey(207,.59,.13)}
def bounds(b,x0,x1,y0,y1,z0,z1,mat,label):
    b.box(((x0+x1)*.5,(y0+y1)*.5,(z0+z1)*.5),(x1-x0,y1-y0,z1-z0),mat,label=label)
def shell(b,shape,y0,y1,material,label):
    b.prism(shape,-y1,-y0,lambda x,z,d:(x,-d,z),material,label)
def rect_uv(u,v):
    p=hom@np.array([u,v,1.]);return p[:2]/p[2]
def rect_xyz(u,v,y=0.):
    return on_face(rect_uv(u,v),y)
def outline(pixels,y):
    return Polygon([(a[0],a[2])for a in [on_face(q,y)for q in pixels]])
def rect(l,t,r,bt,y):
    return outline([rect_uv(u,v)for u,v in [(l,t),(l,bt),(r,bt),(r,t)]],y)
def secondary_on(u,v,i,value):
    eq=secondary[:2]-np.array([[u],[v]])*secondary[2]
    cols=[j for j in range(3)if j!=i]
    q=np.zeros(3);q[cols]=np.linalg.solve(eq[:,cols],-eq[:,3]-value*eq[:,i]);q[i]=value
    return q

def projected_light(pixels):
    # The lower rail of a top-hung sash retains the hinge width. Derive depth from the apparent free corners.
    a,d=[on_face(q,.56)for q in pixels[:2]]
    depths=[]
    for q,hinge in zip(pixels[2:],[d,a]):
        depths.append(brentq(lambda y:on_face(q,y)[0]-hinge[0],-.8,.5))
    low_y=float(np.mean(depths))
    return [a,d,on_face(pixels[2],low_y),on_face(pixels[3],low_y)]

def wall_and_columns(b,lod):
    y=.125
    end0=-22.23;end1=22.40
    apertures=[outline(row['corners_px'],y)for row in F['regular_windows']]
    # Shallow front skin follows the windows' observed edges. The cut stays open along the old camera rays.
    holes=[p.buffer(.031,join_style=2)for p in apertures]
    centre_cut=outline(F['central_dark_opening_px'],y)
    holes.append(centre_cut.buffer(.072,join_style=2))
    for l,t,r,bt in [F['stair_glass']['near_strip_rectified'],F['stair_glass']['far_strip_rectified']]:
        holes.append(rect(l,t,r,bt,y).buffer(.05,join_style=2))
    for row in F['photographed_vent_slots']:holes.append(rect(*row['rectified_bounds'],y))
    pocket_rows=[]
    for row in F['regular_windows']:
        i=row['bay']-1; tier=row['tier_from_top']-1
        l,t,r,bt=row['rectified_bounds']
        col,diam=F['round_front_piers'][i+1]
        right=col-diam/2+.80
        if right>r+3:
            lower=[291,402,493][tier]
            outline_=rect(r,bt+.10,right,lower,y)
            holes.append(outline_);pocket_rows.append((i,tier,r,bt,right,lower))
    wall=box(end0,-12.53,end1,-1.70).difference(unary_union(holes))
    shell(b,wall,y,y+.047,MATERIAL,'Historic frontage | pierced wall and wider centre bay')
    for i,tier,r,top,right,low in pocket_rows:
        label=f'Spandrel {i+1}.{tier+1}'
        recess=rect(r,top,right,low,.57)
        shell(b,recess.buffer(.04,join_style=2),.57,.61,SOFFIT,label+' | recessed side surface')
        # Separate squared return of the light spandrel into the original shadow gap.
        outer=rect(r-.06,top,r+.06,low,y)
        rear=rect(r-.06,top,r+.06,low,.58)
        l0,z0,l1,z1=outer.bounds;rx0,rz0,rx1,rz1=rear.bounds
        poly=Polygon([(l0,y),(l1+.03,y),(rx1+.03,.58),(rx0,.58)])
        b.plan_prism(poly,min(z0,rz0),max(z1,rz1),SOFFIT,label+' | deep jamb')
    for tier,v in enumerate([186,294,405]):
        for i,(left,width) in enumerate(F['round_front_piers'][:-1]):
            right=F['round_front_piers'][i+1][0]
            shell(b,rect(left,v-1.1,right,v+1.0,-.027),-.027,.32,COLUMN,f'Level {tier+1} bay {i+1} | narrow forward floor edge')
    for k,row in enumerate(F['regular_windows']):
        l,t,r,bt=row['rectified_bounds'];frame=.58
        label=f"Bay {row['bay']}, tier {row['tier_from_top']}"
        bnds=outline(row['corners_px'],frame+.071)
        glass=bnds.buffer(.095,join_style=2)
        if row['tier_from_top']==1 and row['bay'] in (1,4):
            v1,v2=row['transoms_rectified_y_px']
            k=0 if row['bay']==1 else 1
            rods=row['mullions_rectified_x_px']
            if k==0:a,d=rods[:2]
            else:a,d=rods[1:3]
            light=rect(a+1.0,v1+1.0,d-1.0,v2-1.0,frame+.071)
            glass=glass.difference(light)
            # The partly opened sash exposes a shallow, dark unmodelled interior between its free rail and the fixed frame.
            backing=rect(a-8,v1-6,d+8,v2+6,1.40)
            shell(b,backing,1.40,1.44,VOID,label+' | shadow behind top-hung light')
        shell(b,glass,frame+.071,frame+.108,GLASS,label+' | dark window plane')
        # Thick reveals follow the two edges in the photograph. The smoothed interior is inferred.
        a=outline(row['corners_px'],y+.039);c=outline(row['corners_px'],frame+.12)
        apts=a.exterior.coords[:-1];cpts=c.exterior.coords[:-1]
        for j in range(4):
            k1=(j+1)%4
            near=[(apts[m][0],y+.039,apts[m][1])for m in (j,k1)]
            far=[(cpts[m][0],frame+.12,cpts[m][1])for m in (j,k1)]
            vs=np.asarray([*near,far[1],far[0]])
            normal=np.cross(vs[1]-vs[0],vs[2]-vs[0]);normal/=np.linalg.norm(normal)
            b.add(np.vstack([vs,vs-normal*.024]),[(0,1,2,3),(7,6,5,4),(1,0,4,5),(2,1,5,6),(3,2,6,7),(0,3,7,4)],SOFFIT,label+f' | recess return {j+1}')
        for i,u in enumerate([l,*row['mullions_rectified_x_px'],r]):
            shell(b,rect(u-.71,t,u+.71,bt,frame),frame,frame+.065,RAIL,label+f' | upright {i+1}')
        for i,v in enumerate([t,*row['transoms_rectified_y_px'],bt]):
            shell(b,rect(l,v-.73,r,v+.73,frame-.016),frame-.016,frame+.040,RAIL,label+f' | transom {i+1}')
    for row in F['photographed_vent_slots']:
        p=rect(*row['rectified_bounds'],.255)
        shell(b,p.buffer(.052,join_style=2),.255,.292,VENT,f"Bay {row['bay']} tier {row['tier']} | recessed vent")
    for i,(u,w) in enumerate(F['round_front_piers']):
        x=rect_xyz(u,250)[0];radius=w/64
        b.tube([(x,.115,-12.58),(x,.115,-1.65)],radius,COLUMN,12 if lod else 32,f'Historical frontage | round pier {i+1}')
    # The stained or patterned glass strips are visible on both ends. The relief pitch approximates the original glass-block coursing.
    for tag,(l,t,r,bt) in [('west',F['stair_glass']['near_strip_rectified']),('east',F['stair_glass']['far_strip_rectified'])]:
        plate=rect(l,t,r,bt,.32);x0,z0,x1,z1=plate.bounds
        bounds(b,x0-.025,x1+.025,.325,.381,z0,z1,FROST,tag+' | translucent stair-light bedding')
        nx=round((x1-x0)/.18);nz=round((z1-z0)/.18)
        if not lod:
            for ix in range(nx):
                for iz in range(nz):
                    l0,l1=x0+(x1-x0)*ix/nx,x0+(x1-x0)*(ix+1)/nx
                    zlo,zhi=z0+(z1-z0)*iz/nz,z0+(z1-z0)*(iz+1)/nz
                    bounds(b,l0+.010,l1-.010,.294+(ix+iz)%3*.002,.326,zlo+.010,zhi-.010,FROSTED if (ix+iz*3)%7 in (1,3,4) else FROST,tag+' | individual pressed glazing units')
        for ix in range(4):
            x=x0+(x1-x0)*ix/3
            bounds(b,x-.044,x+.044,.238,.329,z0-.010,z1+.010,RAIL,tag+f' stair light | tall mullion {ix+1}')
        for iz in range(7):
            z=z0+(z1-z0)*iz/6
            bounds(b,x0-.039,x1+.039,.225,.335,z-.052,z+.052,RAIL,tag+f' stair light | cross-frame {iz+1}')
    for i,pixels in enumerate(F['open_top_hung_lights']):
        points=projected_light(pixels)
        vs=np.array(points);normal=np.cross(vs[1]-vs[0],vs[2]-vs[0]);normal/=np.linalg.norm(normal)
        pane=vs.mean(axis=0)+(vs-vs.mean(axis=0))*.935
        b.add(np.vstack([pane,pane-normal*.012]),[(0,1,2,3),(7,6,5,4),(1,0,4,5),(2,1,5,6),(3,2,6,7),(0,3,7,4)],GLASS,f'Open upper light {i+1} | inclined glass')
        for j in range(4):b.tube([vs[j],vs[(j+1)%4]],.030,OPEN,6 if lod else 12,f'Open upper light {i+1} | edge {j+1}')

def side_return(b,lod):
    # Entrance-court side view. The two vertical reveals and intervening pier are directly visible in the second photograph.
    front_x=SIDE['corners']['near_arris_x_m']
    e=SIDE['corners'];end_y=e['far_eave_xyz_m'][1]
    bands=[[(115,118),(155,99),(155,150),(115,163)],[(162,94),(181,85),(181,142),(162,149)],[(116,189),(154,174),(154,217),(116,228)],[(162,172),(181,166),(181,211),(162,217)],[(115,260),(154,253),(154,294),(115,297)],[(162,252),(181,249),(181,287),(162,292)]]
    wall=box(0.,-12.9,end_y,-1.66);holes=[]
    for i,pix in enumerate(bands):
        projected=[secondary_on(*pt,0,front_x)for pt in pix]
        p=Polygon([(a[1],a[2])for a in projected]);holes.append(p)
        # The shadowed floor-level glazing at the foot of the return is partially hidden in the reference.
        projected=[secondary_on(*pt,0,front_x+.50)for pt in pix]
        far=Polygon([(a[1],a[2])for a in projected]);a,c,d,e=far.bounds
        b.prism(far.buffer(.04,join_style=2),front_x+.52,front_x+.57,lambda y,z,x:(x,y,z),GLASS,f'Return bay {i%2+1} tier {i//2+1} | glass')
        for j in range(1,4):
            cut=far.intersection(box(a+(d-a)*j/4-.03,c-.01,a+(d-a)*j/4+.03,e+.01))
            b.prism(cut,front_x+.45,front_x+.54,lambda y,z,x:(x,y,z),RAIL,f'Return window {i+1} | vertical division {j}')
        for j in (1,2):
            cut=far.intersection(box(a-.01,c+(e-c)*j/3-.03,d+.01,c+(e-c)*j/3+.03))
            b.prism(cut,front_x+.445,front_x+.53,lambda y,z,x:(x,y,z),RAIL,f'Return window {i+1} | horizontal division {j}')
    b.prism(wall.difference(unary_union(holes)),front_x,front_x+.15,lambda y,z,x:(x,y,z),MATERIAL,'Two-bay end elevation and smooth corner pier')
    bounds(b,front_x+.16,front_x+.91,end_y-.16,end_y+.06,-12.9,-1.68,SOFFIT,'Back edge of the documented short return')

def parapet(b,lod):
    # The shallow parapet lies behind the lip of the main eave. Its position leaves the historic roof ornament exposed.
    x0,x1=-22.23,22.43;y=.17
    bounds(b,x0,x1,y,y+.30,-1.76,-.019,MATERIAL,'Long planar rendered parapet')
    bounds(b,x0-.055,x1+.14,-.190,.62,-1.716,-1.622,COLUMN,'Overhanging thin eave on the nine-bay frontage')
    bounds(b,x0-.025,x0+.275,.20,10.77,-1.77,-.014,MATERIAL,'Short returning parapet photographed in profile')
    bounds(b,x0-.17,x0+.61,-.16,10.85,-1.716,-1.622,COLUMN,'Thin eave around short return')
    bounds(b,x0+.21,x1,.48,1.30,-1.50,-1.38,SOFFIT,'Front edge of flat roof behind parapet')
    for i,(u,v) in enumerate([(196,133),(311,153),(412,171),(503,187),(689,217),(753,229),(815,240),(872,251)]):
        p=on_face([u,v],y-.017)
        bounds(b,p[0]-.235,p[0]+.235,y-.028,y-.004,p[2]-.031,p[2]+.031,VENT,f'Parapet | observed horizontal dark inset {i+1}')
    for i,(u,v) in enumerate([(132,125),(360,166),(546,196),(651,212),(784,235),(895,254)]):
        p=on_face((u,v),y-.044)
        b.tube([p-[0,0,.113],p+[0,0,.12]],.045,METAL,8 if lod else 14,f'Parapet | surviving vertical metal fixing {i+1}')
    # The near end stack has a broad plain face and a flat projecting hood. The greater part of the face is clipped by the print margin.
    left=.98
    lx0,lx1=on_face((-16,20),left)[0],on_face((78,42),left)[0]
    z=on_face((74,32),left)[2]
    bounds(b,lx0,lx1,left,left+1.54,-.19,z-.13,MATERIAL,'Near roof pavilion | broad rendered cheek')
    bounds(b,lx0-.25,lx1+.41,left-.22,left+1.87,z-.13,z+.044,CAP,'Near roof pavilion | broad oversailing hood')
    # The right chimney has two square ventilation holes, one in each visible face.
    front=1.21
    a=on_face((876,168),front);d=on_face((899,172),front)
    x0,x1=a[0],d[0];zt=(a[2]+d[2])*.5;zb=on_face((884,200),front)[2]
    def back_error(y):
        at=pixel((x0,y,zt));return (at[0]-849)**2+(at[1]-175)**2
    from scipy.optimize import minimize_scalar
    back=minimize_scalar(back_error,bounds=(front+.2,front+4),method='bounded').x
    width=x1-x0
    bounds(b,x0-.12,x1+.13,front,back,-.22,zb-.05,MATERIAL,'Far roof vent | rectangular plinth')
    bounds(b,x0-.39,x1+.38,front-.20,back+.23,zb-.135,zb+.025,CAP,'Far roof vent | broad lower shoulder')
    throat=box(x0,zb,x1,zt).difference(box(x0+width*.41,zt-.43,x0+width*.68,zt-.10))
    shell(b,throat,front,front+.14,MATERIAL,'Far roof vent | light face with actual square opening')
    side=box(front,zb,back,zt).difference(box(front+(back-front)*.39,zt-.56,front+(back-front)*.64,zt-.27))
    b.prism(side,x0,x0+.145,lambda y,z,x:(x,y,z),CAP,'Far roof vent | shaded side with second square opening')
    bounds(b,x1-.14,x1,front+.12,back-.13,zb,zt,CAP,'Far roof vent | inner return')
    bounds(b,x0,x1,back-.14,back,zb,zt,CAP,'Far roof vent | back of hood')
    bounds(b,x0-.25,x1+.26,front-.16,back+.18,zt,zt+.13,CAP,'Far roof vent | oversailing flat hood')
    # Only the mast portions visible in the dated photograph are continued above the measured ornament.
    a=on_face((597,110),.055);b0=on_face((591,1.0),.055)
    b.tube([a,b0],.041,METAL,8 if lod else 16,'Mast | upper observed length to the edge of the historic print')

def add_facade(b,lod=False):
    wall_and_columns(b,lod)
    side_return(b,lod)
    parapet(b,lod)
