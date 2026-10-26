#!/usr/bin/env python3
"""Photograph-led conditional candidate for129 Wukang Road, not a survey."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import numpy as np
from shapely import constrained_delaunay_triangles, set_precision
from shapely.geometry import Polygon, Point, box
from shapely.geometry.polygon import orient
from shapely.affinity import translate
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
COMMON = HERE / 'common'
sys.path.insert(0, str(COMMON))
from photo_architecture import Builder, Facade, opening, pieces


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def curved_prism(builder, polygon, low, high, mapper, material, label, step=.12):
    """Continuous bent shell: band skins, shared boundary reveals, no internal caps."""
    verts=[];faces=[];lookup={}
    def index(x,z,d):
        key=(round(float(x),8),round(float(z),8),round(float(d),8))
        if key not in lookup:
            lookup[key]=len(verts);verts.append(mapper(*key))
        return lookup[key]
    normalized=set_precision(polygon,1e-8)
    assert normalized.symmetric_difference(polygon).area<1e-6
    for poly in pieces(normalized):
        x0,z0,x1,z1=poly.bounds
        regular=np.linspace(x0,x1,max(1,math.ceil((x1-x0)/step))+1)
        # Include all hole corner abscissae so both skins and jambs share cuts.
        corners=sorted(set(round(float(q[0]),8) for ring in [poly.exterior,*poly.interiors] for q in ring.coords))
        cuts=sorted(set(corners+[round(float(v),8) for v in regular if min(abs(v-x) for x in corners)>1e-7]))
        for a,b in zip(cuts,cuts[1:]):
            region=poly.intersection(box(a,z0-1,b,z1+1))
            for piece in pieces(region):
                for tri in constrained_delaunay_triangles(piece).geoms:
                    pts=list(orient(tri,1).exterior.coords)[:3]
                    faces.append(tuple(index(x,z,high) for x,z in pts));faces.append(tuple(index(x,z,low) for x,z in reversed(pts)))
        for ring in [poly.exterior,*poly.interiors]:
            coords=list(ring.coords)
            for a,b in zip(coords,coords[1:]):
                ts=[0.,1.]
                if abs(b[0]-a[0])>1e-12:
                    ts += [(x-a[0])/(b[0]-a[0]) for x in cuts if min(a[0],b[0])<x<max(a[0],b[0])]
                ts=sorted(set(ts))
                for lo,hi in zip(ts,ts[1:]):
                    p=np.asarray(a)+(np.asarray(b)-a)*lo;q=np.asarray(a)+(np.asarray(b)-a)*hi
                    faces.append((index(*p,low),index(*q,low),index(*q,high),index(*p,high)))
    builder.add(verts,faces,material,label)


def glass_window(f, shape, cols, rows, label, arch=0., blind=False):
    x0,z0,x1,z1=shape.bounds
    margin=min(.055,(x1-x0)*.13)
    inner=shape.buffer(-margin,join_style=2)
    outer=shape.buffer(-.012,join_style=2)
    bars=[];spring=z1-arch
    for i in range(1,cols):
        x=x0+(x1-x0)*i/cols;bars.append(box(x-.017,z0,x+.017,spring))
    for i in range(1,rows):
        z=z0+(spring-z0)*i/rows;bars.append(box(x0,z-.016,x1,z+.016))
    if arch:
        bars.append(box(x0,spring-.022,x1,spring+.022))
        # Two fanlight ribs, visible at the round-end arch.
        from shapely.geometry import LineString
        for angle in [math.pi/3,2*math.pi/3]:
            end=((x0+x1)/2+(x1-x0)/2*math.cos(angle),spring+arch*math.sin(angle))
            bars.append(LineString([((x0+x1)/2,spring),end]).buffer(.017,cap_style=2))
    panes=inner.difference(unary_union(bars)) if bars else inner
    f.prism(outer.difference(panes),-.12,-.04,'red brown joinery',label+'-connected-frame')
    for i,pane in enumerate(pieces(panes)):
        f.prism(pane,-.08,-.06,'interior shadow' if blind else 'dark reflection glass',label+f'-inset-pane-{i}')
    f.box((x0+x1)/2,z0-.045,x1-x0+.18,.09,.27,.025,'gray render',label+'-projecting-sill')
    return {'label':label,'facade_label':f.label,'columns':cols,'rows':rows,'opening_bounds':list(shape.bounds),'frame_depth':[-.12,-.04],'glass_depth':[-.08,-.06],'front_setback_m':.02,'glass_thickness_m':.02,
        'facade_origin_enu':f.center.tolist(),'facade_u_enu':f.t.tolist(),'facade_outward_enu':f.n.tolist()}


def tile_profile(r=.062,t=.012):
    ang=np.linspace(0,math.pi,7)
    return Polygon([(r*math.cos(a),.025+r*math.sin(a)) for a in ang]+[((r-t)*math.cos(a),.025+(r-t)*math.sin(a)) for a in reversed(ang)])


def add_tile(builder, start, down, length, side, label, pale=False):
    side=np.asarray(side);side/=np.linalg.norm(side)
    down=np.asarray(down);down/=np.linalg.norm(down)
    normal=np.cross(down,side);normal/=np.linalg.norm(normal)
    if normal[2]<0:side=-side;normal=-normal
    def mapper(x,h,d):return np.asarray(start)+side*x+normal*(h+.012*d/length)+down*d
    builder.prism(tile_profile(),0,length,mapper,'clay tile varied' if pale else 'clay tile',label)
    # Concave receiving pan between this cover and the next, also finite thickness.
    profile=[(-.072,.032),(-.04,.014),(0,.008),(.04,.014),(.072,.032)]
    pan=Polygon(profile+[(x,z-.008) for x,z in reversed(profile)])
    builder.prism(pan,0,length,lambda x,h,d:mapper(x+.07,h,d),'clay tile',label+'-receiving-pan')


def check_parts(builder):
    rows=[]
    for part in builder.parts:
        vv=np.asarray(part['vertices'],dtype=np.float32).astype(float);keys={};ids=[]
        for p in vv:
            k=tuple(p);keys.setdefault(k,len(keys));ids.append(keys[k])
        edges={};balance={};volume=0.;collapsed=0
        for tri in part['triangles']:
            t=tuple(ids[i] for i in tri);a,b,c=vv[list(tri)]
            collapsed+=int(len(set(t))!=3 or np.linalg.norm(np.cross(b-a,c-a))<1e-12)
            volume+=float(a@np.cross(b,c))/6
            for i,j in zip(t,t[1:]+t[:1]):
                e=tuple(sorted((i,j)));edges[e]=edges.get(e,0)+1;balance[e]=balance.get(e,0)+(1 if i<j else -1)
        row={'label':part['label'],'triangles':len(part['triangles']),'collapsed':collapsed,'boundary':sum(v==1 for v in edges.values()),'nonmanifold':sum(v>2 for v in edges.values()),'winding':sum(v!=0 for v in balance.values()),'volume_m3':volume}
        row['passed']=not any(row[k] for k in ['collapsed','boundary','nonmanifold','winding']) and volume>1e-10
        rows.append(row)
    return {'passed':all(r['passed'] for r in rows),'scope':'Each part FLOAT32 position-welded: closed oriented shell, positive volume. Separate architectural parts intentionally meet/overlap; no claim of global Boolean union.', 'parts':rows}


def build(output):
    output.mkdir(parents=True,exist_ok=True)
    source=json.loads((HERE/'geometry-input.json').read_text())
    metric=json.loads((HERE/'calibration/calibration-independent.json').read_text())
    O=np.asarray(source['front_edge']['center_local_east_north_m'])
    X=-np.asarray(source['front_edge']['tangent_east_north']);Y=-np.asarray(source['front_edge']['outward_normal_east_north'])
    def point(x,y,z):return np.r_[O+X*x+Y*y,z]
    def plan(poly):return Polygon([point(x,y,0)[:2] for x,y in poly.exterior.coords],[[point(x,y,0)[:2] for x,y in r.coords] for r in poly.interiors])
    original=Polygon(source['polygon_local_east_north'])
    uvpoly=Polygon([(float((np.asarray(v)-O)@X),float((np.asarray(v)-O)@Y)) for v in source['polygon_local_east_north']])
    b=Builder({'cream plaster':{'color':[.76,.735,.64],'roughness':.91},'gray render':{'color':[.40,.43,.425],'roughness':.85},
        'red brown joinery':{'color':[.24,.055,.035],'roughness':.62},'dark reflection glass':{'color':[.075,.11,.12],'roughness':.30,'metallic':.12},
        'clay tile':{'color':[.34,.135,.085],'roughness':.88},'clay tile varied':{'color':[.42,.19,.12],'roughness':.88},
        'painted white metal':{'color':[.72,.72,.66],'roughness':.65},'address green':{'color':[.02,.23,.12],'roughness':.55},'brass fitting':{'color':[.40,.28,.10],'roughness':.46,'metallic':.55}})
    def facade(a,c,label):return Facade(b,point(*a,0)[:2],point(*c,0)[:2],label)
    def local_u(f,x,y):return float((point(x,y,0)-f.center)@f.t)
    records=[]
    # Frozen original polygon is retained as the building's ground slab and identity.
    b.plan_prism(original,0,.10,'gray render','exact-original-source-ground-slab')
    # Left gabled block, street plane A, return B separately inferred from photograph.
    left=-7.100317185;hinge=-2.18345386
    A=facade((left,0),(hinge,0),'A-left-gabled-front')
    aw=[]
    for name,u,z,w,h,cols,rows in [('upper-narrow',-5.89,3.80,.385,.985,2,4),('upper-wide',-3.515,3.805,1.27,.983,2,1),('lower-wide',-3.47,1.411,1.306,.813,3,4)]:
        shape=opening(local_u(A,u,0),z,w,h);aw.append(shape);records.append(glass_window(A,shape,cols,rows,name))
    peak=-4.453;top=Polygon([(-A.length/2,0),(A.length/2,0),(A.length/2,5.18),(local_u(A,peak,0),6.516),(-A.length/2,5.18)])
    # One near-front skin later joins A/C/F; do not close each at its shared seam.
    # Shared x coordinates are written once in the common plane. Translating
    # separately normalized facade lengths left ~1e-15m slits in a GEOS union.
    front_surfaces=[Polygon([(left,0),(hinge,0),(hinge,5.18),(peak,6.516),(left,5.18)])]
    front_holes=[translate(h,xoff=(left+hinge)/2) for h in aw]
    A.box(0,.14,A.length,.28,.045,.018,'gray render','wall-foot-course')
    from shapely.geometry import LineString
    coping=LineString([(local_u(A,left,0),5.18),(local_u(A,peak,0),6.516),(local_u(A,hinge,0),5.18)]).buffer(.065,cap_style=2,join_style=2)
    A.prism(coping,.01,.09,'gray render','flat-mitred-gable-gray-coping')
    # Conditional low front extension C: observed end is certain; depth relation is not unique.
    C=facade((hinge,0),(-.45,0),'C-low-front-extension-estimate')
    Ctop=Polygon([(-C.length/2,0),(C.length/2,0),(C.length/2,2.70),(-C.length/2,3.18)])
    front_surfaces.append(Polygon([(hinge,0),(-.45,0),(-.45,2.70),(hinge,3.18)]))
    C.line((-C.length/2,3.18,.02),(C.length/2,2.70,.02),.065,'gray render',8,'sloping-coping-observed')
    B_end=(.09,5.555)
    B=facade((hinge,0),B_end,'B-left-upper-return')
    bw=[]
    for item in metric['window_checks']:
        if item['plane']!='B':continue
        pts=np.asarray(item['u_z_d_m']);center=pts.mean(0);u=local_u(B,center[0],-center[2]);shape=opening(u,item['bottom_z_m'],item['horizontal_width_m'],item['height_m']);bw.append(shape)
        records.append(glass_window(B,shape,2 if 'large' in item['name'] else 1,4,item['name']))
    B.wall(3.12,5.18,bw,.27,'cream plaster')
    B.beam(5.17,.15,.18,'gray render',label='return-eave')
    # Rear and outer sides use the existing mapped outline, blank where unobserved.
    coords=list(orient(original,1).exterior.coords)
    for i,(a,c) in enumerate(zip(coords,coords[1:])):
        f=Facade(b,a,c,f'unphotographed-original-edge-{i}')
        if abs(np.dot(f.n[:2],-Y))>.95:continue
        if i==2:
            # The original straight edge's unsupported front segment made a
            # freestanding plank beside the circular end. Its hidden rear is
            # joined into the single E shell below, not extruded from the street.
            continue
        f.wall(.10,5.18,[],.26,'cream plaster')
        f.box(0,.14,f.length,.28,.04,.018,'gray render','base-course')
    # Upper central D follows a separately fitted orientation, behind the low entrance roof.
    Dend=(4.18,3.415)
    D=facade(B_end,Dend,'D-recessed-upper-center')
    dw=[]
    for item in metric['window_checks']:
        if item['plane']!='D':continue
        pts=np.asarray(item['u_z_d_m']);center=pts.mean(0);u=local_u(D,center[0],-center[2]);shape=opening(u,item['bottom_z_m'],item['horizontal_width_m'],item['height_m']);dw.append(shape)
        records.append(glass_window(D,shape,4 if 'wide' in item['name'] else 1,3,item['name']))
    D.wall(3.10,5.60,dw,.27,'cream plaster');D.beam(5.55,.16,.23,'gray render',label='separate-upper-eave')
    # Central low entry stays on the near street plane, not on upper recessed D.
    F=facade((-.45,0),(3.85,0),'D-low-entrance')
    door_u=local_u(F,1.90,0);door=opening(door_u,.08,1.00,2.08,.50,36)
    flanks=[opening(local_u(F,x,0),.83,.35,.83) for x in [.70,3.24]]
    front_surfaces.append(box(-.45,0,3.85,2.75))
    front_holes.extend(translate(h,xoff=(-.45+3.85)/2) for h in [door,*flanks])
    front_union=unary_union(front_surfaces).difference(unary_union(front_holes))
    assert front_union.geom_type=='Polygon','Front strips must form one connected surface, not touching closed pieces'
    front_clean=front_union.simplify(1e-10,preserve_topology=True)
    assert front_clean.symmetric_difference(front_union).area<1e-10
    b.prism(front_clean,-.30,0,lambda x,z,d:point(x,-d,z),'cream plaster','ACF-single-union-front-with-original-openings')
    for i,shape in enumerate(flanks):records.append(glass_window(F,shape,1,3,f'entry-flank-{i}'))
    F.prism(door.buffer(.19,join_style=2).difference(door),-.015,.075,'gray render','thick-arched-door-surround')
    for n in range(3):
        ring=door.buffer(.04+n*.045,join_style=2).difference(door.buffer(.027+n*.045,join_style=2))
        F.prism(ring,.075,.092,'gray render','nested-arch-moulding')
    F.prism(door.buffer(-.015),-.09,-.045,'red brown joinery','red-arched-entry-leaf')
    # Inset panel shape and restrained visible iron/brass fittings.
    F.prism(opening(door_u,.34,.71,1.05,.08),-.044,-.034,'red brown joinery','entry-raised-lower-panel')
    F.box(door_u,1.26,.33,.018,.018,-.015,'brass fitting','letter-slot')
    F.line((door_u+.34,.90,-.005),(door_u+.34,1.13,-.005),.012,'wrought iron',8,'door-pull')
    F.box(door_u,1.91,.24,.16,.028,.0,'address green','129-address-plate')
    # Seven-segment physical numerals, deliberately simple legible plate lettering.
    digits={'1':'bc','2':'abdeg','9':'abcdfg'};seg={'a':(-.023,.05,.023,.05),'b':(.023,.05,.023,.0),'c':(.023,.0,.023,-.05),'d':(-.023,-.05,.023,-.05),'e':(-.023,.0,-.023,-.05),'f':(-.023,.05,-.023,.0),'g':(-.023,0,.023,0)}
    for i,ch in enumerate('129'):
        for s in digits[ch]:
            x0,z0,x1,z1=seg[s];cx=door_u+(i-1)*.065
            F.line((cx+x0,1.91+z0,.018),(cx+x1,1.91+z1,.018),.0035,'painted white metal',6,'address-numeral-'+ch)
    F.box(door_u,.04,1.20,.08,.40,.10,'gray render','entry-threshold')
    # Round-end wall is a real bent shell with an arched void, not a rectangular block.
    radius=1.65;cx=5.5;cy=1.67
    arc_right=radius*math.pi/2
    # Join the rounded shell to the hidden source-side rear in one continuous
    # extrusion, with no opposing internal caps at either transition. The
    # original source polygon remains the unchanged ground/identity input.
    source_side_front=np.array([7.100317185083083,0.])
    source_side_back=np.array([11.160158332621473,8.94654582861645])
    side_t=source_side_back-source_side_front;side_t/=np.linalg.norm(side_t)
    side_n=np.array([side_t[1],-side_t[0]])
    hidden_join=source_side_front+(source_side_back-source_side_front)*(4.0/source_side_back[1])
    curve_end=np.array([cx+radius,cy]);connector=hidden_join-curve_end
    connector_length=float(np.linalg.norm(connector));rear_length=float(np.linalg.norm(source_side_back-hidden_join))
    shell_right=arc_right+connector_length+rear_length
    def curved(u,z,d):
        if u<=arc_right+1e-9:
            a=u/radius;return point(cx+(radius+d)*math.sin(a),cy-(radius+d)*math.cos(a),z)
        s=u-arc_right
        if s<=connector_length:
            t=s/connector_length;xy=curve_end+connector*t
            normal=np.array([1.,0.])*(1-t)+side_n*t
        else:
            xy=hidden_join+side_t*(s-connector_length);normal=side_n
        return point(*(xy+normal*d),z)
    hole=opening(0,2.34,1.08,2.24,.54,36)
    outline=Polygon([(-arc_right,0),(shell_right,0),(shell_right,5.18),(arc_right,5.18),(arc_right,5.95),(-arc_right,5.95)])
    surface=outline.difference(hole)
    curved_prism(b,surface,-.28,0,curved,'cream plaster','E-rounded-front-true-arch-wall')
    curved_prism(b,box(-arc_right,.02,shell_right,.28),0,.035,curved,'gray render','E-curved-gray-plinth')
    for z,h,d in [(5.88,.14,.08),(5.72,.08,.06),(5.64,.05,.035)]:
        curved_prism(b,box(-radius*math.pi/2,z,radius*math.pi/2,z+h),0,d,curved,'gray render','E-curved-layered-cornice')
    # Flat joinery tangent to the circle; its sides penetrate the thick real jamb.
    E=facade((cx-.65,cy-radius+.02),(cx+.65,cy-radius+.02),'E-upper-arched-door')
    records.append(glass_window(E,hole,2,1,'upper-fanlight-door',.54,blind=True))
    # Bowed balcony slab and belly-shaped wrought-iron balusters.
    angles=np.linspace(-1.04,1.04,33)
    balcony=Polygon([(cx+.72*math.sin(a),cy-radius-.14-.30*math.cos(a)) for a in angles]+[(cx+.62,cy-radius+.07),(cx-.62,cy-radius+.07)])
    for lo,hi,scale in [(2.12,2.19,1.),(2.02,2.12,.91),(1.94,2.02,.78)]:
        from shapely.affinity import scale as pscale
        b.plan_prism(plan(pscale(balcony,xfact=scale,yfact=scale,origin=(cx,cy-radius))),lo,hi,'gray render','E-tiered-curved-balcony-base')
    for zz,depth in [(2.20,.32),(3.08,.23)]:
        pts=[point(cx+.72*math.sin(a),cy-radius-.14-depth*math.cos(a),zz) for a in angles]
        b.tube(pts,.014,'wrought iron',8,'E-bowed-balcony-horizontal-rail')
    for a in np.linspace(-1.04,1.04,15):
        pts=[]
        for t in np.linspace(0,1,9):
            belly=.23+.17*math.sin(math.pi*t)
            pts.append(point(cx+.72*math.sin(a),cy-radius-.14-belly*math.cos(a),2.20+.88*t))
        b.tube(pts,.011,'wrought iron',7,'E-outward-bellied-baluster')
    # Cone-like half-round cap, closed single solid with finite underside.
    arc=np.linspace(-math.pi/2,math.pi/2,49)
    apex_x=6.14;apex_z=7.03
    toppts=[point(apex_x,cy,apex_z)]+[point(cx+1.75*math.sin(a),cy-1.75*math.cos(a),6.02) for a in arc]
    n=len(toppts);vs=toppts+[v-np.array([0,0,.09]) for v in toppts];fs=[]
    for i in range(1,n-1):fs.extend([(0,i,i+1),(n,n+i+1,n+i)])
    boundary=list(range(n))
    for i,j in zip(boundary,boundary[1:]+boundary[:1]):fs.append((n+i,n+j,j,i))
    # Front arc order gives positive top normal; verify below via signed volume.
    b.add(vs,fs,'clay tile','E-half-round-closed-roof-cap-estimate')
    # Real finite lapped barrel tiles over the curved cap. Rear cap extent is unobserved.
    for row,rr in enumerate(np.arange(.26,1.72,.24)):
        count=max(3,math.ceil(math.pi*rr/.14))
        for j,a in enumerate(np.linspace(-math.pi/2+.03,math.pi/2-.03,count)):
            r0=max(.12,rr-.13);r1=min(1.77,rr+.16)
            arcxy=np.array([cx+1.75*math.sin(a),cy-1.75*math.cos(a)])
            pxy=np.array([apex_x,cy])+(arcxy-[apex_x,cy])*(r0/1.75)
            qxy=np.array([apex_x,cy])+(arcxy-[apex_x,cy])*(r1/1.75)
            start=point(*pxy,apex_z-(apex_z-6.02)*r0/1.75)
            end=point(*qxy,apex_z-(apex_z-6.02)*r1/1.75)
            side=np.r_[X*math.cos(a)+Y*math.sin(a),0.]
            add_tile(b,start,end-start,float(np.linalg.norm(end-start)),side,'E-radial-lapped-clay-tile',(row+j)%9==0)
    # Left gable roof: hidden longitudinal extent follows original mapped side direction.
    slope=.370;depth=8.5;ridge=peak
    left_roof=Polygon([(left-.10,-.10),(hinge+.10,-.10),(hinge+.10+slope*depth,depth),(left-.10+slope*depth,depth)])
    def gable_h(x,y):
        localx=x-slope*y
        return 6.516-(6.516-5.18)*abs(localx-ridge)/(ridge-left if localx<ridge else hinge-ridge)
    for sign in [-1,1]:
        a=left-.10 if sign<0 else ridge;c=ridge if sign<0 else hinge+.10
        poly=Polygon([(a,-.1),(c,-.1),(c+slope*depth,depth),(a+slope*depth,depth)])
        b.prism(poly,-.08,0,lambda x,y,d:point(x,y,gable_h(x,y)+d),'clay tile','A-closed-gabled-roof-slope')
        for col,y in enumerate(np.arange(.0,depth-.1,.145)):
            lengthside=(ridge-left) if sign<0 else (hinge-ridge)
            for row,run in enumerate(np.arange(.03,lengthside-.03,.25)):
                r1=min(run+.31,lengthside+.08)
                p=point(ridge+sign*run+slope*y,y,gable_h(ridge+sign*run+slope*y,y))
                q=point(ridge+sign*r1+slope*y,y,gable_h(ridge+sign*r1+slope*y,y))
                add_tile(b,p,q-p,float(np.linalg.norm(q-p)),np.r_[X*slope+Y,0.],'A-finite-lapped-clay-tile',(row+col)%11==0)
    # Front low canopy: finite sloping slab and real overlapping rows.
    canopy=Polygon([(-.50,-.12),(3.90,-.12),(4.25,3.40),(.05,5.52)]).intersection(uvpoly)
    hcan=lambda x,y:2.76+.145*y
    b.prism(canopy,-.09,0,lambda x,y,d:point(x,y,hcan(x,y)+d),'clay tile','D-low-pitched-entrance-canopy')
    for col,x in enumerate(np.arange(-.35,3.9,.14)):
        for row,y in enumerate(np.arange(.03,5.2,.25)):
            y1=min(y+.31,5.5)
            if not canopy.covers(Point(x,y)) or not canopy.covers(Point(x,y1)):continue
            p=point(x,y1,hcan(x,y1));q=point(x,y,hcan(x,y))
            add_tile(b,p,q-p,float(np.linalg.norm(q-p)),np.r_[X,0.],'D-low-canopy-lapped-tile',(row+col)%10==0)
    F.beam(2.72,.13,.16,'gray render',label='lower-canopy-edge')
    # Directly visible in2026: a separate red-tile slope above the recessed
    # upper D windows. The old rear cap was only an unseen closure and did not
    # provide this photographed slope. Depth/ridge are conditional estimates.
    upper_a=np.array(B_end);upper_b=np.array([4.742,3.121])
    upper_t=upper_b-upper_a;upper_length=float(np.linalg.norm(upper_t));upper_t/=upper_length
    upper_in=np.array([-upper_t[1],upper_t[0]])
    upper_depth=.85;upper_eave=5.64;upper_rise=.86
    upper_poly=Polygon([upper_a,upper_b,upper_b+upper_in*upper_depth,upper_a+upper_in*upper_depth])
    def upper_h(x,y):return upper_eave+upper_rise*float((np.array([x,y])-upper_a)@upper_in)/upper_depth
    b.prism(upper_poly,-.065,0,lambda x,y,d:point(x,y,upper_h(x,y)+d),'clay tile','D-visible-upper-pitched-roof-v2')
    for col,u in enumerate(np.arange(.05,upper_length-.04,.14)):
        for row,v in enumerate(np.arange(.015,upper_depth-.01,.18)):
            v1=min(v+.235,upper_depth+.025)
            high=upper_a+upper_t*u+upper_in*v1;low=upper_a+upper_t*u+upper_in*v
            p=point(*high,upper_h(*high));q=point(*low,upper_h(*low))
            add_tile(b,p,q-p,float(np.linalg.norm(q-p)),np.r_[X*upper_t[0]+Y*upper_t[1],0.],'D-visible-upper-lapped-tile-v2',(row+col)%10==0)
    # Unseen rear roof is a conservative closed cap. No invented repeating rear windows.
    rear=uvpoly.intersection(Polygon([B_end,Dend,(20,9),(20,20),(-10,20)]))
    for rp in pieces(rear):b.prism(rp,5.52,5.62,lambda x,y,d:point(x,y,d),'clay tile','unphotographed-rear-roof-closure-estimate')
    # Visible fixed utilities kept restrained; no tree/person/temporary sunflower copied.
    for x in [hinge-.03,3.78]:
        pts=[point(x,0,5.52),point(x,0,2.95),point(x+.10,0,2.8),point(x+.10,0,.22)]
        b.tube(pts,.027,'painted white metal',8,'visible-rainwater-pipe-estimate')
    # Photo2026 right-side entrance outdoor unit, with actual grille and fan circle.
    F.box(local_u(F,3.20,0),2.10,.58,.45,.22,.19,'painted white metal','entry-right-ac-unit-2026')
    for rr in [.13,.145]:
        pts=[F.point(local_u(F,3.11,0)+rr*math.cos(a),2.10+rr*math.sin(a),.315) for a in np.linspace(0,math.tau,33)]
        b.tube(pts,.006,'gray render',6,'ac-fan-ring')
    for zz in np.linspace(1.96,2.24,8):F.line((local_u(F,3.28,0),zz,.312),(local_u(F,3.44,0),zz,.312),.004,'gray render',5,'ac-grille')
    audit=check_parts(b);write(output/'structural-check.json',audit)
    if not audit['passed']:
        print(json.dumps([r for r in audit['parts'] if not r['passed']],indent=2));raise ValueError('Part structure failed')
    metadata={'id':'xuhui-wukang-129','name':'徐汇武康路129号二层住宅','origin':source['anchor'],'observed_storeys':2,'height_is_measured':False,
        'geometry_input_sha256':hashlib.sha256((HERE/'geometry-input.json').read_bytes()).hexdigest(),'photographic_epoch':'2026-02-09, corroborated2017-08-19',
        'source_footprint_and_replacement':'Original four-point OSM-derived footprint and exact local3733 unchanged; photo-inferred superstructure has rounded/recessed faces.',
        'copyright':'Geometry reconstruction: CC-BY-SA-4.0, photo observations by Antigng2017 and Windmemories2026; photographs not embedded. Map data: © OpenStreetMap contributors / Overture Maps Foundation, ODbL-1.0. Code retains project licence.',
        'unknown':'Hidden rear shape/openings, upper/lower left extension relation, exact curved radius and roof rear extent are explicitly estimated. This raw is awaiting visual review.',
        'candidate_revision':'visible-shape-v2','revision_changes':['D photographed upper red-tile slope','E unsupported front straight wall replaced by continuous hidden rear closure','A/C/F same-plane structural union; original openings and all window parts retained']}
    report=b.save(output/'xuhui-wukang-129-raw.glb',metadata);assert report['bytes']<100_000_000
    write(output/'model-summary.json',{k:report[k] for k in ['file','bytes','sha256','triangles','materials','parts','bounds_glb']})
    write(HERE/'calibration-model.json',{'schema':'wukang129-reconstruction-parameters-v1','status':'Photo-specific raw candidate, not visually accepted or measured','frames':'Photo u/v-depth mapped to existing ENU source frame; glTF east/up/-north',
        'left_eaves_m':5.18,'left_gable_peak_m':6.516,'center_upper_eave_m':5.60,'right_eave_m':5.95,'right_cap_peak_m':apex_z,'right_cap_apex_u_depth_m':[apex_x,cy],'right_radius_m':radius,
        'left_upper_return_endpoint_u_depth_m':B_end,'central_upper_other_endpoint_u_depth_m':Dend,'glass_frame_policy':'20mm glass,20mm inside own frame front; no floating glass behind a narrow grid tunnel',
        'windows':records,'estimated_plan':'C low extension assigned near-front plane to match observed ground silhouette; ambiguity explicitly retained. B/D hinged geometry is conditional on camera/envelope assumptions.',
        'roof_tiles':'Finite closed overlapping barrel units; pitch/count/hidden extents estimated. Not a photograph pasted onto a roof.',
        'validation':'output/structural-check.json','frozen_source_geometry_sha256':metadata['geometry_input_sha256'],'source_photo_bytes_changed':False,'browser_or_blender_run':False,
        'candidate_revision':'visible-shape-v2','visible_upper_D_roof':{'eave_m':upper_eave,'ridge_m':upper_eave+upper_rise,'inward_run_m':upper_depth,'front_endpoints_u_depth_m':[upper_a.tolist(),upper_b.tolist()],'depth_and_ridge_are_estimates':True},
        'front_union':{'one_connected_polygon':True,'thickness_m':.30,'A_C_back_changed_from_m':.28,'opening_and_joinery_positions_unchanged':True},
        'E_rear_closure':{'unsupported_source_front_wall_removed':True,'hidden_join_u_depth_m':hidden_join.tolist(),'original_source_back_vertex_u_depth_m':source_side_back.tolist(),'single_closed_curved_and_rear_wall_shell':True}})
    print(json.dumps({k:report[k] for k in ['bytes','sha256','triangles','parts']},indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=HERE/'output');args=ap.parse_args();build(args.output)
