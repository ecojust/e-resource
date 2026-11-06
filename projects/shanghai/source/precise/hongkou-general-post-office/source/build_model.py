"""Original photo-informed Shanghai General Post Office exterior.

The checked image observations, geometry registration, and uncertain roof/court
scope are separate inputs. All architectural subdivisions and ornament are
interpretations; no third-party meshes, photo textures, or surveyed interior.
"""
import argparse,json,math
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,Point,LineString,box,shape
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from common.photo_architecture import Builder,Facade,opening,facade_ring
from common.sign_lettering import add_facade_lettering
from shell_geometry import perimeter_mapper,rectangular_shell
from postal_geometry import transform_plan,loft,fluted_column,sphere,statue_group,clock_face,curve_square_points

ID='hongkou-general-post-office';ROOT=Path(__file__).resolve().parent
PARAMS=json.loads((ROOT/'model-parameters.json').read_text())
PALETTE={'sandstone wall':{'color':[.49,.45,.37],'roughness':.88},'dressed limestone':{'color':[.65,.60,.49],'roughness':.8},'carved pale stone':{'color':[.65,.60,.49],'roughness':.8},'red brick':{'color':[.40,.20,.14],'roughness':.9},'recessed glass':{'color':[.15,.24,.24],'roughness':.29,'metallic':.20},'green window frame':{'color':[.13,.29,.25],'roughness':.62,'metallic':.22},'green spandrel':{'color':[.13,.29,.25],'roughness':.68,'metallic':.18},'verdigris copper':{'color':[.20,.44,.36],'roughness':.55,'metallic':.55},'verdigris bronze':{'color':[.23,.43,.35],'roughness':.65,'metallic':.45},'dark bronze':{'color':[.065,.075,.064],'roughness':.51,'metallic':.35},'ivory clock face':{'color':[.80,.78,.67],'roughness':.7},'roof zinc':{'color':[.27,.29,.27],'roughness':.75},'court glazing':{'color':[.47,.52,.43],'roughness':.30,'metallic':.12,'alpha':.62},'roof guard glass':{'color':[.64,.71,.68],'roughness':.21,'metallic':.05,'alpha':.30},'roof foliage':{'color':[.18,.28,.12],'roughness':.95},'court gold steel':{'color':[.55,.43,.21],'roughness':.63,'metallic':.42},'gold lettering':{'color':[.63,.48,.20],'roughness':.51,'metallic':.55},'red flag':{'color':[.64,.025,.018],'roughness':.8}}


def horizontal_band(b,poly,z,h,projection=.24,material='dressed limestone',label='continuous cornice'):
 band=poly.buffer(projection,join_style=2).difference(poly.buffer(-.25,join_style=2))
 if PARAMS.get('west_neighbor_exclusion_enu_m'):band=band.difference(Polygon(PARAMS['west_neighbor_exclusion_enu_m']).buffer(.20,join_style=2))
 b.plan_prism(band,z,z+h,material,label)


def rusticated_pier(f,u,w,top=15.55):
 # Continuous vertical pier with separated raised courses; bounded joints.
 f.box(u,top/2,w,top,.22,.08,'sandstone wall','rusticated pier backing')
 for z in np.arange(.35,top,.56):f.box(u,z,min(w+.13,w*1.08),.46,.16,.23,'dressed limestone','raised rustication course')


def spandrel(f,u,z,w,lod):
 f.box(u,z,w,.87,.16,-.05,'green spandrel','green metal spandrel')
 f.box(u,z,w-.30,.52,.08,.055,'green spandrel','recessed metal panel frame')
 if not lod:
  f.prism(box(u-w/2+.15,z-.27,u+w/2-.15,z+.27).difference(box(u-w/2+.24,z-.19,u+w/2-.24,z+.19)),.08,.12,'green window frame','raised panel inset edge')
 if z<8:
  ring=Point(u,z).buffer(.31,resolution=12).difference(Point(u,z).buffer(.235,resolution=12));f.prism(ring,.10,.16,'gold lettering','small spandrel wreath ring')


