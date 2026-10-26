#!/usr/bin/env python3
"""Bund 06: source-footprint, photo-informed Imperial Bank of China facade.

Run: python build_model.py --output /independent/output
Only the observed east facade is detailed. Rear openings are not invented.
Coordinates and dimensions are documented in calibration.json / evidence.json.
"""
from pathlib import Path
import argparse,json,hashlib,math,sys
import numpy as np
from shapely.geometry import Polygon,box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'common'))
from photo_architecture import Builder,Facade,opening
from photo_glazing import RegisteredGlazing


def pointed(u,bottom,width,height,rise,segments=28):
    a=width/2;c=(rise*rise-a*a)/(2*a);radius=a+c;spring=bottom+height-rise
    if c<0:raise ValueError('Pointed arch rise must be at least half width')
    right_angle=math.atan2(rise,c);left_angle=math.atan2(rise,-c)
    points=[(u-a,bottom),(u+a,bottom)]
    points.extend((u-c+radius*math.cos(t),spring+radius*math.sin(t)) for t in np.linspace(0,right_angle,segments+1))
    points.extend((u+c+radius*math.cos(t),spring+radius*math.sin(t)) for t in np.linspace(left_angle,math.pi,segments+1)[1:])
    return Polygon(points)


def gable(center,width,shoulder,peak,bottom=13.3):
    return Polygon([(center-width/2,bottom),(center+width/2,bottom),(center+width/2,shoulder),(center,peak),(center-width/2,shoulder)])


def profile_column(builder,facade,u,z0,z1,r=.23,d=.28,label='column'):
    c=facade.point(u,0,d)
    profile=[(z0,r*1.4),(z0+.12,r*1.4),(z0+.20,r*1.17),(z0+.29,r),
             (z1-.34,r*.85),(z1-.27,r*1.07),(z1-.14,r*1.3),(z1,r*1.3)]
    builder.lathe(c[:2],profile,segments=32,label=label)
    if r>.15:
        # Carved capital foliage is visible in2025. Twelve radial relief ribs
        # approximate the silhouette; these are not a surveyed acanthus pattern.
        for a in np.linspace(0,math.tau,12,endpoint=False):
            radial=np.array([math.cos(a),math.sin(a),0.])
            points=[c+radial*(r*.91)+np.array([0,0,z1-.30]),c+radial*(r*1.22)+np.array([0,0,z1-.18]),c+radial*(r*1.27)+np.array([0,0,z1-.09])]
            builder.tube(points,.018,'carved pale stone',8,label+'-capital-relief-rib-estimate')



def finial(builder,facade,u,z,scale=1,label='finial'):
    # Contemporary CC0 photograph: rounded stem and four-lobed floral head,
    # not two rectangular sticks. Lobe profiles remain proportion estimates.
    c=facade.point(u,0,.055)
    builder.lathe(c[:2],[(z,.12*scale),(z+.12*scale,.14*scale),(z+.23*scale,.065*scale),
                        (z+.42*scale,.06*scale),(z+.50*scale,.10*scale),
                        (z+.61*scale,.085*scale),(z+.73*scale,.025*scale)],segments=20,label=label+'-stem-bud')
    for a in [0,math.pi/2,math.pi,math.pi*1.5]:
        center=c[:2]+np.array([math.cos(a),math.sin(a)])*.07*scale
        builder.lathe(center,[(z+.49*scale,.008*scale),(z+.55*scale,.075*scale),(z+.64*scale,.065*scale),(z+.73*scale,.008*scale)],segments=12,label=label+'-floral-lobe')


def hood(facade,shape,width=.13,front=.115,label='archivolt'):
    # One polygonal moulding ring, no independent per-edge stone boxes.
    facade.prism(shape.buffer(width,join_style=2).difference(shape),-.02,front,'carved pale stone',label)
    facade.prism(shape.buffer(width+.075,join_style=2).difference(shape.buffer(width+.03,join_style=2)),.015,.085,'limestone',label+'-outer-bead')


