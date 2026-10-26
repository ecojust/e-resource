#!/usr/bin/env python3
"""Bund09: exact frozen perimeter, open loggias, arched windows and dated detail.

Ordinary Python only. Blender/native/render are performed by the parent task.
Dimensions are proportional estimates, never OSM levels multiplied by height.
"""
from pathlib import Path
import argparse, hashlib, json, math, sys
import numpy as np
from shapely.geometry import Polygon, LineString, Point, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'common'))
from photo_architecture import Builder, Facade, opening, pieces
from sign_lettering import add_facade_lettering


def write(path, data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')


def shifted(f, d, label):
    return Facade(f.builder,(f.a+f.n*d)[:2],(f.b+f.n*d)[:2],label)


def masonry(f, wall, brick=True, exclude=None):
    """Thin explicit mortar, clipped against real holes; no box-wall cells."""
    x0,z0,x1,z1=wall.bounds
    course=.086 if brick else .46; pitch=.26 if brick else 1.02
    half=.0032 if brick else .009
    strips=[]
    for row,z in enumerate(np.arange(math.floor(z0/course)*course,z1,course)):
        strips.append(box(x0,z-half,x1,z+half))
        start=math.floor(x0/pitch)*pitch+(pitch/2 if row%2 else 0)
        for x in np.arange(start,x1,pitch):
            strips.append(box(x-half,z+half,x+half,min(z+course-half,z1)))
    joints=wall.intersection(unary_union(strips))
    if exclude is not None:joints=joints.difference(exclude)
    f.prism(joints,.001,.004,'brick mortar' if brick else 'stone joints','estimated-masonry-joints')


def voussoir_zone(u,width,height=3.65,bottom=.38,rise=None,top_limit=4.38):
    rise=width*.37 if rise is None else rise;spring=bottom+height-rise
    arch=opening(u,bottom,width,height,rise,segments=36)
    # Photo P01: radial stone joints reach an approximately horizontal upper
    # bed, rather than drawing a second decorative semicircular arch outline.
    zone=box(u-width/2-.33,spring,u+width/2+.33,min(top_limit,bottom+height+.35)).difference(arch)
    return zone,spring


def stone_voussoirs(f,u,width,divisions,label):
    zone,spring=voussoir_zone(u,width)
    strips=[]
    for a in np.linspace(0,math.pi,divisions+1)[1:-1]:
        end=(u+6*math.cos(a),spring+6*math.sin(a))
        strips.append(LineString([(u,spring),end]).buffer(.007,cap_style=2,join_style=2))
    cutters=unary_union(strips)
    joint=zone.intersection(cutters);stone0=zone.difference(cutters)
    # Boolean intersections leave exactly collinear intermediate vertices.
    # Remove only sub-nanometre redundant points so CDT skins and side rings
    # have matching edges; the polygonal area and observed contour stay fixed.
    stone=stone0.simplify(1e-9,preserve_topology=True)
    assert stone.symmetric_difference(stone0).area<1e-12
    # Continuous backing plus disjoint stone regions. Faces stand only10mm
    # forward; the dark joint is8mm behind them, with no overlapping box ends.
    f.prism(zone,.0005,.002,'stone joints',label+'-recessed-joint-bed')
    f.prism(stone,.003,.010,'pale stone',label+'-disjoint-radial-stones')
    solids=pieces(stone)
    residual=abs(sum(x.area for x in solids)+joint.area-zone.area)
    overlap=stone.intersection(joint).area
    assert residual<1e-8 and overlap<1e-10
    return {'label':label,'estimated_divisions':divisions,'actual_stone_regions':len(solids),'zone_area_m2':zone.area,'stone_area_m2':stone.area,'joint_area_m2':joint.area,'partition_area_residual_m2':residual,'stone_joint_overlap_m2':overlap,'stone_depth_m':[.003,.010],'joint_backing_depth_m':[.0005,.002],'joint_recess_from_stone_front_m':.008,'source':'P01 inspection-first-arch-crown-v2.jpg; radial pattern is observed, individual divisions and dimensions remain proportion estimates.'}


def arc_window(f, u, bottom, width, height, rise, label, rows=4, columns=2, depth=.30, surround=True):
    shape=opening(u,bottom,width,height,rise,segments=36)
    inner=shape.buffer(-.075,join_style=2);outer=shape.buffer(-.015,join_style=2)
    ix0,iz0,ix1,iz1=inner.bounds; spring=bottom+height-rise
    bars=[box(ix0,spring-.045,ix1,spring+.045)]
    for c in range(1,columns):
        x=ix0+(ix1-ix0)*c/columns
        bars.append(box(x-.027,iz0,x+.027,spring))
    for r in range(1,rows):
        if label=='side-15-f2-a1':
            # Current P01 has three upper lights, a thick transom, then four
            # taller lower lights, rather than seven uniform frame bands.
            frac=[.122,.246,.420,.594,.730,.870][r-1]
            z=spring-(spring-iz0)*frac;half=.11 if r==3 else .029
        else:z=iz0+(spring-iz0)*r/rows;half=.029
        bars.append(box(ix0,z-half,ix1,z+half))
    if rise>.1:
        # Distinct fanlight bars continue from the spring centre.
        for theta in np.linspace(0,math.pi,columns+3)[1:-1]:
            p=(u+width/2*math.cos(theta),spring+rise*math.sin(theta))
            bars.append(LineString([(u,spring),p]).buffer(.021,cap_style=2))
        small=opening(u,spring-.015,width*.34,rise*.35,rise*.35,segments=24)
        # Upper half-ellipse ring, clipped above the spring line.
        bars.append(small.buffer(.022).difference(small.buffer(-.022)).intersection(box(ix0,spring,ix1,iz1)))
    remaining=inner.difference(unary_union(bars))
    # One connected frame grid, then distinct closed glass panes.
    f.prism(outer.difference(remaining),-depth+.045,-depth+.12,'window bronze',label+'-frame-grid')
    panes=[]
    for i,pane in enumerate(sorted(pieces(remaining),key=lambda q:(-q.centroid.y,q.centroid.x))):
        if pane.area<.0002:continue
        plabel=label+f'-pane-{i:02d}'
        # A pane sits inside its own frame:20mm behind the frame front and
        #20mm thick. Keep the entire window/loggia plane at its original depth.
        f.prism(pane,-depth+.08,-depth+.10,'recessed glass',plabel)
        panes.append({'label':f.label+'/'+plabel,'bounds':list(pane.bounds),'polygon':pane,'facade':f,
                      'glass_depth_m':[-depth+.08,-depth+.10],
                      'frame_depth_m':[-depth+.045,-depth+.12]})
    if surround:
        # Red brick archivolt, separate raised rings and stone impost blocks.
        ring=shape.buffer(.14,join_style=2).difference(shape)
        f.prism(ring,-.015,.055,'red brick trim',label+'-brick-archivolt')
        for d,rad in [(0.042,.22),(.025,.29)]:
            f.prism(shape.buffer(rad,join_style=2).difference(shape.buffer(rad-.035,join_style=2)),d,d+.025,'red brick trim',label+'-archivolt-bead')
        for side in [-1,1]:
            f.box(u+side*(width/2+.18),spring,.40,.15,.17,.065,'pale stone',label+'-stone-impost')
    f.box(u,bottom-.075,width+.26,.15,.30,.035,'pale stone',label+'-sill')
    return shape,panes


def column(b,f,u,z0,z1,order,label,r=.18):
    c=f.point(u,0,-.13)
    cap=.47 if order=='corinthian' else .21
    profile=[(z0,r*1.38),(z0+.10,r*1.38),(z0+.16,r*1.12),(z0+.24,r),
             (z0+.60,r*1.015),(z1-cap,r*.84),(z1-cap+.045,r*.98)]
    if order=='tuscan':profile += [(z1-.14,r),(z1-.07,r*1.28),(z1,r*1.31)]
    else:profile += [(z1-.26,r*1.05),(z1-.13,r*1.37),(z1,r*1.44)]
    b.lathe(c[:2],profile,'pale stone',segments=28,label=label+'-shaft-and-profile')
    f.box(u,z0+.055,r*3.1,.11,r*3.1,-.13,'pale stone',label+'-square-plinth')
    f.box(u,z1+.055,r*3.3,.11,r*3.3,-.13,'pale stone',label+'-abacus')
    if order=='corinthian':
        # Two ranks of visible leafy capital relief. Exact carving is estimated.
        for rank in range(2):
            for k in range(8):
                a=math.tau*(k+.5*rank)/8;radial=np.array([math.cos(a),math.sin(a),0.]);tangent=np.array([-radial[1],radial[0],0.])
                z=z1-.43+.14*rank
                leaf=Polygon([(-.075,z),(-.105,z+.13),(-.06,z+.22),(0,z+.30),(.06,z+.22),(.105,z+.13),(.075,z)])
                def mapper(u0,z0,d0,c=c,radial=radial,tangent=tangent):return c+tangent*u0+radial*d0+np.array([0,0,z0])
                b.prism(leaf,r*.92,r*1.40,mapper,'pale stone',label+f'-acanthus-estimate-{rank}-{k}')
        for k in range(4):
            a=math.pi/4+math.pi*k/2
            pts=[]
            for theta in np.linspace(0,math.pi*1.5,24):
                rr=.075*(1-theta/(math.pi*1.8));radial=np.array([math.cos(a),math.sin(a),0.])
                tangent=np.array([-radial[1],radial[0],0.])
                pts.append(c+radial*r*1.35+tangent*rr*math.cos(theta)+np.array([0,0,z1-.09+rr*math.sin(theta)]))
            b.tube(pts,.025,'pale stone',8,label+'-capital-volute-estimate')


def railing(b,f,u0,u1,z,d=0,label='balustrade',baluster_count=None):
    if u1-u0<.25:return
    f.box((u0+u1)/2,z+.055,u1-u0,.11,.34,d,'pale stone',label+'-base')
    f.box((u0+u1)/2,z+.83,u1-u0+.06,.13,.40,d,'pale stone',label+'-continuous-cap')
    count=baluster_count if baluster_count is not None else max(1,round((u1-u0)/.235))
    for i,u in enumerate(np.linspace(u0+.12,u1-.12,count)):
        c=f.point(u,0,d)
        b.lathe(c[:2],[(z+.11,.085),(z+.18,.085),(z+.25,.047),(z+.39,.10),
                      (z+.51,.095),(z+.65,.045),(z+.70,.062),(z+.765,.065)],
                'pale stone',segments=12,label=label+f'-individual-baluster-{i}')


def balcony_corner_post(b,f,u,z,d,label):
    # One closed stepped solid; no stacked overlapping boxes or internal caps.
    profile=[(z,.72,.72),(z+.13,.72,.72),(z+.13,.59,.59),
             (z+.76,.59,.59),(z+.76,.75,.75),(z+.90,.75,.75)]
    vertices=[]
    for zz,w,depth in profile:
        vertices.extend(f.point(u+sx*w/2,zz,d+sy*depth/2) for sx,sy in [(-1,-1),(1,-1),(1,1),(-1,1)])
    faces=[(0,3,2,1),tuple((len(profile)-1)*4+i for i in range(4))]
    for k in range(len(profile)-1):
        for j in range(4):
            a=k*4+j;bb=k*4+(j+1)%4;faces.append((a,bb,bb+4,a+4))
    # Facade u,d,z is a reflected basis; reverse every face consistently.
    b.add(vertices,[tuple(reversed(face)) for face in faces],'pale stone',label)


def curl(f,u,z,width,height,d=.10,label='scroll'):
    # Explicit relief within a frieze, avoiding photograph-projected stone.
    for sign in [-1,1]:
        pts=[]
        for q in np.linspace(0,math.pi*2,35):
            rr=.41*(1-q/(math.pi*2.5))
            pts.append(f.point(u+sign*width*(.16+rr*math.cos(q)),z+height*rr*math.sin(q),d))
        f.builder.tube(pts,.022,'pale stone',7,f.label+'/'+label)


def pediment(f,u,width,z0,peak,label):
    tri=Polygon([(u-width/2,z0),(u+width/2,z0),(u,peak)])
    f.prism(tri,-.23,.08,'pale stone',label+'-solid-triangle')
    for offset,r in [(0,.095),(-.12,.040)]:
        for a,bb in [((u-width/2,z0+offset,.18),(u,peak+offset,.18)),((u,peak+offset,.18),(u+width/2,z0+offset,.18))]:
            f.line(a,bb,r,'pale stone',10,label+'-raking-cornice')
    f.box(u,z0,width+.16,.19,.52,.10,'pale stone',label+'-base-cornice')
    centerz=z0+(peak-z0)*.43
    shield=Point(u,centerz).buffer(1,resolution=24)
    from shapely.affinity import scale
    shield=scale(shield,xfact=.25,yfact=.35,origin=(u,centerz))
    f.prism(shield,-.01,.18,'pale stone',label+'-central-oval-shield')
    f.prism(shield.buffer(.055).difference(shield),.06,.23,'pale stone',label+'-shield-rim')
    for side in [-1,1]:
        for k in range(4):
            uu=u+side*(.42+k*.36);zz=z0+.20+(3-k)*.11
            curl(f,uu,zz,.63,.36,.135,label+'-foliate-relief-estimate')
        # Upper rising foliate ribs follow the visible triangular composition.
        pts=[f.point(u+side*x,z0+y,.145) for x,y in [(.27,.33),(.39,.64),(.67,.79),(1.03,.54),(1.32,.38)]]
        f.builder.tube(pts,.037,'pale stone',8,label+'-rising-leaf-estimate')


def cornice(f,eaves,decorated,entablature=1.50):
    bottom=eaves-entablature
    f.prism(box(-f.length/2,bottom,f.length/2,eaves),-.48,0,'pale stone','continuous-entablature-core')
    for z,h,depth,d in [(bottom+.08,.16,.36,.04),(bottom+.23,.14,.44,.07),(bottom+.38,.16,.38,.05),(bottom+.675,.45,.30,.03),(eaves-.54,.12,.44,.07),(eaves-.36,.24,.56,.10),(eaves-.17,.14,.64,.12),(eaves-.04,.08,.72,.14)]:
        f.box(0,z,f.length+.025,h,depth,d,'pale stone','layered-eaves')
    if decorated:
        n=max(1,round(f.length/.88))
        for u in np.linspace(-f.length/2+.45,f.length/2-.45,n):curl(f,u,bottom+.675,.68,.35,.205,'frieze-scroll-relief-estimate')
        for u in np.arange(-f.length/2+.16,f.length/2,.27):
            f.box(u,eaves-.26,.11,.16,.32,.20,'pale stone','eaves-dentil')


def roof_tile_profile(radius=.06,thickness=.011,segments=8):
    theta=np.linspace(0,math.pi,segments+1)
    outer=[(radius*math.cos(a),.034+radius*math.sin(a)) for a in theta]
    inner=[((radius-thickness)*math.cos(a),.034+(radius-thickness)*math.sin(a)) for a in reversed(theta)]
    return Polygon(outer+inner)


def roof_v2_retained_for_history(b,polygon,edges,eaves):
    inner=polygon.buffer(-1.95,join_style=2)
    if inner.is_empty:raise ValueError('Roof inset failed')
    rise=1.40
    ring=polygon.difference(inner)
    for k,poly in enumerate(pieces(ring)):
        for tri in constrained_delaunay_triangles(poly).geoms:
            pts=list(orient(tri,1.).exterior.coords)[:3]
            verts=[(x,y,eaves+min(1,polygon.exterior.distance(Point(x,y))/1.95)*rise) for x,y in pts]
            b.add(verts,[(0,1,2)],'gray roof tile','roof-hip-surface-sheet')
    b.plan_prism(inner,eaves+rise-.09,eaves+rise,'roof zinc','concealed-roof-core-closure-estimate')
    # P01 close inspection shows pan/cover tiles with finite ends overlapping
    # along the pitch, not thin cylindrical rails. Tile scales are estimates.
    cover=roof_tile_profile()
    pan_top=[(-.112,.037),(-.075,.026),(0,.020),(.075,.026),(.112,.037)]
    pan=Polygon(pan_top+[(x,z-.010) for x,z in reversed(pan_top)])
    tile_count=0;pitch=rise/1.95
    for index in [9,11,15,16,17,18]:
        f=edges[index]
        normal=(f.n*pitch+np.array([0.,0.,1.]));normal/=np.linalg.norm(normal)
        downhill=(f.n+np.array([0.,0.,-pitch]));downhill/=np.linalg.norm(downhill)
        for row,d0 in enumerate(np.arange(.035,1.91,.26)):
            d1=min(d0+.32,1.945);length=(d1-d0)*math.sqrt(1+pitch*pitch)
            for col,u in enumerate(np.arange(-f.length/2+.16,f.length/2-.24,.22)):
                corners=[f.point(u+side,0,-d) for side in [-.12,.232] for d in [d0,d1]]
                if not all(polygon.covers(Point(*p[:2])) for p in corners):continue
                if any(abs(polygon.exterior.distance(Point(*p[:2]))-d)>.035 for p,d in zip(corners,[d0,d1,d0,d1])):continue
                base=f.point(u,eaves+pitch*d1,-d1)
                def mapper(x,y,d,base=base,side=f.t,normal=normal,downhill=downhill,length=length):
                    # Lower tile ends lift14mm, yielding a visible noncoplanar
                    # overlap over the next lower row rather than z-fighting.
                    return base+side*x+normal*(y+.014*d/length)+downhill*d
                mat='gray roof tile light' if (row+col+index)%7==0 else 'gray roof tile'
                b.prism(cover,0,length,mapper,mat,'roof-lapped-cover-tile-v2')
                # Pan centered between two cover ridges; its edge sits under
                # the neighbouring rounded cover, as in the visible tile field.
                def panmapper(x,y,d,mapper=mapper):return mapper(x+.11,y,d)
                b.prism(pan,0,length,panmapper,'gray roof tile','roof-lapped-pan-tile-v2')
                tile_count+=2
    # One clear hip-cap line above the rounded southern return is visible in
    # P01. Its path is an estimated source-corner bisector, not a roof survey.
    chain=[edges[i] for i in [12,13,14]];half=sum(f.length for f in chain)/2;remaining=half
    for f in chain:
        if remaining<=f.length:lowxy=(f.a+f.t*remaining)[:2];break
        remaining-=f.length
    inward=-sum((f.n[:2] for f in chain),np.zeros(2));inward/=np.linalg.norm(inward)
    lo=0.;hi=4.5
    assert polygon.covers(Point(*(lowxy+inward*hi)))
    for _ in range(36):
        mid=(lo+hi)/2
        if polygon.exterior.distance(Point(*(lowxy+inward*mid)))<1.95:lo=mid
        else:hi=mid
    highxy=lowxy+inward*hi;low=np.r_[lowxy,eaves];high=np.r_[highxy,eaves+rise]
    down=low-high;span=float(np.linalg.norm(down));down/=span
    side=np.cross(np.array([0.,0.,1.]),down);side/=np.linalg.norm(side);normal=np.cross(down,side)
    hip=roof_tile_profile(.095,.014,10)
    for k,start in enumerate(np.arange(0,span-.05,.30)):
        length=min(.37,span-start);base=high+down*start
        def hipmapper(x,y,d,base=base,side=side,normal=normal,down=down,length=length):return base+side*x+normal*(y+.016*d/length)+down*d
        b.prism(hip,0,length,hipmapper,'gray roof tile light','roof-observed-rounded-return-lapped-hip-cap-v2')
    return inner,rise


def roof(b,polygon,edges,eaves):
    from roof_surface import build_roof
    return build_roof(b,polygon,edges,eaves)


def check_parts(builder):
    rows=[]
    for part in builder.parts:
        vv=np.asarray(part['vertices'],dtype=np.float32);keys={};ids=[]
        for xyz in vv:
            key=tuple(map(float,xyz));keys.setdefault(key,len(keys));ids.append(keys[key])
        ec={};ew={};vol=0.;collapsed=0
        for face in part['triangles']:
            wf=tuple(ids[i] for i in face);a,b,c=vv[list(face)].astype(float)
            collapsed+=int(len(set(wf))<3 or np.linalg.norm(np.cross(b-a,c-a))<=1e-12)
            vol+=float(np.dot(a,np.cross(b,c)))/6
            for i,j in zip(wf,wf[1:]+wf[:1]):
                edge=tuple(sorted((i,j)));ec[edge]=ec.get(edge,0)+1;ew[edge]=ew.get(edge,0)+(1 if i<j else -1)
        sheet=part['label'].endswith('surface-sheet')
        row={'label':part['label'],'triangles':len(part['triangles']),'float32_collapsed_triangles':collapsed,'boundary_edges':sum(x==1 for x in ec.values()),'nonmanifold_edges':sum(x>2 for x in ec.values()),'winding_conflicts':sum(ec[k]==2 and x!=0 for k,x in ew.items()),'signed_volume_m3':vol,'surface_sheet':sheet}
        row['passed']=collapsed==0 and row['nonmanifold_edges']==0 and row['winding_conflicts']==0 and (sheet or row['boundary_edges']==0 and vol>0)
        rows.append(row)
    return {'passed':all(r['passed'] for r in rows),'scope':'Each generated part after exact FLOAT32 positional welding. Solids are closed with paired winding and positive signed volume. Listed roof sheets intentionally have boundary edges; whole building ornaments are not Boolean-unioned. No render/accuracy claim.','parts':rows}


def build(output):
    source=json.loads((HERE/'geometry-input.json').read_text())
    coords=source['polygon_local_east_north'];polygon=Polygon(coords)
    assert polygon.is_valid and polygon.exterior.is_ccw and len(coords)==19
    b=Builder({'pale stone':{'color':[.61,.59,.52],'roughness':.78},'stone joints':{'color':[.40,.39,.35],'roughness':.87},
       'red brick':{'color':[.43,.18,.105],'roughness':.89},'red brick trim':{'color':[.47,.20,.12],'roughness':.85},
       'brick mortar':{'color':[.37,.27,.21],'roughness':.92},'window bronze':{'color':[.12,.10,.075],'roughness':.48,'metallic':.15},
       'recessed glass':{'color':[.17,.22,.23],'roughness':.29,'metallic':.12},'gray roof tile':{'color':[.19,.20,.195],'roughness':.82},
       'gray roof tile light':{'color':[.24,.245,.23],'roughness':.86}})
    edges=[Facade(b,a,c,f'edge-{i}') for i,(a,c) in enumerate(zip(coords,coords[1:]+coords[:1]))]
    f=edges[17];L=f.length
    cfg={'floor_bands':[0,4.40,9.30,12.80],'eaves':14.30,'entablature_depth':1.50,'pediment_peak':16.00,'loggia_depth':1.85,
         'main_window_centers':[-8.55,-7.05,-3.50,0,3.50,7.05,8.55],
         'brick_pier_centers':[-10.45,-5.75,5.75,10.45],
         'column_u':[-10.04,-6.17,-5.24,-4.77,-1.99,-1.52,1.52,1.99,4.77,5.24,6.17,10.04]}
    if (HERE/'model-calibration-input.json').is_file():cfg.update(json.loads((HERE/'model-calibration-input.json').read_text()))
    floors=cfg['floor_bands'];eaves=cfg['eaves'];depth=cfg['loggia_depth'];entab=cfg['entablature_depth'];walltop=eaves-entab;panes=[];opening_records=[]
    # Full source footprint remains the slab/roof anchor, including southern curve and rear steps.
    for i,z in enumerate([0,floors[1],floors[2],walltop]):b.plan_prism(polygon,z-.12 if i else 0,z+.06 if i else .14,'pale stone',f'full-source-footprint-slab-{i}')
    front_holes=[]
    ground_centers=[-8.24,-3.55,3.55,8.24];ground_widths=[3.02,2.17,2.17,3.02]
    for i,(u,w) in enumerate(zip(ground_centers,ground_widths)):
        sh,pp=arc_window(f,u,.38,w,3.65,w*.37,f'front-ground-{i+1}',rows=5,columns=4 if i in [0,3] else 2,depth=.30,surround=False)
        front_holes.append(sh);panes.extend(pp);opening_records.append({'label':f'front-ground-{i+1}','observed':True,'photo':['P01','P02'],'shape_bounds':list(sh.bounds)})
    portal=opening(0,.08,2.60,4.10,1.15,segments=40);front_holes.append(portal)
    opening_records.append({'label':'front-portal-recess','observed':True,'photo':['P02'],'current_partial':'P01 partly hides and changes the recess; interior glazing is a dated approximate closure','shape_bounds':list(portal.bounds)})
    _,pp=arc_window(f,0,.08,2.60,4.10,1.15,'front-portal-recess',rows=5,columns=2,depth=1.15,surround=False);panes.extend(pp)
    # Outer masonry: THREE genuinely open rectangles, visually divided into five
    # spans by round columns. No fake brick piers at the two central paired columns.
    outer_voids=[]
    for z0,z1 in [(floors[1]+.14,floors[2]-.12),(floors[2]+.16,walltop-.04)]:
        for a,c in [(-10.09,-6.11),(-5.39,5.39),(6.11,10.09)]:outer_voids.append(box(a,z0,c,z1))
    front_holes+=outer_voids
    arch_zones=[voussoir_zone(u,w)[0] for u,w in zip(ground_centers,ground_widths)]
    ground=f.wall(0,floors[1],front_holes,thickness=.48,material='pale stone')
    masonry(f,ground,False,exclude=unary_union(arch_zones))
    voussoir_records=[stone_voussoirs(f,u,w,13 if j in [0,3] else 9,f'front-ground-{j+1}-radial-voussoirs-v2') for j,(u,w) in enumerate(zip(ground_centers,ground_widths))]
    outer=f.wall(floors[1],walltop,front_holes,thickness=.48,material='red brick');masonry(f,outer,True)
    back=shifted(f,-depth,'front-loggia-rear-wall');rearholes=[]
    for floor in [2,3]:
        bot=floors[floor-1]+(.65 if floor==2 else .64);height=3.15 if floor==2 else 2.34
        for axis,u in enumerate(cfg['main_window_centers']):
            sh,pp=arc_window(back,u,bot,1.44 if axis not in [2,3,4] else 1.55,height,.69,f'front-rear-f{floor}-a{axis+1}',rows=5 if floor==2 else 2,columns=2,depth=.25)
            rearholes.append(sh);panes.extend(pp);opening_records.append({'label':f'front-rear-f{floor}-a{axis+1}','observed':True,'photo':['P02'],'current_partial':'P01 has oblique column occlusion','shape_bounds':list(sh.bounds)})
    rear=back.wall(floors[1]-.04,walltop+.04,rearholes,thickness=.40,material='red brick');masonry(back,rear,True)
    for floor in [2,3]:
        z0=floors[floor-1]+.15;z1=(floors[2]-.26) if floor==2 else walltop-.08
        for i,u in enumerate(cfg['column_u']):column(b,f,u,z0,z1,'tuscan' if floor==2 else 'corinthian',f'front-f{floor}-column-{i+1}',r=.18)
        for j,(a,c) in enumerate([(-10.09,-6.11),(-5.39,-2.15),(-1.31,1.31),(2.15,5.39),(6.11,10.09)]):
            if floor==2 and j==2:continue
            railing(b,f,a,c,floors[floor-1]+.17,-.08,f'front-f{floor}-railing-{j+1}')
    # Horizontal bands, pilaster caps and portal carrying the projected balcony.
    for z in floors[1:3]:
        for dz,h,pr in [(-.10,.14,.29),(.06,.14,.39),(.23,.11,.46)]:f.beam(z+dz,h,pr,'pale stone',label='continuous-storey-band')
    for u in [-10.45,-5.75,5.75,10.45]:
        for z in floors[1:3]:f.box(u,z+.13,.90,.30,.64,.04,'pale stone','brick-pier-stone-cap')
    for side in [-1,1]:
        u=side*1.57
        f.box(u,2.08,.42,4.10,.92,.61,'pale stone','portal-projecting-pilaster')
        f.box(u,.16,.62,.26,1.06,.61,'pale stone','portal-base')
        for j in range(5):curl(f,u,3.57+j*.053,.23,.16,1.09,'portal-capital-leaf-estimate')
    f.box(0,4.21,3.64,.50,1.08,.62,'pale stone','portal-entablature')
    f.box(0,4.48,3.80,.12,1.27,.66,'pale stone','portal-cap')
    # P01 crop resolves the gold inscription read right-to-left. The licensed
    # glyph contours are approximate typography, not traced original calligraphy.
    sign_record=add_facade_lettering(f,'局總商招船輪',0,4.21,2.95,.31,1.165,1.195,'aged brass',label='2025-entrance-gold-inscription',font=HERE/'fonts/Bund09SignSubset.otf')
    f.box(0,floors[1]+.12,3.84,.23,1.58,.58,'pale stone','central-balcony-platform')
    railing(b,f,-1.13,1.13,floors[1]+.24,1.22,'central-projecting-balcony',baluster_count=9)
    for side in [-1,1]:balcony_corner_post(b,f,side*1.43,floors[1]+.24,1.22,f'central-balcony-stepped-solid-corner-v2-{side}')
    for side in [-1,1]:
        a=f.point(side*1.71,0,-.08)[:2];c=f.point(side*1.71,0,.94)[:2]
        sidef=Facade(b,a,c,'balcony-side-'+str(side));railing(b,sidef,-sidef.length/2,sidef.length/2,floors[1]+.24,0,'return-balusters')
    for u in [-8.12,8.12]:
        panel=box(u-.26,floors[1]+.17,u+.26,floors[1]+1.03)
        f.prism(panel,-.25,.18,'pale stone','outer-balustrade-crest-panel')
        pts=[f.point(u+.29*math.cos(a),floors[1]+.98+.20*math.sin(a),.12) for a in np.linspace(0,math.pi,32)]
        b.tube(pts,.045,'pale stone',8,'outer-balustrade-arched-crest')
    # The southern rounded return is source edges12/13/14, one photographed
    # window axis. Source wall facets remain untouched; frame/glass are a chord
    # approximation behind the actual opening, not a rounded silhouette box.
    from shapely.affinity import translate
    chain=[12,13,14];total=sum(edges[i].length for i in chain)
    cf=Facade(b,edges[12].a[:2],edges[14].b[:2],'south-rounded-return-window-chord-estimate')
    curvedholes=[]
    for floor in [1,2,3]:
        bot=.38 if floor==1 else floors[floor-1]+.66;height=3.65 if floor==1 else 3.15 if floor==2 else 2.34
        sh,pp=arc_window(cf,0,bot,1.40,height,.70,f'south-curve-f{floor}',rows=5 if floor<3 else 3,columns=2,depth=.27)
        curvedholes.append(sh);panes.extend(pp)
        opening_records.append({'label':f'south-curve-f{floor}','observed':floor>1,'photo':['P01'],'status':'One opening spans source rounded-return facets12-14; upper windows seen, ground partly tree-hidden. Planar frame chord and depth are estimates.','shape_bounds':list(sh.bounds)})
    start=-total/2
    for i in chain:
        side=edges[i];center=start+side.length/2
        holes=[translate(sh,xoff=-center) for sh in curvedholes]
        wall=side.wall(0,walltop,holes,thickness=.43,material='red brick');masonry(side,wall,True)
        for z in floors[1:3]:side.beam(z,.17,.21,'red brick trim',label='side-storey-band')
        cornice(side,eaves,True,entab);start+=side.length
    # North and southern photographed return. Others remain explicitly unobserved,
    # with source-perimeter walls and no invented repeated window grid.
    for i,side in enumerate(edges):
        if i in [12,13,14,17]:continue
        holes=[];jobs=[]
        if i==18:axes=[-3.90,0,3.90];evidence=['P03'];status='2013 north side; current unchanged not separately confirmed'
        elif i==15:axes=[0];evidence=['P01','P02'];status='2025 east-facing short south wing'
        elif i==11:axes=[-1.24,1.24];evidence=['P01'];status='2025 upper arch crowns visible behind tree; lower openings are inferred continuations'
        else:axes=[];evidence=[];status='No observed openings reconstructed'
        for floor in [1,2,3]:
            bot=.38 if floor==1 else floors[floor-1]+.66;height=3.65 if floor==1 else 3.15 if floor==2 else 2.34
            for ai,u in enumerate(axes):
                rows=(7 if floor==2 else 3 if floor==3 else 5) if i==15 else (5 if floor<3 else 2)
                sh,pp=arc_window(side,u,bot,1.42,height,.71,f'side-{i}-f{floor}-a{ai+1}',rows=rows,columns=2,depth=.29,surround=not(i==18 and floor==1))
                holes.append(sh);panes.extend(pp);opening_records.append({'label':f'side-{i}-f{floor}-a{ai+1}','observed':not(i==11 and floor<3),'photo':evidence,'status':status,'shape_bounds':list(sh.bounds)})
        groundmat='pale stone' if i==18 else 'red brick'
        wall0=side.wall(0,floors[1],holes,thickness=.43,material=groundmat)
        wall1=side.wall(floors[1],walltop,holes,thickness=.43,material='red brick')
        if i in [9,10,11,12,13,14,15,16,18]:masonry(side,wall0,groundmat=='red brick');masonry(side,wall1,True)
        for z in floors[1:3]:
            side.beam(z,.17,.21,'pale stone' if i==18 else 'red brick trim',label='side-storey-band')
        cornice(side,eaves,i in [9,10,11,12,13,14,15,16,18],entab)
    cornice(f,eaves,True,entab)
    inner,roofrise=roof(b,polygon,edges,eaves+.01)
    for side in [-1,1]:pediment(f,side*8.22,5.00,eaves+.02,cfg['pediment_peak'],'front-end-pediment-'+str(side))
    # Northern roof: three visible2013 dormer/gable units, deliberately distinct
    # from the two eastern pediments. Position and relief dimensions estimated.
    north=edges[18]
    for k,u in enumerate([-4.25,0,4.25]):
        bot=eaves+.28;peak=eaves+(1.80 if k==1 else 1.36);width=1.48 if k==1 else 1.34
        face=shifted(north,-.70,'north-roof-dormer-'+str(k+1))
        outline=Polygon([(u-width/2,bot),(u+width/2,bot),(u+width/2,bot+.37),(u,peak),(u-width/2,bot+.37)])
        hole=Point(u,bot+.48).buffer(.22,resolution=24) if k==1 else opening(u,bot+.04,.43,.55,.215,segments=24)
        face.prism(outline.difference(hole),-.20,.04,'pale stone','north-dormer-cut-wall')
        face.prism(hole.buffer(-.025),-.22,-.20,'recessed glass','north-dormer-dark-opening')
        for a,c in [((u-width/2,bot+.37,.09),(u,peak,.09)),((u,peak,.09),(u+width/2,bot+.37,.09))]:face.line(a,c,.065,'pale stone',8,'north-dormer-raking-cap')
        if k==1:
            center=face.point(u,0,0);b.lathe(center[:2],[(peak,.06),(peak+.12,.07),(peak+.23,.03),(peak+.48,.026)],'pale stone',16,'north-dormer-centre-terminal-estimate')
        for sign in [-1,1]:
            v=[face.point(u,peak,.01),face.point(u+sign*width/2,bot+.37,.01),face.point(u+sign*width/2,bot+.37,-.85),face.point(u,peak,-.85)]
            order=(0,1,2,3)
            if np.cross(v[1]-v[0],v[2]-v[0])[2]<0:order=tuple(reversed(order))
            b.add(v,[order],'gray roof tile','north-dormer-roof-surface-sheet')
    # Low roof access/parapet strip is visible2025, concealed extent estimated.
    f.box(0,eaves+roofrise+.24,L*.72,.46,.24,-5.2,'pale stone','visible-upper-roof-parapet-estimate')
    # Current central gold circled company mark. Outline approximates photograph;
    # not a reproduced trademark typeface or geometrically exact logo tracing.
    cz=eaves-entab+.70
    for rad in [.275,.305]:
        pts=[f.point(rad*math.cos(a),cz+rad*math.sin(a),.25) for a in np.linspace(0,math.tau,65)]
        b.tube(pts,.022,'aged brass',8,'current2025-central-round-emblem-rim')
    for xs in [[-.16,-.06,0,.07,.17],[-.14,-.045,.04,.12]]:
        pts=[f.point(x,cz+(.075 if j%2 else -.08),.27) for j,x in enumerate(xs)];b.tube(pts,.026,'aged brass',8,'current2025-central-emblem-strokes-estimate')
    output.mkdir(parents=True,exist_ok=True)
    write(output/'roof-continuity-v3-check.json',b.roof_surface_report)
    write(output/'visible-detail-v2-check.json',{'schema':'bund09-visible-detail-v2-geometry-check-v1','source':'references/inspection-ground-voussoirs-v2.jpg; inspection-central-balcony-v2.jpg; inspection-roof-laps-v2.jpg','source_date':'2025-05-01','prior_raw_sha256':'de7fdbd4bb3f4b66e0f506aed39b4412a05481c610bea8607d352ebe4971dce6','voussoir_partitions':voussoir_records,'roof_lapped_tile_parts':sum(p['label'] in ['roof-lapped-cover-tile-v2','roof-lapped-pan-tile-v2'] for p in b.parts),'roof_observed_hip_cap_parts':sum(p['label']=='roof-observed-rounded-return-lapped-hip-cap-v2' for p in b.parts),'balcony_corner_posts':{'count':2,'construction':'Each post is one closed stepped mesh; no internal stacked-box caps','estimated_profile_m':{'body_width':.59,'plinth_width':.72,'cap_width':.75,'height':.90},'front_balusters_between_posts':9},'explicit_estimates':['13outer/9inner arch-stone division counts and joint widths','Pan/cover tile dimensions, exact lap and one visible rounded-return hip-cap path','Balcony post and cap dimensions'],'unchanged_unknown_roof':'Broad rear roof closure remains an estimate; no new survey claim.'})
    photo_report=None
    if (HERE/'photo-glass-controls.json').is_file():
        from photo_glazing import register
        photo_report=register(b,panes);write(output/'photo-uv-evidence.json',photo_report)
    by_label={part['label']:part for part in b.parts};inset_rows=[]
    for pane in panes:
        part=by_label[pane['label']];facade=pane['facade'];xyz=np.asarray(part['vertices'],dtype=np.float32).astype(float)
        ds=(xyz-facade.center)@facade.n;fb,ff=pane['frame_depth_m'];gap=ff-float(ds.max())
        row={'part':pane['label'],'actual_float32_glass_depth_m':[float(ds.min()),float(ds.max())],
             'frame_depth_m':[fb,ff],'front_recess_m':gap,
             'passed':float(ds.min())>=fb-.000003 and float(ds.max())<=ff+.000003 and abs(gap-.02)<.000003}
        inset_rows.append(row)
    inset={'schema':'bund09-actual-glass-frame-inset-v1','passed':all(r['passed'] for r in inset_rows),
           'scope':'All arc_window panes measured from actual FLOAT32 vertices in their own local facade normal. North dormer dark openings without independent grid frames are excluded and unchanged.',
           'unchanged_planes':'Each original facade, frame and rear-loggia1.85m plane is unchanged; only pane thickness/depth moved within its own frame.',
           'panes':inset_rows}
    write(output/'glass-frame-depth-check.json',inset);assert inset['passed']
    audit=check_parts(b);write(output/'bund09-all-parts-check.json',audit)
    assert audit['passed'],[r for r in audit['parts'] if not r['passed']][:20]
    metadata={'name':'Bund09 · 轮船招商总局大楼','id':'bund09','origin':source['anchor'],'source_footprint':'OSM way178408820 v9, exact19-vertex frozen perimeter','source_floor_tag_not_used':5,'observed_principal_floors':3,'height_is_measured':False,'front_outer_colonnade_shaft_positions_per_level':12,'rear_arches_per_upper_floor':7,'estimated_dimensions':cfg,'photo_source_date':'2025-05-01','historical_support_photo_date':'2013-12-29','source_photographs_embedded':bool(photo_report),'unknown_elevations':'Rear openings and obscured south ground are not surveyed; no repeated rear window grid invented','copyright':'Original geometry: MIT; footprint: © OpenStreetMap contributors, ODbL-1.0; Overture mapping source retained in geometry-input. Photograph if embedded: Suicasmo, CC0-1.0, 2025-05-01. Geometry observation also uses Legolas1024 CC BY-SA4.0 2013 photos, not embedded.'}
    report=b.save(output/'bund09-raw.glb',metadata)
    calibration={'schema':'bund09-photo-calibration-v1','geometry_input_sha256':hashlib.sha256((HERE/'geometry-input.json').read_bytes()).hexdigest(),'common_helper_sha256':hashlib.sha256((HERE.parent/'common/photo_architecture.py').read_bytes()).hexdigest(),'estimated_dimensions_m':cfg,'source_front_edge_length_m':L,'source_polygon_vertices':len(coords),'source_polygon_area_m2':polygon.area,'height_is_measured':False,'floor_tag5_not_used':True,'roof_hip_rise_m':roofrise,'observed_principal_floors':3,'front_upper_shaft_positions_per_level':12,'column_orders_by_level':{'2':'Tuscan, plain capital','3':'Corinthian, two ranks of estimated acanthus and volutes'},'front_rear_openings_per_upper_floor':7,'front_pediments':2,'north_roof_structures':3,'north_roof_date_status':'Observed2013, not separately confirmed2025','opening_records':opening_records,'roof_hidden_extent':'Inferred continuous hipped skirt and rear cap over exact footprint; full rear roof plan unknown','review_status':'Main front heights adjusted to independent2025 camera metric; all other proportions remain photo estimates. Parent fixed-camera visual acceptance is separate and pending.','entrance_sign':sign_record,'rendering_not_run':True,'bounds_glb':report['bounds_glb']}
    calibration['candidate_revision']='roof-continuity-v3'
    calibration['roof_revision']={'basis':'V2 actual native/photo review found uncovered triangular slope-join patches','geometry_check':'output/roof-continuity-v3-check.json','source_surface':'Same original polygon,inset1.95m andrise1.40m; all tile vertices share a continuous distance-to-boundary height function','scope':'Only gray roof tile/light meshes rebuilt; all non-roof geometry, including glass,stone arch joints,balcony posts,brick and lettering, remains exactly as v2. Balcony9front balusters retained as an explicitly uncertain estimate.'}
    calibration['visible_detail_revision']={'basis':'Native/photo review ofde7 candidate; root requested3visible fixes','geometry_check':'output/visible-detail-v2-check.json','changes':['4ground arches radial voussoir joints','Finite-thickness overlapping roof pan/cover tiles and one photographed hip-cap line','2stronger central balcony corner posts with9balusters between them'],'unchanged':'Source footprint, facade/loggia/window/column planes, glass depth, all photo control points, sourceJPEG, inferred rear-roof policy.'}
    calibration['glass_frame_depth_policy']={'frame_relative_to_depth_m':[.045,.12],'glass_relative_to_depth_m':[.08,.10],'front_recess_m':.02,'glass_thickness_m':.02,'unchanged_loggia_depth_m':depth,'actual_vertex_check':'output/glass-frame-depth-check.json','excluded':'Northern roof dormer dark openings have no separate grid frame and were not moved.'}
    write(HERE/'calibration.json',calibration)
    write(output/'bund09-summary.json',{k:report[k] for k in ['file','bytes','sha256','triangles','materials','parts','bounds_glb']})
    print(json.dumps({k:report[k] for k in ['file','bytes','triangles','materials','parts','bounds_glb']},ensure_ascii=False))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=HERE/'output');args=ap.parse_args();build(args.output)
