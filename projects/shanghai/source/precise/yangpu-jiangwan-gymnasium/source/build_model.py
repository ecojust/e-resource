"""Original exterior geometry of the independent Jiangwan gymnasium.

Coordinates are east/north/up metres around the frozen source1558 anchor. The
1934 design and modern observations constrain a bounded reconstruction; no
current measured elevation, interior, neighbouring building or photo texture is
claimed. All building construction below is new for this gymnasium.
"""
from pathlib import Path
import argparse,json,math
import numpy as np
from shapely.geometry import Polygon,Point,box as rect
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from common.photo_architecture import Builder,Facade,opening,facade_ring

ID='yangpu-jiangwan-gymnasium'
PARAMS=Path(__file__).resolve().with_name('model-parameters.json')


def build(lod=False):
 p=json.loads(PARAMS.read_text());b=Builder({'gym brick':{'color':[.43,.23,.16],'roughness':.9},'warm stone':{'color':[.70,.68,.60],'roughness':.85},'roof sheet':{'color':[.40,.43,.41],'roughness':.75,'metallic':.2},'roof glazing':{'color':[.24,.34,.36],'roughness':.28,'metallic':.2},'light roof frame':{'color':[.60,.63,.59],'roughness':.55,'metallic':.25}})
 features=[];probes=[];poly=orient(Polygon(p['source_footprint_enu']['coordinates'][0]),sign=1.)
 ymin,ymax=-22.335936396563174,22.511263738359155;yc=(ymin+ymax)/2;half=(ymax-ymin)/2
 xf=-26.466545932081665
 def backx(y):return 35.199225649288095+(33.66969410988612-35.199225649288095)*(y-ymin)/(ymax-ymin)
 eave=p.get('selected_eave_height_m',12.0);apex=p.get('selected_apex_height_m',20.0)
 rise=apex-eave;radius=(half*half+rise*rise)/(2*rise);cz=apex-radius
 def roofz(y):return cz+math.sqrt(max(0.,radius*radius-(y-yc)**2))
 def roof_poly(ya,yb,offset=0,thickness=.24,segments=None):
  n=segments or (12 if lod else 28);ys=np.linspace(ya,yb,n+1)
  return Polygon([(y,roofz(y)+offset) for y in ys]+[(y,roofz(y)+offset-thickness) for y in ys[::-1]])
 def roof_sweep(shape,xa,xb,material,label):
  # Rear end follows the modest source skew; front end remains its own plane.
  def mapper(y,z,d):
   start=xa(y) if callable(xa) else xa;end=xb(y) if callable(xb) else xb
   return [start+(end-start)*d,y,z]
  b.prism(shape,0.,1.,mapper,material,label)
 def probe(f,shape,label,material='recessed glass',depth=.32):
  minx,minz,maxx,maxz=shape.bounds;u=(minx+maxx)/2+.12*(maxx-minx);z=(minz+maxz)/2+.11*(maxz-minz)
  q=f.point(u,z,0);probes.append({'label':label,'kind':'recess','point':q.tolist(),'normal':f.n.tolist(),'depth':depth,'material':material})
 def window(f,shape,label,columns=2,rows=3,trim=True):
  f.window(shape,columns=columns,rows=rows,trim=trim,label=label)
  if label.startswith('upper-octagonal'):
   # Small octagonal high windows have a ring, not the helper's rectangular sill.
   assert b.parts[-1]['label'].endswith(label+'-sill');b.parts.pop()
  probe(f,shape,label)
 def wall_layers(f,holes,top=eave,material='gym brick'):
  f._openings=list(holes)
  for lo,hi,mat in [(0,1.15,'granite base'),(1.15,top-.30,material),(top-.30,top,'warm stone')]:f.wall(lo,hi,holes,thickness=.65,material=mat)
 def belt(f,z,h=.14,d=.12,label='belt'):
  shape=rect(-f.length/2-.05,z-h/2,f.length/2+.05,z+h/2)
  if getattr(f,'_openings',None):shape=shape.difference(unary_union(f._openings).buffer(.025,join_style=2))
  f.prism(shape.simplify(1e-7,preserve_topology=True),-.44,d+.04,'warm stone',label)
 # Separate long sides. Each has real upper octagonal and lower rectangular
 # openings, not black panels placed over an uncut wall.
 for side,y,a,c in [('north',ymax,[backx(ymax)-.60,ymax],[xf+.60,ymax]),('south',ymin,[xf+.60,ymin],[backx(ymin)-.60,ymin])]:
  f=Facade(b,a,c,'long-'+side);holes=[];windows=[]
  slots=np.linspace(-f.length/2+2.4,f.length/2-2.4,16)
  for j,u in enumerate(slots):
   angle=np.arange(8)*math.tau/8+math.pi/8;r=.71
   shape=Polygon([(u+r*math.cos(t),9.3+r*math.sin(t)) for t in angle]);holes.append(shape);windows.append((shape,f'upper-octagonal-{j}',2,2))
   if j not in [3,12]:
    shape=opening(float(u),2.25,1.36,3.55);holes.append(shape);windows.append((shape,f'lower-window-{j}',2,4))
  doors=[]
  for j in [3,12]:
   u=float(slots[j]);shape=opening(u,0,1.65,3.1);holes.append(shape);doors.append((u,shape,j))
  wall_layers(f,holes)
  for shape,label,cols,rows in windows:window(f,shape,label,cols,rows)
  for u,shape,j in doors:
   f.prism(shape,-.55,-.52,'dark stone',f'side-door-{j}-closed-stop')
   # Actual behind-plane door mullions remain inside the cutout.
   for q in [-.42,0,.42]:f.box(u+q,1.55,.04,3.03,.08,-.46,'wrought iron',f'side-door-{j}-bar')
   probe(f,shape,f'side-door-{j}',material='dark stone',depth=.52)
   probes.append({'label':f'{side}-door-{j}-low-belt-cutout','kind':'recess','point':f.point(u+.19,1.15,0).tolist(),'normal':f.n.tolist(),'depth':.52,'material':'dark stone'})
   f.prism(shape.buffer(.13,join_style=2).difference(shape).intersection(rect(-100,0,100,100)),-.03,.09,'warm stone',f'side-door-{j}-surround')
  for z,h in [(1.15,.18),(6.65,.13),(7.0,.20),(10.55,.12),(11.75,.20)]:belt(f,z,h,.18)
  # Brick coursing is shallow relief, clipped around real openings.
  if not lod:
   surface=rect(-f.length/2,1.4,f.length/2,eave-.55).difference(unary_union(holes).buffer(.035))
   for z in np.arange(1.6,eave-.6,.25):f.prism(surface.intersection(rect(-f.length/2,z,f.length/2,z+.018)),-.012,.005,'red brick','brick-bed-joint')
  features.append({'kind':'long_facade','side':side,'a':a,'b':c,'upper_octagonal_windows':16,'lower_rectangular_windows':14,'side_closed_doors':2,'all_dimensions_estimated':True})
 # Source-constrained main end walls. West main wall is behind attached
 # entrance volumes; the exposed upper tympanum follows the barrel profile.
 for name,a,c in [('rear-east',[backx(ymin),ymin],[backx(ymax),ymax]),('front-main-west',[xf,ymax],[xf,ymin])]:
  f=Facade(b,a,c,name);coords=[]
  for u in np.linspace(-f.length/2,f.length/2,48 if not lod else 24):
   yy=f.point(float(u),0)[1];coords.append((float(u),roofz(yy)-.18))
  outline=Polygon([(-f.length/2,0),(f.length/2,0)]+coords[::-1]);holes=[];wins=[]
  if name=='rear-east':
   for j,u in enumerate([-15,-11,-6.5,-2.2,2.2,6.5,11,15]):
    sh=opening(u,3.2,1.35,3.5);holes.append(sh);wins.append((sh,f'back-lower-{j}',2,4))
   for j,u in enumerate([-11,-6.5,-2.2,2.2,6.5,11]):
    sh=opening(u,10.0,1.2,2.6);holes.append(sh);wins.append((sh,f'back-upper-{j}',2,3))
  else:
   # Modern west photograph shows a plain red-brick curved tympanum.
   # The three high windows belong to the forward pale entrance wall below.
   pass
  f.wall(0,apex,holes,.65,'gym brick' if name=='front-main-west' else 'warm stone',outline);f._openings=holes
  for sh,label,cols,rows in wins:window(f,sh,label,cols,rows)
  for z,h in [(1.15,.18),(7.,.20),(11.75,.20)]:belt(f,z,h,.16)
  features.append({'kind':'end_wall','side':name,'a':a,'b':c,'openings':len(wins)})
 # Arch-shaped roof with a genuine ridge aperture, filled by separate glazing
 # panels and framing. No solid metal sheet lies directly under the glass.
 skyhalf=p.get('selected_skylight_half_width_m',4.4);skystart=xf+15.5;skyend=22.5
 roof_sweep(roof_poly(ymin-.24,yc-skyhalf),xf-.2,lambda y:backx(y)+.2,'roof sheet','barrel-roof-south')
 roof_sweep(roof_poly(yc+skyhalf,ymax+.24),xf-.2,lambda y:backx(y)+.2,'roof sheet','barrel-roof-north')
 roof_sweep(roof_poly(yc-skyhalf,yc+skyhalf),xf-.2,skystart,'roof sheet','barrel-roof-front-cap')
 roof_sweep(roof_poly(yc-skyhalf,yc+skyhalf),skyend,lambda y:backx(y)+.2,'roof sheet','barrel-roof-rear-cap')
 nx=12 if not lod else 8;ny=3
 for j in range(nx):
  x0=skystart+(skyend-skystart)*j/nx;x1=skystart+(skyend-skystart)*(j+1)/nx
  for k in range(ny):
   y0=yc-skyhalf+2*skyhalf*k/ny;y1=yc-skyhalf+2*skyhalf*(k+1)/ny
   roof_sweep(roof_poly(y0+.035,y1-.035,.08,.09,4 if not lod else 2),x0+.045,x1-.045,'roof glazing',f'ridge-glazing-{j}-{k}')
 for x in np.linspace(skystart,skyend,nx+1):roof_sweep(roof_poly(yc-skyhalf-.10,yc+skyhalf+.10,.17,.16,12 if not lod else 6),float(x)-.055,float(x)+.055,'light roof frame','skylight-transverse-frame')
 for y in np.linspace(yc-skyhalf,yc+skyhalf,ny+1):roof_sweep(roof_poly(float(y)-.055,float(y)+.055,.18,.18,1),skystart-.10,skyend+.10,'light roof frame','skylight-longitudinal-frame')
 # Raised standing seams emphasize the curved surface without texture maps.
 if not lod:
  for x in np.linspace(xf+.5,33,120):
   for ya,yb in ([(ymin,ymax)] if x<skystart-.1 or x>skyend+.1 else [(ymin,yc-skyhalf-.16),(yc+skyhalf+.16,ymax)]):roof_sweep(roof_poly(ya,yb,.045,.055,64 if yb-ya>30 else 32),float(x)-.022,float(x)+.022,'roof zinc','roof-standing-seam')
 roof_sweep(roof_poly(ymin-.35,ymax+.35,.04,.26,48 if not lod else 24),xf-.41,xf-.09,'warm stone','west-arched-end-coping')
 roof_sweep(roof_poly(ymin-.35,ymax+.35,.04,.26,48 if not lod else 24),lambda y:backx(y)-.10,lambda y:backx(y)+.25,'warm stone','east-arched-end-coping')
 features.append({'kind':'barrel_roof','eave_m':eave,'apex_m':apex,'radius_m':radius,'profile_center_north_m':yc,'profile_center_height_m':cz,'skylight_x': [skystart,skyend],'skylight_y':[yc-skyhalf,yc+skyhalf],'all_dimensions_estimated':True})
 # Modern west entrance: three tall windows with three projecting perforated
 # balconies, three deep arch recesses, and bounded low side wings. The dated
 # modern photographs do not support a row of stadium towers/urns here.
 annex=poly.intersection(rect(-100,-100,xf,100)).buffer(0);front_face=None
 for f in facade_ring(b,annex,'west-annex'):
  if f.center[0] < -35 and f.length>20:front_face=f
 assert front_face is not None
 fy0,fy1=-10.613769473788373,11.299445703208432
 core=annex.intersection(rect(-100,fy0,xf,fy1));side_roof=annex.difference(core)
 main_door_centers=[-6.45,0.,6.45]
 for f in facade_ring(b,annex,'west-annex'):
  if f.center[0] > xf-.1:continue # Internal junction to the main hall.
  isfront=f.center[0] < -35 and f.length>20
  holes=[];wins=[]
  if isfront:
   for j,u in enumerate(main_door_centers):
    sh=opening(u,.12,2.80,4.95,arch=1.40,segments=20 if not lod else 10);holes.append(sh)
    hi=opening(u,7.15,1.30,6.15);holes.append(hi);wins.append((hi,f'tall-front-window-{j}',2,7))
   # Two small low side vents are clearly separate from the three portals.
   for j,u in enumerate([-9.3,9.3]):
    sh=opening(u,1.35,.60,.70);holes.append(sh);wins.append((sh,f'front-small-vent-{j}',1,1))
  elif abs(f.n[0])>.95 and f.length>3:
   sh=opening(0,2.0,.72,1.55);holes.append(sh);wins.append((sh,'wing-small-window',1,2))
  wall_layers(f,holes,16.4 if isfront else 13.5,'warm stone')
  for sh,label,cols,rows in wins:window(f,sh,label,cols,rows)
  if not isfront:
   for z,h in [(1.15,.17),(5.65,.16),(13.25,.24)]:belt(f,z,h,.13)
   continue
  for j,u in enumerate(main_door_centers):
   arch=holes[j*2];inner=arch.buffer(-.10,join_style=2)
   # Outer side gates retain the modern square lattice, center remains a dark
   # recess terminated deeper inside, without inventing an identical gate.
   depth=1.80 if j!=1 else 2.25
   f.prism(arch,-depth-.10,-depth,'interior shadow',f'portal-{j}-bounded-dark-back')
   if j!=1:
    diamonds=[]
    for yy in np.arange(.28,4.85,.30):
     for xx in np.arange(u-1.20,u+1.21,.30):
      diamond=Polygon([(xx,yy+.105),(xx+.105,yy),(xx,yy-.105),(xx-.105,yy)])
      if inner.contains(diamond):diamonds.append(diamond)
    gate=inner.difference(unary_union(diamonds))
    f.prism(gate,-1.43,-1.32,'painted window frame',f'portal-{j}-true-perforated-lattice-gate')
    q=f.point(u,2.38,0) # Actual center of a diamond hole, not a bar.
    probes.append({'label':f'portal-{j}-through-lattice-hole-to-back','kind':'recess','point':q.tolist(),'normal':f.n.tolist(),'depth':depth,'material':'interior shadow'})
    q=f.point(u+.15,2.38,0)
    probes.append({'label':f'portal-{j}-lattice-bar','kind':'recess','point':q.tolist(),'normal':f.n.tolist(),'depth':1.32,'material':'painted window frame'})
   else:probe(f,arch,f'portal-{j}-bounded-dark-back',material='interior shadow',depth=depth)
   for h in [.50,1.20,1.70,2.80,4.0,4.75]:
    probes.append({'label':f'portal-{j}-unblocked-prefix-at-{h}','kind':'portal-clear-prefix','point':f.point(u,h,0).tolist(),'normal':f.n.tolist(),'depth':1.25,'maximum_depth':2.30,'material':'any actual gate or bounded rear closure'})
   # Deep recess side walls/soffit are a closed ring from facade to rear stop.
   ring=arch.buffer(.17,join_style=2).difference(arch).intersection(rect(-100,0,100,100))
   f.prism(ring,-depth,0.,'warm stone',f'portal-{j}-deep-jamb')
   for offset,thick,out in [(.10,.09,.075),(.23,.075,.045)]:
    band=arch.buffer(offset,join_style=2).difference(arch.buffer(offset-thick,join_style=2))
    f.prism(band.intersection(rect(-100,0,100,100)),-.03,out,'carved pale stone',f'portal-{j}-rolled-arch')
   # A shallow sill/threshold is supported by the modern ground-level entry;
   # no broad multi-flight stairs are inferred from the1934 rendering.
   f.box(u,.065,2.76,.13,1.55,-.60,'granite base',f'portal-{j}-threshold')
   # Distinct projecting platform, perforated front rail and side rails.
   z=6.05;w=3.10;projection=1.02
   f.box(u,z,w,.26,projection+.22,projection/2-.03,'warm stone',f'balcony-{j}-deck')
   rail=rect(u-w/2,z+.13,u+w/2,z+.92)
   cutouts=[Point(u+t,z+.53).buffer(.18,quad_segs=8 if not lod else 4) for t in [-.87,0,.87]]
   f.prism(rail.difference(unary_union(cutouts)),projection-.10,projection+.09,'warm stone',f'balcony-{j}-perforated-front')
   for sg in [-1,1]:
    f.box(u+sg*(w/2-.09),z+.52,.18,.79,projection,.45,'warm stone',f'balcony-{j}-side-rail')
    # Small cantilever brackets under deck, closed polygonal masses.
    profile=Polygon([(-.18,z-.13),(.95,z-.13),(.61,z-.38),(.20,z-.56),(-.18,z-.56)])
    origin=f.point(u+sg*.94,0,0)
    mapper=lambda d,h,t,origin=origin: origin+f.n*d+np.array([0,0,h])+f.t*t
    # n cross up = -t, so the thickness direction must be -t.
    mapper=lambda d,h,t,origin=origin: origin+f.n*d+np.array([0,0,h])-f.t*t
    b.prism(profile,-.14,.14,mapper,'warm stone',f'balcony-{j}-bracket')
   for t in [-.87,0,.87]:
    probes.append({'label':f'balcony-{j}-true-round-hole-{t}','kind':'recess','point':f.point(u+t,z+.53,projection+.09).tolist(),'normal':f.n.tolist(),'depth':projection+.09,'material':'warm stone'})
   probes.append({'label':f'balcony-{j}-clear-under-projecting-center','kind':'recess','point':f.point(u,5.40,1.2).tolist(),'normal':f.n.tolist(),'depth':1.2,'material':'warm stone'})
   probes.append({'label':f'balcony-{j}-solid-deck-top','kind':'recess','point':f.point(u,z+.13,.50).tolist(),'normal':[0,0,1],'depth':0.,'material':'warm stone'})
   features.append({'kind':'front_portal','index':j,'facade_point_enu':f.point(u,2.3).tolist(),'normal_enu':f.n.tolist(),'arch_bottom_m':.12,'arch_apex_m':5.07,'rear_stop_depth_m':depth,'rear_stop_kind':'dark back behind a truly perforated side lattice gate' if j!=1 else 'bounded dark internal closure, not claimed existing door','side_gate_depth_m':1.32 if j!=1 else None,'threshold_top_m':.13,'balcony_deck_z_m':z,'balcony_front_projection_m':projection,'all_dimensions_estimated':True})
  for z,h in [(1.15,.17),(5.65,.18),(14.95,.14),(16.22,.25)]:belt(f,z,h,.13)
  # Pale block seams are geometry and stop around openings, not a photo decal.
  if not lod:
   surf=rect(-f.length/2,.25,f.length/2,16.10).difference(unary_union(holes).buffer(.035))
   for row,z in enumerate(np.arange(.55,16,.52)):
    f.prism(surf.intersection(rect(-f.length/2,z,f.length/2,z+.018)).simplify(1e-5,preserve_topology=True),-.012,.005,'limestone','pale-block-bed')
    for u in np.arange(-f.length/2+(row%2)*1.0,f.length/2,2.0):f.prism(surf.intersection(rect(u,z,u+.018,z+.50)).simplify(1e-5,preserve_topology=True),-.012,.005,'limestone','pale-block-head')
 # Core side return walls close the higher front volume, behind its facade.
 for f in facade_ring(b,core,'front-core-upper-return'):
  if (f.center[0] < -35 and f.length>20) or f.center[0] > xf-.1:continue
  f.wall(13.5,16.4,(),.50,'warm stone');belt(f,16.22,.25,.13)
  probes.append({'label':f.label+'-complete-upper-return','kind':'recess','point':f.point(0,14.5).tolist(),'normal':f.n.tolist(),'depth':0.,'material':'warm stone'})
 b.plan_prism(side_roof,13.45,13.65,'warm stone','west-wing-flat-roof')
 b.plan_prism(core,16.35,16.55,'warm stone','front-core-flat-roof')
 features.append({'kind':'modern_west_entrance','main_face_a':front_face.a.tolist(),'main_face_b':front_face.b.tolist(),'main_wall_height_m':16.4,'side_wing_height_m':13.5,'central_rectangular_windows':3,'projecting_balconies':3,'perforations_per_balcony_front':3,'arched_portals':3,'one_shallow_threshold_no_invented_long_stair':True,'modern_photo_basis':'2011 archive KIC exterior pair, capture date not photograph date'})

 if p.get('modern_photographs_pending',True):
  meta={'id':ID,'name':'江湾体育馆私有原型','status':'private-prototype-awaiting-modern-exterior','scope':'Private main hall prototype only; west annex intentionally unfinished and not deliverable.'}
 else:meta={'id':ID,'name':'江湾体育馆历史主楼','status':'photo-guided-exterior-estimated-dimensions','scope':'Independent enclosed historical gymnasium exterior, arched roof, west entrance annex, differentiated long and rear facades; no interior, stadium, swimming hall or site slab.'}
 meta.update(local_origin_wgs84=[p['frame']['lng'],p['frame']['lat']],local_heading_deg=0,source_local_ids=[1558],source_macro='14-13722-6690',all_elevation_datums_estimated=True,all_architectural_detail_dimensions_estimated=True,current_height_surveyed_m=None,photos_embedded=False,interiors_modeled=False,underground_modeled=False,site_slab_modeled=False,outdoor_stadium_modeled=False,swimming_hall_modeled=False,walk_integration=False,geometry_license='MIT',map_reference_license='ODbL-1.0',original_historic_state_claimed=False,design_vs_map_length_difference_retained=True)
 return b,meta,features,probes


def main():
 parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);parser.add_argument('--lod',action='store_true');a=parser.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 b,m,f,p=build(a.lod);suffix='-lod' if a.lod else '-raw';r=b.save(a.out/(ID+suffix+'.glb'),m)
 for name,data in [('features'+('-lod' if a.lod else ''),f),('surface-probes'+('-lod' if a.lod else ''),p)]: (a.out/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:r[k] for k in ['file','bytes','triangles','parts','bounds_glb']}))
if __name__=='__main__':main()
