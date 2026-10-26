#!/usr/bin/env python3
"""Photo-led Bund07 architecture; original OSM plan, real wall holes and roof masses.

Metres east/north/up. Heights/depths remain photo estimates, never survey values.
The adjacent common package is a portable dependency; no production path needed.
"""
from pathlib import Path
import argparse, hashlib, json, math, sys
import numpy as np
from shapely.geometry import Polygon, Point, LineString, box
from shapely.geometry.polygon import orient
from shapely import affinity
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'common'))
from photo_architecture import Builder, Facade, opening, facade_ring
from sign_lettering import add_facade_lettering
from photo_glazing import RegisteredGlazing
from thai_sign import add_thai_bank_sign
from arch_grid_refinement import replace_front_arch_frame
from refine_components import ground_window, entrance_gate, observed_crest, dense_perimeter, dense_cap_profile


def build(output):
 geo=json.loads((HERE/'geometry-input.json').read_text());c=json.loads((HERE/'calibration.json').read_text())
 footprint=Polygon(geo['polygon_local_east_north'])
 B=Builder({'limestone':{'color':[.68,.662,.608],'roughness':.83},'carved pale stone':{'color':[.76,.74,.68],'roughness':.78},'stone joint':{'color':[.56,.548,.512],'roughness':.91},'roof zinc':{'color':[.038,.043,.041],'roughness':.76,'metallic':.28},'roof seam':{'color':[.072,.078,.071],'roughness':.79,'metallic':.21},'weathered stone':{'color':[.46,.455,.418],'roughness':.88},'recessed glass light':{'color':[.35,.39,.38],'roughness':.33,'metallic':.05},'blue roof cladding':{'color':[.27,.37,.40],'roughness':.75},'ground upper dark glass':{'color':[.075,.105,.105],'roughness':.33},'ground curtained glass':{'color':[.34,.38,.35],'roughness':.70},'gate dark backing':{'color':[.025,.029,.026],'roughness':.89},'gate old brass':{'color':[.14,.115,.065],'roughness':.65,'metallic':.4},'crest feather bronze':{'color':[.26,.092,.060],'roughness':.62,'metallic':.22},'crest blue green':{'color':[.16,.25,.22],'roughness':.65,'metallic':.18},'sign red':{'color':[.43,.055,.032],'roughness':.56},'sign gold':{'color':[.54,.39,.12],'roughness':.43,'metallic':.55}})
 fs=facade_ring(B,footprint);f=fs[3];W=f.length;H=c['levels_m'];E=c['end_centers_m'];C=c['central_centers_m'];wb=c['window_bottoms_m'];wh=c['window_heights_m']
 photoglass=RegisteredGlazing();walls=[];holes_record=[];stats={'main_storeys':4,'front_architectural_axes_upper':11,'windows':0,'front_roof_caps':2,'curved_front_pediments':2,'single_full_front_walls':1,'central_third_floor_pair':2};signs=[]
 def wall(fac,lo,hi,holes=(),outline=None):
  surface=fac.wall(lo,hi,holes,c['wall_thickness_m'],outline=outline);walls.append((fac,surface))
  holes_record.extend({'facade':fac.label,'bounds_uz':list(q.bounds),'area_m2':q.area} for q in holes);return surface
 def window(fac,q,label,cols=2,rows=2,trim=True,light=True):
  if label in photoglass.windows:photoglass.window(fac,q,label)
  elif label.startswith('front-L') and cols==2 and rows==2:
   inner=q.buffer(-.09,join_style=2);a,b,c0,d=inner.bounds;split=d-(d-b)*.40;mx=(a+c0)/2
   panes=[box(a,split+.042,c0,d),box(a,b,mx-.030,split-.042),box(mx+.030,b,c0,split-.042)]
   for k,pane in enumerate(panes):fac.prism(pane,-.20,-.18,'recessed glass light',label+f'-T-pane-{k}')
   fac.prism(q.buffer(-.025,join_style=2).difference(unary_union(panes)),-.27,-.16,'bronze window frame',label+'-T-frame-grid')
   if trim:fac.prism(q.buffer(.16,join_style=2).difference(q),-.025,.105,'carved pale stone',label+'-surround')
   a,b,c0,d=q.bounds;fac.box((a+c0)/2,b-.07,c0-a+.30,.14,.60,.10,label=label+'-sill')
  else:
   # Local construction correction; the frozen common generator is unchanged.
   # Keep its glass polygon/triangulation and shift only that solid along d.
   # Frame front=-.16; estimated glass front=-.18, back=-.20.
   first=len(B.parts)
   fac.window(q,cols,rows,trim=trim,glass='recessed glass light' if light else 'recessed glass',label=label)
   selected=[p for p in B.parts[first:] if p['label']==fac.label+'/'+label+'-glass']
   assert len(selected)==1
   selected[0]['vertices']=[tuple(np.asarray(v)+fac.n*.14) for v in selected[0]['vertices']]
   if label.startswith('front-ground-end-'):replace_front_arch_frame(fac,q,label)
  stats['windows']+=1
 def profile_beam(fac,z,width=None,center=0,large=False):
  for dz,ht,depth in ([(-.24,.13,.23),(-.10,.15,.36),(.065,.18,.66),(.22,.12,.78)] if large else [(-.10,.12,.18),(.035,.14,.31),(.15,.09,.40)]):
   fac.box(center,z+dz,width or fac.length+.10,ht,.50+depth,depth/2-.20,label='profiled-entablature')
  if large:
   w=width or fac.length;count=max(3,round(w/.49))
   for u in np.linspace(center-w/2+.18,center+w/2-.18,count):fac.box(u,z-.35,.19,.19,.45,.24,'weathered stone','cornice-dentil')
 def cornice_curve(fac,points,width=.10,low=.04,high=.35,label='curved-moulding'):
  fac.prism(LineString(points).buffer(width,cap_style=2,join_style=2),low,high,'carved pale stone',label)
 def pilaster(fac,u,z0,z1,width=.44,depth=.20):
  fac.box(u,(z0+z1)/2,width,z1-z0,depth,depth/2-.015,label='pilaster-shaft')
  fac.box(u,z0+.12,width+.18,.24,depth+.15,depth/2+.02,label='pilaster-foot')
  fac.box(u,z1-.06,width+.29,.15,depth+.24,depth/2+.05,label='pilaster-capital-abacus')
  # Photo shows shallow Ionic volutes, not leafy Corinthian capitals.
  for s in [-1,1]:
   pts=[fac.point(u+s*(width*.43+.065*math.cos(t)),z1-.24+.075*math.sin(t),depth+.04) for t in np.linspace(0,math.tau*1.6,24)]
   B.tube(pts,.025,'carved pale stone',8,fac.label+'/capital-scroll')
  fac.box(u,z1-.32,width*.36,.28,depth+.06,depth/2+.025,label='capital-pendant')
 def column(fac,u,z0,z1,r=.19,d=.25):
  cp=fac.point(u,0,d)
  B.lathe(cp[:2],[(z0,r*1.40),(z0+.12,r*1.40),(z0+.20,r*1.17),(z0+.28,r),(z1-.35,r*.90),(z1-.25,r*1.15),(z1-.15,r*1.30),(z1-.06,r*1.30)],segments=20,label=fac.label+'/round-column')
  fac.box(u,z1-.02,r*3.4,.14,r*3.4,d,label='column-abacus')
  for s in [-1,1]:
   pts=[fac.point(u+s*(r*1.05+.075*math.cos(t)),z1-.18+.072*math.sin(t),d+r*.91) for t in np.linspace(0,math.tau*1.5,24)]
   B.tube(pts,.025,'carved pale stone',8,fac.label+'/column-volute')
 def stone_rail(fac,u,z,w,d=.20):
  fac.box(u,z,w+.18,.14,.55,d,label='balustrade-foot');fac.box(u,z+.74,w+.20,.12,.48,d+.04,'weathered stone','balustrade-cap')
  n=max(3,round(w/.28))
  for x in np.linspace(u-w/2+.13,u+w/2-.13,n):
   p=fac.point(x,0,d);B.lathe(p[:2],[(z+.07,.085),(z+.13,.09),(z+.22,.05),(z+.38,.085),(z+.48,.085),(z+.57,.045),(z+.66,.07),(z+.70,.07)],segments=10,label=fac.label+'/stone-baluster')
 def iron_rail(fac,u,z,w,d=.29):
  fac.box(u,z-.045,w+.14,.12,.50,d-.08,label='juliet-sill')
  for zh,r in [(z+.10,.017),(z+.65,.028)]:fac.line((u-w/2,zh,d),(u+w/2,zh,d),r,label='juliet-rail')
  for x in np.linspace(u-w/2,u+w/2,max(4,round(w/.21))):fac.line((x,z+.06,d),(x,z+.66,d),.016,label='juliet-upright')
  for x in np.linspace(u-w/2+.20,u+w/2-.20,max(2,round(w/.5))):
   pts=[fac.point(x+.10*math.cos(t),z+.36+.22*math.sin(t),d) for t in np.linspace(0,math.tau,25)]
   # Do not repeat the same end point: tube caps close each nearly complete oval.
   B.tube(pts[:-1],.012,'wrought iron',7,fac.label+'/juliet-oval-scroll')
 def pediment(fac,u,z,w,rise,curved=False):
  pts=[(u-w/2,z),(u+w/2,z)]
  if curved:pts.extend((u+w/2*math.cos(t),z+rise*math.sin(t)) for t in np.linspace(0,math.pi,33))
  else:pts.append((u,z+rise))
  q=Polygon(pts);fac.prism(q,-.015,.15,'carved pale stone','window-curved-pediment' if curved else 'window-triangular-pediment')
  upper=([(u-w/2,z),(u,z+rise),(u+w/2,z)] if not curved else [(u-w/2*math.cos(t),z+rise*math.sin(t)) for t in np.linspace(0,math.pi,33)])
  cornice_curve(fac,upper,.09,.09,.37,'pediment-upper-moulding');fac.box(u,z-.035,w+.22,.16,.59,.18,label='pediment-base')
  if curved:
   cornice_curve(fac,[(u-w*.40*math.cos(t),z+.12+rise*.73*math.sin(t)) for t in np.linspace(0,math.pi,30)],.045,.15,.22,'pediment-inner-curve')
 def surround_stepped(fac,q):
  x0,z0,x1,z1=q.bounds;u=(x0+x1)/2
  fac.box(u,z1+.16,x1-x0+.52,.18,.26,.04,label='window-stepped-lintel')
  for s in [-1,1]:fac.box((x0 if s<0 else x1)+s*.20,z1-.12,.20,.56,.20,.06,label='window-ear-trim')
 # Slabs retain the frozen map plan; front/side walls are perforated shells.
 B.plan_prism(footprint,0,H[0],'granite base','original-footprint-base')
 for z in H[1:]:B.plan_prism(footprint.buffer(-.055),z-.19,z-.06,'interior shadow','internal-floor-slab')
 B.plan_prism(footprint,H[-1]-.05,H[-1]+.12,'roof zinc','main-fourth-floor-roof')
 qs=[];records=[]
 for u in E:
  q=opening(u,wb[0],4.40,wh[0],.68,36);qs.append(q);records.append((q,f'front-ground-end-{u:+.2f}',4,3,False))
  for level in [1,2,3]:
   for off,width in zip(c['end_window_offsets_m'],c['end_window_widths_m']):
    q=opening(u+off,wb[level],width,wh[level]);qs.append(q);records.append((q,f'front-L{level+1}-end-{u+off:+.2f}',2 if off==0 else 1,2,True))
   if level==1:pediment(f,u,wb[level]+wh[level]+.12,3.15,.90,True);stone_rail(f,u,wb[level]-.74,4.50,.22)
   elif level==2:
    for off,width in zip(c['end_window_offsets_m'],c['end_window_widths_m']):iron_rail(f,u+off,wb[level]-.75,width+.10)
    for off in [-2.90,-2.40,-.94,.94,2.40,2.90]:column(f,u+off,H[2]+.26,H[3]-.65,.18,.31)
   else:
    for off in [-2.90,-2.40,-.94,.94,2.40,2.90]:column(f,u+off,wb[level]-.15,H[4]-.40,.14,.30)
    f.box(u,wb[level]-.48,5.75,.75,.26,.08,label='end-fourth-floor-solid-apron')
 for j,u in enumerate(C):
  q=opening(u,wb[0],1.92,wh[0]);qs.append(q);records.append((q,f'front-ground-center-{j}',3,5,False))
  for level in [1,2,3]:
   if level==2 and j==2:
    for k in [-1,1]:
     q=opening(k*.48,wb[level],.71,wh[level]);qs.append(q);records.append((q,f'front-L3-middle-pair-{k}',1,2,True));iron_rail(f,k*.48,wb[level]-.75,.74)
   else:
    q=opening(u,wb[level],c['central_window_width_by_level_m'][level],wh[level]);qs.append(q);records.append((q,f'front-L{level+1}-center-{j}',2,2,True))
    if level==2:iron_rail(f,u,wb[level]-.75,c['central_window_width_by_level_m'][level]+.04)
   if level==1:pediment(f,u,wb[level]+wh[level]+.12,2.60,.94,j%2==1);stone_rail(f,u,wb[level]-.74,2.04,.22)
   elif level==3:stone_rail(f,u,wb[level]-.74,2.05,.21)
  if j<4:
   # Paired pilasters at inner bay divisions, seen in the 2025 close view.
   for off in [-.19,.19]:pilaster(f,(u+C[j+1])/2+off,H[2]+.28,H[3]-.65,.27,.20)
 wall(f,H[0],H[-1],qs)
 for q,label,cols,rows,trim in records:
  if label=='front-ground-center-2':entrance_gate(f,q,label)
  elif label.startswith('front-ground-center-'):ground_window(f,q,label);stats['windows']+=1
  else:window(f,q,label,cols,rows,trim)
  if '-L4-' in label or ('-L3-' in label and '-center-' in label):surround_stepped(f,q)
 # Ground rustication uses shallow faced courses over a continuous wall core.
 for u in [-14.2,-7.1,7.1,14.2]:f.box(u,(H[0]+H[1])/2,.55,H[1]-H[0],.22,.06,label='ground-pier-face')
 for u in E:
  arch=opening(u,wb[0],4.4,wh[0],.68,36)
  f.prism(arch.buffer(.30,join_style=2).difference(arch),.006,.10,'carved pale stone','ground-segmental-arch-surround')
  spring=wb[0]+wh[0]-.68
  for theta in np.linspace(.10,math.pi-.10,11):
   # Thin recessed-looking joints terminate in the wall, not through gaps.
   a=(u+2.20*math.cos(theta),spring+.68*math.sin(theta));b=(u+2.52*math.cos(theta),spring+1.12*math.sin(theta))
   line=LineString([a,b]).buffer(.008).difference(arch)
   if not line.is_empty:f.prism(line,.101,.105,'stone joint','radial-arch-joint')
 for u in [-1.38,1.38]:column(f,u,H[0]+.06,H[1]-.26,.23,.42)
 f.box(0,H[1]-.14,14.2,.73,.72,.26,label='bank-sign-lintel')
 pediment(f,0,H[1]+.20,4.65,1.15,True)
 # Readable observed wording. Font is a licensed approximation, not bank logo tracing.
 font=HERE.parent/'common/fonts/BundSignSubset-v6-1.otf'
 if font.is_file():
  signs.append(add_facade_lettering(f,'盤谷銀行',-4.82,H[1]-.16,3.44,.43,.622,.642,'sign gold',label='bank-Chinese-sign',font=font))
  signs.append(add_facade_lettering(f,'Bangkok Bank',3.72,H[1]-.16,5.55,.43,.622,.642,'sign gold',label='bank-English-sign',font=font))
  signs.append(add_thai_bank_sign(f,-1.02,H[1]-.18,3.90,.43,.622,.642))
 # Layered photo-observed silhouette/colors; microcarving remains approximate.
 crest_evidence=observed_crest(f)
 # Second-floor pediments interrupt the band: do not lay a full beam across their peaks.
 for z in [H[1],H[3],H[4]]:profile_beam(f,z,large=z>=H[3])
 # Separate returns: north seven visible axes; south nine axes from 2025.
 # Exact spacing and lower obscured openings remain explicit estimates.
 # The main front is original edge 3; edges 2 and 4 run along opposite sides.
 for idx in [2,4]:
  fac=fs[idx];is_north=idx==4;sideqs=[];side_recs=[]
  depths=c['side_axis_depths_from_front_m'] if is_north else c['south_side_axis_depths_from_front_m'];widths=c['side_window_widths_m'] if is_north else c['south_side_window_widths_m']
  for j,(dep,width) in enumerate(zip(depths,widths)):
   u=(-fac.length/2+dep) if is_north else (fac.length/2-dep)
   for level in range(4):
    lo=wb[level];ht=wh[level];wid=width if level else max(1.2,width);rise=.50 if level==0 else 0
    q=opening(u,lo,wid,ht,rise);sideqs.append(q);side_recs.append((q,f'side-{idx}-L{level+1}-bay-{j}',2 if width>1 else 1,2,level>0))
   if j in ([0,1,2] if is_north else [0,1,2,6,7,8]):
    for level in [2,3]:
     for off in [-width/2-.22,width/2+.22]:column(fac,u+off,H[level]+.27,H[level+1]-.65,.14,.25)
   if j in [3,4,5]:
    iron_rail(fac,u,wb[2]-.75,width+.05)
    for level in [2,3]:surround_stepped(fac,opening(u,wb[level],width,wh[level]))
   if j in ([1] if is_north else [1,7]):
    pediment(fac,u,wb[1]+wh[1]+.12,3.20,.90,True);stone_rail(fac,u,wb[1]-.74,4.30,.20)
  wall(fac,H[0],H[-1],sideqs)
  for q,label,col,row,trim in side_recs:window(fac,q,label,col,row,trim)
  for z in H[1:]:profile_beam(fac,z,large=z>=H[2])
  if is_north:
   # 2012 side photo confirms a low triangular attic dormer behind the corner drum.
   dep=10.8;u=(-fac.length/2+dep) if is_north else (fac.length/2-dep);base=H[-1]+.25
   q=opening(u,base+.25,2.85,.82);outline=Polygon([(u-2.65,base),(u+2.65,base),(u+2.65,base+1.05),(u,base+2.35),(u-2.65,base+1.05)])
   wall(fac,base,base+2.35,[q],outline);window(fac,q,f'side-{idx}-attic-dormer',2,1)
   cornice_curve(fac,[(u-2.70,base+1.08),(u,base+2.39),(u+2.70,base+1.08)],.13,-.02,.34,'side-attic-triangular-coping')
   # Far side curved gable is visible in 2012; placement/depth remain estimates.
   u=(-fac.length/2+20.3) if is_north else (fac.length/2-20.3);base=H[-1]+.10
   arc=[(u-2.45*math.cos(t),base+3.20*math.sin(t)) for t in np.linspace(0,math.pi,41)]
   outline=Polygon([(u-2.45,H[-1]),(u+2.45,H[-1])]+list(reversed(arc)))
   fac.prism(outline,-.40,.02,'limestone','estimated-position-observed-side-curved-gable')
   cornice_curve(fac,arc,.15,-.02,.26,'side-curved-gable-coping')
   fac.box(u,H[-1]+.44,.30,2.55,.18,.06,label='side-curved-gable-central-blind-tablet')
 # Rear: unobserved, therefore conservative plain walls, no fabricated window grid.
 for idx in [0,1]:
  wall(fs[idx],H[0],H[-1]);profile_beam(fs[idx],H[-1]);fs[idx].beam(H[-1]+.33,.55,.10,label='estimated-blind-rear-parapet')
 # Thin courses are clipped around actual holes; the full wall core remains intact.
 for fac,surface in [(a,b) for a,b in walls if a is f or a is fs[2] or a is fs[4]]:
  for z in np.arange(H[0]+.38,H[-1],.53):
   seam=box(-fac.length/2,z-.010,fac.length/2,z+.010).intersection(surface)
   if not seam.is_empty:fac.prism(seam,.002,.006,'stone joint','shallow-stone-course')
 # Center roof parapet, iron rail and separate flagstaffs.
 f.box(0,(H[-1]+c['central_roof_parapet_top_m'])/2,14.10,c['central_roof_parapet_top_m']-H[-1],.48,-.09,label='central-roof-parapet')
 f.box(0,c['central_roof_parapet_top_m'],14.30,.14,.70,-.02,label='parapet-coping')
 pediment(f,0,H[-1]+.13,3.05,1.13,False)
 for u in np.linspace(-6.75,6.75,35):f.line((u,c['central_roof_parapet_top_m']+.06,-.08),(u,c['central_roof_parapet_top_m']+.61,-.08),.014,label='roof-iron-upright')
 f.line((-6.85,c['central_roof_parapet_top_m']+.61,-.08),(6.85,c['central_roof_parapet_top_m']+.61,-.08),.024,label='roof-iron-toprail')
 for u in [-2.2,2.2]:
  cp=f.point(u,0,-1.0);B.lathe(cp[:2],[(H[-1]+.15,.055),(c['flagstaff_peak_m']-.12,.027),(c['flagstaff_peak_m'],.025)],'painted window frame',12,'roof-unflagged-pole')
 # Two rounded-rectangle closed metal caps, not hemispheres or open pavilions.
 for u in E:
  drum_top=c['roof_drum_top_m'];drum_bottom=c['roof_drum_base_m'];cw=c['roof_cap_width_m'];cd=c['roof_cap_depth_m'];depth=c['roof_cap_center_depth_m']
  base=box(-cw/2+.65,-cd/2+.65,cw/2-.65,cd/2-.65).buffer(.65,quad_segs=16)
  points=list(orient(base,sign=1.).exterior.coords)[:-1]
  # Horizontal CCW in world coordinates: facade tangent x inward normal.
  worldplan=Polygon([f.point(u+x,0,-depth-y)[:2] for x,y in points])
  # Perimeter shell: front ellipse and side lights are real holes, not glass
  # rectangles over a solid drum. Every small rounded-corner edge is retained.
  for df in facade_ring(B,worldplan,'corner-roof-drum'):
   dot=float(np.dot(df.n,f.n));side=abs(float(np.dot(df.n,f.t)));dqs=[]
   if dot>.99 and df.length>3.0:
    ez=c['front_curved_pediment_base_m']+.78
    dqs=[affinity.scale(Point(0,ez).buffer(1,quad_segs=24),.60,.39,origin=(0,ez))]
   elif side>.99 and df.length>3.0:
    dqs=[opening(du,drum_top-1.35,1.25,1.12) for du in [-1.10,1.10]]
   df.wall(drum_bottom,drum_top,dqs,.30)
   if side>.99:
    for j,dq in enumerate(dqs):window(df,dq,f'roof-drum-small-side-light-{j}',1,1)
   df.beam(drum_top-.08,.16,.10,label='roof-drum-cornice')
  B.plan_prism(worldplan,drum_top-.06,drum_top+.02,'roof zinc','corner-drum-top-slab')
  # Main curved pediment cuts an actual elliptical oculus through its shell.
  z0=c['front_curved_pediment_base_m'];zp=c['front_curved_pediment_peak_m'];gw=5.85
  arc=[(u-gw/2*math.cos(t),z0+(zp-z0)*math.sin(t)) for t in np.linspace(0,math.pi,41)]
  shape=Polygon([(u-gw/2,z0-.12),(u+gw/2,z0-.12)]+list(reversed(arc)))
  eye=affinity.scale(Point(u,z0+.78).buffer(1,quad_segs=24),.60,.39,origin=(u,z0+.78))
  f.prism(shape.difference(eye),-.44,.14,'carved pale stone','front-curved-pediment-with-oculus')
  f.prism(eye,.155,.175,'recessed glass light','front-roof-elliptical-oculus-glass')
  f.prism(eye.buffer(.10).difference(eye),.13,.24,'carved pale stone','elliptical-oculus-surround')
  f.box(u,z0+.78,.045,.76,.07,.16,'painted window frame','oculus-central-mullion')
  cornice_curve(f,arc,.14,.10,.51,'curved-roof-pediment-coping');cornice_curve(f,[(x,z-.20) for x,z in arc],.065,.15,.30,'curved-roof-inner-moulding')
  profile_beam(f,z0,width=gw+.48,center=u)
  for side in [-1,1]:
   f.box(u+side*3.02,z0+.04,.56,.37,.70,.11,label='roof-pediment-corner-plinth')
   cp=f.point(u+side*3.02,0,.10);B.lathe(cp[:2],[(z0+.20,.11),(z0+.38,.16),(z0+.55,.07),(z0+.65,.03)],segments=12,label='roof-corner-stone-acroterion')
  points=dense_perimeter(orient(base,sign=1.),.24)
  profile=dense_cap_profile(c['roof_cap_crown_depth_scale'])
  vertices=[];n=len(points);rise=c['roof_cap_peak_m']-drum_top
  for zh,xscale,yscale in profile:
   vertices.extend(f.point(u+x*xscale,drum_top+zh*rise,-depth-y*yscale) for x,y in points)
  bottom_center=len(vertices);vertices.append(f.point(u,drum_top,-depth));top_center=len(vertices);vertices.append(f.point(u,c['roof_cap_peak_m'],-depth))
  last=(len(profile)-1)*n
  faces=[(bottom_center,(j+1)%n,j) for j in range(n)]+[(top_center,last+j,last+(j+1)%n) for j in range(n)]
  for k in range(len(profile)-1):
   for j in range(n):a=k*n+j;b=k*n+(j+1)%n;faces.append((a,b,b+n,a+n))
  B.add(vertices,faces,'roof zinc','closed-rounded-rectangular-metal-cap')
  # Fine closed curvature; standing seam spacing is an estimated ~0.55 m.
  for j in np.linspace(0,n-1,44,dtype=int):
   x,y=points[j];pts=[f.point(u+x*xs,drum_top+zh*rise+.018,-depth-y*ys) for zh,xs,ys in profile]
   B.tube(pts,.012,'roof seam',6,'roof-cap-standing-seam')
  # Front/back urn positions follow the 2012 ridge view; exact offsets estimated.
  for dd in [depth+off for off in c['roof_finial_center_offsets_depth_m']]:
   cp=f.point(u,0,-dd);z=c['roof_cap_peak_m']-.12
   B.lathe(cp[:2],[(z,.09),(z+.12,.13),(z+.25,.09),(z+.44,.20),(z+.62,.22),(z+.76,.13),(z+.85,.04)],'roof zinc',16,'roof-ridge-urn-finial')
 # Rear roof: two arched stone hoods each side of a separate central triangle.
 # 2016 front photograph resolves this topology; 2025 corroborates the exposed
 # arch heads/triangle but hides lower openings behind the front stone parapet.
 dep=c['setback_roof_depth_from_front_m'];rw=c['setback_roof_width_m'];rh=c['setback_roof_height_m'];a=f.point(-rw/2,0,-dep)[:2];b=f.point(rw/2,0,-dep)[:2];rf=Facade(B,a,b,'setback-roof-front')
 roofholes=[]
 for u in c['setback_arch_axes_m']:
  q=opening(u,c['setback_window_bottom_m'],1.55,c['setback_window_height_m']);roofholes.append(q)
 # Blue cladding is observed in the dated 2016 photograph, not a claimed 2025 albedo measurement.
 rf.wall(H[-1],H[-1]+rh,roofholes,.22,'blue roof cladding');holes_record.extend({'facade':rf.label,'bounds_uz':list(q.bounds),'area_m2':q.area} for q in roofholes)
 for j,(u,q) in enumerate(zip(c['setback_arch_axes_m'],roofholes)):
  window(rf,q,f'setback-rectangular-light-{j}',2,2)
  pediment(rf,u,c['setback_window_bottom_m']+c['setback_window_height_m']+.05,1.95,.68,True)
 # No fifth arched glass light is invented in the central obscured section.
 pediment(rf,0,c['setback_central_triangle_base_m'],1.75,c['setback_central_triangle_peak_m']-c['setback_central_triangle_base_m'],False)
 rplan=Polygon([f.point(u,0,-d)[:2] for u,d in [(-rw/2,dep),(rw/2,dep),(rw/2,dep+4.0),(-rw/2,dep+4.0)]])
 B.plan_prism(rplan,H[-1]+rh-.03,H[-1]+rh+.10,'roof zinc','estimated-setback-roof-top')
 # Thin blue edge/corrugated ridge clue; micro-corrugation shape/depth is estimated.
 rf.box(0,H[-1]+rh+.08,rw+.20,.12,.42,.05,'blue roof cladding','observed-rear-roof-edge')
 for fac in facade_ring(B,rplan,'setback'):
  if np.dot(fac.n,f.n)<.9:fac.wall(H[-1],H[-1]+rh,(),.22,'blue roof cladding')
 stats.update({'central_ground_gate':1,'central_ground_three_by_five_windows':4,'setback_arched_stone_hoods':4,'setback_central_triangle':1,'setback_unproven_fifth_arch_removed':True,'cap_vertical_profile_rings':37})
 metadata={'name':'Bund07 Great Northern Telegraph Building / Bangkok Bank','building_id':'bund07','anchor':geo['anchor'],'copyright':'Procedural source MIT. Frozen footprint © OpenStreetMap contributors / Overture Maps Foundation, ODbL-1.0. Geometry references: Suicasmo (2025) CC0; Ferox Seneca (2012) CC BY-SA 3.0; xiquinhosilva (2016) CC BY 2.0; Chainwit. (2024) CC BY 4.0. Original 2025 JPEG by Suicasmo (CC0-1.0) is embedded unchanged only in eighteen individually registered glass panes; other reference photos are not embedded.','sources':['https://www.openstreetmap.org/way/178408810','https://commons.wikimedia.org/wiki/File:Great_Northern_Telegraph_Building_20250501.jpg'],'geometry_input_sha256':hashlib.sha256((HERE/'geometry-input.json').read_bytes()).hexdigest(),'calibration_sha256':hashlib.sha256((HERE/'calibration.json').read_bytes()).hexdigest(),'height_is_measured':False,'front_width_m':W,'features':stats,'raised_sign_lettering':signs,'limitations':c['uncertainties']+['Rear walls intentionally plain because rear openings are unobserved.','Chinese, Thai and English bank wording uses licensed approximate typefaces, not exact bank logo tracing. Garuda major wing/crown/leg/scroll forms follow the photograph; microcarving and tiny scroll lettering remain simplified.','Photographic glass is limited to six unobstructed central upper windows; other glazing remains geometric material.']}
 metadata['photographic_glazing']=photoglass.report()
 metadata['arched_ground_window_revision']={'previous_raw_sha256':'3325262c62958cbfeb5a1ad07e19c42b1644b0b0e1a654558204e7d68562c832','target_frame_parts':2,'columns':4,'rows':4,'row_height_fractions_bottom_to_top':[.64/3,.64/3,.64/3,.36],'dimensions_are_photo_estimates':True,'scope':'Only two front large arch frame-grid solids replaced; all other parts/materials/photoUV/JPEG unchanged. Fine blind slats are not misrepresented as structural frames.'}
 metadata['visual_shape_revision']={'status':'source-observed corrections; calibrated perspective/native review pending','crest':crest_evidence,'evidence':'visual-refinement-controls.json','previous_raw_sha256':'77a72f8737f7e3b9afbffb9adf6e4e199d10cfe7af2d10cf0ab57afeb623ac31'}
 metadata['glass_frame_fit']={'status':'construction estimate, not measurement','ordinary_glass_depth_m':[-.20,-.18],'ordinary_frame_depth_m':[-.27,-.16],'oculus_glass_depth_m':[.155,.175],'oculus_mullion_depth_m':[.125,.195],'glass_front_setback_from_frame_front_m':.020,'glass_thickness_m':.020,'scope':'The accepted 20 mm glass/frame gap is retained. Ground four windows and central gate are now topology-corrected; six upper photo windows retain identical geometry and UV/image bytes. Shared common helper remains frozen.'}
 report=B.save(output/'bund07.glb',metadata)
 (output/'photo-uv-evidence.json').write_text(json.dumps(photoglass.report(),ensure_ascii=False,indent=2)+'\n')
 audit={'schema':'bund07-geometry-report-v1','status':'Independent metric incorporated; source glass inspected; root photographic/native preview pending','input_footprint_preserved':True,'front_edge':3,'front_width_m':W,'map_area_m2':footprint.area,'opening_count':len(holes_record),'holes':holes_record,'features':stats,'no_render_run':True,'outputs':{k:v for k,v in report.items() if k!='part_summary'}}
 (output/'geometry-report.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n');return B,report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=HERE/'output');a=p.parse_args();_,r=build(a.output);print(json.dumps({k:v for k,v in r.items() if k!='part_summary'},ensure_ascii=False,indent=2))
