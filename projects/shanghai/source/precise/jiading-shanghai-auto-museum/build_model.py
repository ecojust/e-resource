#!/usr/bin/env python3
"""Reproducible Shanghai Auto Museum raw authoring; root executes generation.

Five-floor, curved, stepped photographic reconstruction. All local dimensions
are declared estimates. No photographic pixels or unlicensed website assets are
embedded. Raw export is separate from native, independent and browser review.
"""
from pathlib import Path
import argparse,hashlib,json,math,sys
import numpy as np
from shapely.geometry import Polygon,LineString,Point,box,shape
from shapely.affinity import scale
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from common.photo_architecture import Builder,pieces
from curves import sample,smooth,lower_roof_z,lower_band_z,upper_band_z
from solids import surface_solid,profile_sweep,panel,ring_stations,subpath,path_data,audit_parts

PALETTE={
 'Museum silver honeycomb aluminium':{'color':[.67,.69,.70],'metallic':.72,'roughness':.36},
 'Museum soffit silver aluminium':{'color':[.53,.55,.56],'metallic':.55,'roughness':.44},
 'Museum recessed panel joint':{'color':[.13,.145,.15],'metallic':.23,'roughness':.69},
 'Museum standing seam underlayer':{'color':[.28,.30,.31],'metallic':.58,'roughness':.52},
 'Museum warm yellow honeycomb ribbon':{'color':[.96,.54,.035],'metallic':.27,'roughness':.33},
 'Museum pale glass':{'color':[.53,.66,.65],'roughness':.19,'metallic':.06,'transmission':.38,'ior':1.46},
 'Museum blue green glass':{'color':[.48,.61,.62],'roughness':.21,'metallic':.05,'transmission':.34,'ior':1.46},
 'Museum warm clear glass':{'color':[.55,.66,.61],'roughness':.19,'metallic':.04,'transmission':.42,'ior':1.46},
 'Museum balustrade glass':{'color':[.72,.82,.80],'roughness':.17,'metallic':.02,'transmission':.64,'ior':1.46,'glass_thickness':.018},
 'Museum dark mullion frame':{'color':[.115,.15,.16],'metallic':.62,'roughness':.39},
 'Museum brushed rail metal':{'color':[.52,.55,.55],'metallic':.80,'roughness':.30},
 'Museum horizontal sun louvre':{'color':[.18,.225,.23],'metallic':.66,'roughness':.43},
 'Museum interior concrete':{'color':[.42,.43,.41],'roughness':.85},
 'Museum interior floor':{'color':[.39,.40,.39],'roughness':.73},
 'Museum pale terrace paver':{'color':[.62,.63,.59],'roughness':.87},
 'Museum dark terrace paver':{'color':[.39,.41,.40],'roughness':.91},
 'Museum terrace timber':{'color':[.42,.26,.115],'roughness':.83},
 'Museum dark sign stone':{'color':[.10,.115,.12],'roughness':.68},
 'Museum white sign relief':{'color':[.91,.92,.89],'roughness':.52},
 'Museum orange sign detail':{'color':[.93,.34,.045],'roughness':.55},
 'Museum planter':{'color':[.24,.26,.24],'roughness':.88},
 'Museum restrained leaf foliage':{'color':[.14,.29,.12],'roughness':.96},
 'Museum white flag fabric':{'color':[.82,.82,.78],'roughness':.91},
 'Museum red flag fabric':{'color':[.65,.018,.025],'roughness':.89},
}

def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def const(z):return lambda x,y:float(z)


