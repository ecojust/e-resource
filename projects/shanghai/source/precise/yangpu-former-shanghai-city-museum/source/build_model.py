"""Original exterior of the former Shanghai City Museum at Jiangwan.

Mapped plan, modern photographs and documentary dimensions remain separate.
The western main range, two present two-storey wings and central yellow-roof
entrance are modeled. The present eastern hall is represented only as a simplified estimated low
volume; courtyard link sources remain separate. All detailed elevations and hidden surfaces are bounded estimates.
"""
from pathlib import Path
import argparse,json,math
import numpy as np
from shapely.geometry import Polygon,box as rect
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from common.photo_architecture import Builder,Facade,opening,facade_ring,pieces
from components import PALETTE,Surface,roof,rail,bracket

ID='yangpu-former-shanghai-city-museum'
PARAMS=Path(__file__).with_name('model-parameters.json')
PALETTE=PALETTE|{'warm stone':{'color':[.70,.69,.62],'roughness':.88},'carved pale stone':{'color':[.74,.72,.64],'roughness':.8},'glazed yellow tile':{'color':[.72,.41,.065],'roughness':.31},'yellow tile roll':{'color':[.82,.50,.09],'roughness':.29},'golden glazed crest':{'color':[.83,.54,.14],'roughness':.32},'vermilion timber':{'color':[.62,.045,.025],'roughness':.65},'roof concrete':{'color':[.43,.45,.42],'roughness':.9},'dark timber':{'color':[.10,.085,.055],'roughness':.82},'grey recessed glazing':{'color':[.18,.23,.24],'roughness':.33},'roof loft stone':{'color':[.58,.55,.43],'roughness':.84},'gallery glazing':{'color':[.45,.50,.49],'roughness':.45}}


def octagon(u,z,r):
 return Polygon([(u+r*math.cos(math.pi/8+j*math.pi/4),z+r*math.sin(math.pi/8+j*math.pi/4))for j in range(8)])


def rotate_roof(parts,cx,cy):
 for part in parts:part['vertices']=[(cx-y,cy+x,z)for x,y,z in part['vertices']]


def hip_skirt(b,*,name,cx,cy,hw,hd,iw,idp,eave,top,detailed):
 """Closed lower roof with a flat central upper cover below the upper loft."""
 tmp=Builder(PALETTE);mesh=Surface();nx,ny,nr=(24,12,7)if detailed else(12,6,4)
 def ring(t):
  hx=hw+(iw-hw)*t;hy=hd+(idp-hd)*t;pts=[]
  for side,count in enumerate([nx,ny,nx,ny]):
   for j in range(count):
    f=-1+2*j/count
    if side==0:x,y=hx*f,-hy
    elif side==1:x,y=hx,hy*f
    elif side==2:x,y=-hx*f,hy
    else:x,y=-hx,-hy*f
    z=eave+(top-eave)*t**1.42+.65*abs(f)**8*(1-t)**2;pts.append((x,y,z))
  return pts
 rings=[ring(k/nr)for k in range(nr+1)];n=len(rings[0])
 for a,c in zip(rings,rings[1:]):
  for j in range(n):k=(j+1)%n;mesh.face([a[j],a[k],c[k],c[j]])
 for j in range(n):
  k=(j+1)%n;mesh.face([rings[-1][j],rings[-1][k],(0,0,top)])
  a,bp=rings[0][j],rings[0][k];aa=(a[0],a[1],eave-.26);bb=(bp[0],bp[1],eave-.26)
  mesh.face([aa,bb,bp,a]);mesh.face([(0,0,eave-.26),bb,aa])
 tmp.add(mesh.vertices,mesh.faces,'glazed yellow tile',name+' / closed hip cover')
 for sx in [-1,1]:
  for sy in [-1,1]:
   points=[(sx*(hw+(iw-hw)*t),sy*(hd+(idp-hd)*t),eave+(top-eave)*t**1.42+.65*(1-t)**2+.09)for t in np.linspace(0,1,14 if detailed else 7)]
   tmp.tube(points,.14,'golden glazed crest',sides=8,label=name+' / hip ridge')
 for side in range(4):
  count=max(3,int((2*iw if side%2==0 else 2*idp)/(.48 if detailed else 1.7)))
  for j,f in enumerate(np.linspace(-.97,.97,count)):
   points=[]
   for t in np.linspace(0,1,14 if detailed else 7):
    hx=hw+(iw-hw)*t;hy=hd+(idp-hd)*t
    if side==0:x,y=hx*f,-hy
    elif side==1:x,y=hx,hy*f
    elif side==2:x,y=-hx*f,hy
    else:x,y=-hx,-hy*f
    z=eave+(top-eave)*t**1.42+.65*abs(f)**8*(1-t)**2
    points.append((x,y,z+.045))
   tmp.tube(points,.06,'yellow tile roll',sides=6,label=name+f' / roll {side}/{j}')
 rotate_roof(tmp.parts,cx,cy);b.parts.extend(tmp.parts)


