"""China Aviation Association building: original photo-informed exterior.

Map-fitted ENU placement. Dimensions and all elevations are bounded estimates;
2010/2013/2022-presented photographs document repaired modern fabric, not 1935.
"""
from pathlib import Path
import argparse,json,math
import numpy as np
from shapely.geometry import Polygon,Point,LineString,box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from common.photo_architecture import Builder,Facade
from aviation_geometry import cut_shell,cylindrical_mapper,curved_plate,curved_window
ID='yangpu-china-aviation-association-building'
PALETTE={'pale grey stone':{'color':[.64,.66,.62],'roughness':.83},'light stone coping':{'color':[.72,.73,.68],'roughness':.78},'weathered stone base':{'color':[.42,.45,.41],'roughness':.86},'dark recessed glass':{'color':[.075,.13,.13],'roughness':.3,'metallic':.15},'dark green metal':{'color':[.08,.115,.09],'roughness':.57,'metallic':.25},'grey roof':{'color':[.29,.32,.30],'roughness':.91},'dark door':{'color':[.065,.075,.06],'roughness':.65},'muted brass':{'color':[.52,.39,.12],'roughness':.58,'metallic':.5},'stone seam':{'color':[.43,.46,.42],'roughness':.85}}
PARAMS=Path(__file__).with_name('model-parameters.json')

def rounded(bounds,r,segments):
 x0,y0,x1,y1=bounds
 return orient(box(x0+r,y0+r,x1-r,y1-r).buffer(r,quad_segs=segments),sign=1)

