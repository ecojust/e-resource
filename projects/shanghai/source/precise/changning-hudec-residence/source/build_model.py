#!/usr/bin/env python3
"""Hudec current-restoration exterior: estimated C scale, original procedural materials."""
import sys, json, math, hashlib
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE / 'common'))
from photo_architecture import Builder, Facade, opening
from hudec_detail import roof_builder, detail_window, enrich, apply_atlas
MODE = sys.argv[1] if len(sys.argv)>1 else 'full'
OUTPUT = Path(sys.argv[2]).resolve() if len(sys.argv)>2 else Path(__file__).resolve().parent.parent/'review-v2'
if MODE not in ('full','lod'):
    raise ValueError('Use full or lod; web is compressed from full without simplification')
if (OUTPUT/('hudec-C-'+MODE+'.glb')).exists():
    raise FileExistsError('Use a fresh output directory; accepted assets are immutable')

D = json.loads((HERE / 'model-input.json').read_text())
T = np.array(D['provisional_architecture_east_axis_enu'])
N = np.array(D['provisional_architecture_north_axis_enu'])
OFFSET = np.array([1.175, 1.325])
PALETTE = {
    'white plaster': {'color': [.76, .75, .68], 'roughness': .9},
    'unverified service plaster': {'color': [.61, .57, .46], 'roughness': .9},
    'dark timber': {'color': [.045, .038, .028], 'roughness': .8},
    'slate-like plain roof': {'color': [.27, .18, .16], 'roughness': .85},
    'red brick silhouette': {'color': [.40, .12, .075], 'roughness': .85},
    'window glass': {'color': [.24, .30, .29], 'roughness': .45},
    'spatial ground base': {'color': [.40, .39, .34], 'roughness': .9},
    'dark metal': {'color':[.19,.21,.20], 'roughness':.58},
    'window lead': {'color':[.81,.80,.74], 'roughness':.65},
    'brick mortar': {'color':[.48,.47,.42], 'roughness':.95},
    'door wood': {'color': [.17, .09, .035], 'roughness': .85},
}


