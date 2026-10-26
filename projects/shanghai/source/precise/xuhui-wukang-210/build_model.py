#!/usr/bin/env python3
"""210 Wukang Road: photograph-led candidate, original city footprint preserved.
Photos establish visible features, not surveyed dimensions. No network/Blender.
"""
import argparse, hashlib, json, math, sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, LineString, box, shape
from shapely.ops import unary_union
from shapely.geometry.polygon import orient
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'common'))
from photo_architecture import Builder, Facade, opening, pieces
from curved_prism import curved_prism

def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def window(f,poly,label,cols=2,rows=3,arch=0,glass='estimated muted glass',sill=True):
    x0,z0,x1,z1=poly.bounds;inner=poly.buffer(-.052,join_style=2);bars=[];spring=z1-arch
    for i in range(1,cols):
        x=x0+(x1-x0)*i/cols;bars.append(box(x-.014,z0,x+.014,spring))
    for i in range(1,rows):
        z=z0+(spring-z0)*i/rows;bars.append(box(x0,z-.014,x1,z+.014))
    if arch:bars.append(box(x0,spring-.019,x1,spring+.019))
    clear=inner.difference(unary_union(bars));f.prism(poly.buffer(-.008).difference(clear),-.115,-.035,'black joinery',label+'-frame')
    for i,p in enumerate(pieces(clear)):f.prism(p,-.077,-.057,glass,label+f'-glass-{i}')
    if sill:f.box((x0+x1)/2,z0-.04,x1-x0+.13,.08,.18,.025,'red painted coping',label+'-sill')
    return {'label':label,'opening':list(poly.exterior.coords),'facade_origin':f.center.tolist(),'facade_u':f.t.tolist(),'facade_out':f.n.tolist(),'frame_depth':[-.115,-.035],'glass_depth':[-.077,-.057],'glass_recess_from_frame_front_m':.022}

def audit_parts(b):
    bad=[];mins=[];ntris=0
    for p in b.parts:
        v=np.asarray(p['vertices'],np.float32).astype(float);t=np.asarray(p['triangles']);a,c,d=v[t[:,0]],v[t[:,1]],v[t[:,2]];areas=np.linalg.norm(np.cross(c-a,d-a),axis=1)/2;vol=np.einsum('ij,ij->i',a,np.cross(c,d)).sum()/6
        # Position-weld vertices before edge counting: prism vertices retain identities.
        _,inv=np.unique(v,axis=0,return_inverse=True);tt=inv[t];edges={}
        for tri in tt:
            for x,y in zip(tri,np.roll(tri,-1)):
                k=(min(x,y),max(x,y));co,bal=edges.get(k,(0,0));edges[k]=(co+1,bal+(1 if x<y else -1))
        edge_bad=sum(c!=2 or balance!=0 for c,balance in edges.values());ntris+=len(t);mins.append(float(areas.min()))
        if areas.min()<=1e-12 or vol<=1e-12 or edge_bad:bad.append({'label':p['label'],'area_min':float(areas.min()),'signed_volume':float(vol),'bad_edges':edge_bad})
    return {'passed':not bad,'parts':len(b.parts),'triangles':ntris,'bad_parts':bad,'min_triangle_area_m2':min(mins),'scope':'Every authored solid independently FLOAT32-welded edge pairing, positive volume and nonzero triangle area; not a union/interior-space survey.'}