def ring(builder,c,r,z0,z1,width,material,label,n=96):
 outer=Point(c).buffer(r,quad_segs=n//4);inner=Point(c).buffer(r-width,quad_segs=n//4)
 builder.plan_prism(outer.difference(inner),z0,z1,material,label)

def build(lod=False):
 p=json.loads(PARAMS.read_text());detail=not lod;n=96 if detail else 48
 cx,cy=p['tower_center_enu_m'];r=p['tower_radius_m'];wingtop=p['wing_roof_m'];towertop=p['outer_terrace_m'];tailtop=p['rear_roof_m'];linktop=p['connector_eave_m']
 b=Builder(PALETTE);features=[];probes=[];recess=p['flat_roof_surface_recess_m']
 front=rounded(p['front_wing_bounds_enu_m'],1.8,12 if detail else 6)
 rear=rounded(p['rear_wing_bounds_enu_m'],.9,10 if detail else 5)
 rearport=rounded([23.95,-2.8,25.25,5.1],.55,8 if detail else 4)
 link=box(*p['connector_bounds_enu_m']);circle=Point(cx,cy).buffer(r,quad_segs=n//4)
 poly=orient(unary_union([front,rear,rearport,link,circle]),sign=1.)
 # A single perimeter shell avoids whole solid building blocks behind windows
 # and avoids internal cross-walls where the four plan volumes join.
 xy=np.asarray(poly.exterior.coords)[:-1];edges=np.roll(xy,-1,axis=0)-xy;lengths=np.linalg.norm(edges,axis=1);tangents=edges/lengths[:,None];normals=np.stack([tangents[:,1],-tangents[:,0]],axis=1)
 offsets=np.array([(normals[j-1]+normals[j])/(1+np.dot(normals[j-1],normals[j])) for j in range(len(xy))]);starts=np.r_[0,np.cumsum(lengths)];total=starts[-1];line=LineString(poly.exterior.coords)
 def mapper(u,z,d=0):
  u=float(u)%total;i=min(len(lengths)-1,int(np.searchsorted(starts,u,side='right')-1));f=(u-starts[i])/lengths[i];j=(i+1)%len(xy)
  q=xy[i]*(1-f)+xy[j]*f+d*(offsets[i]*(1-f)+offsets[j]*f)
  return (q[0],q[1],z)
 def height(u):
  x,y,_=mapper(u,0)
  if x<cx-.01 and abs(math.hypot(x-cx,y-cy)-r)<.04:return wingtop
  if x< -4.39:return wingtop
  if x<17.19:return linktop
  return tailtop
 windows=[];holes=[]
 def window(u,z,w,h,label,vertical=False):
  sh=box(u-w/2,z,u+w/2,z+h);holes.append(sh);windows.append((sh,label,vertical))
 def project(x,y):return line.project(Point(x,y))
 # Long front elevations: three observed bands, including closely spaced low
 # bands; these are not an assertion of three equal-height occupied floors.
 for side in [-1,1]:
  ys=np.linspace(cy+side*8.2,side*15.5,3)
  for j,y in enumerate(ys):
   u=project(-14.8,float(y))
   for k,(z,h) in enumerate([(1.15,.8),(2.7,.85),(6.65,.95)]):window(u,z,2.15,h,f'front wing {side}/{j}/{k}')
 # Wrapped corner windows and plain side elevations remain conservative.
 for side in [-1,1]:
  y=-18.2 if side<0 else 18.;u=project(-9.6,y)
  for k,(z,h) in enumerate([(1.15,.8),(2.7,.85),(6.65,.95)]):window(u,z,4.7,h,f'rounded wing end {side}/{k}')
  for x in [-13.7,-5.5]:
   y=(-17.55 if side<0 else 17.35);u=project(x,y)
   for k,(z,h) in enumerate([(2.7,.85),(6.65,.95)]):window(u,z,1.1,h,f'wing corner {side}/{x}/{k}')
  for j,y in enumerate(np.linspace(7.4,15.5,3)*side):
   u=project(-4.4,float(y))
   for k,z in enumerate([1.3,5.3]):window(u,z,1.65,1.3,f'wing rear estimated {side}/{j}/{k}')
 # West round-tower five narrow upper slots and entrance.
 for j,theta in enumerate(np.linspace(math.pi-.76,math.pi+.76,5)):
  u=project(cx+r*math.cos(theta),cy+r*math.sin(theta));window(u,5.3,.69,2.55,f'tower vertical window {j}',True)
 dooru=project(cx-r,cy);door=box(dooru-1.25,.53,dooru+1.25,3.65);holes.append(door)
 # Connector side windows, rear wing windows. The rear portal is photo-led;
 # other side spacing is bounded inference, not a measured fenestration claim.
 for side,y in [('south',-2.94),('north',5.21)]:
  for j,x in enumerate(np.linspace(-1.5,14.6,6)):
   for k,z in enumerate([1.15,4.5]):window(project(float(x),y),z,1.04,1.25,f'connector {side}/{j}/{k}')
 for side,y in [('south',-9.56),('north',11.84)]:
  for j,x in enumerate([19.,22.3]):
   for k,z in enumerate([1.2,4.65]):window(project(x,y),z,1.1,1.25,f'tail {side}/{j}/{k}')
 for j,y in enumerate([-7.5,-4.9,7.15,9.75]):
  for k,z in enumerate([1.2,4.65]):
   for x in [17.2,24.63]:window(project(x,y),z,1.05,1.25,f'tail transverse {x}/{j}/{k}')
 rear_u=project(25.25,1.15);rear_door=box(rear_u-1.05,.36,rear_u+1.05,3.15);holes.append(rear_door)
 balcony_door=box(rear_u-.8,4.0,rear_u+.8,6.25);holes.append(balcony_door);windows.append((balcony_door,'east balcony door',False))
 for yy in [-1.25,3.55]:
  for k,z in enumerate([1.6,4.85]):window(project(25.25,yy),z,.8,1.55,f'east portal side slot {yy}/{k}',True)
 us=list(starts);zs=[0,linktop,tailtop,tailtop+.45,wingtop,towertop]
 for sh in holes:
  u0,z0,u1,z1=sh.bounds;us.extend([u0,u1]);zs.extend([z0,z1])
 # Tiny grid slivers are deliberately prevented at serialized FLOAT32 precision.
 us=sorted(set(round(u,7) for u in us));zs=sorted(set(round(z,7) for z in zs))
 cut_shell(b,mapper,us,zs,holes,-.35,0,'pale grey stone','single connected perimeter wall with actual openings',True,height)
 for sh,label,vertical in windows:
  curved_window(b,mapper,sh,label,detail,vertical)
  u0,z0,u1,z1=sh.bounds;uu=(u0+u1)/2;point=np.array(mapper(uu,(z0+z1)/2));out=np.array(mapper(uu,(z0+z1)/2,.1))-point;out/=np.linalg.norm(out)
  probes.append({'label':label,'point':point.tolist(),'normal':out.tolist(),'depth':.29,'material':'dark recessed glass'})
 # Underfloor closure follows the footprint only; no site slab/ground.
 b.plan_prism(poly.buffer(-.08),0,.12,'weathered stone base','closed footprint floor')
 b.plan_prism(front.buffer(-.08).difference(circle),wingtop-.18,wingtop-recess,'grey roof','two flat front wing roof fields')
 b.plan_prism(unary_union([rear,rearport]).buffer(-.08),tailtop-.18,tailtop-recess,'grey roof','closed rear roof field')
 # Narrow raised portal roof (the source photograph shows an eastern projection).
 b.plan_prism(rearport.difference(rearport.buffer(-.22)),tailtop,tailtop+.45,'pale grey stone','eastern raised portal upper wall')
 b.plan_prism(rearport.buffer(-.08),tailtop+.30,tailtop+.45-recess,'grey roof','eastern raised portal roof')
 # The tower overlaps the front wing in plan. Its complete upper cylinder
 # starts at the wing roof; only the exposed lower arc appears in the common
 # perimeter shell. This avoids both internal cylinder walls and duplicated
 # coplanar exterior faces after photo-based tower registration.
 cm=cylindrical_mapper(cx,cy,r)
 cut_shell(b,cm,np.linspace(0,math.tau*r,n+1),[wingtop,towertop],[],-.35,0,'pale grey stone','tower complete upper cylindrical shell',True)
 b.plan_prism(circle.buffer(-.08),towertop-.2,towertop-recess,'grey roof','outer circular terrace closed floor')
 # Three progressively smaller terrace rail rings, with true openings.
 def terrace_rail(radius,z,label):
  mm=cylindrical_mapper(cx,cy,radius);circ=math.tau*radius;count=max(12,round(circ/1.55));gap=circ/count;hs=[]
  for j in range(count):hs.append(box(gap*(j+.5)-gap*.27,z+.31,gap*(j+.5)+gap*.27,z+.52))
  uu=list(np.linspace(0,circ,n+1));zz=[z,z+.31,z+.52,z+.83]
  for h in hs:uu.extend([h.bounds[0],h.bounds[2]])
  cut_shell(b,mm,uu,zz,hs,-.22,0,'light stone coping',label+' / pierced parapet',True)
  ring(b,(cx,cy),radius+.045,z+.83,z+.93,.31,'light stone coping',label+' / continuous cap',n)
  for j in range(count):
   a=math.tau*j/count;q=(cx+(radius-.06)*math.cos(a),cy+(radius-.06)*math.sin(a),z+.94)
   b.box(q,(.25,.25,.2),'light stone coping',label=label+f' / post cap {j}')
 terrace_rail(r,towertop,'outer terrace')
 for radius,z,previous,label in [(4.88,13.65,towertop,'middle terrace'),(3.48,14.95,13.65,'inner terrace')]:
  ring(b,(cx,cy),radius,previous,z,.28,'pale grey stone',label+' / closed riser',n)
  b.plan_prism(Point(cx,cy).buffer(radius-.08,quad_segs=n//4),z-.15,z-recess,'grey roof',label+' / platform')
  terrace_rail(radius,z,label)
 # The centre is a low glazed circular skylight pavilion with a flat cover.
 pr=2.21;pz=14.95;pt=16.55;pm=cylindrical_mapper(cx,cy,pr);pc=math.tau*pr;ph=[]
 for j in range(16):ph.append(box(pc*(j+.5)/16-.22,pz+.28,pc*(j+.5)/16+.22,pt-.24))
 pu=list(np.linspace(0,pc,n+1));pzv=[pz,pz+.28,pt-.24,pt]
 for h in ph:pu.extend([h.bounds[0],h.bounds[2]])
 cut_shell(b,pm,pu,pzv,ph,-.22,0,'pale grey stone','central low circular window pavilion',True)
 for j,h in enumerate(ph):curved_window(b,pm,h,f'pavilion short window {j}',False,True)
 b.plan_prism(Point(cx,cy).buffer(pr+.16,quad_segs=n//4),pt,pt+.15,'light stone coping','central flat circular lid')
 # Closed low barrel roof; the observed section bows across the narrow width.
 x0,y0,x1,y1=p['connector_bounds_enu_m'];width=y1-y0;steps=28 if detail else 14
 # The union footprint removes internal seams at ground level. Height changes
 # still need exposed step walls above the lower curved roof. Their lower
 # boundary follows that roof exactly; no opaque wall is placed inside it.
 curve=[(-width/2+width*k/steps,linktop+1.03*math.sin(math.pi*k/steps))for k in range(steps+1)]
 under=Polygon([(-width/2,0),(width/2,0),*reversed(curve)])
 for xx,top,side,label in [(x0,wingtop,1,'front wing east step wall above barrel'),(x1,tailtop,-1,'rear wing west step wall above barrel')]:
  ff=Facade(b,(xx,(y0+y1)/2-side*width/2),(xx,(y0+y1)/2+side*width/2),label)
  ff.prism(box(-width/2,linktop,width/2,top).difference(under),-.35,0,'pale grey stone','exposed roof-height junction closure')
 vs=[]
 for x in [x0,x1]:
  for k in range(steps+1):
   y=y0+width*k/steps;z=linktop+1.03*math.sin(math.pi*k/steps);vs.append((x,y,z))
  vs.extend([(x,y1-.08,linktop-.17),(x,y0+.08,linktop-.17)])
 m=steps+3;fs=[]
 profile=list(range(m))
 fs.append(tuple(reversed(profile)));fs.append(tuple(j+m for j in profile))
 for j,k in zip(profile,profile[1:]+profile[:1]):fs.append((j,k,k+m,j+m))
 # x-oriented profile winding is corrected by signed mesh volume if required.
 arr=np.asarray(vs);vol=sum(np.dot(arr[f[0]],np.cross(arr[f[k]],arr[f[k+1]])) for f in fs for k in range(1,len(f)-1))/6
 if vol<0:fs=[tuple(reversed(f)) for f in fs]
 b.add(vs,fs,'grey roof','closed low barrel connector roof')
 if detail:
  for x in np.linspace(x0+.45,x1-.45,34):
   pts=[(x,y0+width*k/steps,linktop+1.03*math.sin(math.pi*k/steps)+.02)for k in range(steps+1)]
   b.tube(pts,.016,'stone seam',sides=4,label='barrel roof subtle joint')
 # Front/rear roof parapets use clipped plan rings so no wall spans the tower
 # or the connector roof. All borders are closed volumes.
 for pp,z,excl,label in [(front,wingtop,circle.buffer(.035),'front wing'),(rear,tailtop,unary_union([link,rearport]).buffer(.02),'rear wing')]:
  border=pp.difference(pp.buffer(-.22,join_style=2)).difference(excl)
  b.plan_prism(border,z,z+.62,'pale grey stone',label+' / perimeter parapet')
  b.plan_prism(border.buffer(.04,join_style=2),z+.62,z+.7,'light stone coping',label+' / coping')
 # Two curved rooftop stair flights, as seen in the 2022 overhead photos.
 for side in [-1,1]:
  a0,a1=(.90,1.95) if side>0 else(-1.95,-.90);count=12
  for j in range(count):
   aa=a0+(a1-a0)*j/count;bb=a0+(a1-a0)*(j+1)/count
   rise=(j+1)/count if side>0 else(count-j)/count;z=wingtop+(towertop-wingtop)*rise
   pts=[(cx+rr*math.cos(a),cy+rr*math.sin(a))for rr,angles in [(r+.10,np.linspace(aa,bb,4)),(r+.94,np.linspace(bb,aa,4))]for a in angles]
   b.plan_prism(Polygon(pts),wingtop,z,'light stone coping',f'curved roof stair {side}/{j}')
  # A sloping masonry outside balustrade, with no invented rail decoration.
  mm=cylindrical_mapper(cx,cy,r+1.0,a0);span=(a1-a0)*(r+1);uu=np.linspace(0,span,25 if detail else 13);verts=[]
  for u in uu:
   t=u/span;zz=wingtop+(towertop-wingtop)*(t if side>0 else 1-t)
   verts.extend([mm(u,zz-.08,-.15),mm(u,zz-.08,0),mm(u,zz+.66,0),mm(u,zz+.66,-.15)])
  faces=[(3,2,1,0),(len(verts)-4,len(verts)-3,len(verts)-2,len(verts)-1)]
  for j in range(len(uu)-1):
   for k in range(4):faces.append((4*j+k,4*j+(k+1)%4,4*(j+1)+(k+1)%4,4*(j+1)+k))
  b.add(verts,[tuple(reversed(f)) for f in faces],'pale grey stone',f'curved stair sloping outside parapet {side}')
 # West portal, simplified winged medallion, and four dark panel leaves.
 f=Facade(b,(cx-r,cy+4),(cx-r,cy-4),'west portal')
 f.prism(box(-1.23,.53,1.23,3.63),-.44,-.40,'dark door','bounded four-leaf gate')
 for j in range(4):
  u=-.92+j*.613;f.box(u,2.08,.035,3.04,.045,-.35,'muted brass','thin door divider')
  if detail:
   for z in np.linspace(.92,3.2,6):
    sh=Point(u,z).buffer(.13,resolution=8);f.prism(sh.difference(sh.buffer(-.035)),-.34,-.30,'muted brass','simplified door roundel')
 for u in [-1.52,1.52]:
  f.box(u,2.08,.4,3.18,.2,-.04,'light stone coping','carved jamb simplified')
  if detail:
   pts=[f.point(u+.09*math.sin(t*math.tau*2.5),.62+t*2.9,.085)for t in np.linspace(0,1,48)]
   b.tube(pts,.037,'pale grey stone',sides=6,label='photo-informed dragon jamb flowing relief, not exact carving')
 f.box(0,3.8,3.45,.28,.2,-.03,'light stone coping','door lintel')
 emblem=Point(0,4.38).buffer(.46,resolution=24 if detail else 12)
 f.prism(emblem,.02,.12,'light stone coping','aviation medallion disc')
 f.prism(emblem.difference(emblem.buffer(-.045)),.125,.15,'muted brass','aviation medallion rim')
 for side in [-1,1]:
  wing=Polygon([(side*.4,4.06),(side*1.47,4.55),(side*1.5,4.75),(side*.38,4.74)])
  f.prism(wing,.02,.10,'light stone coping','simplified winged emblem silhouette')
  if detail:
   for z in [4.2,4.37,4.54]:f.prism(Polygon([(side*.48,z),(side*1.26,z+.28),(side*1.31,z+.34),(side*.48,z+.06)]),.105,.13,'pale grey stone','winged emblem feather band')
 plane=Polygon([(-.34,4.39),(-.05,4.34),(.16,4.22),(.24,4.25),(.12,4.39),(.35,4.48),(.27,4.53),(.03,4.47),(-.17,4.54),(-.24,4.51),(-.11,4.43)])
 f.prism(plane,.155,.19,'muted brass','simplified aircraft relief, inscription omitted')
 # Broad shallow semicircular entrance stair: slabs are disjoint stacked risers,
 # rather than overlapping solid cylinders. No surrounding paving is included.
 for j,(rr,ztop) in enumerate([(8.2,.16),(7.75,.32),(7.3,.48)]):
  sector=Point(cx,cy).buffer(rr,quad_segs=n//4).intersection(box(cx-20,cy-12,cx,cy+12)).difference(poly)
  b.plan_prism(sector,0 if j==0 else j*.16,ztop,'weathered stone base',f'west broad shallow step {j}')
 # East doorway and observed short projecting balcony; typography is omitted.
 ef=Facade(b,(25.25,-3.0),(25.25,5.3),'east portal');eu=1.15-ef.center[1]
 ef.prism(box(eu-1.03,.36,eu+1.03,3.13),-.43,-.39,'dark door','bounded dark double gate')
 ef.box(eu,1.75,.035,2.72,.04,-.34,'dark green metal','door middle stile')
 ef.box(eu,3.35,2.55,.27,.24,.01,'light stone coping','four medallion lintel')
 for u in np.linspace(eu-.83,eu+.83,4):ef.prism(Point(u,3.35).buffer(.115,resolution=2),.145,.20,'light stone coping','octagonal lintel boss')
 ef.box(eu,3.88,3.2,.18,1.12,.5,'light stone coping','balcony slab')
 for u in [eu-1.27,eu+1.27]:ef.box(u,3.62,.2,.42,.67,.28,'dark green metal','balcony end support')
 for z in [4.0,4.43,4.88]:ef.box(eu,z,3.06,.07,.075,1.03,'dark green metal','balcony horizontal rail')
 for u in np.linspace(eu-1.48,eu+1.48,7):ef.box(float(u),4.44,.065,.95,.075,1.03,'dark green metal','balcony upright')
 if detail:
  for u in np.linspace(eu-1.22,eu+1.22,6):
   for z in [4.2,4.65]:
    sh=box(u-.15,z-.1,u+.15,z+.1);ef.prism(sh.difference(sh.buffer(-.035)),.99,1.07,'dark green metal','simplified cloud fret balcony motif')
 for side in [-1,1]:ef.box(eu+side*1.51,4.44,.07,.95,1.03,.5,'dark green metal','balcony side rail')
 for j in range(3):ef.box(eu,.06+j*.12,2.35,.12,1.06-j*.27,.58-j*.135,'weathered stone base','east short entrance step')
 # Observed outer-tower eave band and eight very simplified projecting heads.
 ring(b,(cx,cy),r+.05,towertop-.32,towertop-.2,.18,'light stone coping','outer tower narrow eave',n)
 for j in range(8):
  a=math.tau*j/8;b.box((cx+(r+.16)*math.cos(a),cy+(r+.16)*math.sin(a),towertop-.39),(.25,.25,.18),'light stone coping',label='eight simplified eave projections')
 features=[{'kind':'photo-supported-form','name':s}for s in ['rounded front cross-wing with three unequal window bands','west cylindrical tower with five slit windows','three decreasing pierced stone terrace rails','low circular window pavilion and flat lid','two curved roof access stairs','low barrel connector roof','rear cross-wing with slight central projection','west winged aviation medallion and dark four-leaf portal','east balcony with simplified cloud fretwork']]
 meta={'id':ID,'name':'中国航空协会旧址（长海医院飞机楼）','status':'photo-informed bounded exterior estimate','scope':'Present repaired standalone airplane-shaped building only; no adjacent hospital buildings, site slab, interior rooms or underground geometry.','coordinate_convention':'author ENU metres; GLB east/up/south; heading 0','all_dimensions_estimated':True,'all_elevations_estimated':True,'flat_roof_surface_recess_m':recess,'measured_survey':False,'1935_foundation_1936_completion_distinguished':True,'historic_1935_reconstruction_claimed':False,'documented_total_floor_area_m2':1522,'floor_area_not_used_as_footprint':True,'wing_three_window_bands_not_three_equal_floors':True,'photographs_embedded':False,'invented_text_inscriptions':False,'sculptural_relief_simplified':True,'detail_variant':'lod' if lod else'full','map_source':'OpenStreetMap w442978597@2; frozen localId1349','source_register':'source/precise/'+ID+'/source-register.json','copyright':'Original geometry MIT; map reference ODbL-1.0; source photographs retain separate licences'}
 return b,meta,features,probes

def main():
 a=argparse.ArgumentParser();a.add_argument('--out',type=Path,required=True);a.add_argument('--lod',action='store_true');args=a.parse_args();args.out.mkdir(parents=True,exist_ok=True)
 b,meta,features,probes=build(args.lod);suffix='lod'if args.lod else'raw';r=b.save(args.out/(ID+'-'+suffix+'.glb'),meta)
 (args.out/('features-'+suffix+'.json')).write_text(json.dumps({'id':ID,'features':features,'recess_probes':probes},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in r.items()if k!='part_summary'},indent=2))
if __name__=='__main__':main()