def inset_window(facade,shape,label,rows=2,columns=2,depth=.38,surround=True,glazing=None,door=False):
    x0,z0,x1,z1=shape.bounds
    glazing.panes(facade,shape,label,rows,columns,depth)
    if surround and (x1-x0)>.40:hood(facade,shape,label=label+'-hood')
    if not door:facade.box((x0+x1)/2,z0-.075,(x1-x0)+.29,.15,.48,.08,'carved pale stone',label+'-sill')


def roof_plane(builder,facade,coords,label,material='roof zinc'):
    verts=[facade.point(u,z,d) for u,z,d in coords]
    # Determine upward-facing orientation in east/north/up space.
    normal=np.cross(verts[1]-verts[0],verts[2]-verts[0])
    order=tuple(range(len(verts)))
    if normal[2]<0:order=tuple(reversed(order))
    builder.add(verts,[order],material,label)


def build(output):
    source=json.loads((HERE/'geometry-input.json').read_text())
    coords=source['polygon_local_east_north'];polygon=orient(Polygon(coords),sign=1.)
    assert polygon.is_valid
    # Freeze keeps original vertex order; it is CCW. No reversed outward facade.
    assert Polygon(coords).exterior.is_ccw
    edges=[Facade(None,a,b,f'edge-{i}') for i,(a,b) in enumerate(zip(coords,coords[1:]+coords[:1]))]
    palette={
        'painted plaster':{'color':[.64,.625,.59],'roughness':.86},
        'carved pale stone':{'color':[.74,.72,.67],'roughness':.72},
        'limestone':{'color':[.66,.645,.61],'roughness':.79},
        'roof zinc':{'color':[.135,.145,.15],'roughness':.71,'metallic':.10},
        'recessed glass':{'color':[.07,.09,.08],'roughness':.27,'metallic':.18},
        'bronze window frame':{'color':[.028,.031,.029],'roughness':.53,'metallic':.18},
    }
    b=Builder(palette);glazing=RegisteredGlazing()
    for f in edges:f.builder=b
    front=edges[9];annex=edges[7];L=front.length
    assert abs(L-source['front_edge']['length_m'])<1e-6
    levels=[0,4.80,9.45,13.75];eaves=13.95;ridge=21.25;central_peak=22.03;roof_depth=14.2;ridge_depth=6.9
    group_lengths=[L*.18,L*.18,L*.28,L*.18,L*.18]
    groups=[];pos=-L/2
    for i,w in enumerate(group_lengths):
        groups.append({'index':i,'center':pos+w/2,'width':w,'axes':3 if i==2 else 2});pos+=w
    holes=[];window_jobs=[];observed_axes=[]
    for group in groups:
        gi=group['index'];center=group['center']
        for floor in range(3):
            # 2025 original resolves FOUR central windows on the third main
            # storey. Lower main storeys and the Gothic attic have three.
            centers=([-3.26,-1.40,.46,2.33] if floor==2 else [-3.12,-.47,2.13] if floor==1 else [center-2.5,center,center+2.5]) if gi==2 else [center-.93,center+.93]
            for ai,u in enumerate(centers):
                observed_axes.append({'group':gi,'axis':ai,'floor':floor+1,'u_m':u})
                bottom=[.02 if gi==2 else .92,5.97,10.52 if gi==2 else 10.40][floor]
                width=(2.10 if gi==2 else 1.30) if floor==0 else 1.36 if floor==2 and gi==2 else 1.45 if floor==1 and gi==2 else 1.60
                h=[3.76 if gi==2 else 2.58,2.30 if gi==2 else 2.10,2.36 if gi==2 else 2.45][floor]
                shape=opening(u,bottom,width,h,[width/2,.38,0][floor],segments=32)
                holes.append(shape)
                rows=[2,4,6][floor];columns=2 if floor==0 else 3
                window_jobs.append((shape,f'front-g{gi+1}-a{ai+1}-floor{floor+1}',rows,columns,1.05 if floor==0 and gi==2 else .38))
        # Small paired, central triple Gothic roof openings.
        if gi==2:
            for ai,u in enumerate([center-2.15,center,center+2.15]):
                shape=pointed(u,14.94,.95,2.53 if ai==1 else 1.86,.66)
                holes.append(shape);window_jobs.append((shape,f'central-attic-lancet-{ai+1}',5,3,.39))
            for vi,u in enumerate([center-.42,center,center+.42]):
                shape=opening(u,18.58,.17,1.72 if vi==1 else 1.42,.085,segments=16)
                holes.append(shape);window_jobs.append((shape,f'central-high-triple-vent-{vi+1}',1,1,.29))
        else:
            for ai,u in enumerate([center-.50,center+.50]):
                shape=pointed(u,14.65,.80,1.50,.48)
                holes.append(shape);window_jobs.append((shape,f'small-gable-{gi+1}-lancet-{ai+1}',4,2,.38))
            slot=opening(center,17.02,.21,.67);holes.append(slot);window_jobs.append((slot,f'small-gable-{gi+1}-rectangular-vent',1,1,.25))
    gables=[gable(g['center'],8.35 if g['index']==2 else 3.30,16.09 if g['index']==2 else 16.45,central_peak if g['index']==2 else 18.55) for g in groups]
    outline=unary_union([box(-L/2,0,L/2,eaves),*gables])
    wall=front.wall(0,ridge,holes,thickness=.50,material='painted plaster',outline=outline)
    for shape,label,rows,columns,depth in window_jobs:inset_window(front,shape,label,rows,columns,depth,glazing=glazing,door=depth>1)
    # Front grouped panels and vertical section mouldings; no invented repeated stone-block joints.
    boundaries=[-L/2,-L/2+group_lengths[0],-L/2+sum(group_lengths[:2]),L/2-sum(group_lengths[-2:]),L/2-group_lengths[-1],L/2]
    for j,u in enumerate(boundaries):
        front.box(u,eaves/2,.22,eaves,.24,.06,'limestone',f'group-boundary-{j}')
        for z in levels[1:]:front.box(u,z,.48,.27,.38,.1,'carved pale stone',f'group-cap-{j}')
    for z,h,d in [(0.16,.3,.18),(4.80,.21,.32),(4.98,.10,.38),(9.45,.20,.32),(9.63,.10,.37),(13.75,.23,.38),(13.98,.13,.42)]:
        front.beam(z,h,d,label='continuous-storey-cornice')
    # Thin framed apron panels below each actually observed upper-floor axis.
    for axis in observed_axes:
        if axis['floor']==1:continue
        u=axis['u_m'];z=5.08 if axis['floor']==2 else 9.71;top=5.77 if axis['floor']==2 else 10.20
        half=.67 if axis['floor']==3 and axis['group']==2 else .79
        panel=box(u-half,z,u+half,top)
        front.prism(panel.buffer(.035,join_style=2).difference(panel),.005,.065,'limestone','recessed-apron-panel-border')
    for group in groups:
        c=group['center'];span=7.90 if group['index']==2 else 4.38
        outer=box(c-span/2,10.20,c+span/2,13.15);inner=box(c-span/2+.17,10.20,c+span/2-.17,12.98)
        front.prism(outer.difference(inner),.025,.16,'carved pale stone','third-floor-group-architrave')
    for u in [-2.33,-.47,1.395]:profile_column(b,front,u,9.77,12.92,.075,.19,'central-third-floor-slender-pilaster')
    outer_vent=opening(0,18.37,1.56,2.35,.76)
    hood(front,outer_vent,.09,.065,'central-triple-slot-round-headed-surround')
    # Central entrance is deep and has four round columns supporting three arches.
    for i,u in enumerate([-3.81,-1.25,1.25,3.81]):
        profile_column(b,front,u,.12,2.71,.205,.30,f'central-porch-column-{i+1}')
    front.box(0,.08,8.55,.16,1.15,.2,'granite base','central-porch-step')
    front.box(0,5.43,9.03,1.00,.23,.65,'painted plaster','central-porch-solid-balcony-parapet')
    front.box(0,6.00,9.18,.14,.38,.65,'carved pale stone','central-porch-balcony-top-cap')
    front.box(0,4.78,9.20,.21,1.05,.32,'carved pale stone','central-porch-projecting-platform')
    # The photo metric separates lower OUTER pinnacles from taller INNER
    # pinnacles. Inner shafts also terminate in suspended tapered corbels.
    for i,u in enumerate([-L/2+.08,-group_lengths[2]/2,group_lengths[2]/2,L/2-.08]):
        c=front.point(u,0,.15);outer=i in [0,3]
        if outer:
            profile=[(9.45,.29),(9.60,.34),(9.75,.28),(13.73,.25),(13.91,.34),(14.12,.29),
                     (15.70,.23),(15.85,.30),(16.00,.28),(17.45,.075),(17.55,.06)]
            cone_end=17.55
        else:
            profile=[(11.05,.035),(11.22,.12),(11.42,.19),(11.58,.29),(11.76,.27),
                     (13.73,.25),(13.91,.34),(14.12,.29),(16.70,.23),(16.85,.30),(17.00,.28),(18.62,.075),(18.72,.06)]
            cone_end=18.72
        b.lathe(c[:2],profile,segments=32,label=f'four-round-pinnacles-{i+1}')
        finial(b,front,u,cone_end,.60,f'round-pinnacle-floral-finial-{i+1}')
    # Actual steep main roof; depth and pitch are explicitly inferred, not from an OSM roof tag.
    roof_plane(b,front,[(-L/2,eaves,-.04),(L/2,eaves,-.04),(L/2,ridge,-ridge_depth),(-L/2,ridge,-ridge_depth)],'front-main-roof')
    roof_plane(b,front,[(-L/2,ridge,-ridge_depth),(L/2,ridge,-ridge_depth),(L/2,eaves,-roof_depth),(-L/2,eaves,-roof_depth)],'back-main-roof')
    # Close end triangles. Back/side massing is source outline only, without invented fenestration.
    for sign in [-1,1]:
        u=sign*L/2;verts=[front.point(u,eaves,0),front.point(u,ridge,-ridge_depth),front.point(u,eaves,-roof_depth)]
        b.add(verts,[(0,1,2) if sign<0 else (0,2,1)],'painted plaster','main-roof-end')
    slope=(ridge-eaves)/ridge_depth
    for g,shape in zip(groups,gables):
        u=g['center'];wide=8.35 if g['index']==2 else 3.30;shoulder=16.09 if g['index']==2 else 16.45;peak=central_peak if g['index']==2 else 18.55
        d_eave=-(shoulder-eaves)/slope;d_peak=-(peak-eaves)/slope
        if peak<=ridge:
            roof_plane(b,front,[(u-wide/2,shoulder,.02),(u,peak,.02),(u,peak,d_peak),(u-wide/2,shoulder,d_eave)],f'gable-{g["index"]+1}-left-roof')
            roof_plane(b,front,[(u,peak,.02),(u+wide/2,shoulder,.02),(u+wide/2,shoulder,d_eave),(u,peak,d_peak)],f'gable-{g["index"]+1}-right-roof')
        else:
            # The central observed gable rises above the estimated main roof.
            # Close its small rear triangle at the ridge rather than leaving a
            # floating/open roof; this concealed intersection is an estimate.
            cut=(peak-ridge)/(peak-shoulder)*(wide/2)
            roof_plane(b,front,[(u-wide/2,shoulder,.02),(u,peak,.02),(u,peak,-ridge_depth),(u-cut,ridge,-ridge_depth),(u-wide/2,shoulder,d_eave)],f'gable-{g["index"]+1}-left-roof')
            roof_plane(b,front,[(u,peak,.02),(u+wide/2,shoulder,.02),(u+wide/2,shoulder,d_eave),(u+cut,ridge,-ridge_depth),(u,peak,-ridge_depth)],f'gable-{g["index"]+1}-right-roof')
            b.add([front.point(u-cut,ridge,-ridge_depth),front.point(u,peak,-ridge_depth),front.point(u+cut,ridge,-ridge_depth)],[(0,1,2)],'roof zinc',f'gable-{g["index"]+1}-ridge-rear-return')
        for side in [-1,1]:
            x=u+side*wide/2
            verts=[front.point(x,eaves,0),front.point(x,shoulder,0),front.point(x,shoulder,d_eave)]
            b.add(verts,[(0,1,2) if side<0 else (0,2,1)],'painted plaster',f'gable-{g["index"]+1}-return')
        # Separate outer and inner bargeboard mouldings follow the triangular silhouette.
        for a,bb in [((u-wide/2,shoulder,.12),(u,peak,.12)),((u,peak,.12),(u+wide/2,shoulder,.12))]:front.line(a,bb,.11,'carved pale stone',10,'gable-bargeboard')
        finial(b,front,u,peak,1.32 if g['index']==2 else 1.12,f'gable-{g["index"]+1}-floral-finial')
    # Discreet standing-seam geometry on observed dark roof; spacing is an estimate.
    for u in np.linspace(-L/2+.3,L/2-.3,65):
        b.tube([front.point(u,eaves+.026,-.05),front.point(u,ridge+.026,-ridge_depth)],.012,'roof zinc',6,'roof-seam-estimated-spacing')
    # The 2025 original resolves these as a blind rectangular-panel parapet,
    # not open vase balusters (the lower-resolution institutional image was ambiguous).
    occupied=unary_union([box(g['center']-(4.25 if g['index']==2 else 1.75),0,g['center']+(4.25 if g['index']==2 else 1.75),1) for g in groups])
    gaps=box(-L/2,0,L/2,1).difference(occupied)
    for gap in (gaps.geoms if hasattr(gaps,'geoms') else [gaps]):
        x0,_,x1,_=gap.bounds
        if x1-x0<=.10:continue
        count=max(1,round((x1-x0)/.43));step=(x1-x0)/count
        recesses=[box(x0+i*step+.065,14.10,x0+(i+1)*step-.065,14.48) for i in range(count)]
        front.prism(box(x0,13.98,x1,14.60).difference(unary_union(recesses)),-.06,.14,'carved pale stone','eaves-blind-parapet-frame')
        for pane in recesses:front.prism(pane,-.095,-.07,'painted plaster','eaves-blind-parapet-recess')
        front.box((x0+x1)/2,14.60,x1-x0,.14,.27,.08,'carved pale stone','eaves-parapet-top-rail')
    # Build the real mapped offset south annex independently, with 3 rectangular axes.
    ah=[];aj=[]
    for floor in range(3):
        for k in range(3):
            u=(k-1)*1.62;sh=opening(u,[.92,5.97,10.40][floor],1.18,[2.58,2.10,2.45][floor]);ah.append(sh);aj.append((sh,f'south-annex-floor{floor+1}-axis{k+1}'))
    annex.wall(0,eaves,ah,.48,'painted plaster')
    for sh,label in aj:inset_window(annex,sh,label,rows=6 if 'floor3' in label else 4 if 'floor2' in label else 2,columns=2,depth=.35,glazing=glazing)
    for z in [.16,4.80,9.45,13.75,14.43]:annex.beam(z,.20,.22,label='annex-horizontal-band')
    count=round(annex.length/.43);step=annex.length/count
    recesses=[box(-annex.length/2+i*step+.065,13.98,-annex.length/2+(i+1)*step-.065,14.31) for i in range(count)]
    annex.prism(box(-annex.length/2,13.84,annex.length/2,14.41).difference(unary_union(recesses)),-.06,.14,'carved pale stone','annex-blind-parapet-frame')
    for pane in recesses:annex.prism(pane,-.095,-.07,'painted plaster','annex-blind-parapet-recess')
    # Photo-observed black rainwater pipes on the main section junctions.
    # Exact pipe diameter/clamp spacing are proportional estimates.
    for i,u in enumerate([boundaries[1],boundaries[2]-.40,boundaries[3]+.40,boundaries[4]]):
        points=[front.point(u,eaves-.10,.13),front.point(u,eaves-.38,.24),front.point(u,.20,.24)]
        b.tube(points,.047,'wrought iron',12,f'observed-rainpipe-{i+1}')
        for z in np.arange(1.0,eaves-.7,2.0):
            front.box(u,z,.15,.045,.16,.23,'wrought iron','rainpipe-clamp-estimate')
    # Repeating dentils beneath the main attic cornice, visible on the source.
    for f in [front,annex]:
        for u in np.arange(-f.length/2+.24,f.length/2-.12,.54):
            z=eaves-.47
            profile=Polygon([(u-.15,z+.15),(u+.15,z+.15),(u+.15,z+.07),(u+.09,z+.07),(u+.075,z-.10),(u-.075,z-.10),(u-.09,z+.07),(u-.15,z+.07)])
            f.prism(profile,-.025,.22,'carved pale stone','observed-cornice-dentil-estimated-profile')
    # Frieze strips beneath upper-floor sills: seven clearly recurring dark
    # recessed vent positions, not an invented full ventilation system.
    vent_u=[]
    for g in groups:
        vent_u.extend([g['center']-2.02,g['center'],g['center']+2.02] if g['index']==2 else [g['center']])
    for band in levels[1:3]:
        z=band-.27
        voids=[box(u-.095,z-.075,u+.095,z+.075) for u in vent_u]
        front.prism(box(-L/2,z-.15,L/2,z+.15).difference(unary_union(voids)),.025,.18,'painted plaster','observed-under-cornice-frieze')
        for sh in voids:front.prism(sh,.005,.015,'interior shadow','blind-vent-recess-unmeasured-duct')
        # Larger support blocks are aligned with window group jambs.
        for g in groups:
            xs=[g['center']-1.88,g['center']+1.88] if g['index']!=2 else [g['center']-3.88,g['center']+3.88]
            for u in xs:
                front.box(u,z,.19,.28,.26,.09,'carved pale stone','observed-floor-cornice-corbel')
    # Whole original nonrectangular outline retained as a low-information rear envelope.
    for i,f in enumerate(edges):
        if i in [7,9]:continue
        f.wall(0,eaves,thickness=.48,material='painted plaster')
        f.beam(.18,.34,.10,material='granite base',label='mapped-base')
        f.beam(eaves,.20,.12,label='unobserved-rear-eaves-envelope')
    b.plan_prism(polygon,0,.10,'granite base','whole-footprint-base')
    # Rear/annex flat cap outside the main pitched roof footprint; exact source perimeter retained.
    front_roof_plan=Polygon([front.point(-L/2,0,0)[:2],front.point(L/2,0,0)[:2],front.point(L/2,0,-roof_depth)[:2],front.point(-L/2,0,-roof_depth)[:2]])
    rear_cap=polygon.difference(front_roof_plan)
    if not rear_cap.is_empty:b.plan_prism(rear_cap,eaves-.12,eaves,'roof zinc','unobserved-rear-flat-cap-estimate')
    metadata={'name':'Bund 06 · 中国通商银行大楼','id':'bund06','origin':source['anchor'],'facade_accuracy':'Photo-observed east facade topology; scale and hidden elevations explicitly inferred','source_footprint':'OSM way178408827 exact frozen polygon','source_floor_tag_not_used':6,'observed_main_floors':3,'roof_register':'five gables, attic','source_photographs_embedded':True,'primary_current_photo':'references/2025-suicasmo-cc0.jpg','copyright':'Original geometry: MIT; footprint: © OpenStreetMap contributors, ODbL-1.0. Photographic glazing: Suicasmo,2025-05-01,CC0-1.0 original JPEG; photo observations: Shanghai Urban Construction Archives source link;1908public-domain book.','height_is_measured':False,'estimated_roof_ridge_m':ridge,'independent_photo_metric':'calibration-independent.json','estimated_central_gable_stone_apex_m':central_peak}
    photo_report=glazing.apply(b)
    structural=[]
    for part in b.parts:
        if not part['label'].endswith('continuous-open-wall'):continue
        edge_counts={};edge_orientation={};v=np.asarray(part['vertices'],float);volume=0.
        for face in part['triangles']:
            a,bb,c=v[list(face)];volume+=float(np.dot(a,np.cross(bb,c)))/6
            for i,j in zip(face,face[1:]+face[:1]):
                edge=tuple(sorted((i,j)));edge_counts[edge]=edge_counts.get(edge,0)+1;edge_orientation[edge]=edge_orientation.get(edge,0)+(1 if i<j else -1)
        row={'label':part['label'],'vertices':len(v),'triangles':len(part['triangles']),
             'unpaired_edges':sum(x!=2 for x in edge_counts.values()),'winding_conflicts':sum(x!=0 for x in edge_orientation.values()),'signed_volume_m3':volume}
        row['passed']=row['unpaired_edges']==0 and row['winding_conflicts']==0 and volume>0
        structural.append(row)
    assert structural and all(row['passed'] for row in structural),structural
    output.mkdir(parents=True,exist_ok=True)
    (output/'bund06-photo-glazing-report.json').write_text(json.dumps(photo_report,ensure_ascii=False,indent=2)+'\n')
    (output/'bund06-structural-check.json').write_text(json.dumps({'passed':True,'scope':'Per continuous facade wall: paired indices, opposite directed edge winding, positive signed volume. No camera/render judgement.','walls':structural},ensure_ascii=False,indent=2)+'\n')
    solid_results=[];sheet_results=[]
    for part in b.parts:
        xyz=np.asarray(part['vertices'],dtype=np.float32)
        unique={};ids=[]
        for q in xyz:
            key=tuple(float(v) for v in q)
            if key not in unique:unique[key]=len(unique)
            ids.append(unique[key])
        ecounts={};ewinding={};volume=0.;collapsed=0
        for face in part['triangles']:
            wf=tuple(ids[i] for i in face)
            a,bb,c=xyz[list(face)].astype(float);cross=np.cross(bb-a,c-a)
            collapsed+=int(len(set(wf))<3 or np.linalg.norm(cross)<=1e-12)
            volume+=float(np.dot(a,np.cross(bb,c)))/6
            for i,j in zip(wf,wf[1:]+wf[:1]):
                edge=tuple(sorted((i,j)));ecounts[edge]=ecounts.get(edge,0)+1;ewinding[edge]=ewinding.get(edge,0)+(1 if i<j else -1)
        row={'label':part['label'],'triangles':len(part['triangles']),'float32_collapsed_triangles':collapsed,'boundary_edges':sum(v==1 for v in ecounts.values()),'nonmanifold_edges':sum(v>2 for v in ecounts.values()),'winding_conflicts':sum(ecounts[k]==2 and v!=0 for k,v in ewinding.items()),'signed_volume_m3':volume}
        is_sheet=(part['label'] in ['front-main-roof','back-main-roof','main-roof-end'] or part['label'].startswith('gable-') and part['label'].endswith(('-left-roof','-right-roof','-return')))
        row['passed']=collapsed==0 and row['nonmanifold_edges']==0 and row['winding_conflicts']==0 and (is_sheet or row['boundary_edges']==0 and volume>0)
        (sheet_results if is_sheet else solid_results).append(row)
    allparts={'passed':all(x['passed'] for x in solid_results+sheet_results),'scope':'Actual builder parts after FLOAT32 positional welding; closed solids separated from intentionally open roof and dormer surface sheets.','solids':solid_results,'surface_sheets':sheet_results,'common_helper_sha256':hashlib.sha256((HERE.parent/'common/photo_architecture.py').read_bytes()).hexdigest()}
    (output/'bund06-all-parts-check.json').write_text(json.dumps(allparts,ensure_ascii=False,indent=2)+'\n')
    assert allparts['passed'],[x for x in solid_results+sheet_results if not x['passed']]
    report=b.save(output/'bund06-raw.glb',metadata)
    calibration={'schema':'bund06-photo-calibration-v1','geometry_input_sha256':hashlib.sha256((HERE/'geometry-input.json').read_bytes()).hexdigest(),'common_helper_sha256':hashlib.sha256((HERE.parent/'common/photo_architecture.py').read_bytes()).hexdigest(),'topology_observed':{'ground_and_second_floor_groups':[2,2,3,2,2],'third_floor_groups':[2,2,4,2,2],'main_floor_window_counts':[11,11,12],'attic_groups':[2,2,3,2,2],'principal_floors':3,'main_gables':5,'tall_round_pinnacles':4,'south_flat_annex_axes':3,'high_central_lancet_vents':3},'map_dimensions':{'main_front_m':L,'annex_front_m':annex.length,'offset_connector_m':edges[8].length,'preserved_original_polygon_vertices':len(coords),'footprint_area_m2':polygon.area},'photo_observation_source':'evidence/official-photo-observations.json','primary_photo_observation_source':'evidence/2025-photo-observations.json','superseded_initial_interpretation':'Third floor central4windows; eaves blind panels; floral finials corrected using2025original.','calibration_status':'Revised after independent approximate camera/vanishing-line photo metric and root full orthographic review. Values remain estimates, not a survey; repeat root render acceptance required.','estimated_dimensions_m':{'principal_floor_bands':levels,'roof_eaves':eaves,'main_roof_ridge':ridge,'central_gable_stone_apex':central_peak,'pinnacle_outer_tip':17.988,'pinnacle_inner_tip':19.158,'outer_principal_window_bottoms':[.92,5.97,10.40],'outer_principal_window_heights':[2.58,2.10,2.45],'central_ground_door_bottom_width_height':[.02,2.10,3.76],'central_second_bottom_width_height':[5.97,1.45,2.30],'central_third_bottom_width_height':[10.52,1.36,2.36],'central_third_centers':[-3.26,-1.40,.46,2.33],'central_attic_bottom_height':[14.94,2.53],'small_attic_bottom_height':[14.65,1.50],'main_roof_depth':roof_depth,'ridge_setback':ridge_depth,'opening_width_varies_by_observed_type':True,'wall_thickness':.50,'window_frame_depth_parameter':.38,'ordinary_glass_front_d':-.315,'annex_glass_front_d':-.285,'central_portico_frame_depth_parameter':1.05,'central_portico_glass_front_d':-.985,'glass_behind_frame_front':.02,'glass_thickness':.02,'maximum_with_finials':report['bounds_glb']['max'][1],'roof_pitch_degrees':round(math.degrees(math.atan((ridge-eaves)/ridge_depth)),3)},'estimate_basis':'Independent2025photo metric uses EXIF Canon EOS M2/22mm, official approximate sensor size,7fitted facade line pairs and frozen32.218m main width. It yields approximate4.8/9.45/13.95m bands and smaller raised-sill openings; see calibration-independent.json sensitivity/plane limits. Main roof ridge21.25m at d=-6.9m remains an estimated depth-constrained fit. Prior19.2m baseline was only6floors*3.2m and is not a survey.','unobserved':['Rear windows, rear material divisions and complete rear roof layout','Precise roof pitch and column/arch thickness','2025 CC0 photograph confirms main south ground arch pair and fine pane-grid rhythm; absolute frame dimensions remain estimated','2025 CC0 photo confirms south annex ground3rectangular openings; fine material/depth dimensions are still estimates'], 'historic_features_not_transferred':['1908 roof ridge iron cresting','1908 chimney bundles','1908 flags, hanging signs and street poles'], 'facade_opening_count':len(holes),'annex_opening_count':len(ah),'wall_difference_area_m2':wall.area,'source_footprint_vertices_unmodified':True,'rendering_not_run':True,'glazing_rebate_revision':'Estimated glass seating20mm behind each existing frame front; all same-construction procedural/photo panes moved+.085m; walls/frames/UVs unchanged','photo_glazing_report':'output/bund06-photo-glazing-report.json','photographic_glass_panes':len(photo_report['panes']),'refined_window_evidence':'photo-glass-controls.json','ground_window_evidence':'ground-opening-photo-check.json','refinement_note':'Manual fine black-frame boundaries supersede earlier coarse upper-window rectangle widths. Central selected3F clear pane extent about1.19x2.19m; structural openings1.36x2.36m. Ground outer windows have raised sills; central doors remain floor-level with no window sill. Annex sill elevation is an unmeasured visual continuation, not a projection through the main plane.'}
    (HERE/'calibration.json').write_text(json.dumps(calibration,ensure_ascii=False,indent=2)+'\n')
    (output/'bund06-summary.json').write_text(json.dumps({'file':report['file'],'bytes':report['bytes'],'triangles':report['triangles'],'sha256':report['sha256'],'bounds_glb':report['bounds_glb'],'calibration':'calibration.json','provenance':'evidence.json'},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['file','bytes','triangles','materials','parts','bounds_glb']},ensure_ascii=False))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=HERE/'output');args=ap.parse_args();build(args.output)