def build(h):
    b = Builder(PALETTE)
    parts = {k: list(v) for k, v in D['parts_in_door_units'].items()}
    H = D['heights_in_door_units']
    sx = h['north_service_east_offset_units']
    sy = h['north_service_north_offset_units']
    service = parts['north_service']
    service[:] = [service[0] + sx, service[1] + sx,
                  service[2] + sy, service[3] + sy]
    parts['north_connection'][1] += sx
    parts['north_connection'][3] += sy

    def region(r):
        return box(r[0], r[2], r[1], r[3])

    roof_panel = roof_builder(b,D,parts,MODE)

    def window(f,shape,label,cols=3,rows=3):
        detail_window(b,f,shape,label,cols,rows,MODE)

    def wall(f, eave, windows=(), door=None, material='white plaster', outline=None):
        holes = [v[0] for v in windows]
        if door is not None:
            holes.append(door)
        f.wall(.07, eave, holes=holes, thickness=.12, material=material, outline=outline)
        for shape, label, cols, rows in windows:
            window(f, shape, label, cols, rows)
        if door is not None:
            f.prism(door, -.14, -.11, 'door wood', 'door-recess-plane')
            frame = door.buffer(.04, join_style=2).difference(door)
            f.prism(frame, -.06, .035, 'dark timber', 'door-frame')

    def facade_rect(r, suffix, material='white plaster', height=2.9,
                    decorate=False, south_holes=(), north_holes=(), north_door=None):
        x0, x1, y0, y1 = r
        faces = [Facade(b, (x0, y0), (x1, y0), suffix + '/south'),
                 Facade(b, (x1, y0), (x1, y1), suffix + '/east'),
                 Facade(b, (x1, y1), (x0, y1), suffix + '/north'),
                 Facade(b, (x0, y1), (x0, y0), suffix + '/west')]
        for i, f in enumerate(faces):
            wins = south_holes if i == 0 else north_holes if i == 2 else ()
            wall(f, height, wins, north_door if i == 2 else None, material)
            if decorate and i in (0, 2):
                for z in (1.42, height - .07):
                    f.beam(z, .07, .035, 'dark timber', label='storey-beam')
        b.plan_prism(region(r), 0, .07, 'spatial ground base', suffix + '/plinth')
        return faces

    core = parts['main_core']
    sf = Facade(b, (core[0], core[2]), (core[1], core[2]), 'main-core/south')
    north_wins = [(opening(x, z, w, hh), 'north-window-grid', 3, 3)
                  for x, z, w, hh in [(-2.4, 1.65, 1.45, .98),
                                      (0, 1.65, .82, .98), (2.0, 1.65, .90, .98),
                                      (-.8, .35, .65, .90), (1.5, .35, .85, .90)]]
    south_wins = [(opening(x, .43, .52, .72), 'central-ground-window', 2, 2)
                  for x in (-.9, .9)]
    south_wins += [(opening(0, 1.65, 1.75, .98), 'central-upper-window', 4, 3)]
    fs = facade_rect(core, 'main-core', height=H['main_eave'], decorate=True,
                      south_holes=south_wins, north_holes=north_wins)
    # Arch is placed in the central south facade; rebuild that one small area
    # with a real opening, not a painted arch on the wall.
    # The first south skin is removed before replacement; other skins stay.
    b.parts = [p for p in b.parts if not p['label'].startswith('main-core/south/')]
    south = fs[0]
    door = opening(0, .07, .62, 1.0, arch=.24, segments=16)
    wall(south, H['main_eave'], south_wins, door)
    for z in (H['first_floor_beam'], H['second_floor_beam']):
        south.beam(z, .075, .03, 'dark timber', label='south-storey-beam')

    # North face is observed in the restored entrance photograph. Its exact
    # bearing/position remains conditional because camera GPS is not control.
    north = fs[2]
    for x in (-3.85, -3.0, -1.65, -.2, .75, 2.75, 3.85):
        top=H['main_eave']-.07
        north.box(x, (1.42+top)/2, .065, top-1.42, .065, .035, 'dark timber', 'observed-post-rhythm')
    for a, c in [((-3.7, 1.45, .04), (-2.9, H['main_eave']-.07, .04)),
                 ((2.7, 1.45, .04), (3.6, H['main_eave']-.07, .04))]:
        north.line(a, c, .032, 'dark timber', 4, 'observed-diagonal-brace')

    # Main roof, with two independently projecting south cross gables.
    x0, x1, y0, y1 = core
    yr = .18
    eave, ridge = H['main_eave'], H['main_ridge']
    roof_panel([(x0-.08,y0-.09,eave), (x1+.08,y0-.09,eave),
                (x1+.08,yr,ridge), (x0-.08,yr,ridge)], 'main/front-roof')
    roof_panel([(x0-.08,yr,ridge), (x1+.08,yr,ridge),
                (x1+.08,y1+.09,eave), (x0-.08,y1+.09,eave)], 'main/back-roof')
    b.tube([(x0-.09,yr,ridge+.025),(x1+.09,yr,ridge+.025)], .035,
           'slate-like plain roof', 6, 'main/ridge')
    for x, label in [(x0, 'west'), (x1, 'east')]:
        if label=='west':
            f=Facade(b,(x,y1),(x,y0),'main/west-gable')
            poly=Polygon([(-f.length/2,eave),(f.length/2,eave),(-yr,ridge)])
            w=opening(.85,3.33,.60,.40)
            f.prism(poly.difference(w),-.10,0,'white plaster','gable-infill')
            window(f,w,'observed-upper-west-window-provisional',2,1)
        else:
            b.add([(x,y0,eave),(x,y1,eave),(x,yr,ridge)], [(0,1,2)],
                  'white plaster', 'main/east-gable-infill')

    for key in ('south_west_projected_bay', 'south_east_projected_bay'):
        r = parts[key]
        xa, xb, ya, yb = r
        mid = (xa+xb)/2
        front = Facade(b,(xa,ya),(xb,ya),key+'/front')
        wins = [(opening(0,z,D['bay_window_widths_in_door_units'][key],.91),'projected-bay-grid',4 if key=='south_west_projected_bay' else 3,4)
                for z in (.28,1.55)]
        wall(front,eave,wins)
        for xx in (xa,xb):
            b.box((xx,(ya+yb)/2,eave/2),(.10,yb-ya,eave),
                  'white plaster',label=key+'/bay-return')
        peak = H['front_gable_peaks'][key]
        tri = Polygon([(-(xb-xa)/2,eave),((xb-xa)/2,eave),(0,peak)])
        aw = opening(0,2.96,D['bay_attic_window_widths_in_door_units'][key],.66)
        front.prism(tri.difference(aw),-.10,0,'white plaster','gable-real-attic-opening')
        window(front,aw,'attic-window',2,2)
        for z in (H['first_floor_beam'],H['second_floor_beam']):
            front.beam(z,.075,.04,'dark timber',label='bay-storey-beam')
        for xx in (-(xb-xa)/2+.045,0,(xb-xa)/2-.045):
            front.box(xx,(.07+eave)/2,.065,eave-.07,.07,.045,'dark timber','bay-post')
        front.line((-(xb-xa)/2,eave,.035),(0,peak,.035),.04,'dark timber',4,'gable-verge')
        front.line((0,peak,.035),((xb-xa)/2,eave,.035),.04,'dark timber',4,'gable-verge')
        front.line((0,eave,.035),(0,peak,.035),.035,'dark timber',4,'gable-kingpost')
        front.beam(3.75,.065,.03,'dark timber',width=(xb-xa)*.49,label='gable-crossbeam')
        curve=[(-(xb-xa)/2+.12+.50*t,eave+.50*t-.15*t*t,.04) for t in np.linspace(0,1,7)]
        b.tube([front.point(*p) for p in curve],.029,'dark timber',4,key+'/curved-brace')
        for sign in (-1,1):
            edge = mid+sign*(xb-xa)/2
            roof_panel([(edge,ya-.06,eave),(mid,ya-.06,peak),
                        (mid,yr,peak),(edge,yr,eave)],key+'/cross-roof-'+str(sign))
        b.tube([(mid,ya-.08,peak+.025),(mid,yr,peak+.025)],.03,
               'slate-like plain roof',6,key+'/ridge')

    # Lower side roofs really curve in section. They are not triangular boxes.
    for side,key in [(-1,'west_low_wing'),(1,'east_low_wing')]:
        r=parts[key];xa,xb,ya,yb=r
        outer=xa if side<0 else xb
        inner=xb if side<0 else xa
        fac=facade_rect(r,key,height=H['low_wing_eave'])
        front=fac[0]
        for xx in (-.35,.35):
            front.box(xx,.76,.045,1.15,.06,.025,'dark timber','low-wing-post')
        curve=[]
        for t in np.linspace(0,1,25 if MODE!='lod' else 13):
            x=inner+(outer-inner)*t
            z=H['low_wing_eave']+(eave-H['low_wing_eave'])*(1-t)**1.65
            curve.append((x,z))
        for (xx,zz),(xxx,zzz) in zip(curve,curve[1:]):
            roof_panel([(xx,ya-.08,zz),(xxx,ya-.08,zzz),
                        (xxx,yb+.04,zzz),(xx,yb+.04,zz)],key+'/curved-roof-strip')
        for y, back in [(ya,False),(yb,True)]:
            f=Facade(b,(xb,y),(xa,y),key+'/curved-back') if back else Facade(b,(xa,y),(xb,y),key+'/curved-front')
            sign=-1 if back else 1
            poly=Polygon([(sign*(x-(xa+xb)/2),z) for x,z in curve]+[
                (sign*(outer-(xa+xb)/2),.07),(sign*(inner-(xa+xb)/2),.07)])
            f.prism(poly,-.10,0,'white plaster','curved-side-fill')
        b.tube([(x,ya-.10,z+.015) for x,z in curve],.033,
               'dark timber',4,key+'/curved-verge')

    # Two tall main chimneys are explicitly supported by the historic front
    # image and restored close view. Brick joint texture is not attempted here.
    for x in (-4.05,4.05):
        b.box((x,.20,3.25),(.43,.50,2.3),'white plaster',label='main-chimney/white-base')
        b.box((x,.20,5.12),(.48,.48,1.96),'red brick silhouette',label='main-chimney/tall-shaft')
        b.box((x,.20,6.07),(.59,.60,.12),'red brick silhouette',label='main-chimney/cap')
        for dx in (-.20,.20):
            b.box((x+dx,-.055,5.12),(.045,.055,1.8),'red brick silhouette',label='main-chimney/vertical-rib')
        for z,w in [(4.15,.62),(4.24,.56),(4.33,.50)]:
            b.box((x,.20,z),(w,.59,.09),'red brick silhouette',label='main-chimney/stepped-foot')

    # Simple central roof dormer with three panes: spatial rhythm only.
    z=3.76
    df=Facade(b,(-.70,-1.60),(.70,-1.60),'main-central-dormer/front')
    dw=opening(0,z-.18,1.15,.40)
    df.wall(z-.31,z+.31,holes=[dw],thickness=.075,material='white plaster')
    for x in (-.70,.70):
        b.box((x,-1.25,z),(.07,.65,.62),'white plaster',label='main-central-dormer/side-return')
    b.box((0,-.925,z),(1.40,.07,.62),'white plaster',label='main-central-dormer/back-return')
    window(df,dw,'central-dormer-window',3,1)
    roof_panel([(-.79,-1.72,z+.32),(.79,-1.72,z+.32),(.79,-.80,z+.43),(-.79,-.80,z+.43)],'main-central-dormer/top')

    # Restored north entry porch: not the detached brick garden gate.
    r=parts['current_north_entry_porch'];xa,xb,ya,yb=r;mid=(xa+xb)/2
    porch=Facade(b,(xb,yb),(xa,yb),'current-north-entry-porch/front')
    po=opening(0,.08,.72,1.05,arch=.12,segments=12)
    tri=Polygon([(-(xb-xa)/2,.07),((xb-xa)/2,.07),((xb-xa)/2,1.4),(0,2.4),(-(xb-xa)/2,1.4)])
    wall(porch,1.4,door=po,outline=tri)
    for sign in (-1,1):
        edge=mid+sign*(xb-xa)/2
        roof_panel([(edge,yb+.08,1.4),(mid,yb+.08,2.4),
                    (mid,ya-.08,2.4),(edge,ya-.08,1.4)],'entry-porch/roof-'+str(sign))
    for u in (-(xb-xa)/2,0,(xb-xa)/2):
        porch.line((u,.08,.03),(u,1.4 if u else 2.4,.03),.038,'dark timber',4,'porch-post')
    porch.beam(1.4,.08,.04,'dark timber',label='porch-tie')
    porch.line((-(xb-xa)/2,1.4,.04),(0,2.4,.04),.047,'dark timber',4,'porch-verge')
    porch.line((0,2.4,.04),((xb-xa)/2,1.4,.04),.047,'dark timber',4,'porch-verge')

    # North-east service volume and neck are intentionally differentiated.
    # Their positions/hidden elevations are not architecturally accepted.
    for key,eh,rh in [('north_connection',1.9,2.22),('north_service',2.45,3.6)]:
        r=parts[key];xa,xb,ya,yb=r
        facade_rect(r,key,material='unverified service plaster',height=eh)
        xx=(xa+xb)/2
        for sign in (-1,1):
            edge=xa-.05 if sign<0 else xb+.05
            roof_panel([(edge,ya-.06,eh),(xx,ya-.06,rh),
                        (xx,yb+.06,rh),(edge,yb+.06,eh)],key+'/inferred-roof')
        b.tube([(xx,ya-.07,rh+.02),(xx,yb+.07,rh+.02)],.03,
               'slate-like plain roof',6,key+'/ridge')
        for y,reverse in [(ya,False),(yb,True)]:
            b.add([(xa,y,eh),(xb,y,eh),(xx,y,rh)],[(2,1,0)] if reverse else [(0,1,2)],
                  'unverified service plaster',key+'/inferred-gable-closure')
    # North repaired chimney is a stated restoration clue, not a measured site
    # position. It stays visibly on the separately labelled service component.
    s=parts['north_service'];cx=(s[0]+s[1])/2;cy=s[3]-.55
    b.box((cx,cy,3.38),(.32,.40,1.60),'red brick silhouette',label='north-service/provisional-repaired-chimney')

    # Three flying-bird silhouette markers, not a generic weather vane.
    gx=-2.5;gy=-2.72;gz=4.85
    b.tube([(gx,gy,4.58),(gx,gy,gz+.36)],.014,'dark timber',4,'three-birds/support')
    for i,(dx,dz) in enumerate([(-.17,.12),(.13,.34),(.15,-.04)]):
        verts=[(gx+dx-.13,gy,gz+dz),(gx+dx,gy-.03,gz+dz+.04),
               (gx+dx+.12,gy,gz+dz+.16),(gx+dx+.07,gy+.04,gz+dz-.01),
               (gx+dx-.02,gy+.01,gz+dz-.035)]
        b.add(verts,[(0,1,2,3,4)],'dark timber','three-birds/abstract-silhouette-'+str(i))

    enrich(b,D,parts,MODE)
    apply_atlas(b,ROOT)

    # Affine transform from our provisional architectural axes into source-
    # compatible ENU. The viewer must apply no additional model heading.
    scale=h['door_height_m_prior']
    for part in b.parts:
        vs=[]
        for x,y,z in part['vertices']:
            local=(np.array([x,y])-OFFSET)*scale
            en=T*local[0]+N*local[1]
            vs.append((float(en[0]),float(en[1]),float(z*scale)))
        part['vertices']=vs
    foot=unary_union([region(r) for r in parts.values()])
    def en_polygon(poly):
        return Polygon([(T*((x-OFFSET[0])*scale)+N*((y-OFFSET[1])*scale)).tolist()
                        for x,y in poly.exterior.coords])
    poly=en_polygon(foot)
    raw=Polygon(D['source_polygon_local_enu'])
    meta={'name':'Hudec House detailed exterior '+MODE,
          'id':D['id'],'stage':'root-authorized estimated exterior; appearance review pending',
          'revision':D['revision'],
          'hypothesis':h,'anchor':D['anchor_wgs84'],'heading_y':0,
          'source_uuid':D['source_uuid'],'source_osm':D['source_osm'],
          'height_is_measured':False,'source_polygon_is_house_wall':False,
          'mapped_footprint_m2':float(poly.area),'outside_coarse_source_m2':float(poly.difference(raw).area),
          'geometry_topology_provisional':False,'architectural_dimensions_measured':False,'roof_planes_valley_clipped':True,'roof_junctions_final_boolean_validated':False,
          'photographs_embedded':False,'aerial_red_roof_identity_unverified':True,'no_aerial_relocation':True,
          'south_photo_correspondence_sha256':D['south_photo_correspondence']['sha256'],
          'material_textures_original_procedural':True,'texture_license':'MIT','quality':MODE,
          'copyright':'Original geometry and procedural material atlases by agent, MIT; code MIT. Source map context: © OpenStreetMap contributors, ODbL-1.0. Reference photographs remain separately licensed and are not embedded.'}
    report=b.save(OUTPUT/('hudec-C-'+MODE+'.glb'),meta)
    return {'hypothesis':h,'metadata':meta,
            'footprint_enu':list(poly.exterior.coords),
            'parts_architecture_door_units':parts,
            'report':{k:v for k,v in report.items() if k!='part_summary'}}


result={'schema':'hudec-detailed-construction-metadata-v1','id':D['id'],
        'revision':D['revision'],
        'status':'estimated C exterior; review asset, not production acceptance','input_sha256':hashlib.sha256((HERE/'model-input.json').read_bytes()).hexdigest(),
        'hypotheses':[build(h) for h in D['hypotheses']],
        'selected_hypothesis':'C','main_written':False,'remote_written':False,
        'completed_model':False,'original_source_owner_replaced':False}
(OUTPUT/('model-metadata-'+MODE+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
for h in result['hypotheses']:
    print(h['hypothesis']['name'],h['report']['bytes'],h['report']['triangles'],
          h['metadata']['mapped_footprint_m2'],h['metadata']['outside_coarse_source_m2'])