def build(out):
    g=json.loads((HERE/'geometry-input.json').read_text());cal=json.loads((HERE/'calibration-model.json').read_text());fr=g['facade_frame'];origin=np.asarray(fr['origin_local_east_north_m']);X=np.asarray(fr['u_east_north'])*fr['photographic_left_to_right_native_u_sign'];Y=np.asarray(fr['inward_v_east_north']);W=fr['front_width_m'];scale=W/14.242
    def point(x,y,z=0):q=origin+X*x+Y*y;return np.array([q[0],q[1],z])
    # x is photographic left-to-right; y is behind street-facing wall.
    b=Builder({'cream stippled render':{'color':[.67,.66,.57],'roughness':.94},'red painted coping':{'color':[.38,.105,.065],'roughness':.70},'terracotta tile':{'color':[.43,.19,.11],'roughness':.9},'tile edge':{'color':[.33,.14,.08],'roughness':.9},'black joinery':{'color':[.055,.06,.055],'roughness':.52,'metallic':.28},'estimated muted glass':{'color':[.19,.22,.215],'roughness':.24,'metallic':.20},'curtain glass':{'color':[.38,.39,.35],'roughness':.45,'metallic':.1},'wood entry':{'color':[.20,.105,.055],'roughness':.8},'gray cement':{'color':[.43,.43,.39],'roughness':.87},'plate green':{'color':[.045,.17,.12],'roughness':.7},'plate letters':{'color':[.78,.79,.67],'roughness':.72},'service pale':{'color':[.68,.67,.57],'roughness':.82}})
    def facade(a,c,label):return Facade(b,point(*a)[:2],point(*c)[:2],label)
    def prism(poly,lo,hi,material,label):b.prism(poly,lo,hi,lambda x,y,z:point(x,y,z),material,label)
    def line(coords,r,material,label,sides=8):b.tube([point(*p) for p in coords],r,material,sides,label)
    left=-W/2;right=W/2;L=-2.40*scale;R=2.05*scale;depth=7.15
    original=shape(g['model_geometry_local_east_north_m']);b.plan_prism(original,-.12,0,'gray cement','source-footprint-foundation')
    F=facade((left,0),(right,0),'street-ground-and-wings');records=[];holes=[]
    # Lower front is one continuous surface. Upper wing profiles extend from it.
    door=opening(-.20*scale,.05,1.12,2.35,.56,32);holes.append(door)
    rightxs=[4.24*scale,5.20*scale,6.16*scale]
    for i,x in enumerate(rightxs):
        p=opening(x,.80,.48,1.26);holes.append(p);records.append(window(F,p,f'north-ground-triple-{i}',1,2,sill=False))
        # Outer anti-intrusion bars observed, separate from the recessed frames.
        for dx in [-.13,0,.13]:line([(x+dx,-.08,.83),(x+dx,-.08,2.02)],.012,'wrought iron',f'north-ground-security-{i}-{dx}')
    p=opening(2.64*scale,.80,.47,1.26);holes.append(p);records.append(window(F,p,'ground-entry-right-narrow',1,2))
    leftwin=opening(-4.95*scale,3.57,1.22,2.88,.61,36);holes.append(leftwin);records.append(window(F,leftwin,'south-arched-balcony-door',2,6,.61,'curtain glass'))
    for i,x in enumerate(rightxs):
        p=opening(x,4.15,.54,1.53,.27,28);holes.append(p);records.append(window(F,p,f'north-upper-triple-arch-{i}',1,3,.27,sill=False))
    F.box(sum(rightxs)/3,.76,rightxs[-1]-rightxs[0]+.61,.08,.18,.025,'red painted coping','north-ground-triple-shared-continuous-sill')
    F.box(sum(rightxs)/3,4.11,rightxs[-1]-rightxs[0]+.67,.08,.18,.025,'red painted coping','north-upper-triple-shared-continuous-sill')
    profile=Polygon([(left,0),(right,0),(right,7.54),(R,7.54),(R,3.84),(L,3.84),(L,6.97),(left,6.97)])
    wall=profile.difference(unary_union(holes)).difference(box(L,0,R,3.84));F.prism(wall,-.28,0,'cream stippled render','front-wings-with-real-window-voids')
    def curve(x):return -.38*(1-((x-(L+R)/2)/((R-L)/2))**2)
    class CurvedEntrance:
        def point(self,u,z,d=0):return point(u,curve(u)-d,z)
        def prism(self,poly,low,high,material,label):curved_prism(b,poly,low,high,self.point,material,label,.10)
        def box(self,u,z,w,h,depth,d,material,label):self.prism(box(u-w/2,z-h/2,u+w/2,z+h/2),d-depth/2,d+depth/2,material,label)
        def line(self,a,c,r,material,sides,label):b.tube([self.point(*a),self.point(*c)],r,material,sides,label)
    D=CurvedEntrance();D.prism(box(L,0,R,3.84).difference(door),-.28,0,'cream stippled render','middle-gentle-bow-entrance-wall-with-real-arch-hole')
    D.prism(box(L,0,R,.28),.002,.05,'red painted coping','middle-curved-base-course')
    F.box(0,.14,W,.28,.065,.025,'red painted coping','front-red-plinth')
    # Door is genuinely recessed behind its hole; a wooden leaf closes interior.
    D.prism(door.buffer(-.035),-.18,-.12,'wood entry','recessed-arched-wood-entry-leaf')
    for i in range(5):D.box(-.20*scale-.40+i*.20,1.04,.018,1.8,.012,-.103,'wood entry','door-vertical-board')
    D.line((.15*scale,.98,-.075),(.15*scale,1.18,-.075),.012,'wrought iron',8,'door-handle')
    D.box(-.20*scale,.035,1.30,.07,.48,.13,'gray cement','door-threshold')
    # Tiny legible numeric address is mesh, not a pasted photograph.
    pu=-1.17*scale;pz=2.19;D.box(pu,pz,.30,.23,.025,.025,'plate green','210-address-plate')
    segments={'a':(-.024,.066,.024,.066),'b':(.024,.066,.024,0),'c':(.024,0,.024,-.066),'d':(-.024,-.066,.024,-.066),'e':(-.024,0,-.024,-.066),'f':(-.024,.066,-.024,0),'g':(-.024,0,.024,0)}
    for i,ch in enumerate('210'):
        for s in {'2':'abged','1':'bc','0':'abcdef'}[ch]:
            x0,z0,x1,z1=segments[s];u=pu+(i-1)*.082;D.line((u+x0,pz+z0,.042),(u+x1,pz+z1,.042),.004,'plate letters',6,'address-numeral-'+ch)
    # Recessed central upper bay: separate back plane and visible return walls.
    C=facade((L,1.12),(R,1.12),'recessed-upper-middle');cp=opening(-.55,4.12,1.76,1.65);C.wall(3.84,6.28,[cp],.27,'cream stippled render');records.append(window(C,cp,'central-recessed-upper-window',3,3))
    A=facade((L,0),(L,1.12),'south-upper-return');A.wall(3.84,6.97,[],.27,'cream stippled render')
    B=facade((R,1.12),(R,0),'north-upper-return');bp=opening(0,4.15,.53,1.61);B.wall(3.84,7.54,[bp],.27,'cream stippled render');records.append(window(B,bp,'north-return-upper-window',1,3))
    # Roof-junction v3: the observed front returns end at1.12m. Their
    # previously missing hidden extensions left a visible cavity below the
    # raised hips. These solid, unfenestrated inferred walls close that gap.
    # They meet the old front returns edge-to-edge; no front aperture changes.
    south_hidden=facade((L,1.12),(L,depth),'south-inferred-inner-return-behind-front')
    north_hidden=facade((R,depth),(R,1.12),'north-inferred-inner-return-behind-front')
    south_hidden.wall(3.84,7.37,[],.27,'cream stippled render')
    north_hidden.wall(3.84,7.87,[],.27,'cream stippled render')
    # Continuous solid side/rear skins follow frozen source edge segments.
    coords=list(orient(original,1).exterior.coords);side_eaves=[]
    for i,(a,c) in enumerate(zip(coords,coords[1:])):
        side=Facade(b,a,c,f'unobserved-original-edge-{i}')
        if np.dot(side.n[:2],-Y)>.94:continue
        if abs(np.dot(side.t[:2],X))>.9:
            # Hidden rear is a closed stepped envelope under the three roofs,
            # not one tall blank plane sticking above the lower south roof.
            ua,uc=float(np.dot(np.asarray(a)-origin,X)),float(np.dot(np.asarray(c)-origin,X));cuts=[-side.length/2,side.length/2]
            for sx in [L,R]:
                t=(sx-ua)/(uc-ua)
                if 0<t<1:cuts.append(-side.length/2+t*side.length)
            cuts=sorted(cuts);top=[]
            for lo,hi in zip(cuts,cuts[1:]):
                sx=ua+(uc-ua)*((lo+hi)/2+side.length/2)/side.length;h=7.43 if sx<L else 8.01 if sx>R else 7.22
                top.extend([(lo,h),(hi,h)])
            outline=Polygon([(-side.length/2,0),(side.length/2,0)]+list(reversed(top)))
            side.wall(0,8.01,[],.28,'cream stippled render',outline=outline)
        else:
            z=6.97 if np.dot((np.asarray(a)+np.asarray(c))/2-origin,X)<0 else 7.54
            side.wall(0,z,[],.28,'cream stippled render');side_eaves.append((side,z))
        side.box(0,.14,side.length,.28,.045,.01,'red painted coping','unobserved-side-base')
    # Terrace front: observed curved red coping and plaster face, estimated depth.
    ellipse=LineString([(x,curve(x)) for x in np.linspace(L,R,65)])
    # A finite shell, no photographic foliage baked onto the building.
    prism(ellipse.buffer(.145,cap_style=2),3.84,3.96,'red painted coping','middle-curved-red-coping')
    prism(Polygon(list(ellipse.coords)+[(R,1.15),(L,1.15)]),3.69,3.80,'gray cement','middle-terrace-slab')
    for i,x in enumerate([-1.45,-.12,1.20]):
        # Three polygonal wall planters visible2017;2026 third is obscured.
        poly=Polygon([(x-.24,3.56),(x+.24,3.56),(x+.19,3.34),(x-.14,3.31)])
        D.prism(poly,.04,.22,'black joinery',f'middle-planter-{i}')
        D.prism(LineString([(x-.23,3.57),(x,3.73),(x+.23,3.57)]).buffer(.018,join_style=2),.025,.06,'wrought iron',f'planter-hook-{i}')
    # South balcony: half-ellipse finite bowl; rods bow outward at midheight.
    bx=-4.95*scale;rx=1.40;topz=3.58
    def bowl(levels,label,mat):
        verts=[];faces=[];n=48
        for z,s in levels:
            verts.extend(point(bx+rx*s*math.cos(a),-.03-.80*s*math.sin(a),z) for a in np.linspace(math.pi,0,n+1))
        count=n+1
        faces.append(tuple(range(count-1,-1,-1)));off=(len(levels)-1)*count;faces.append(tuple(range(off,off+count)))
        for j in range(len(levels)-1):
            for k in range(count):q=(k+1)%count;faces.append((j*count+k,j*count+q,(j+1)*count+q,(j+1)*count+k))
        # Ring path is CCW in local x/depth; point transform has positive XY determinant.
        b.add(verts,faces,mat,label)
    bowl([(2.98,.28),(3.08,.47),(3.40,.82),(3.52,1.0),(3.58,1.0)],'balcony-modelled-bowl-support','cream stippled render')
    bowl([(3.58,1.04),(3.68,1.04)],'balcony-red-edge-slab','red painted coping')
    for z,s in [(3.70,1.0),(4.69,.92),(4.84,.92)]:line([(bx+rx*s*math.cos(a),-.04-.80*s*math.sin(a),z) for a in np.linspace(0,math.pi,61)],.025,'wrought iron','balcony-bowed-horizontal-rail',10)
    for i,a in enumerate(np.linspace(0,math.pi,27)):
        arr=[]
        for t in np.linspace(0,1,17):
            s=1.0+.14*math.sin(math.pi*t)-.08*t;arr.append((bx+rx*s*math.cos(a),-.04-.80*s*math.sin(a),3.70+1.14*t))
        line(arr,.013,'wrought iron',f'balcony-belly-baluster-{i}')
        if i not in [0,26]:
            # Restrained individual C scrolls in local tangent/vertical planes.
            center=np.array([bx+rx*.92*math.cos(a),-.04-.80*.92*math.sin(a),4.71]);tan=np.array([-math.sin(a),-.7*math.cos(a),0.]);tan/=np.linalg.norm(tan)
            coords=[]
            for t in np.linspace(0,1.75*math.pi,22):
                r=.071*(1-t/(2.4*math.pi));p=center+tan*r*math.cos(t)+np.array([0,0,r*math.sin(t)]);coords.append(p)
            line(coords,.009,'wrought iron',f'balcony-top-scroll-{i}',6)
    # Layered red cornices and individual pale dentils, consistent on seen returns.
    def cornice(f,z,label):
        for zz,h,proj in [(z-.03,.13,.12),(z+.10,.12,.25),(z+.24,.11,.34),(z+.34,.08,.28)]:f.beam(zz,h,proj,'red painted coping',label=label+'-layer')
        for x in np.linspace(-f.length/2+.11,f.length/2-.11,max(2,int(f.length/.31))):f.box(x,z-.18,.13,.24,.13,.055,'cream stippled render',label+'-dentil')
    for side,z in side_eaves:cornice(side,z,'inferred-side-eave-continuation')
    cornice(facade((left,0),(L,0),'south-eave'),6.97,'south')
    cornice(A,6.97,'south-return');cornice(C,6.28,'middle');cornice(B,7.54,'north-return');cornice(facade((R,0),(right,0),'north-eave'),7.54,'north')
    # Continue the red cap behind the photographed return. The old cornice
    # extends50mm beyond its1.12m edge; begin at1.17m and use exact width,
    # avoiding coplanar overlapping bands at the join. No invented rear holes.
    for f,z,label in [(facade((L,1.17),(L,depth),'south-hidden-cornice'),6.97,'south-hidden'),(facade((R,depth),(R,1.17),'north-hidden-cornice'),7.54,'north-hidden')]:
        for zz,h,proj in [(z-.03,.13,.12),(z+.10,.12,.25),(z+.24,.11,.34),(z+.34,.08,.28)]:f.beam(zz,h,proj,'red painted coping',width=f.length,label=label+'-continuation-layer')
    # Pale external downpipes and simplified flower-head hopper funnels.
    for x,z in [(L-.32,6.80),(R+.20,6.80)]:
        line([(x,-.08,.38),(x,-.08,z-.38),(x,-.17,z-.38),(x,-.17,z)],.038,'service pale','external-downpipe',10)
        F.box(x,z-.37,.25,.17,.21,.10,'service pale','square-downpipe-hopper')
    line([(1.0,-.04,.43),(6.65*scale,-.04,.43)],.018,'service pale','observed-low-horizontal-service-pipe')
    # Hipped tiled roof surfaces. Tile courses follow slope, with real6cm lap,
    # butt joints and raised side folds; no random spots substituted for texture.
    roof_report=[]
    def roof_surface(poly,zfun,label):
        pp=orient(Polygon(poly),1);coords=list(pp.exterior.coords)[:-1]
        verts=[point(x,y,zfun(x,y)-.10) for x,y in coords]+[point(x,y,zfun(x,y)) for x,y in coords];n=len(coords);faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)];b.add(verts,faces,'tile edge',label+'-underlay')
        # Each projected tile is clipped at the true hip border; slope stays exact.
        gx=zfun(1.,0.)-zfun(0.,0.);gy=zfun(0.,1.)-zfun(0.,0.);axis=0 if abs(gx)>abs(gy) else 1;sgn=1 if (gx if axis==0 else gy)>=0 else -1
        def toxy(along,across):return (sgn*along,across) if axis==0 else (across,sgn*along)
        alongs=[sgn*p[axis] for p in coords];across=[p[1-axis] for p in coords];count=0
        for row,a in enumerate(np.arange(min(alongs)-.30,max(alongs),.285)):
            for col,c in enumerate(np.arange(min(across)-.22,max(across),.20)):
                candidate=Polygon([toxy(a+.003,c+.004),toxy(a+.348,c+.004),toxy(a+.348,c+.196),toxy(a+.003,c+.196)])
                tile=pp.intersection(candidate)
                for frag in pieces(tile):
                    if frag.area<.00004:continue
                    # Upper course physically overlaps the previous course.
                    # At a shared xy: base difference=.285*.060=.0171m,
                    # exceeding12mm thickness by5.1mm; no coplanar lap faces.
                    def mapper(tx,ty,d):return point(tx,ty,zfun(tx,ty)+.045-.060*(sgn*(tx if axis==0 else ty)-a)+d)
                    b.prism(frag,0,.012,mapper,'terracotta tile',label+f'-course-{row}-tile-{col}');count+=1
                    fold=Polygon([toxy(a+.006,c+.016),toxy(a+.342,c+.016),toxy(a+.342,c+.029),toxy(a+.006,c+.029)])
                    for lip in pieces(frag.intersection(fold)):
                        if lip.area>.00004:b.prism(lip,.012,.022,mapper,'terracotta tile',label+f'-course-{row}-tile-{col}-side-fold')
        roof_report.append({'label':label,'tiles':count,'row_pitch_m':.285,'tile_length_m':.345,'overlap_m':.060,'tile_width_m':.192,'butt_gap_m':.008,'physical_course_offset_m':.0171,'tile_thickness_m':.012,'lap_clearance_m':.0051,'long_axis_follows_steepest_slope':True,'estimated_hidden_slopes':True})
    def hip(x0,x1,y0,y1,eave,rise,label):
        # Common eaves are coplanar; choose ridge parallel long axis.
        cy=(y0+y1)/2;run=(y1-y0)/2;rx0=x0+min((x1-x0)*.30,run);rx1=x1-min((x1-x0)*.30,run)
        if rx1<rx0:rx0=rx1=(x0+x1)/2
        roof_surface([(x0,y0),(x1,y0),(rx1,cy),(rx0,cy)],lambda x,y:eave+rise*(y-y0)/run,label+'-front-slope')
        roof_surface([(x0,y1),(rx0,cy),(rx1,cy),(x1,y1)],lambda x,y:eave+rise*(y1-y)/run,label+'-rear-inferred')
        roof_surface([(x0,y0),(rx0,cy),(x0,y1)],lambda x,y:eave+rise*(x-x0)/max(1e-6,rx0-x0),label+'-left-hip')
        roof_surface([(x1,y0),(x1,y1),(rx1,cy)],lambda x,y:eave+rise*(x1-x)/max(1e-6,x1-rx1),label+'-right-hip')
        if rx1-rx0>.01:line([(rx0,cy,eave+rise+.055),(rx1,cy,eave+rise+.055)],.07,'tile edge',label+'-ridge-cap',10)
    hip(left-.27,L+.10,-.22,depth,7.38,1.16,'south-raised-hip')
    hip(R-.10,right+.26,-.22,depth,7.95,.82,'north-high-hip')
    roof_surface([(L,1.02),(R,1.02),(R,3.20),(L,3.20)],lambda x,y:6.67+(y-1.02)*.48,'middle-lower-front-slope')
    roof_surface([(L,3.20),(R,3.20),(R,depth),(L,depth)],lambda x,y:7.72-(y-3.20)*.13,'middle-rear-connection-inferred')
    audit=audit_parts(b);out.mkdir(parents=True,exist_ok=True);write(out/'solid-audit.json',audit)
    if not audit['passed']:raise ValueError(f"Invalid parts: {audit['bad_parts'][:3]}")
    metadata={'id':g['id'],'name':g['name_zh'],'anchor':g['anchor'],'ground_elevation_m':0,'model_license':'CC-BY-SA-4.0','copyright':'Model: CC BY-SA4.0; photo reference: Antigng2017 and Windmemories2026, CC BY-SA4.0; footprint © OpenStreetMap contributors / Overture Maps Foundation, ODbL1.0.','images_embedded':0,'source_geometry_sha256':hashlib.sha256((HERE/'geometry-input.json').read_bytes()).hexdigest(),'height_is_surveyed':False,'observed_and_estimated':cal,'replacement_exact_ids':g['replacement']['building_ids']}
    report=b.save(out/'xuhui-wukang-210-raw.glb',metadata);write(out/'opening-audit.json',{'windows':records,'wall_holes':len(holes)+2,'door_opening':list(door.exterior.coords),'all_glass_embedded_inside_frame_thickness':True,'no_photographic_texture_or_baked_tree_occlusion':True});write(out/'roof-evidence.json',{'surfaces':roof_report,'note':'Tile-course dimensions and unseen rear slopes are estimates; visible layered red ridges/eaves, hips and lower center slope follow licensed photographs.'});write(out/'build-summary.json',{'geometry':report,'solid_audit':audit,'raw_file':str(out/'xuhui-wukang-210-raw.glb'),'ground_m':0,'front_outward_azimuth_deg':g['front_edge']['outward_azimuth_deg'],'native_recommended_camera_azimuth_deg':[g['front_edge']['outward_azimuth_deg'],(g['front_edge']['outward_azimuth_deg']+25)%360],'source_hashes':{f:hashlib.sha256((HERE/f).read_bytes()).hexdigest() for f in ['build_model.py','geometry-input.json','calibration-model.json','common/photo_architecture.py','common/curved_prism.py']}});print(json.dumps({k:report[k] for k in ['file','bytes','sha256','triangles','parts']},indent=2));return b,records,g
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,default=HERE/'output');args=ap.parse_args();build(args.output.resolve())