def build(lod=False):
 p=json.loads(PARAMS.read_text());detailed=not lod
 source=orient(Polygon(p['source_footprint_enu']['coordinates'][0]),sign=1.)
 # Exact authored scope will be frozen by mapping; no opaque floor in courts.
 poly=orient(Polygon(p.get('modeled_footprint_enu',p['source_footprint_enu'])['coordinates'][0]),sign=1.)
 tower_source=Polygon(p['tower_footprint_enu']['coordinates'][0]);_,ty0,_,ty1=tower_source.bounds
 tx1=tower_source.bounds[2]
 tower=orient(poly.intersection(rect(-100,ty0,tx1,ty1)),sign=1.)
 cx,cy=tower.centroid.x,tower.centroid.y
 b=Builder(PALETTE);features=[];probes=[]
 retained=unary_union([Polygon(r['geometry_local_enu']['coordinates'][0]) for r in p['retained_contact_sources']]).buffer(p['contact_trim_clearance_m'],join_style=2)
 def rprobe(f,shape,label,depth=.34,material='grey recessed glazing'):
  a,z,c,h=shape.bounds;probes.append({'label':label,'point':f.point(a+(c-a)*.37,z+(h-z)*.41).tolist(),'normal':f.n.tolist(),'depth':depth,'material':material})
 def win(f,shape,label,columns=2,rows=3,trim=True,glass='grey recessed glazing'):
  x0,z0,x1,z1=shape.bounds;inner=shape.buffer(-.09,join_style=2);outer=shape.buffer(-.025,join_style=2);bars=[]
  for i in range(1,columns):u=x0+(x1-x0)*i/columns;bars.append(rect(u-.03,z0,u+.03,z1))
  for i in range(1,rows):z=z0+(z1-z0)*i/rows;bars.append(rect(x0,z-.028,x1,z+.028))
  panes=inner.difference(unary_union(bars))if bars else inner
  f.prism(outer.difference(panes),-.28,-.16,'dark timber',label+' / one-piece frame')
  f.prism(inner,-.365,-.34,glass,label+' / recessed glass')
  if trim:f.prism(shape.buffer(.105,join_style=2).difference(shape),-.025,.08,'carved pale stone',label+' / surround')
  f.box((x0+x1)/2,z0-.06,x1-x0+.19,.12,.20,-.015,'warm stone',label+' / shallow sill')
  rprobe(f,shape,label,material=glass)
 def bands(f,holes,top):
  for z,h,front in [(.54,.16,.06),(top-.66,.15,.075),(top-.12,.22,.11)]:
   sh=rect(-f.length/2,z-h/2,f.length/2,z+h/2)
   if holes:sh=sh.difference(unary_union(holes).buffer(.02,join_style=2))
   if z>9 and hasattr(f,'central_span'):sh=sh.difference(rect(f.central_span[0],0,f.central_span[1],20))
   for a,c in getattr(f,'contact_spans',[]):sh=sh.difference(rect(a,0,c,20))
   f.prism(sh,-.48,front,'carved pale stone',f'opening-aware band {z}')
 def door(f,u,label,width=2.8,height=3.2):
  sh=opening(u,0,width,height,arch=width/2,segments=32 if detailed else 16)
  f.prism(sh.buffer(-.09,join_style=2),-.91,-.87,'interior shadow',label+' / bounded rear closure')
  for amount,depth in [(.39,.14),(.17,.19)]:
   ring=sh.buffer(amount,join_style=2).difference(sh.buffer(amount-.10,join_style=2)).intersection(rect(-100,0,100,100));f.prism(ring,-.025,depth,'carved pale stone',label+' / carved arch surround')
  for v in np.linspace(-width*.32,width*.32,5):
   bar=sh.buffer(-.12,join_style=2).intersection(rect(u+v-.035,0,u+v+.035,height));f.prism(bar,-.67,-.60,'dark timber',label+' / bounded door bar')
  f.box(u,.045,width-.03,.09,.54,-.20,'granite base',label+' / nearly flush threshold')
  for z in [.4,1.1,2.1,2.7]:probes.append({'kind':'portal-clear-prefix','label':label+f' / open recess at {z}','point':f.point(u+.15,z).tolist(),'normal':f.n.tolist(),'depth':.5,'maximum_depth':.92,'material':'bounded gate or rear stop'})
  features.append({'kind':'entrance','name':label,'center_enu':f.point(u,0).tolist(),'normal':f.n.tolist(),'arch_width_m':width,'arch_apex_m':height,'near_flush_threshold_m':.09,'interior_access_claimed':False})
  return sh
 # Every outer wall skin follows the actual retained main source with miters.
 fs=facade_ring(b,poly,'main-perimeter');front=None
 for i,f in enumerate(fs):
  # Project the retained neighbours onto this facade only where decorative
  # profiles could actually contact them. Abutting spans stay plain and solid.
  footprint=Polygon([f.point(u,0,d)[:2] for u,d in [(-f.length/2,0),(f.length/2,0),(f.length/2,.205),(-f.length/2,.205)]])
  f.contact_spans=[]
  for cut in pieces(footprint.intersection(retained)):
   us=[float(np.dot(np.asarray(v)-f.center[:2],f.t[:2])) for v in cut.exterior.coords]
   f.contact_spans.append((min(us)-.001,max(us)+.001))
  def joint(g,h,v):
   a=np.asarray(v[:2])-.52*g.n[:2];c=np.asarray(v[:2])-.52*h.n[:2];M=np.stack([g.t[:2],-h.t[:2]],axis=1)
   return a+g.t[:2]*np.linalg.solve(M,c-a)[0] if abs(np.linalg.det(M))>1e-9 else a
  left=joint(fs[i-1],f,f.a);right=joint(f,fs[(i+1)%len(fs)],f.b)
  ml=np.dot(left-f.a[:2],f.t[:2])/.52;mr=np.dot(right-f.b[:2],f.t[:2])/.52
  def mapper(u,z,dep,f=f,ml=ml,mr=mr):
   shift=ml if abs(u+f.length/2)<1e-8 else mr if abs(u-f.length/2)<1e-8 else 0
   return f.point(u-dep*shift,z,dep)
  holes=[];windows=[];top=p['selected_wing_wall_m'];shape=rect(-f.length/2,0,f.length/2,top)
  isfront=bool(f.n[0]<-.95 and abs(f.center[0]+20)<2 and f.length>30)
  if isfront:
   front=f;u0=(ty0-f.center[1])/f.t[1];u1=(ty1-f.center[1])/f.t[1];u0,u1=sorted([u0,u1]);uc=(u0+u1)/2
   f.central_span=(u0,u1)
   # A continuous solid tier starts at10.08m; cut the same front span
   # here so the wall and tier have no duplicate outer coplanar skin.
   shape=shape.difference(rect(u0,10.08,u1,top+1))
   holes.append(door(f,uc,'west central single arch'))
   for j,u in enumerate(np.linspace(uc-4.6,uc+4.6,5)):
    sh=opening(float(u),5.05,.82,3.55);holes.append(sh);windows.append((sh,f'west high slot {j}',1,4))
   for j,u in enumerate([uc-5.25,uc+5.25]):
    sh=octagon(u,2.25,.69);holes.append(sh);windows.append((sh,f'west octagonal window {j}',1,1))
   for j,u in enumerate(np.linspace(-f.length/2+2.6,f.length/2-2.6,max(2,int(f.length/4.7)))):
    if u0-1<u<u1+1:continue
    for k,z in enumerate([1.05,5.85]):
     sh=opening(float(u),z,1.28,2.25);holes.append(sh);windows.append((sh,f'west connector ordinary window {j}/{k}',2,3))
   for z,h in [(10.7,.18),(11.72,.23)]:f.prism(rect(u0,z-h/2,u1,z+h/2),-.51,.11,'carved pale stone','tower stone cornice')
   # A simplified wave band records visible scrollwork, not exact carving.
   for j in range(14 if detailed else 6):
    count=14 if detailed else 6;aa=u0+.35+(u1-u0-.70)*j/count;ww=(u1-u0-.70)/count
    pts=[f.point(aa+ww*t,11.15+.14*math.sin(t*math.tau),.105)for t in np.linspace(0,1,17 if detailed else 9)]
    b.tube(pts,.032,'carved pale stone',sides=6,label=f'west tower / simplified scroll band {j}')
  elif f.center[0]>-7.5 and abs(f.center[1])<11:
   # Present mapped rear hall: deliberately plain estimated low volume.
   # Its current fabric and opening pattern have not been photographed.
   features.append({'kind':'unverified_rear_hall_simple_wall','a':f.a.tolist(),'b':f.b.tolist(),'current_fabric_date_unverified':True,'openings_claimed':False})
  else:
   # Repeated bay count on hidden/oblique elevations is a bounded estimate.
   n=max(1,int(f.length/4.6)) if f.length>3 else 0
   for j,u in enumerate(np.linspace(-f.length/2+f.length/(2*n),f.length/2-f.length/(2*n),n) if n else []):
    for k,z in enumerate([1.05,5.85]):
     width=min(1.35,f.length/n*.45)
     if any(u+width/2+.11>a and u-width/2-.11<c for a,c in f.contact_spans):continue
     sh=opening(float(u),z,width,2.3);holes.append(sh);windows.append((sh,f'ordinary window {i}/{j}/{k}',2,3))
  if holes:shape=shape.difference(unary_union(holes))
  b.prism(shape,-.52,0,mapper,'warm stone',f.label+' / closed mitered opened wall')
  for sh,name,cols,rows in windows:win(f,sh,name,cols,rows)
  bands(f,holes,top)
  for z in [1.0,4.0,9.5]:
   u=-f.length/2+.65 if f.length>2 else 0
   point=f.point(u,z);probes.append({'kind':'ray','label':f.label+f' / solid corner height {z}','origin':(point+f.n*.25).tolist(),'direction':(-f.n).tolist(),'max_distance':.4,'material':'warm stone'})
  features.append({'kind':'outer_wall','a':f.a.tolist(),'b':f.b.tolist(),'normal':f.n.tolist(),'height_m':top,'window_count':len(windows),'west_central_high_part':isfront,'dimension_confidence':'estimated'})
 assert front is not None
 # Flat roofs follow the bounded footprint; east/south/north courts stay void.
 b.plan_prism(poly.buffer(.035,join_style=2).difference(retained),10.02,10.12,'roof concrete','main wings / closed flat roofs below parapet')
 # A single closed tier avoids coplanar corner/end-cap overlap between
 # separate rectangular return walls. The central west span stops at10.08m
 # and this tier overlaps the10.02..10.12m flat roof by4cm.
 clean_tower=tower.simplify(1e-10,preserve_topology=True)
 b.plan_prism(clean_tower,10.08,p['selected_tower_base_m'],'warm stone','central tower / single closed upper stone tier')
 for f in facade_ring(b,clean_tower,'tower single-tier return'):
  for u in [-f.length*.35,0,f.length*.35]:
   for z in [10.15,10.25,10.45,10.9,11.4]:probes.append({'kind':'ray','label':f.label+f' / sealed return {u}/{z}','origin':(f.point(u,z)+f.n*.3).tolist(),'direction':(-f.n).tolist(),'max_distance':.5,'material':'warm stone'})
 b.plan_prism(tower.buffer(.12,join_style=2),11.90,12.15,'carved pale stone','central tower / actual raised gallery floor')
 # Open red-column gallery; inset window walls leave a real passage behind posts.
 gx0,gx1=cx-5.45,cx+5.45;gy0,gy1=cy-8.45,cy+8.45
 room=rect(cx-3.65,cy-8.0,cx+3.65,cy+8.0)
 for i,f in enumerate(facade_ring(b,room,'inset gallery room')):
  n=5 if abs(f.n[0])>.9 else 2;holes=[]
  for j,u in enumerate(np.linspace(-f.length/2+f.length/(2*n),f.length/2-f.length/(2*n),n)):
   sh=opening(float(u),12.60,min(2.55,f.length/n-.55),2.45);holes.append(sh);win(f,sh,f'gallery recessed bay {i}/{j}',2,2,False,'gallery glazing')
  f.wall(12.15,15.65,holes,.40,'warm stone')
  f.beam(15.35,.22,.06,'dark timber',width=f.length)
 columns=[]
 for x in [gx0,gx1]:
  for y in np.linspace(gy0,gy1,6):columns.append((float(x),float(y)))
 for y in [gy0,gy1]:
  for x in [cx-1.8,cx+1.8]:columns.append((float(x),float(y)))
 for j,(x,y)in enumerate(columns):
  b.lathe((x,y),[(12.15,.42),(12.30,.42),(12.45,.34),(15.45,.29),(15.72,.36)],'vermilion timber',segments=24 if detailed else 12,label=f'open gallery / red column {j}')
  b.lathe((x,y),[(12.15,.46),(12.28,.46),(12.38,.37)],'warm stone',segments=12,label=f'open gallery / stone foot {j}')
  normal=(-1,0)if x<cx-4 else(1,0)if x>cx+4 else(0,-1)if y<cy else(0,1)
  bracket(b,x,y,15.25,normal,f'gallery bracket {j}',detailed)
 for label,a,c in [('west',[gx0-.40,gy0-.35,0],[gx0-.40,gy1+.35,0]),('east',[gx1+.40,gy1+.35,0],[gx1+.40,gy0-.35,0]),('north',[gx0-.40,gy1+.35,0],[gx1+.40,gy1+.35,0]),('south',[gx1+.40,gy0-.35,0],[gx0-.40,gy0-.35,0])]:
  rail(b,a=a,b=c,z=12.15,height=.95,spacing=1.8,label='gallery open stone balustrade / '+label,detailed=detailed,include_end=False)
 # Test actual gallery void between one column pair and the recessed glazing wall.
 for x,normal in [(gx0,[-1,0,0]),(gx1,[1,0,0])]:
  for y in [gy0+(gy1-gy0)*.10,gy0+(gy1-gy0)*.30,gy0+(gy1-gy0)*.70]:
   probes.append({'kind':'void','label':'open gallery passage before inset room','origin':[x,y,13.95],'direction':[-normal[0],0,0],'max_distance':1.35})
 features.append({'kind':'open_gallery','floor_m':12.15,'columns':len(columns),'window_room_bounds_enu':list(room.bounds),'column_rectangle_enu':[gx0,gy0,gx1,gy1],'void_depth_m':1.35,'upper_access_claimed':False})
 hip_skirt(b,name='lower yellow eave',cx=cx,cy=cy,hw=11.15,hd=7.75,iw=8.8,idp=5.15,eave=15.8,top=17.15,detailed=detailed)
 # Closed upper loft: every side bridges lower top and upper roof underside.
 loft=rect(cx-5.05,cy-8.7,cx+5.05,cy+8.7)
 for f in facade_ring(b,loft,'upper loft closed return'):
  f.wall(16.95,18.30,thickness=.40,material='roof loft stone')
  for z in [17.3,17.9]:probes.append({'kind':'ray','label':f.label+f' / sealed height {z}','origin':(f.point(.13,z)+f.n*.30).tolist(),'direction':(-f.n).tolist(),'max_distance':.5,'material':'roof loft stone'})
 tmp=Builder(PALETTE)
 roof(tmp,name='upper yellow hip-and-gable roof',cx=0,cy=0,half_width=10.1,half_depth=7.0,inner_width=8.2,inner_depth=4.2,eave_z=18.2,skirt_z=20.1,ridge_z=22.3,corner_lift=.80,ridge_end_lift=.27,detailed=detailed)
 # Two pale gable panels on the true closed triangular gable, not open holes.
 for sign in [-1,1]:
  contour=[(-4.05,20.16),(4.05,20.16)]+[(float(y),20.1+(22.3-20.1)*(1-(abs(y)/4.2)**.88)+.27*(1-(abs(y)/4.2)**2)-.10)for y in np.linspace(3.95,-3.95,21)]
  sh=Polygon(contour).buffer(0)
  mapper=(lambda u,z,d,s=sign:(s*(8.2+d),s*u,z))
  tmp.prism(sh,.02,.055,mapper,'warm stone','upper roof / pale closed triangular gable')
 rotate_roof(tmp.parts,cx,cy);b.parts.extend(tmp.parts)
 # Vertical coverage controls at roof/corner transitions, and downward roof probes.
 for dx,dy,z in [(0,0,24.5),(6,0,20),(0,10,19),(-6,6,20)]:
  probes.append({'kind':'solid','label':'closed roof coverage','origin':[cx+dx,cy+dy,z],'direction':[0,0,-1],'max_distance':10})
 features.append({'kind':'double_eave_hip_gable','center_enu':[cx,cy],'ridge_axis':'north-south','lower_eave_m':15.8,'upper_eave_m':18.2,'selected_main_ridge_m':22.3,'nominal_overall_crest_target_m':24,'exact_documentary_height_datums_unconfirmed':True,'roof_geometry':'two closed roofs; lower hip skirt and upper hip-and-gable; closed connecting loft'})
 meta={'id':ID,'name':'旧上海市博物馆江湾馆舍','status':'photo-guided-exterior-estimated-dimensions','scope':'Western historic museum range with present two-storey north/south wings and central yellow double-eaved tower, open red-column gallery, narrow high windows and octagonal entrance windows. The current eastern rear hall is a deliberately plain estimated low volume, not a verified historical reconstruction. Courtyard links and other hospital sources remain separate. Not an exact 1930s reconstruction; interiors, exhibits, trees, banners and site surfaces excluded.','local_origin_wgs84':[p['frame']['lng'],p['frame']['lat']],'local_heading_deg':0,'source_macro':p['source_macro'],'source_local_ids':p['source_local_ids'],'all_elevation_datums_estimated':True,'all_architectural_detail_dimensions_estimated':True,'documentary_wing_wall_height_m':10.5,'documentary_tower_height_m':24,'documentary_height_datums_not_measured':True,'modern_two_storey_wings_not_original_single_storey_claim':True,'photos_embedded':False,'interiors_modeled':False,'underground_modeled':False,'site_slab_modeled':False,'walk_integration':False,'geometry_license':'MIT','map_reference_license':'ODbL-1.0'}
 return b,meta,features,probes

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--out',type=Path,required=True);a.add_argument('--lod',action='store_true');x=a.parse_args();x.out.mkdir(parents=True,exist_ok=True)
 b,meta,features,probes=build(x.lod);suffix='-lod'if x.lod else'';path=x.out/(ID+('-lod.glb'if x.lod else'-raw.glb'));b.save(path,meta)
 (x.out/('features'+suffix+'.json')).write_text(json.dumps(features,ensure_ascii=False,indent=2)+'\n');(x.out/('surface-probes'+suffix+'.json')).write_text(json.dumps(probes,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(path),'parts':len(b.parts),'triangles':sum(len(p['triangles'])for p in b.parts)},ensure_ascii=False))
