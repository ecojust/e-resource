#!/usr/bin/env python3
"""Bund05 individually photo-calibrated architecture and original per-pane glazing.

Local geographic geometry is frozen in geometry-input.json. Architectural
heights/depths are estimates recorded in calibration.json, not measured survey.
"""
from pathlib import Path
import argparse,hashlib,json,math,sys
import numpy as np
from shapely.geometry import Polygon,LineString,Point,box
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'common'))
from photo_architecture import Builder,Facade,opening,facade_ring
from photo_glazing import RegisteredGlazing
from sign_lettering import add_facade_lettering


def build(output):
 geo=json.loads((HERE/'geometry-input.json').read_text());cal=json.loads((HERE/'calibration.json').read_text())
 ring=geo['polygon_local_east_north'];footprint=Polygon(ring)
 B=Builder({'limestone':{'color':[.66,.645,.602],'roughness':.84},'carved pale stone':{'color':[.72,.705,.657],'roughness':.80},'stone joint':{'color':[.535,.525,.49],'roughness':.9},'plinth stone':{'color':[.46,.43,.36],'roughness':.83},'door wood':{'color':[.085,.065,.049],'roughness':.6},'door bronze':{'color':[.22,.16,.09],'roughness':.54,'metallic':.4},'recessed glass':{'color':[.105,.125,.125],'roughness':.28,'metallic':.12},'recessed glass light':{'color':[.20,.225,.215],'roughness':.30,'metallic':.1}})
 fs=facade_ring(B,footprint,'edge');front=fs[6];W=front.length;H=cal['levels_m'];P=cal['roof_parapet_m'];G=cal['gable_peak_m'];bays=[(n-.5)*W for n in cal['front_bay_centers_normalized']];outer=[bays[0],bays[-1]];middle=bays[1:3]
 stats={'windows':0,'open_walls':0,'three_face_bay_stacks':0,'balconies':0,'south_axis_count_estimated':12,'gable_count':0}
 walls=[];openings=[];photoglass=RegisteredGlazing();sign_records=[]
 def remember_wall(f,low,high,holes=(),thickness=.48,outline=None,material='limestone'):
  surface=f.wall(low,high,holes,thickness,material,outline);stats['open_walls']+=1;walls.append((f,surface))
  openings.extend({'facade':f.label,'bounds_uz':list(q.bounds),'area_m2':q.area} for q in holes)
  return surface
 def win(f,q,columns=4,rows=4,trim=True,label='window',glass='recessed glass'):
  if f is front and label in ('central-level-3','central-level-4','central-level-5'):photoglass.window(f,q,label)
  else:
   first=len(B.parts)
   f.window(q,columns,rows,trim=trim,label=label,glass=glass)
   # The common helper is frozen. Seat its same-frame ordinary glass20mm
   # behind the -.16m frame front; preserve every wall/frame/UV and triangle.
   moved=[]
   for part in B.parts[first:]:
    if part['material']==glass and part['label'].endswith('/'+label+'-glass'):
     part['vertices']=[tuple(np.asarray(v)+f.n*.14) for v in part['vertices']];moved.append(part)
   assert len(moved)==1,(f.label,label,len(moved))
  stats['windows']+=1
 def cornice(f,z,large=False,width=None):
  levels=[(-.22,.13,.18),(-.08,.14,.38),(.09,.18,.66),(.23,.12,.79)] if large else [(-.09,.12,.17),(.035,.13,.28),(.13,.08,.37)]
  for dz,h,p in levels:f.beam(z+dz,h,p,width=width,label='moulded-cornice')
  if large:
   count=max(3,round((width or f.length)/.56))
   for u in np.linspace(-(width or f.length)/2+.22,(width or f.length)/2-.22,count):f.box(u,z-.32,.25,.29,.70,.26,label='cornice-modillion')
 def rail(f,u,z,w,d=.70,stone=False):
  stats['balconies']+=1
  f.box(u,z-.05,w+.25,.18,d+.3,d/2-.04,label='balcony-slab')
  if stone:
   f.box(u,z+.80,w,.14,.26,d,label='stone-balustrade-rail')
   for x in np.linspace(u-w/2+.15,u+w/2-.15,max(4,int(w/.30))):
    c=f.point(x,0,d);B.lathe(c[:2],[(z+.03,.09),(z+.12,.11),(z+.19,.055),(z+.40,.095),(z+.57,.095),(z+.65,.055),(z+.73,.09)],segments=12,label=f.label+'/baluster')
  else:
   f.line((u-w/2,z+.88,d),(u+w/2,z+.88,d),.028,label='balcony-toprail');f.line((u-w/2,z+.16,d),(u+w/2,z+.16,d),.018,label='balcony-bottomrail')
   for x in np.linspace(u-w/2,u+w/2,max(4,int(w/.22))):f.line((x,z+.1,d),(x,z+.87,d),.018,label='balcony-upright')
   for sign in [-1,1]:f.line((u+sign*w/2,z+.88,.02),(u+sign*w/2,z+.88,d),.026,label='balcony-side-toprail')
   for k in range(4):
    a=u-w/2+k*w/4;b=a+w/4
    f.line((a,z+.18,d),(b,z+.73,d),.012,label='balcony-cross');f.line((a,z+.73,d),(b,z+.18,d),.012,label='balcony-cross')
 def panel(f,u,z,w,h,d=.08,label='relief'):
  f.prism(box(u-w/2,z-h/2,u+w/2,z+h/2),-.006,d,'carved pale stone',label)
 def pilaster(f,u,z0,z1,w=.78):
  f.box(u,(z0+z1)/2,w,z1-z0,.23,.075,label='giant-pilaster-shaft');f.box(u,z0+.18,w+0.3,.36,.37,.13,label='pilaster-base')
  q=Polygon([(u-w/2-.17,z1-.5),(u-w/2-.32,z1-.18),(u-w/2-.33,z1+.13),(u+w/2+.33,z1+.13),(u+w/2+.32,z1-.18),(u+w/2+.17,z1-.5)])
  f.prism(q,.02,.32,'carved pale stone','photo-simplified-curved-capital');f.box(u,z1+.17,w+.72,.12,.42,.18,label='capital-abacus')
 def front_pilaster(f,u,w=.78):
  # 2025 photo: shaft ends near the fifth-floor sill; the long pendant
  # capital/console continues upward to the small entablature above that row.
  # Proportions are hand-read from the independent planar rectification.
  z0=H[2]+.25;shaft_top=19.84
  f.box(u,(z0+shaft_top)/2,w,shaft_top-z0,.23,.075,label='front-giant-pilaster-shaft')
  f.box(u,z0+.18,w+.30,.36,.37,.13,label='front-pilaster-base')
  q=Polygon([(u-w*.45,19.70),(u-w*.69,19.76),(u-w*.83,19.91),
             (u-w*.87,20.12),(u-w*.76,20.30),(u-w*.52,20.44),
             (u-w*.48,21.88),(u-w*.72,22.18),(u+w*.72,22.18),
             (u+w*.48,21.88),(u+w*.52,20.44),(u+w*.76,20.30),
             (u+w*.87,20.12),(u+w*.83,19.91),(u+w*.69,19.76),
             (u+w*.45,19.70)])
  f.prism(q,.018,.31,'carved pale stone','front-photo-long-pendant-capital')
  f.box(u,22.23,w+0.72,.13,.45,.19,label='front-capital-abacus')
 def bay_stack(f,u,width=3.8,flat=2.35,depth=.8):
  stats['three_face_bay_stacks']+=1
  local=[(u-width/2,0),(u-flat/2,depth),(u+flat/2,depth),(u+width/2,0)]
  world=[tuple(f.point(x,0,d)[:2]) for x,d in local]
  for idx,(a,b) in enumerate(zip(world,world[1:])):
   bf=Facade(B,a,b,f'{f.label}/canted-bay-{u:.3f}/face-{idx}');qs=[]
   for floor in range(2,5):
    q=opening(0,[11.3,15.3,19.55][floor-2],bf.length-.27,2.35);qs.append(q)
   remember_wall(bf,H[2],H[5]-.05,qs,.27)
   for floor,q in enumerate(qs):
    win(bf,q,4 if idx==1 else 1,4,trim=True,label=f'bay-level-{floor+3}',glass='recessed glass light' if floor==1 else 'recessed glass')
    if floor<2:panel(bf,0,q.bounds[3]+.68,max(.25,bf.length-.48),1.12,.07,'bay-interstorey-panel')
  bp=Polygon(world+[tuple(f.point(u-width/2,0,0)[:2])])
  for z in [H[2],H[3],H[4],H[5]-.08]:B.plan_prism(bp,z-.10,z+.06,'limestone',f'{f.label}/bay-floor-cap')
  return opening(u,H[2]-.01,width,H[5]-H[2]+.02)
 def roof_gable(f,u,w=6.20,flagstaff=True):
  stats['gable_count']+=1
  q=Polygon([(u-w/2,H[6]-.05),(u+w/2,H[6]-.05),(u,G)])
  f.prism(q,-.45,.07,'limestone','triangular-gable-stone')
  for thickness,back,projection in [(.18,-.01,.43),(.08,.36,.58)]:
   border=LineString([(u-w/2-.12,H[6]),(u,G+.04),(u+w/2+.12,H[6])]).buffer(thickness,cap_style=2,join_style=2);f.prism(border,back,projection,'carved pale stone','sloping-pediment-moulding')
  relief=unary_union([box(u-.50,G-1.25,u+.50,G-.35),box(u-.21,H[5]+2.47,u+.21,G-.35)]);f.prism(relief,.065,.20,'carved pale stone','gable-central-tablet-and-vertical-keystone')
  fin=cal['gable_back_parapet_top_m'];back=Polygon([(u-2.72,H[6]),(u+2.72,H[6]),(u+2.72,fin-.80),(u+2.20,fin-.80),(u+2.20,fin-.16),(u+1.92,fin-.16),(u+1.92,fin),(u-1.92,fin),(u-1.92,fin-.16),(u-2.20,fin-.16),(u-2.20,fin-.80),(u-2.72,fin-.80)]);f.prism(back,-.80,-.32,'limestone','separate-stepped-stone-fin-behind-pediment')
  if flagstaff:
   c=f.point(u,0,-.60);B.lathe(c[:2],[(G-.15,.055),(cal['flagstaff_peak_m']-.15,.032),(cal['flagstaff_peak_m'],.025)],'painted window frame',segments=12,label=f.label+'/flagstaff-no-flag')
 # Footprint-preserving horizontal internal slabs; not a solid cuboid facade.
 vents=[]
 for center in middle:
  for off,w in [(-1.00,.46),(0,1.20),(1.00,.46)]:
   u=center+off
   pts=[tuple(front.point(a,0,d)[:2]) for a,d in [(u-w/2,.04),(u+w/2,.04),(u+w/2,-.43),(u-w/2,-.43)]]
   vents.append(Polygon(pts))
   front.box(u,.35,w,.46,.025,-.435,'interior shadow','plinth-vent-recess-back')
   for x in np.linspace(u-w/2+.05,u+w/2-.05,max(3,int(w/.10))):front.box(x,.35,.012,.45,.02,-.12,'wrought iron','plinth-vent-vertical-grille')
   for z in [.21,.35,.49]:front.box(u,z,w,.012,.02,-.12,'wrought iron','plinth-vent-horizontal-grille')
 B.plan_prism(footprint,0,.10,'plinth stone','source-footprint-plinth-lower')
 B.plan_prism(footprint.difference(unary_union(vents)),.10,.59,'plinth stone','source-footprint-plinth-open-vents')
 B.plan_prism(footprint,.59,H[0],'plinth stone','source-footprint-plinth-cap')
 for z in H[1:]:B.plan_prism(footprint.buffer(-.08),z-.17,z-.03,'interior shadow','internal-floor-slab')
 B.plan_prism(footprint,H[6]-.04,H[6]+.12,'roof zinc','sixth-floor-roof')
 # Front lower levels, central three-storey lights and a true canted bay cavity.
 f=front;holes=[];front_windows=[]
 for u in middle:
  q=opening(u,1.35,2.90,4.00,1.45,32);holes.append(q);front_windows.append((q,3,4,'ground-central-arch'))
  q=opening(u,H[1]+.60,1.75,2.75);holes.append(q);front_windows.append((q,4,4,'second-central-french'));rail(f,u,H[1]+.58,2.05,.66)
  for floor in range(2,5):
   q=opening(u,[11.3,15.3,19.55][floor-2],1.45,2.35);holes.append(q);front_windows.append((q,4,4,f'central-level-{floor+1}'))
  q=opening(u,24.25,1.35,1.45);holes.append(q);front_windows.append((q,3,3,'attic-central'))
  rail(f,u,H[2]+.30,2.25,.18,stone=True)
 for u in outer:
  q=opening(u,H[0],3.02,H[1]-H[0]-.75);holes.append(q)
  f.prism(q,-.41,-.35,'door wood','recessed-wood-door')
  # Carved panel door, a deep portal and two actual round columns.
  for side in [-1,1]:
   du=u+side*.75
   for z in [H[0]+1.2,H[0]+3.8]:
    circle=Point(du,z);ring_shape=circle.buffer(.432,quad_segs=16).difference(circle.buffer(.368,quad_segs=16));f.prism(ring_shape,-.33,-.285,'door bronze','door-circular-relief')
   f.box(du,H[0]+2.5,1.38,.12,.05,-.30,'door bronze','door-middle-crossbar')
   cp=f.point(u+side*1.69,0,.28);B.lathe(cp[:2],[(H[0],.25),(H[0]+.15,.26),(H[0]+.25,.20),(H[1]-.95,.18),(H[1]-.82,.23),(H[1]-.68,.27)],segments=28,label='front-portal-round-column')
  f.box(u,H[1]-.39,4.05,.65,.40,.10,label='portal-signboard-stone');f.box(u,H[1]-.10,4.20,.15,.78,.23,label='portal-entablature');f.box(u,H[1]+.06,4.50,.16,.96,.30,label='portal-canopy');f.box(u,H[1]-.68,3.9,.12,.46,.10,label='portal-lower-lintel')
  for text,off,width in [('HF Bank',-.99,1.25),('恒丰银行',.83,1.57)]:
   sign_records.append(add_facade_lettering(f,text,u+off,H[1]-.39,width,.32,.302,.322,'aged brass',label='2025-HF-Bank-raised-lettering'))
  logo=Polygon([(u-.25,H[1]-.39),(u+.02,H[1]-.13),(u+.29,H[1]-.39),(u+.02,H[1]-.65)])
  f.prism(logo,.302,.322,'aged brass','2025-HF-Bank-approximate-diamond-mark')
  q=opening(u,H[1]+.45,3.65,H[2]-H[1]-1.05,1.48,32);holes.append(q);front_windows.append((q,4,4,'second-outer-arch'))
  holes.append(bay_stack(f,u,cal['outer_bay_total_width_m'],cal['outer_bay_front_width_m'],cal['outer_bay_projection_m']))
  q=opening(u,24.36,3.50,2.00,.77,32);holes.append(q);front_windows.append((q,3,2,'attic-outer-segmental'))
  # Separate thick stone mullions, following the broad 3-part attic openings.
  for x in [u-.62,u+.62]:f.prism(box(x-.07,H[5]+.56,x+.07,H[5]+3.12).intersection(q),-.05,.15,'carved pale stone','attic-stone-mullion')
  f.prism(box(u-1.74,H[5]+1.45,u+1.74,H[5]+1.60).intersection(q),-.05,.15,'carved pale stone','attic-stone-transom')
  roof_gable(f,u)
 remember_wall(f,H[0],H[6],holes,.54)
 for q,cols,rows,label in front_windows:win(f,q,cols,rows,trim='ground' not in label and 'arch' not in label,label=label)
 # Rusticated arch rings; jointed solid stone shapes, not painted black arcs.
 for u in middle:
  q=opening(u,1.35,2.90,4.00,1.45,32)
  for x in [u-.94,u+.94]:f.prism(box(x-.06,1.35,x+.06,5.35).intersection(q),-.12,.02,'carved pale stone','ground-arch-stone-mullion')
  f.prism(box(u-1.45,3.80,u+1.45,3.95).intersection(q),-.12,.02,'carved pale stone','ground-arch-stone-transom')
  f.prism(q.buffer(.18,join_style=2).difference(q),-.02,.07,'carved pale stone','ground-arch-surround')
 for u in [bays[0]+2.36,0,bays[-1]-2.36]:front_pilaster(f,u,.68 if u else .80)
 for z,h,depth in [(22.34,.12,.39),(22.49,.12,.26)]:f.box(0,z,8.00,h,depth,depth/2-.02,label='front-central-fifth-floor-entablature')
 for u in outer:
  for sign in [-1,1]:
   f.box(u+sign*2.22,H[5]-.82,.45,1.28,.27,.055,label='bay-top-bracket-panel');f.box(u+sign*2.22,H[5]-.08,.65,.17,.42,.12,label='bracket-abacus')
 for z,large in [(H[2],False),(H[5],True)]:cornice(f,z,large)
 for u in [-3.65,0,3.65]:f.box(u,(H[6]+P)/2,.30,P-H[6],.38,.02,label='parapet-pier')
 f.box(0,H[6]+.06,7.6,.17,.45,.02,label='balustrade-base');f.box(0,P,7.6,.17,.49,.04,label='balustrade-coping')
 for u in np.linspace(-3.40,3.40,22):
  cp=f.point(u,0,.02);B.lathe(cp[:2],[(H[6]+.13,.085),(H[6]+.21,.10),(H[6]+.29,.05),(H[6]+.40,.09),(P-.18,.05),(P-.09,.085)],segments=12,label='front-roof-stone-baluster')
 # South long facade: rectangular bays with alternating projected balconies.
 # Count is explicitly provisional; windows are individually opened in one wall.
 south=fs[1];pitch=south.length/12;centers=np.linspace(-south.length/2+pitch/2,south.length/2-pitch/2,12)
 qs=[];side_windows=[]
 for j,u in enumerate(centers):
  for floor in range(6):
   lo=H[floor]+(.55 if floor else .9);height=H[floor+1]-lo-.55;width=1.40 if floor==5 else 1.65;rise=0
   if floor==5:lo=24.25;height=1.45
   if floor<2 and j in [1,10]:width=2.7;rise=1.25
   q=opening(u,lo,width,height,rise,28);qs.append(q);side_windows.append((q,floor,j))
  if j in (3,4,5,8,9,10,11):
   for floor in range(2,5):rail(south,u,H[floor]+.50,2.35,.72)
  if j%2==0:pilaster(south,u+pitch/2,H[2]+.25,H[5]-.75,.47)
 remember_wall(south,H[0],H[6],qs,.48)
 for q,floor,j in side_windows:win(south,q,3,4,trim=True,label=f'south-{j}-level-{floor+1}',glass='recessed glass light' if j%3==1 else 'recessed glass')
 for z,large in [(H[2],False),(H[5],True)]:cornice(south,z,large)
 south.beam(H[6]+.25,.50,.16,label='side-roof-parapet')
 # Preserve every small original return/chamfer. The north front wall is blind.
 for idx,f in enumerate(fs):
  if idx in (1,6):continue
  holes=[];ws=[]
  if idx in (3,5):
   count=2 if idx==3 else 1
   for u in np.linspace(-f.length/2+f.length/count/2,f.length/2-f.length/count/2,count):
    for floor in range(6):
     if idx==5 and floor==5:continue
     if idx==3 and floor==5:continue
     lo=H[floor]+(.55 if floor else .95);h=H[floor+1]-lo-.55;w=min(2.15,f.length/count-.7);arch=min(1.05,h*.4) if floor in (0,1,5) else 0
     if idx==5 and floor==1:arch=0 # 2011 chamfer second-floor light is rectangular.
     q=opening(u,lo,w,h,arch);holes.append(q);ws.append(q)
   if idx==3:
    q=opening(0,24.36,3.50,2.00,.77,32);holes.append(q);ws.append(q)
    roof_gable(f,0,w=6.20,flagstaff=False)
  elif idx in (0,9,11,13,15):
   # Unseen/rear planes are explicitly conservative estimated opening layouts.
   count=max(1,int(f.length/3.8))
   for u in np.linspace(-f.length/2+f.length/count/2,f.length/2-f.length/count/2,count):
    for floor in range(6):
     q=opening(u,H[floor]+.65,min(1.5,f.length/count-.8),min(2.25,H[floor+1]-H[floor]-1.25));holes.append(q);ws.append(q)
  remember_wall(f,H[0],H[6],holes,.46)
  if idx==5:
   # Visible 2011 blind attic panel: shallow stepped cross, not another window.
   cross=unary_union([box(-.45,25.10,.45,26.62),box(-.88,25.48,.88,26.16)])
   f.prism(cross,.008,.073,'carved pale stone','southeast-attic-blind-stepped-cross-relief')
  for q in ws:win(f,q,3,4,label='return-photo-window' if idx in (3,5) else 'estimated-rear-window')
  for z,large in [(H[2],False),(H[5],idx in (3,4,5,7))]:cornice(f,z,large)
  f.beam(H[6]+.23,.42,.12,label='return-roof-parapet')
 # Shallow light mortar courses, clipped to wall openings. They do not create
 # through-wall gaps or cover glass; no separate closed full-thickness blocks.
 for f,surface in walls:
  z0,z1=surface.bounds[1],surface.bounds[3]
  if '/canted-' in f.label:spacing=.44
  else:spacing=.52 if f.label in ('edge-6','edge-7','edge-5') else .65
  for z in np.arange(z0+.32,z1,spacing):
   line=box(-f.length/2,z-.008,f.length/2,z+.008).intersection(surface)
   if not line.is_empty:f.prism(line,.002,.005,'stone joint','shallow-horizontal-stone-joint')
 metadata={'name':'Bund05 Nissin Building — individually photo-registered architecture','building_id':'bund05','anchor':geo['anchor'],'copyright':'Original procedural geometry MIT; source footprint © OpenStreetMap contributors / Overture Maps Foundation, ODbL-1.0; geometry reference photographs: Suicasmo CC0 (2025), Can Pac Swire CC BY-SA2.0 (2011). Original 2025 JPEG by Suicasmo (CC0-1.0) is embedded unchanged only in individually registered central glass panes. 2011 photo is a geometric reference and is not embedded.','sources':['https://commons.wikimedia.org/wiki/File:Nissin_Building_20250501.jpg','https://commons.wikimedia.org/wiki/File:Formerly_the_Nissin_(Nihsin%3F)_Navigation_Co._Building_(6086545479).jpg','https://www.openstreetmap.org/way/178408821'],'geometry_input_sha256':hashlib.sha256((HERE/'geometry-input.json').read_bytes()).hexdigest(),'calibration_sha256':hashlib.sha256((HERE/'calibration.json').read_bytes()).hexdigest(),'height_is_measured':False,'front_width_m':W,'geometry_limitations':['Absolute heights/depths are photo-based estimates, not surveyed.','2025 front and2011 south facade references; south far-bay spacing and hidden rear openings remain provisional.','Only six central window assemblies have individually registered original photographic glazing; other surfaces retain geometric materials. No interiors or current-condition claim for historical fixtures.'],'features':stats}
 metadata['photographic_glazing']=photoglass.report();metadata['raised_sign_lettering']=sign_records
 report=B.save(output/'bund05.glb',metadata)
 (output/'photo-uv-evidence.json').write_text(json.dumps(photoglass.report(),ensure_ascii=False,indent=2)+'\n')
 audit={'schema':'bund05-photo-geometry-audit-v1','status':'built; requires root photographic camera comparison before acceptance','input_footprint_preserved':True,'front_edge':6,'front_width_m':W,'opening_count':len(openings),'stats':stats,'source_footprint_area_m2':footprint.area,'estimated_gable_top_m':G,'estimated_stone_fin_top_m':cal['gable_back_parapet_top_m'],'estimated_flagstaff_top_m':cal['flagstaff_peak_m'],'source_height_baseline_m':geo['existing_height']['height_m'],'source_height_baseline_is_measured':False,'outputs':{k:v for k,v in report.items() if k!='part_summary'},'holes':openings,'no_render_run':True,'no_main_project_modified':True}
 (output/'geometry-report.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k!='part_summary'},ensure_ascii=False,indent=2));return B,report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=HERE/'output');a=p.parse_args();build(a.output)