class Museum:
 def __init__(self):
  self.g=json.loads((HERE/'geometry-input.json').read_text());self.c=json.loads((HERE/'calibration.json').read_text())
  assert self.g['id']=='jiading-shanghai-auto-museum'
  assert sha(HERE/'geometry-input.json')==self.c['source_geometry_sha256']
  self.e=self.c['estimated'];self.cv=self.c['curves'];self.b=Builder(PALETTE)
  self.repairs=json.loads((HERE/'repair-inputs.json').read_text())
  self.base=sample(self.cv['lower_glass_knots_enu_m']);self.upper=sample(self.cv['upper_outer_knots_enu_m'])
  self.lower_roof=self.base.buffer(self.cv['lower_roof_overhang_m'],quad_segs=12)
  self.entry_line=LineString(self.base.exterior.coords)
  self.entry_s=self.entry_line.project(Point(*self.e['entry_enu_approx']))
  self.openings=[];self.contact_targets=[];self.curved_roles=[];self.facade_records=[]
  self.glass_materials=['Museum pale glass','Museum blue green glass','Museum warm clear glass']
  self.spine_path=self.get_north_spine()
  self.spine_line=LineString(self.spine_path)
  self.spine_cut=self.spine_line.buffer(4.86,cap_style=2,join_style=2)
  self.upper_plate=self.upper.difference(self.spine_cut)
  self.lower_visible_roof=self.lower_roof.difference(self.upper.buffer(-.18,quad_segs=10))
  # This strip overlaps the upper deck by18cm; both meet at the same22.55m
  # datum. No invented floating vertical separation or coincident whole roofs.
  self.terrace=self.lower_visible_roof.intersection(box(-15,-28,28,-5))

 def roof_z(self,x,y):return lower_roof_z(x,y,self.e)

 def beam(self,a,b,width,depth,mat,label,face=(1,0,0)):
  a=np.asarray(a,float);b=np.asarray(b,float);axis=b-a;length=np.linalg.norm(axis)
  if length<.005:return
  axis/=length;normal=np.asarray(face,float);across=np.cross(normal,axis)
  if np.linalg.norm(across)<1e-8:across=np.cross([0,0,1] if abs(axis[2])<.9 else [0,1,0],axis)
  across/=np.linalg.norm(across);normal=np.cross(axis,across)
  self.b.box((a+b)/2,(width,depth,length),mat,basis=[across,normal,axis],label=label)

 def get_north_spine(self):
  q=ring_stations(self.upper,.45);mask=q[:,1]>self.e['north_spine_start_north_m']
  # Rotate after an unselected station to recover one continuous northern arc.
  start=next(i for i,x in enumerate(mask) if not x);q=np.roll(q,-start,axis=0);mask=np.roll(mask,-start)
  groups=[];part=[]
  for xy,yes in zip(q,mask):
   if yes:part.append(xy)
   elif part:groups.append(part);part=[]
  if part:groups.append(part)
  if len(groups)!=1:raise ValueError('Expected one northern spine arc')
  return np.asarray(groups[0])

 def foundations_and_depth(self):
  self.b.plan_prism(self.base.buffer(.20),0,self.e['ground_slab_top_m'],'Museum pale terrace paver','foundation/continuous-ground-slab')
  # Two explicit atrium holes follow the published1–3storey shared-space idea.
  # Positions/axes are estimates; no exhibits or measured interior plan claimed.
  atria=unary_union([scale(Point(8,24).buffer(1,quad_segs=24),8.4,11.3),scale(Point(-22,-28).buffer(1,quad_segs=24),6.8,9.1)])
  for i,z in enumerate(self.e['interior_plate_levels_m'][:2]):
   plan=self.base.buffer(-self.e['lower_glass_storey_insets_m'][i+1]+.15).difference(atria)
   self.b.plan_prism(plan,z-.28,z,'Museum interior floor',f'interior-estimate/lower-floor-{i+2}-real-atrium-holes')
  upplan=self.upper.buffer(-2.6).difference(self.spine_cut.buffer(.15))
  z=self.e['upper_mezzanine_z_m']
  self.b.plan_prism(upplan,z-.27,z,'Museum interior floor','interior-estimate/fifth-floor-plate')
  self.b.plan_prism(box(5,7,12,16),.18,31.15,'Museum interior concrete','interior-estimate/service-core')
  for i,(x,y) in enumerate([[-5,9],[-3,38],[29,36],[31,9],[-24,-24],[-31,-42],[0,-29]]):
   z=min(self.roof_z(x,y)-.8,22.55)
   self.b.tube([[x,y,.17],[x,y,z]],.35,'Museum interior concrete',12,f'interior-estimate/column-{i}')

 def curtain_layer(self,polygon,zbottom,ztop,layer,upper=False):
  line=LineString(polygon.exterior.coords);bay=self.e['glazing_nominal_bay_m'];count=math.ceil(line.length/bay)
  breaks=list(np.linspace(0,line.length,count+1))
  entry=None
  if layer==0:
   centre=line.project(Point(*self.e['entry_enu_approx']));half=self.e['entry_clear_opening_m'][0]/2
   entry=(centre-half,centre+half);breaks.extend(entry)
  breaks=sorted(set(float(x) for x in breaks));active=[];pane_count=0
  for bi,(s0,s1) in enumerate(zip(breaks,breaks[1:])):
   if s1-s0<.045:continue
   q=subpath(line,s0,s1,self.cv['sample_step_m']);mid=q[len(q)//2]
   if upper and min(q[:,1])>46.2:continue  # opaque slotted north wrapper
   topmin=min(float(ztop(*xy)) for xy in q);height=topmin-zbottom
   if height<.3:continue
   rows=max(1,math.ceil(height/self.e['glazing_horizontal_transom_m']))
   fractions=list(np.linspace(0,1,rows+1))
   in_entry=entry and s0>=entry[0]-1e-7 and s1<=entry[1]+1e-7
   if in_entry:
    f=(self.e['ground_slab_top_m']+self.e['entry_clear_opening_m'][1]-zbottom)/height
    fractions=sorted(set([0.,f,*[v for v in fractions if v>f],1.]))
   lean=self.e['lower_glass_outward_lean_per_storey_m'] if not upper else .12
   for row,(a,b) in enumerate(zip(fractions,fractions[1:])):
    if in_entry and b*height<=self.e['entry_clear_opening_m'][1]+1e-6:continue
    bottom=lambda x,y,a=a:zbottom+(float(ztop(x,y))-zbottom)*a
    top=lambda x,y,b=b:zbottom+(float(ztop(x,y))-zbottom)*b
    outward=path_data(q)[2][len(q)//2]
    mat=self.glass_materials[2 if upper and outward[0]<-.35 else 1 if outward[0]>.3 else 0]
    label=f'curtain/layer-{layer+1}/bay-{bi:03d}/glass-pane-{row}'
    panel(self.b,q,bottom,top,mat,label,self.e['curtain_glass_thickness_m'],lean*a,lean*b);pane_count+=1
    # A separate curved solid transom; the glass remains an actual thin solid.
    z=lambda x,y,b=b:zbottom+(float(ztop(x,y))-zbottom)*b
    shift=lean*b
    profile=[[shift-.075,-.0325],[shift+.09,-.0325],[shift+.09,.0325],[shift-.075,.0325]]
    profile_sweep(self.b,q,profile,'Museum dark mullion frame',label.replace('glass-pane','transom'),z_offset=z)
   active.append((bi,s0,s1))
  # One boundary mullion per bay, each tilted to the same layer's glass plane.
  used=sorted(set([s for _,a,b in active for s in (a,b)]))
  for mi,s in enumerate(used):
   q=subpath(line,s-.04,s+.04,.04);xy=q[1];t=q[-1]-q[0];t/=np.linalg.norm(t);n=np.array([t[1],-t[0]])
   if upper and xy[1]>46.3:continue
   low=zbottom
   if entry and entry[0]+.08<s<entry[1]-.08:low=.18+self.e['entry_clear_opening_m'][1]
   top=float(ztop(*xy));lean=self.e['lower_glass_outward_lean_per_storey_m'] if not upper else .12
   self.beam([*xy,low],[*(xy+n*lean),top],.065,.145,'Museum dark mullion frame',f'curtain/layer-{layer+1}/mullion-{mi:03d}',[*n,0])
  self.facade_records.append({'layer':layer+1,'upper':upper,'zbottom_m':zbottom,'plan_area_m2':polygon.area,'glass_panes':pane_count,'entry_cut':list(entry) if entry else None,'lower_inset_or_upper_inset_m':self.e['upper_storey_glass_insets_m'][layer-3] if upper else self.e['lower_glass_storey_insets_m'][layer],'outward_lean_m':lean,'dimensions_measured':False})

 def glazing(self):
  levels=self.e['lower_glass_storey_bottoms_m']
  for i,(z,inset) in enumerate(zip(levels,self.e['lower_glass_storey_insets_m'])):
   polygon=self.base.buffer(-inset,quad_segs=12)
   top=const(levels[i+1]) if i+1<len(levels) else lambda x,y:self.roof_z(x,y)-.76
   self.curtain_layer(polygon,z,top,i)
   if i:
    # Real step deck joins the differently recessed facades; these are not
    # three identical walls concealed behind yellow stripes.
    terrace=self.base.buffer(-self.e['lower_glass_storey_insets_m'][i-1]+.12).difference(polygon.buffer(-.10))
    self.b.plan_prism(terrace,z-.18,z,'Museum soffit silver aluminium',f'curtain/layer-{i+1}/physical-setback-ledge')
  for k,inset in enumerate(self.e['upper_storey_glass_insets_m']):
   low=self.e['upper_glass_bottom_m'] if not k else self.e['upper_mezzanine_z_m']
   high=self.e['upper_mezzanine_z_m'] if not k else self.e['upper_glass_top_m']
   self.curtain_layer(self.upper.buffer(-inset,quad_segs=12),low,const(high),3+k,True)

 def ribbon(self,polygon,zfunc,label,projection=None,height=None,keep=None):
  projection=self.e['yellow_ribbon_projection_m'] if projection is None else projection
  height=self.e['yellow_ribbon_height_m'] if height is None else height
  q=ring_stations(polygon,.45)
  profile=[[-.22,-height/2],[projection,-height/2],[projection,height/2],[-.22,height/2]]
  if keep is None:
   profile_sweep(self.b,q,profile,'Museum warm yellow honeycomb ribbon',label,zfunc,closed=True);segments=1
  else:
   active=[bool(keep(*((q[i]+q[(i+1)%len(q)])/2))) for i in range(len(q))]
   if all(active):raise ValueError('A specified ribbon interruption must exist')
   start=next(i for i,a in enumerate(active) if not a);segment=[];groups=[]
   for k in range(1,len(q)+1):
    i=(start+k)%len(q);j=(i+1)%len(q)
    if active[i]:
     if not segment:segment.append(q[i])
     segment.append(q[j])
    elif segment:groups.append(segment);segment=[]
   if segment:groups.append(segment)
   for i,segment in enumerate(groups):profile_sweep(self.b,segment,profile,'Museum warm yellow honeycomb ribbon',f'{label}/segment-{i}',zfunc)
   segments=len(groups)
  self.curved_roles.append({'label':label,'role':'yellow_transition_ribbon','stations':len(q),'closed':keep is None,'segments':segments,'actual_thickness_m':height,'projection_m':projection})

 def ribbons_and_louvres(self):
  for band in range(2):
   keep=(lambda x,y:not(x<-11 and 22<y<34)) if band==0 else None
   self.ribbon(self.base.buffer(.12),lambda x,y,band=band:lower_band_z(x,y,band,self.e),f'ribbon/lower-transition-{band+1}',keep=keep)
   # Physical backing behind the folded band. Its sharply changing elevation
   # is NOT treated as the height of an accessible walking route.
   strip=self.base.buffer(.80).difference(self.base.buffer(-1.90))
   if band==0:strip=strip.difference(box(-100,22,-11,34))
   top=lambda x,y,band=band:lower_band_z(x,y,band,self.e)+.26
   surface_solid(self.b,strip,top,lambda x,y,top=top:top(x,y)-.28,'Museum soffit silver aluminium',f'ramp/band-support-strip-{band+1}',grid=3)
   if band==1:self.rail(np.asarray(self.base.buffer(.82).exterior.coords),top,'balustrade/upper-exterior-strip')
  self.ribbon(self.upper.buffer(-2.55),lambda x,y:upper_band_z(x,y,self.e),'ribbon/upper-height-transition',projection=.72,keep=lambda x,y:y<45.3)
  # Louvres remain discrete blades and standoffs with open air between rows.
  for prefix,poly,zvalues in [
   ('ground',self.base.buffer(.23),[3.6,4.05,4.5,4.95]),
   ('third',self.base.buffer(-.64),[15.5,15.94,16.38,16.82,17.26]),
   ('upper',self.upper.buffer(-2.5),[23.35,23.79,24.23,24.67,25.11])]:
   line=LineString(poly.exterior.coords);nseg=math.ceil(line.length/4.)
   for j in range(nseg):
    s0=j*line.length/nseg;s1=(j+1)*line.length/nseg;q=subpath(line,s0,s1,.55);mid=q[len(q)//2]
    if prefix=='upper' and mid[1]>45:continue
    if prefix=='ground' and mid[0]<-10 and 4<mid[1]<15:continue
    if prefix=='third' and mid[0]<-15 and mid[1]<-14:continue
    for k,z in enumerate(zvalues):
     profile=[[-.04,-.0375],[.36,-.0375],[.36,.0375],[-.04,.0375]]
     profile_sweep(self.b,q,profile,'Museum horizontal sun louvre',f'louvre/{prefix}/strip-{j:03d}/blade-{k}',const(z))
    xy,t,normal=path_data(q);i=len(q)//2;p=xy[i];n=normal[i]
    self.beam([*p,zvalues[0]-.05],[*p,zvalues[-1]+.05],.08,.20,'Museum horizontal sun louvre',f'louvre/{prefix}/strip-{j:03d}/standoff',[*n,0])
    reach={'ground':.50,'third':.85,'upper':1.0}[prefix]
    for k,z in enumerate([zvalues[0]+.03,zvalues[-1]-.03]):
     self.beam([*(p-n*reach),z],[*(p+n*.12),z],.065,.075,'Museum horizontal sun louvre',f'louvre/{prefix}/strip-{j:03d}/anchor-{k}',[0,0,1])

 def panel_grid(self,polygon,zfunc,underside,prefix,material,step=2.4):
  # Separate shallow solids leave actual25mm seams exposing the dark substrate.
  x0,y0,x1,y1=polygon.bounds;gap=.025
  for ix in range(math.floor(x0/step),math.ceil(x1/step)):
   for iy in range(math.floor(y0/step),math.ceil(y1/step)):
    q=polygon.intersection(box(ix*step+gap/2,iy*step+gap/2,(ix+1)*step-gap/2,(iy+1)*step-gap/2))
    for j,p in enumerate(pieces(q)):
     if p.area<.04:continue
     top=lambda x,y:float(zfunc(x,y))+(0.055 if underside else 0.)
     label=f'{prefix}/panel-{ix}-{iy}-{j}'
     extra=self.repairs['changed_part']['bottom_extension_m'] if label==self.repairs['changed_part']['label'] else 0.
     bottom=lambda x,y,extra=extra:float(zfunc(x,y))-(0. if underside else .055)-extra
     surface_solid(self.b,p,top,bottom,material,label,grid=step)

 def fascia(self,polygon,zfunc,thick,prefix,skip_north=False):
  line=LineString(polygon.exterior.coords);count=math.ceil(line.length/1.8);gap=.025
  for i in range(count):
   s0=i*line.length/count+gap/2;s1=(i+1)*line.length/count-gap/2;q=subpath(line,s0,s1,.45)
   if skip_north and max(q[:,1])>46.8:continue
   profile=[[-.10,-thick],[.08,-thick],[.08,0],[-.10,0]]
   profile_sweep(self.b,q,profile,'Museum silver honeycomb aluminium',f'{prefix}/edge-panel-{i}',zfunc)

 def c_outer_profile(self):
  top=self.e['upper_roof_top_m'];bottom=self.e['upper_lower_deck_top_m']-self.e['upper_lower_deck_thickness_m'];r=3.8
  q=[[-5.0,top],[-r,top]]
  q.extend([[-r+r*math.cos(t),top-r+r*math.sin(t)] for t in np.linspace(math.pi/2,0,19)[1:]])
  q.append([0,bottom+r])
  q.extend([[-r+r*math.cos(t),bottom+r+r*math.sin(t)] for t in np.linspace(0,-math.pi/2,19)[1:]])
  q.append([-5.0,bottom]);return np.asarray(q)

 def north_wrapped_spine(self):
  outer=LineString(self.c_outer_profile());core_outer=outer.offset_curve(-.05,join_style=1);inner=outer.offset_curve(-.94,join_style=1)
  csolid=Polygon([*core_outer.coords,*list(inner.coords)[::-1]])
  if not csolid.is_valid:raise ValueError('C shell section invalid')
  # Five glazing strips are genuine omissions from the opaque wrapper.
  # A recessed curved glass solid fills each opening; these are not empty holes.
  length=self.spine_line.length;w=self.e['north_spine_slot_width_m']
  holes=[(f*length-w/2,f*length+w/2) for f in self.e['north_spine_slots_arc_fractions']]
  bounds=[0.,*[v for pair in holes for v in pair],length]
  for j,(a,b) in enumerate(zip(bounds,bounds[1:])):
   inside=any(a>=lo-1e-6 and b<=hi+1e-6 for lo,hi in holes)
   q=subpath(self.spine_line,a,b,.45)
   if inside:
    glassline=outer.offset_curve(-.16,join_style=1);profile=glassline.buffer(.0325,cap_style=2,join_style=1)
    profile_sweep(self.b,q,list(profile.exterior.coords),'Museum blue green glass',f'north-spine/glazed-wrap-slot-{j//2+1}')
    rr=3.8-.16;upper_c=self.e['upper_roof_top_m']-3.8;lower_c=self.e['upper_lower_deck_top_m']-.95+3.8
    for ti,z in enumerate([23.,25.,27.,29.,31.]):
     if z<lower_c:d=-3.8+math.sqrt(rr*rr-(z-lower_c)**2)
     elif z>upper_c:d=-3.8+math.sqrt(rr*rr-(z-upper_c)**2)
     else:d=-.16
     bars=[[d-.045,z-.03],[d+.045,z-.03],[d+.045,z+.03],[d-.045,z+.03]]
     profile_sweep(self.b,q,bars,'Museum dark mullion frame',f'north-spine/slot-{j//2+1}-transom-{ti}')
    for side,s in enumerate([a,b]):
     jamb=subpath(self.spine_line,max(0,s-.035),min(length,s+.035),.035)
     profile_sweep(self.b,jamb,list(csolid.exterior.coords),'Museum dark mullion frame',f'north-spine/slot-{j//2+1}-jamb-{side}')
    self.openings.append({'role':'north_curved_glazed_slot','label':f'north-spine/glazed-wrap-slot-{j//2+1}','arc_interval_m':[a,b],'nominal_width_m':w,'curves_into_underside':True,'filled_with_real_recessed_glass':True})
   else:
    profile_sweep(self.b,q,list(csolid.exterior.coords),'Museum recessed panel joint',f'north-spine/structural-C-segment-{j}')
    n=math.ceil((b-a)/1.8)
    skin=outer.offset_curve(-.035,join_style=1).buffer(.025,cap_style=2,join_style=1)
    for k in range(n):
     start=a+(b-a)*k/n+.0125;stop=a+(b-a)*(k+1)/n-.0125
     qp=subpath(self.spine_line,start,stop,.45)
     profile_sweep(self.b,qp,list(skin.exterior.coords),'Museum silver honeycomb aluminium',f'north-spine/silver-wrap-panel-{j}-{k}')
  self.curved_roles.append({'role':'continuous_silver_frame','label':'north-spine','vertical_corner_radius_est_m':3.8,'outer_profile_d_z_m':self.c_outer_profile().tolist(),'glazed_slots':len(holes),'note':'C section has curved top/vertical/underside; not merely planar-rounded roof slabs.'})

 def roofs_and_soffits(self):
  low=self.lower_visible_roof;upper=self.upper_plate;top=self.e['upper_roof_top_m'];deck=self.e['upper_lower_deck_top_m']
  surface_solid(self.b,low,lambda x,y:self.roof_z(x,y)-.055,lambda x,y:self.roof_z(x,y)-.80,'Museum standing seam underlayer','roof/lower-curved-continuous-underlayer')
  surface_solid(self.b,upper,const(top-.055),const(top-1.0),'Museum standing seam underlayer','roof/upper-top-underlayer')
  surface_solid(self.b,upper,const(deck-.04),const(deck-.93),'Museum recessed panel joint','roof/upper-deep-cantilever-underlayer')
  finish=upper.difference(low)
  inside=finish.intersection(self.upper.buffer(-3.1))
  outside=finish.difference(inside)
  surface_solid(self.b,inside,const(deck),const(deck-.06),'Museum interior floor','roof/fourth-floor-finish')
  self.panel_grid(outside,const(deck),False,'roof/upper-deck-rim-finish','Museum silver honeycomb aluminium')
  self.panel_grid(low.difference(self.terrace),self.roof_z,False,'roof/lower-silver-top','Museum silver honeycomb aluminium')
  self.panel_grid(upper,const(top),False,'roof/upper-silver-top','Museum silver honeycomb aluminium')
  self.panel_grid(upper,const(deck-.95),True,'soffit/upper-deep-grid','Museum soffit silver aluminium')
  self.panel_grid(low,lambda x,y:self.roof_z(x,y)-.85,True,'soffit/lower-grid','Museum soffit silver aluminium')
  self.fascia(self.lower_roof,self.roof_z,.85,'silver-frame/lower-continuous-edge')
  self.fascia(self.upper,const(top),1.05,'silver-frame/upper-roof-edge',True)
  self.fascia(self.upper,const(deck),.95,'silver-frame/upper-bottom-edge',True)
  self.north_wrapped_spine()
  self.contact_targets.append({'role':'upper-deck-to-low-wing','upper_deck_z_m':deck,'lower_north_roof_z_m':self.roof_z(0,0),'plan_overlap_band_m':.18,'actual_exported_contact_pending':True})

 def entrance(self):
  w,h=self.e['entry_clear_opening_m'];q=subpath(self.entry_line,self.entry_s-w/2,self.entry_s+w/2,.4)
  xy,t,n=path_data(q);center=q[len(q)//2];along=t[len(q)//2];out=n[len(q)//2];floor=.18
  mapper=lambda u,z,d:np.array([*(center+along*u+out*d),z])
  for i,u in enumerate([-w/2,-w/6,w/6,w/2]):
   self.beam(mapper(u,floor-.015,0),mapper(u,floor+h+.10,0),.10,.18,'Museum brushed rail metal',f'entry/main-jamb-{i}',[*out,0])
  self.beam(mapper(-w/2,floor+h,0),mapper(w/2,floor+h,0),.12,.18,'Museum brushed rail metal','entry/continuous-head',[*out,0])
  for door in range(6):
   cell=door//2;side=door%2;leafw=w/6-.075;u=-w/2+cell*w/3+(0 if not side else w/3)
   angle=math.radians(24 if door==2 else (-18 if door==3 else 0))
   direction=(along if not side else -along)*math.cos(angle)+out*math.sin(angle)
   hinge=mapper(u,floor,0);normal=np.array([direction[1],-direction[0],0])
   origin=hinge;point=lambda x,z,d:origin+np.array([direction[0]*x,direction[1]*x,z])+normal*d
   # Closed actual glass and separate frame around it; six independent leaves.
   self.b.box(point(leafw/2,(h-.12)/2,0),(leafw,.045,h-.12),'Museum pale glass',basis=[[*direction,0],normal,[0,0,1]],label=f'entry/leaf-{door}/glass')
   for k,x in enumerate([0,leafw]):self.beam(point(x,0,0),point(x,h-.12,0),.055,.075,'Museum brushed rail metal',f'entry/leaf-{door}/vertical-{k}',normal)
   for k,z in enumerate([0,h-.12]):self.beam(point(0,z,0),point(leafw,z,0),.055,.075,'Museum brushed rail metal',f'entry/leaf-{door}/horizontal-{k}',normal)
   self.b.tube([point(leafw*.80,.9,.10),point(leafw*.80,1.5,.10)],.021,'Museum brushed rail metal',8,f'entry/leaf-{door}/open-grip')
   for k,z in enumerate([.9,1.5]):
    self.b.tube([point(leafw*.80,z,.01),point(leafw*.80,z,.10)],.018,'Museum brushed rail metal',8,f'entry/leaf-{door}/grip-attachment-{k}')
  self.openings.append({'role':'ground_entry_opening','width_est_m':w,'height_est_m':h,'base_z_m':floor,'centre_enu':center.tolist(),'arc_interval_m':[self.entry_s-w/2,self.entry_s+w/2],'door_leaves':6,'door_angles_degrees':[0,0,24,-18,0,0],'navigability_accepted':False})

 def rail(self,points,zfunc,label,glass=True):
  q=np.asarray(points,float);count=max(1,math.ceil(LineString(q).length/1.8));line=LineString(q)
  for i in range(count):
   a=i*line.length/count;b=(i+1)*line.length/count;segment=np.asarray([line.interpolate(v).coords[0] for v in np.linspace(a,b,4)])
   for j,xy in enumerate([segment[0]] if i<count-1 or line.is_ring else [segment[0],segment[-1]]):
    z=float(zfunc(*xy));self.b.tube([[*xy,z-.02],[*xy,z+1.12]],.032,'Museum brushed rail metal',8,f'{label}/post-{i}-{j}')
   if glass:panel(self.b,segment,lambda x,y:float(zfunc(x,y))+.12,lambda x,y:float(zfunc(x,y))+1.04,'Museum balustrade glass',f'{label}/glass-{i}',.018)
   self.b.tube([[*xy,float(zfunc(*xy))+1.12] for xy in segment],.033,'Museum brushed rail metal',8,f'{label}/top-rail-{i}')
   if not glass:self.b.tube([[*xy,float(zfunc(*xy))+.58] for xy in segment],.022,'Museum brushed rail metal',8,f'{label}/open-middle-rail-{i}')

 def garden(self):
  if self.terrace.is_empty:raise ValueError('Fourth-level terrace missing')
  self.panel_grid(self.terrace,self.roof_z,False,'terrace/pavers','Museum pale terrace paver',step=1.25)
  x0,y0,x1,y1=self.terrace.bounds
  for y in np.arange(math.ceil(y0/2.5)*2.5,y1,2.5):
   stripe=self.terrace.intersection(box(x0,y,x1,y+.18))
   surface_solid(self.b,stripe,lambda x,y:self.roof_z(x,y)+.006,lambda x,y:self.roof_z(x,y)-.03,'Museum dark terrace paver',f'terrace/dark-paving-stripe-{y:.1f}',grid=3)
  # This bounded garden edge is estimated from an unscaled partial plan/photo.
  for j,poly in enumerate(pieces(self.terrace)):
   self.rail(np.asarray(poly.exterior.coords),self.roof_z,f'terrace/open-glass-balustrade-{j}')
  for i,(x,y) in enumerate([[-7,-21],[4,-21],[15,-21],[21,-13]]):
   if not self.terrace.buffer(-1.1).contains(Point(x,y)):continue
   z=self.roof_z(x,y);self.b.box((x,y,z+.31),(1.9,.8,.62),'Museum planter',label=f'terrace/planter-{i}')
   for j in range(5):self.b.lathe((x-.7+j*.35,y),[(z+.61,.20),(z+.95,.30),(z+1.20,.12)],'Museum restrained leaf foliage',8,f'terrace/plant-{i}-{j}')

 def external_stair(self):
  center=np.asarray(self.e['external_stair_estimate_enu'],float);along=np.array([-.6,-.8]);out=np.array([.8,-.6]);width=1.7
  flights=4;rise=self.e['external_stair_total_rise_m']/flights;steps=18;run=steps*.27
  landing=1.45;floor=.18
  for f in range(flights):
   sign=1 if f%2==0 else -1;side=(f%2-.5)*(width+.16)
   start=center+out*side-along*run/2*sign;z0=floor+f*rise
   for j in range(steps):
    mid=start+along*sign*(j+.5)*.27;z=z0+(j+1)*rise/steps
    self.b.box([*mid,z-.065],(.285,width,.13),'Museum interior concrete',basis=[[*along,0],[*out,0],[0,0,1]],label=f'stair/flight-{f+1}/tread-{j+1:02d}')
   end=start+along*sign*run
   for k,side2 in enumerate([-width/2,width/2]):
    a=start+out*side2;b=end+out*side2
    self.beam([*a,z0-.08],[*b,z0+rise-.08],.16,.20,'Museum warm yellow honeycomb ribbon',f'stair/flight-{f+1}/solid-stringer-{k}',[*out,0])
    pts=np.asarray([a,b]);self.rail(pts,lambda x,y,a=a,z0=z0,sign=sign:z0+np.dot(np.array([x,y])-a,along*sign)/run*rise,f'stair/flight-{f+1}/open-rail-{k}',False)
   self.b.box([*(end-out*side+along*sign*landing/2),z0+rise-.09],(landing,width*2+.28,.18),'Museum interior concrete',basis=[[*along,0],[*out,0],[0,0,1]],label=f'stair/landing-{f+1}')
  for i,(a,b) in enumerate([(-run/2-landing,.0),(run/2+landing,.0)]):
   xy=center+along*a+out*b
   level=3 if a>0 else 4
   self.b.tube([[*xy,.12],[*xy,floor+rise*level-.05]],.105,'Museum brushed rail metal',10,f'stair/estimated-support-post-{i}')
  self.contact_targets.append({'role':'external_stair','centre_enu':center.tolist(),'flights_estimated':flights,'steps_per_flight_estimated':steps,'step_rise_m':rise/steps,'tread_run_m':.27,'width_m':width,'structure_and_rail_actual_contacts_pending':True,'neighbor_nonintersection_pending':True})

 def ground_curved_ramp(self):
  # The observed outer low ramp is separate from the sharp facade band folds.
  # Its position/rise are estimates, with no claim of certified accessibility.
  line=LineString(self.base.exterior.coords)
  a=line.project(Point(-38,-16));b=line.project(Point(28,-17))
  if b<=a:raise ValueError('Southern curved-ramp endpoints reversed')
  q=subpath(line,a,b,.45);route=LineString(q);length=route.length
  def z(x,y):return .28+5.42*float(smooth(route.project(Point(x,y))/length))
  profile_sweep(self.b,q,[[-.4,-.25],[2.5,-.25],[2.5,0],[-.4,0]],'Museum pale terrace paver','ramp/ground-curved-access-deck',z)
  profile_sweep(self.b,q,[[2.30,-.25],[2.61,-.25],[2.61,.34],[2.30,.34]],'Museum warm yellow honeycomb ribbon','ramp/ground-curved-yellow-edge',z)
  xy,t,n=path_data(q);outer=xy+n*2.45
  # Project the edge back to the same route to preserve the ramp height.
  self.rail(outer,z,'ramp/ground-curved-glass-balustrade')
  self.contact_targets.append({'role':'ground_curved_ramp','plan_route_length_estimate_m':length,'height_range_estimate_m':[.28,5.70],'maximum_cubic_grade_estimate':1.5*5.42/length,'width_estimate_m':2.9,'source':'Observed low outer curvedramp; unmeasured endpoints and grade','certified_accessibility':False,'actual_contacts_pending':True})

 def entrance_sign(self):
  # An explicitly modeled, perforated wheel-like museum emblem; no image logo.
  origin=np.array([-31.,-5.,.18]);along=np.array([0.,-1.,0.]);out=np.array([-1.,0.,0.])
  self.b.box(origin+[0,0,.72],(.55,8.3,1.44),'Museum dark sign stone',label='sign/low-stone-name-base')
  centre=origin+along*2.4+[0,0,1.4];outer=Point(0,0).buffer(1.12,quad_segs=32)
  cut=[]
  for angle,r in [(90,.27),(18,.18),(-43,.25),(-125,.29),(160,.34)]:
   a=math.radians(angle);cut.append(Point(.57*math.cos(a),.57*math.sin(a)).buffer(r,quad_segs=16))
  ring=outer.difference(unary_union(cut))
  self.b.prism(ring,0,.17,lambda u,z,d:centre+along*u+np.array([0,0,z])+out*d,'Museum white sign relief','sign/perforated-wheel-emblem')
  for i,(angle,r) in enumerate([(90,.15),(-43,.17),(-125,.19)]):
   a=math.radians(angle);disk=Point(.57*math.cos(a),.57*math.sin(a)).buffer(r,quad_segs=16)
   self.b.prism(disk,-.01,.025,lambda u,z,d:centre+along*u+np.array([0,0,z])+out*d,'Museum orange sign detail',f'sign/emblem-orange-inset-{i}')
  self.openings.append({'role':'museum_sign','perforated_emblem_holes':len(cut),'dimensions_estimated':True,'exact_trademark_vector_claim':False})
  glyphs=json.loads((HERE/'references'/'museum-sign-outlines.json').read_text())['glyphs']
  for row,text,size,baseline,mat in [(0,'上海汽车博物馆',.56,.80,'Museum white sign relief'),(1,'SHANGHAI AUTO MUSEUM',.22,.42,'Museum orange sign detail')]:
   width=sum(glyphs[ch]['advance_em']*size for ch in text);u=-1.35-width/2
   for i,ch in enumerate(text):
    outline=shape(glyphs[ch]['outline'])
    if not outline.is_empty:
     position=origin+along*u+np.array([0,0,baseline])+out*.285
     self.b.prism(outline,0,.035,lambda x,z,d,position=position:position+along*x*size+np.array([0,0,z*size])+out*d,mat,f'sign/letter-row-{row}-{i}')
    u+=glyphs[ch]['advance_em']*size

 def forecourt_poles(self):
  for i,y in enumerate([-4.2,-2.3,-.4]):
   x=-34.;height=14.2 if i==1 else 13.6
   self.b.lathe((x,y),[(.0,.24),(.13,.24),(.17,.10)],'Museum brushed rail metal',16,f'forecourt/pole-{i}/base')
   self.b.tube([[x,y,.14],[x,y,height]],.044,'Museum brushed rail metal',12,f'forecourt/pole-{i}/shaft')
   if i==2:continue
   q=np.asarray([[x+.12*math.sin(t*5),y-t*1.85] for t in np.linspace(0,1,15)])
   bottom=lambda xx,yy,height=height,y=y:height-1.22-.10*max(0,y-yy)
   top=lambda xx,yy,height=height,y=y:height-.10*max(0,y-yy)
   panel(self.b,q,bottom,top,'Museum red flag fabric' if i==1 else 'Museum white flag fabric',f'forecourt/pole-{i}/bounded-cloth',.016)

 def local_repairs(self):
  existing={p['label'] for p in self.b.parts}
  for row in self.repairs['added_parts']:
   if row['label'] in existing:raise ValueError('Repair label already exists')
   self.b.plan_prism(shape(row['plan']),row['bottom_m'],row['top_m'],row['material'],row['label'])
   self.contact_targets.append({'role':'local-v2-repair','label':row['label'],'actual_v1_targets':row['actual_v1_target_labels'],'actual_v2_contact_pending':True,'not_structural_certification':True})

 def build(self,output):
  if output.exists():raise ValueError('Use a fresh output directory; preserve prior attempts')
  self.foundations_and_depth();self.glazing();self.ribbons_and_louvres()
  self.roofs_and_soffits();self.entrance();self.garden();self.external_stair();self.ground_curved_ramp();self.entrance_sign();self.forecourt_poles()
  self.local_repairs()
  qa=audit_parts(self.b.parts);qa.update({'repair_inputs_sha256':sha(HERE/'repair-inputs.json'),'declared_change_scope_sha256':sha(HERE/'change-scope.json'),'actual_changed_part_inventory_pending':True,'schema':'auto-museum-float32-geometry-v11','source_geometry_sha256':sha(HERE/'geometry-input.json'),'calibration_sha256':sha(HERE/'calibration.json'),'builder_sha256':sha(Path(__file__)),'openings':self.openings,'curved_roles':self.curved_roles,'facade_layers':self.facade_records,'contact_targets':self.contact_targets,'floor_count_source_supported':5,'level_heights_measured':False,'nominal_height_m':32.45,'native_visual_passed':False,'browser_passed':False,'actual_exported_contact_passed':False})
  output.mkdir(parents=True);write(output/'geometry-report.json',qa)
  if not qa['passed']:raise ValueError('Individual Float32 solid validation failed: '+str(qa['failures'][:12]))
  meta={'repair_inputs_sha256':sha(HERE/'repair-inputs.json'),'declared_change_scope_sha256':sha(HERE/'change-scope.json'),'baseline_raw_sha256':self.repairs['baseline_raw']['sha256'],'id':self.g['id'],'name':'上海汽车博物馆','model_revision':self.c['model_revision'],'copyright':'Model CC-BY-SA-4.0; code MIT; original footprint © OpenStreetMap contributors/Overture Maps ODbL-1.0; reference photographs retain their licenses; no photo pixels embedded.','license':'CC-BY-SA-4.0','source_geometry_sha256':sha(HERE/'geometry-input.json'),'source_anchor':self.g['anchor'],'source_boundary':self.g['geometry'],'calibration_sha256':sha(HERE/'calibration.json'),'height_measured':False,'nominal_official_height_m':32.45,'appearance_epoch':self.c['appearance_epoch'],'uncertainty':self.c['limits'],'embedded_photos':False}
  photos=json.loads((HERE/'references'/'photo-register.json').read_text())['photos']
  meta['source_photos']=[{'author':p['artist'],'license':p['license'],'license_url':p['license_url'],'source':p['commons_page'],'sha256':p['sha256'],'embedded_as_texture':False} for p in photos]
  raw=output/'jiading-shanghai-auto-museum-raw.glb';export=self.b.save(raw,meta)
  if raw.stat().st_size>=self.c['lod_protection']['raw_target_max_bytes']:raise ValueError('Raw exceeds45MB author budget; reduce hidden detail without dropping protected geometry')
  record={'schema':'auto-museum-raw-metadata-v11','id':self.g['id'],'raw':{'file':raw.name,'bytes':raw.stat().st_size,'sha256':sha(raw)},'geometry_report_sha256':sha(output/'geometry-report.json'),'source_geometry_sha256':sha(HERE/'geometry-input.json'),'triangles':export['triangles'],'parts':export['parts'],'materials':export['materials'],'embedded_images':0,'ground_base_m':0,'height_estimate_m':qa['bounds_enu_m'][1][2],'height_measured':False,'geometry_builder_preflight_passed':True,'actual_exported_structure_passed':False,'native_visual_passed':False,'browser_passed':False,'role_and_contact_checks_required':True}
  write(output/'asset-metadata.json',record);print(json.dumps(record,ensure_ascii=False,indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();Museum().build(a.output)