def add_top_gallery(b,f,centers,width,lod,probes):
 # Open street arcade backed by a distinct recessed glazed wall.
 inset=2.05;a=f.a[:2]-f.n[:2]*inset;c=f.b[:2]-f.n[:2]*inset;back=Facade(b,a,c,f.label+' recessed fourth-floor gallery wall');holes=[]
 for j,u in enumerate(centers):
  hole=opening(u,16.2,width*.78,2.35);holes.append(hole);back.window(hole,2,2,frame='green window frame',trim=False,label='fourth-floor inset gallery window')
 back.wall(15.85,19.25,holes,.30,'sandstone wall')
 # Continuous floor and ceiling inside the individual edge avoids open sky
 # gaps above the short square piers, while preserving a 2m-deep arcade.
 for z in [15.93,19.23]:f.box(0,z,f.length,.15,2.15,-1.0,'dressed limestone','open gallery continuous floor or ceiling')
 for u in centers:
  f.box(u,16.05,width,.24,.30,.04,'dressed limestone','gallery low sill')
 if centers:
  u=centers[len(centers)//2]+width*.26
  probes.append({'label':f.label+' fourth-floor arcade clear prefix','kind':'void','origin':f.point(u,17.15,.2).tolist(),'direction':(-f.n).tolist(),'max_distance':1.45})


def body(b,lod,features,probes):
 foundation=Polygon(PARAMS['body_polygon_enu_m']);poly=orient(foundation.intersection(Polygon(PARAMS['author_envelope_enu_m']).buffer(-.85,join_style=2)),sign=1.)
 source=PARAMS['source_vertices_enu_m'];old_edges=[LineString([source[i],source[(i+1)%len(source)]]) for i in range(len(source))]
 mapper,starts,_=perimeter_mapper(poly);ps=list(poly.exterior.coords);us=list(starts);zs=[0,19.5];cuts=[];count=0;parts=[]
 for i,(a,c) in enumerate(zip(ps,ps[1:])):
  f=Facade(b,a,c,f'body perimeter {i}');mid=Point(f.center[:2]);nearest=min(range(len(old_edges)),key=lambda j:old_edges[j].distance(mid));distance=old_edges[nearest].distance(mid);inner=distance>1.5;party=not inner and nearest==1;street=not inner and nearest in [0,5];entrance=not inner and nearest==6;brick=inner or nearest in [2,3]
  if party:continue
  if f.length<2.:continue
  if entrance:
   # Tall door with four attached columns, semicircular transom, three upper windows.
   centers=[0.];floors=[(.7,4.9,3.5),(7.0,2.8,6.2),(11.2,3.3,5.7),(16.35,2.10,5.9)]
  else:
   spacing=4.6 if street else 4.2;num=max(1,round((f.length-(10 if street else 2))/spacing));margin=4.2 if street else .75
   spacing=(f.length-2*margin)/num;centers=[-f.length/2+margin+spacing*(j+.5) for j in range(num)];width=min(3.55,spacing-.75)
   floors=[(.85,3.70,width),(6.15,3.55,width),(11.35,3.65,width)]
   if not street:floors.append((16.45,2.15,width))
  for j,u in enumerate(centers):
   for k,(bottom,h,w) in enumerate(floors):
    hole=opening(u,bottom,w,h);glob=box(starts[i]+u+f.length/2-w/2,bottom,starts[i]+u+f.length/2+w/2,bottom+h);cuts.append(glob);us.extend([glob.bounds[0],glob.bounds[2]]);zs.extend([bottom,bottom+h]);f.window(hole,3 if w>3 else 2,3 if not lod else 2,frame='green window frame',trim=brick,label='estimated inward-facing court window' if inner else 'photographed rhythm recessed window');count+=1
    if street and k in [0,1]:spandrel(f,u,bottom+h+.60,w,lod)
    if k==1 and j in [0,len(centers)//2]:probes.append({'label':f.label+f' lower recessed window {j}','kind':'ray','origin':f.point(u+w*.08,bottom+h*.36,.7).tolist(),'direction':(-f.n).tolist(),'material':'recessed glass','max_distance':1.5})
  if street:
   width=min(3.55,spacing-.75)
   for u in centers:
    glob=box(starts[i]+u+f.length/2-width/2,16.15,starts[i]+u+f.length/2+width/2,18.95);cuts.append(glob);us.extend([glob.bounds[0],glob.bounds[2]]);zs.extend([16.15,18.95])
   add_top_gallery(b,f,centers,width,lod,probes)
   for k in range(len(centers)+1):
    u=centers[0]-spacing*.5+k*spacing;fluted_column(b,f.point(u,0,.53)[:2],.26,15.48,.51,lod,f.label+' three-storey fluted giant column',tangent=f.t[:2])
   for sign in [-1,1]:rusticated_pier(f,sign*(f.length/2-1.45),2.6)
   for u in [f.length/2-1.45,-f.length/2+1.45]:
    f.box(u,17.5,1.45,2.35,.18,.15,'dressed limestone','attic terminal framed panel')
   for z in [15.55,19.30]:
    for u in np.arange(-f.length/2+.25,f.length/2,.43 if not lod else .86):f.box(u,z,.19,.23,.36,.19,'dressed limestone','cornice dentil')
  elif entrance:
   for u in [-4.7,4.7]:rusticated_pier(f,u,1.3,15.5)
   for u in [-2.1,-1.40,1.40,2.1]:fluted_column(b,f.point(u,0,.62)[:2],.25,6.40,.26,lod,'corner entrance four columns',tangent=f.t[:2])
   f.box(0,6.43,5.5,.35,.72,.46,'dressed limestone','entrance projecting entablature')
   # Semicircular transom ring fills the rectangular opening corners with stone.
   rect=box(-3.1,7.,3.1,9.8);arc=opening(0,7.,6.2,2.8,2.8,24 if not lod else 12)
   f.prism(rect.difference(arc),-.45,.025,'sandstone wall','corner doorway rounded transom solid spandrels')
   f.prism(arc.buffer(.16,join_style=2).difference(arc).simplify(1e-6,preserve_topology=True),.03,.19,'dressed limestone','corner doorway semicircular surround')
   for u in [-1.0,1.0]:f.box(u,12.85,.18,3.45,.22,.18,'dressed limestone','upper triple window separator')
   add_facade_lettering(f,'上海邮政博物馆',0,10.45,7.2,.66,.21,.27,'gold lettering',label='documented museum name, approximate typeface')
  elif brick:
   for u in centers:
    for z in [5.1,10.1,15.5]:f.box(u,z,3.7,.17,.18,.08,'dressed limestone','brick bay horizontal lintel')
   if not lod:
    # Limited shallow horizontal mortar courses outside all real openings.
    for z in np.arange(.25,15.6,.35):
     strip=box(-f.length/2,z-.012,f.length/2,z+.012)
     localcuts=[]
     for u in centers:
      for bo,h,w in floors:localcuts.append(box(u-w/2-.16,bo-.15,u+w/2+.16,bo+h+.16))
     strip=strip.difference(unary_union(localcuts))
     if not strip.is_empty:f.prism(strip,.005,.015,'sandstone wall','shallow brick course')
  parts.append({'edge':i,'source_edge':nearest,'street_colonnade':street,'courtyard_side':inner,'red_brick':brick,'length_m':f.length,'bays':len(centers)})
 # Make one continuous closed shell, then choose the wall material region by
 # edge in a companion clipped skin; the stone inner structural shell remains.
 rectangular_shell(b,mapper,us,zs,cuts,-.48,'sandstone wall','closed continuous U perimeter wall',True)
 # Visible brick skins have exactly the same openings and sit 12mm outward.
 for row in parts:
  if not row['red_brick']:continue
  i=row['edge'];f=Facade(b,ps[i],ps[i+1],f'brick face {i}');holes=[]
  for cut in cuts:
   x0,z0,x1,z1=cut.bounds
   if x0>=starts[i]-1e-6 and x1<=starts[i+1]+1e-6:holes.append(box(x0-starts[i]-f.length/2,z0,x1-starts[i]-f.length/2,z1))
  surface=box(-f.length/2,0,f.length/2,19.5).difference(unary_union(holes));f.prism(surface,.002,.012,'red brick','bounded brick skin with true openings')
 b.plan_prism(foundation.buffer(-.02,join_style=2),0,.18,'dark stone','U-plan ground closure within source, no new site plaza')
 b.plan_prism(poly.buffer(-.43,join_style=2),19.14,19.44,'roof zinc','continuous inset U roof under wall cap')
 for z,h,p in [(0,.35,.10),(15.45,.42,.45),(15.95,.20,.52),(19.15,.35,.48)]:horizontal_band(b,poly,z,h,p)
 features['main_body']={'height_estimate_m':19.5,'window_openings':count,'plan_area_m2':poly.area,'facades':parts,'top_gallery_clear_depth_m':2.05,'giant_columns_span_three_lower_window_registers':True,'north_red_brick':True}
 return poly


def tower(b,lod,features,probes):
 t=np.asarray(PARAMS['tower_tangent_enu']);n=np.array([t[1],-t[0]]);center=np.asarray(PARAMS['tower_center_enu_m']);detail=not lod
 # Concave-side/rounded-shoulder lower block, with one southeast clock face.
 pts=[(-4.5,4.5),(4.5,4.5)]
 for a in np.linspace(math.pi/2,-math.pi/2,13 if detail else 7)[1:]:pts.append((4.5+2.0*math.cos(a),1.0+3.5*math.sin(a)))
 pts += [(4.5,-5.0),(-4.5,-5.0)]
 for a in np.linspace(-math.pi/2,math.pi/2,13 if detail else 7)[1:-1]:pts.append((-4.5-2.0*math.cos(a),1.+3.5*math.sin(a)))
 poly=orient(transform_plan(pts,center,t),sign=1.)
 b.plan_prism(poly,19.4,32.2,'sandstone wall','tower lower curved shoulders and single clock wall')
 for z,h,p in [(19.5,.32,.27),(31.68,.22,.28),(32.10,.35,.55)]:horizontal_band(b,poly,z,h,p,label='tower curved lower entablature')
 f=Facade(b,center-t*4.5+n*4.5,center+t*4.5+n*4.5,'southeast single clock front');clock_face(f,25.85,1.85,lod)
 for u in [-4.04,4.04]:
  for z in np.arange(20.,31.5,.62):f.box(u,z,1.0,.48,.19,.17,'dressed limestone','clock front quoins')
 for u in [-3.08,3.08]:
  f.box(u,25.95,.60,1.3,.22,.17,'dressed limestone','clock flanking ornamental console')
  for z in [25.5,26.4]:sphere(b,f.point(u,z,.38),(.24,.24,.24),'dressed limestone','clock console carved roundel',lod)
 # Circular cartouche wreath and drop beneath the clock, seen in low-angle photos.
 for a in np.linspace(math.pi*1.05,math.pi*1.95,11 if detail else 6):
  u=math.cos(a)*2.22;zz=25.85+math.sin(a)*2.22
  sphere(b,f.point(u,zz,.33),(.13,.12,.19),'dressed limestone','clock cartouche pendant foliage',lod)
 f.prism(Polygon([(-.38,23.72),(.38,23.72),(.23,23.18),(0,23.02),(-.23,23.18)]),.14,.38,'dressed limestone','clock central lower drop')
 for side in [-1,1]:
  q=center+t*side*6.4+n*3.1
  b.lathe(q,[(19.5,.48),(19.8,.58),(20.,.42),(20.2,.37),(20.6,.61),(20.95,.68),(21.15,.54),(21.38,.30),(21.6,.22),(21.9,.08)],'dressed limestone',20 if detail else 10,'photographed tower-foot stone urn')
 # Photo-evidenced narrow side marks are sealed shallow dark panels, not
 # extra clock faces or an assertion of verified open internal apertures.
 for side in [-1,1]:
  pc=center+t*side*6.50+n*.8;ff=Facade(b,pc+n*.27,pc-n*.27,'curved clock-side narrow window')
  if side<0:ff=Facade(b,pc-n*.27,pc+n*.27,'curved clock-side narrow window')
  ff.box(0,25.0,.50,.95,.025,.03,'dark bronze','small side slit')
  probes.append({'label':'clock shoulder visible narrow dark panel '+str(side),'kind':'ray','origin':[*list(center+t*side*8+n*.8),25.0],'direction':[*list(-t*side),0.0],'max_distance':3.0,'material':'dark bronze'})
 # Checked rooftop wording, freestanding raised glyphs on a thin support rail.
 add_facade_lettering(f,'人民邮电',0,33.75,8.1,1.35,.45,.57,'verdigris bronze',label='documented rooftop postal inscription')
 f.box(0,32.9,8.5,.07,.07,.42,'dark bronze','rooftop lettering support')
 for u in [-3.0,-1.0,1.0,3.0]:f.box(u,33.40,.045,1.9,.045,.40,'dark bronze','lettering narrow vertical support')
 # Two original three-person silhouette groups stand on curved side ledges.
 for side,label in [(-1,'west'),(1,'east')]:
  c=center+t*side*5.7+n*.8;stangent=n if side==1 else -n
  statue_group(b,c,stangent,32.43,lod,label+' three figure copper statuary')
 # Four corners each carry a close pair of round columns: eight in total.
 crown_base=transform_plan(curve_square_points(4.85,.48,8 if detail else 4),center,t)
 b.plan_prism(crown_base,32.35,33.0,'dressed limestone','open upper tower platform')
 for u,v in [(-3.4,-3.4),(3.4,-3.4),(3.4,3.4),(-3.4,3.4)]:
  # Pair follows the tangent of its adjacent facade, with diagonal corner gap.
  for du,dv in [(.70 if u>0 else -.70,0),(0,.70 if v>0 else -.70)]:
   c=center+t*(u+du)+n*(v+dv);fluted_column(b,c,33.0,42.12,.43,lod,'upper tower paired corner column',tangent=t,fluted=False)
 # Slender corner piers link pair capitals without filling the four openings.
 for u,v in [(-3.4,-3.4),(3.4,-3.4),(3.4,3.4),(-3.4,3.4)]:
  c=center+t*u+n*v;b.box([*c,37.5],[.44,.44,9.0],'sandstone wall',label='upper open-tower corner pier')
 # Continuous curved cornice and ceiling; four sides bow inward horizontally.
 canopy=transform_plan(curve_square_points(5.25,1.0,12 if detail else 6),center,t)
 def wave(poly,z):
  local=[((np.asarray(q)-center)@t,(np.asarray(q)-center)@n)for q in list(poly.exterior.coords)[:-1]]
  r=max(max(abs(u),abs(v))for u,v in local)
  return [z+.72*min(1.,max(0.,(r-1.)/3.5))*(min(abs(u),abs(v))/r)**2 for u,v in local]
 # Thick eaves rise at the four paired-column corners and sag between them.
 loft(b,[canopy,canopy],[wave(canopy,41.58),wave(canopy,42.18)],'dressed limestone','upper tower thick vertically curved concave cornice')
 lower=transform_plan(curve_square_points(5.34,1.01,12 if detail else 6),center,t)
 loft(b,[lower,lower],[wave(lower,41.63),wave(lower,41.84)],'sandstone wall','dark inset curved cornice fascia')
 # Copper pagoda-like mansard silhouette tapers rapidly, curves into a neck,
 # and ends in a low bulb. The profile is an author fit to checked photographs.
 profiles=[(41.98,5.1,1.0),(42.32,5.08,1.0),(42.65,4.55,.88),(43.10,3.91,.72),(43.75,3.25,.53),(44.65,2.78,.36),(45.45,2.54,.22),(46.05,2.50,.18),(46.26,2.82,.22),(46.53,2.82,.22),(46.66,2.49,.18),(47.15,2.37,.16),(47.64,1.94,.11),(48.05,1.38,.04),(48.33,.76,0),(48.55,.55,0)]
 loops=[transform_plan(curve_square_points(r,a,12 if detail else 6),center,t) for z,r,a in profiles];loft(b,loops,[wave(poly,z+.20) for poly,(z,r,a) in zip(loops,profiles)],'verdigris copper','swept concave copper crown')
 # Vertical panel seams follow four corners and midpoints, floating 2cm outside.
 for side in range(4):
  for frac in [-1.,-.5,0,.5,1.] if detail else [-1.,0,1.]:
   points=[]
   for z,r,a in profiles:
    u=r*frac;v=r-a*(1-frac*frac)
    if side==0:x,y=u,v
    elif side==1:x,y=v,-u
    elif side==2:x,y=-u,-v
    else:x,y=-v,u
    q=center+t*x+n*y;points.append([q[0],q[1],z+.225+.72*min(1.,max(0.,(r-1.)/3.5))*(min(abs(x),abs(y))/r)**2])
   b.tube(points,.028,'verdigris bronze',5,'copper roof raised seam')
 b.lathe(center,[(48.70,.55),(48.84,.57),(49.08,.35),(49.30,.22),(49.50,.10)],'verdigris copper',16 if detail else 8,'small crown finial below flagstaff')
 b.lathe(center,[(49.48,.065),(57.70,.038)],'aged brass',8,'8.2m documentary flagstaff above selected 49.5m roof tip')
 # Tiny fixed red cloth indicates the photographed national flag, without
 # fabric animation or invented wind direction as a measured fact.
 q=center+np.array([1.15,0]);b.box([q[0],q[1],56.9],[2.3,.035,1.25],'red flag',label='red rooftop flag simplified static cloth')
 for v,label in [(4.25,'front'),(-4.25,'rear')]:
  q=center+n*v;direction=-n if v>0 else n
  probes.append({'label':'upper tower '+label+' real through-opening','kind':'void','origin':[q[0],q[1],37.2],'direction':[direction[0],direction[1],0],'max_distance':8.1})
 features['tower']={'center_enu_m':center.tolist(),'tangent_enu':t.tolist(),'selected_total_without_flagstaff_m':49.5,'flagstaff_m':8.2,'top_m':57.7,'documented_alternative_height_m':51.16,'main_roof_m':19.5,'lower_clock_top_m':32.5,'upper_colonnade_top_m':42.0,'single_southeast_clock':True,'side_clock_faces':False,'upper_columns':8,'statuary_groups':2,'figures_per_group':3,'sculpture_scope':'original simplified silhouettes; no exact cast or portrait reconstruction'}


def court_roof(b,lod,features,probes):
 court=Polygon(PARAMS['court_polygon_enu_m']);origin=np.asarray(PARAMS['plan_origin_enu_m']);t=np.asarray(PARAMS['plan_tangent_enu']);inn=np.array([-t[1],t[0]])
 uv=Polygon([[(np.asarray(p)-origin)@t,(np.asarray(p)-origin)@inn]for p in court.exterior.coords]);x0,y0,x1,y1=uv.bounds;mid=(y0+y1)/2;half=(y1-y0)/2;spring=19.45;rise=3.3
 def z(v):
  q=max(0,1-((v-mid)/half)**2);return spring if q<1e-10 else spring+rise*q**.5
 def mapper(u,v,d):
  xy=origin+t*u+inn*v;return xy[0],xy[1],z(v)+d
 # Subdivide into narrow panels before extrusion, so their triangles follow
 # the actual curved top rather than bridging the whole roof as a flat plane.
 nx=max(2,round((x1-x0)/3.5));ny=14 if not lod else 8
 xs=np.linspace(x0,x1,nx+1);ys=np.linspace(y0,y1,ny+1)
 for i in range(nx):
  for j in range(ny):
   cell=uv.intersection(box(xs[i],ys[j],xs[i+1],ys[j+1]))
   if cell.area<1e-4:continue
   b.prism(cell,-.09,0,mapper,'court glazing','2010-evidenced curved canopy pane, estimated plan')
 # Cross-vault ribs and longitudinal purlins stop at the mapped source.
 for x in xs:
  line=uv.intersection(LineString([(x,y0-.01),(x,y1+.01)]))
  if line.geom_type!='LineString' or line.length<.1:continue
  lo,hi=line.bounds[1],line.bounds[3];points=[mapper(x,y,.045)for y in np.linspace(lo,hi,25 if not lod else 13)]
  b.tube(points,.08,'court gold steel',6 if not lod else 4,'curved canopy transverse rib')
 for y in ys:
  line=uv.intersection(LineString([(x0-.01,y),(x1+.01,y)]))
  if line.geom_type!='LineString' or line.length<.1:continue
  lo,hi=line.bounds[0],line.bounds[2];b.tube([mapper(lo,y,.055),mapper(hi,y,.055)],.06,'court gold steel',6 if not lod else 4,'canopy longitudinal purlin')
 # Close both visible vaulted end faces, using the same y samples as the
 # roof panel grid. Framed translucent end glass is evidenced in photo07;
 # exact bay arrangement is estimated rather than copied as an interior plan.
 for k,ff in enumerate(facade_ring(b,court,'courtyard barrel end')):
  av=(ff.a[:2]-origin)@inn;cv=(ff.b[:2]-origin)@inn
  if abs(cv-av)<half:continue
  count=ny;upper=[]
  for fraction in np.linspace(0,1,count+1):
   u=-ff.length/2+ff.length*fraction;yy=av+(cv-av)*fraction;upper.append((u,z(yy)))
  outline=Polygon([(-ff.length/2,spring),(ff.length/2,spring),*reversed(upper)]).simplify(1e-7,preserve_topology=True)
  ff.prism(outline,-.08,-.015,'court glazing','continuous arched end glazing')
  bars=[]
  for u in np.linspace(-ff.length/2,ff.length/2,9):bars.append(box(u-.055,spring,u+.055,spring+rise+.1))
  for zz in [spring+.08,spring+1.3,spring+2.5]:bars.append(box(-ff.length/2,zz-.055,ff.length/2,zz+.055))
  frame=outline.intersection(unary_union(bars))
  ff.prism(frame,-.04,.055,'court gold steel','arched end vertical and horizontal glazing grid')
  ff.builder.tube([ff.point(u,zz,.04)for u,zz in upper],.075,'court gold steel',6 if not lod else 4,'continuous canopy curved end rim')
  for fraction in [.25,.50,.75]:
   u=-ff.length/2+ff.length*fraction;zz=spring+1.05
   probes.append({'label':f'curved canopy end {k} sealed point {fraction}','kind':'solid','origin':ff.point(u,zz,.5).tolist(),'direction':(-ff.n).tolist(),'max_distance':.8})
 # An estimated roof enclosure is delivered, not an accessible reconstructed
 # museum interior. Its bottom is a plain bounded floor, not display cases.
 b.plan_prism(court,0,.16,'dark stone','bounded unexhibited courtyard floor')
 features['courtyard_cover']={'photo_reference_year':2010,'photographic_evidence':'photo-07 and official museum interior context','plan_estimated':True,'present_day_state_verified':False,'canopy_spring_m':spring,'canopy_highest_m':spring+rise,'interiors_modeled':False,'plan_area_m2':court.area}


def roof_details(b,poly,lod,features):
 # Modern perimeter glazing is directly visible in the checked south views.
 # Its posts, panel rhythm and exact offsets are authored estimates.
 frame=PARAMS['source_vertices_enu_m'];lines=[LineString([frame[i],frame[(i+1)%len(frame)]])for i in range(len(frame))];rails=0
 for f in facade_ring(b,poly,'roof perimeter guard'):
  mid=Point(f.center[:2]);j=min(range(len(lines)),key=lambda k:lines[k].distance(mid))
  if lines[j].distance(mid)>1.3 or j==1 or f.length<2.:continue
  if j==6:continue # tower covers the corner bay
  count=max(1,round(f.length/2.7));spacing=f.length/count
  f.box(0,20.48,f.length,.065,.065,-.4,'dark bronze','roof handrail')
  f.box(0,19.60,f.length,.07,.07,-.4,'dark bronze','roof glass lower rail')
  for u in np.linspace(-f.length/2+.05,f.length/2-.05,count+1):f.box(u,20.04,.06,.94,.08,-.40,'dark bronze','roof guard post')
  for i in range(count):
   u=-f.length/2+spacing*(i+.5);f.box(u,20.03,spacing-.13,.80,.025,-.4,'roof guard glass','thin translucent roof guard panel')
  rails+=count
 # Two low rear rooftop service boxes and two shallow planters express only
 # photo-visible roof occupancy, not the complete equipment or garden plan.
 origin=np.asarray(PARAMS['plan_origin_enu_m']);t=np.asarray(PARAMS['plan_tangent_enu']);inn=np.array([-t[1],t[0]])
 for j,(u,v,w,d,h)in enumerate([(20,54,7.8,4.3,1.9),(76,53,5.2,3.6,1.6)]):
  c=origin+t*u+inn*v;foot=transform_plan([(-w/2,-d/2),(w/2,-d/2),(w/2,d/2),(-w/2,d/2)],c,t)
  assert poly.contains(foot), 'rooftop room outside the accepted main footprint'
  b.plan_prism(foot,19.45,19.5+h,'sandstone wall','estimated photo-visible low roof service box')
  b.plan_prism(foot.buffer(.1,join_style=2),19.5+h,19.64+h,'roof zinc','roof service box cap')
  ff=Facade(b,c-t*w*.40+inn*d*.51,c+t*w*.40+inn*d*.51,'roof service louver')
  for k in range(4):ff.box(0,19.9+k*.18,w*.55,.10,.025,.03,'dark bronze','ventilation louver')
 for j,(u,v)in enumerate([(35,54),(62,55)]):
  c=origin+t*u+inn*v;foot=transform_plan([(-2,-1),(2,-1),(2,1),(-2,1)],c,t)
  assert poly.contains(foot)
  b.plan_prism(foot,19.46,19.9,'sandstone wall','small estimated roof planter')
  for k,du in enumerate([-1.1,0,1.1]):
   q=c+t*du;sphere(b,[*q,20.65],[.85,.70,.9],'roof foliage','low photo-informed roof planting mass',lod)
 features['roof_details']={'perimeter_glass_panels':rails,'service_boxes':2,'low_planters':2,'reference':'photo01 visible perimeter guards, low structures and vegetation; exact layout estimated','complete_current_roof_reconstructed':False}

def build(lod=False):
 b=Builder(PALETTE);features={};probes=[];main=body(b,lod,features,probes);roof_details(b,main,lod,features);tower_start=len(b.parts);tower(b,lod,features,probes);tower_parts=b.parts[tower_start:];court_roof(b,lod,features,probes)
 verts=np.concatenate([np.asarray(p['vertices'])for p in tower_parts]);features['tower']['actual_component_bounds_enu_m']={'min':verts.min(0).tolist(),'max':verts.max(0).tolist()}
 meta={'id':ID,'name':'上海邮政总局历史主楼与钟塔','scope':PARAMS['scope'],'anchor':PARAMS['anchor'],'variant':'lod' if lod else 'raw','height_m':57.7,'selected_documentary_height_without_flagstaff_m':49.5,'all_architectural_subdivisions_estimated':True,'source_register':'source-register.json','copyright':'Original geometry MIT; OpenStreetMap plan reference ODbL-1.0; no photo pixels or third-party model mesh embedded'}
 return b,meta,features,probes

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--lod',action='store_true');p.add_argument('--out',type=Path,required=True);a=p.parse_args();b,m,f,r=build(a.lod);report=b.save(a.out,m);a.out.with_suffix('.features.json').write_text(json.dumps({'features':f,'probes':r},ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='part_summary'},ensure_ascii=False))
