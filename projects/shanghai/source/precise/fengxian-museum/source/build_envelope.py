#!/usr/bin/env python3
"""Fengxian spatial/level draft. All curved forms and levels are estimates.

No private photograph pixels; source mask remains unchanged. This is not the
complete fin/window/landscape detail model and must be visually reviewed.
"""
from pathlib import Path
import argparse,math,json,hashlib,sys
import numpy as np
from shapely.geometry import Polygon,Point,LineString,box as rect,shape
from shapely.geometry.polygon import orient
from shapely.affinity import scale
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
from scipy.interpolate import CubicSpline
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'common'))
from photo_architecture import Builder,Facade,pieces
P={'copper fins':{'color':[.33,.13,.065],'roughness':.49,'metallic':.63},'bronze roof screen':{'color':[.36,.14,.075],'roughness':.54,'metallic':.55},'low iron glass':{'color':[.16,.27,.31],'roughness':.16,'metallic':.03,'alpha':.34},'blue grey spandrel':{'color':[.17,.24,.27],'roughness':.62},'glass guard':{'color':[.60,.76,.78],'roughness':.13,'alpha':.22,'metallic':0},'white structural':{'color':[.75,.76,.72],'roughness':.83},'white coping':{'color':[.84,.84,.79],'roughness':.75},'roof plants':{'color':[.25,.37,.075],'roughness':.97},'roof path':{'color':[.54,.56,.52],'roughness':.92},'dark roof walk':{'color':[.22,.24,.21],'roughness':.90},'dark metal':{'color':[.13,.16,.16],'roughness':.48,'metallic':.6},'light floor':{'color':[.46,.49,.48],'roughness':.91}}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def smooth(points,n=120):
 q=np.array(points,float);q=np.vstack([q,q[0]]);t=np.r_[0,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))];t/=t[-1];f=CubicSpline(t,q,bc_type='periodic');return f(np.linspace(0,1,n,endpoint=False))
class Museum:
 def __init__(self):
  self.b=Builder(P);self.g=json.loads((HERE/'geometry-input.json').read_text());self.reg=json.loads((HERE.parent/'registration-v1/registration.json').read_text());a=math.radians(self.reg['rotation_ccw_from_image_x_to_east_deg']);self.R=np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]]);self.s=self.reg['metres_per_pixel'];self.pc=np.array(self.reg['plan_origin_pixel_x_up_y']);self.translation=np.array(self.reg['translation_east_north_m']);self.features=[]
  self.outer=self.poly(smooth(self.reg['manual_outer_control_points_px'],160));self.source=shape(self.g['model_geometry_local_east_north_m']);self.hole=Polygon(self.source.interiors[0]);self.shell=self.outer.difference(self.hole)
  self.leaves={
   'A':self.poly(smooth([(365,140),(389,144),(410,164),(422,194),(421,232),(410,261),(389,279),(361,284),(335,273),(316,253),(308,223),(309,190),(326,158),(347,143)],100)),
   'B':self.poly(smooth([(286,292),(312,292),(333,304),(348,328),(350,354),(337,378),(311,390),(279,391),(249,381),(235,362),(234,341),(248,321),(267,306)],90)),
   'C':self.poly(smooth([(410,287),(438,296),(457,316),(470,346),(471,371),(455,393),(426,401),(396,396),(377,379),(368,355),(370,329),(386,302)],90))}
  # Authored floor plates stay inside the independently continuous veil.
  # This small outer-edge trim does not change any inner courtyard/roof holes.
  self.leaves={name:poly.intersection(self.outer.buffer(-.25)) for name,poly in self.leaves.items()}
  self.recesses={'A':(self.xy([331,218]),17*self.s),'B':(self.xy([285,317]),20*self.s)}
 def xy(self,p):return (np.array(p)*[1,-1]-self.pc)@self.R.T*self.s+self.translation
 def poly(self,points):return orient(Polygon([self.xy(p) for p in points]),sign=1)
 def zroof(self,x,y):return float(np.clip(16.3+.9*math.sin(x/27)+.7*math.cos(y/25),15.,18.))
 def ring(self,c,r,z,thick,label,material='white structural',inner=0):
  p=Point(c).buffer(r,resolution=40)
  if inner:p=p.difference(Point(c).buffer(inner,resolution=40))
  self.b.plan_prism(p,z-thick,z,material,label);return p
 def wall_loop(self,poly,bottom,top,material,label,pitch=3.0):
  pts=list(poly.exterior.coords)
  for i,(a,b) in enumerate(zip(pts,pts[1:])):
   za=top(*a) if callable(top) else top;zb=top(*b) if callable(top) else top;f=Facade(self.b,a,b,label+f'/panel-{i}');profile=Polygon([(-f.length/2,bottom),(f.length/2,bottom),(f.length/2,zb),(-f.length/2,za)])
   f.prism(profile,-.055,0,material,'true-curved-skin')
  if pitch:
   line=poly.exterior;count=max(3,round(line.length/pitch))
   for j in range(count):
    p=np.array(line.interpolate(j/count,normalized=True).coords[0]);q=np.array(line.interpolate((j/count+1e-4)%1,normalized=True).coords[0]);t=(q-p)/np.linalg.norm(q-p);n=np.array([t[1],-t[0]]);h=(top(*p) if callable(top) else top)-bottom
    self.b.box([*p,bottom+h/2],(.065,.085,h),'dark metal',[[*t,0],[*n,0],[0,0,1]],label+f'/mullion-{j}')
 def railing(self,line,z,label):
  length=line.length;count=max(6,round(length/2.2));points=[np.array(line.interpolate(j/count,normalized=True).coords[0]) for j in range(count+1)]
  for i,(a,b) in enumerate(zip(points,points[1:])):
   f=Facade(self.b,a,b,label+f'/{i}');zz=z(*a) if callable(z) else z;zb=z(*b) if callable(z) else z
   f.prism(Polygon([(-f.length/2,zz+.10),(f.length/2,zb+.10),(f.length/2,zb+1.10),(-f.length/2,zz+1.10)]),-.008,.008,'glass guard','guard-panel')
   self.b.tube([[*a,zz+1.12],[*b,zb+1.12]],.027,'dark metal',6,label+'/toprail')
   self.b.tube([[*a,zz],[*a,zz+1.12]],.022,'dark metal',6,label+'/post')
 def roof_surface(self,poly,label,top=None,material='roof plants',thickness=.25):
  top=top or self.zroof
  x0,y0,x1,y1=poly.bounds;vs=[];faces=[];lookup={}
  def index(x,y,d):
   key=(round(x,10),round(y,10),d)
   if key not in lookup:lookup[key]=len(vs);vs.append([x,y,top(x,y)+d])
   return lookup[key]
  for i,x in enumerate(np.arange(x0,x1,5)):
   for j,y in enumerate(np.arange(y0,y1,5)):
    clipped=poly.intersection(rect(x,y,x+5,y+5))
    for p in pieces(clipped):
     # Unified top/bottom mesh; no coincident vertical walls at internal grid
     # boundaries. Only the actual architectural perimeter gets a side skin.
     for tri in constrained_delaunay_triangles(p).geoms:
      q=list(orient(tri,sign=1).exterior.coords)[:3];faces.append(tuple(index(xx,yy,0.) for xx,yy in q));faces.append(tuple(index(xx,yy,-thickness) for xx,yy in reversed(q)))
     for ring in [p.exterior,*p.interiors]:
      q=list(ring.coords)
      for a,b in zip(q,q[1:]):
       midpoint=Point((a[0]+b[0])/2,(a[1]+b[1])/2)
       if poly.boundary.distance(midpoint)<1e-7:faces.append((index(*a,-thickness),index(*b,-thickness),index(*b,0.),index(*a,0.)))
  self.b.add(vs,faces,material,label+'/unified-curved-roof-solid')
 def fin_loop(self,line,bottom,top,pitch,material,label):
  count=round(line.length/pitch)
  for i in range(count):
   p=np.array(line.interpolate(i/count,normalized=True).coords[0]);q=np.array(line.interpolate((i/count+1e-4)%1,normalized=True).coords[0]);t=(q-p)/np.linalg.norm(q-p);n=np.array([t[1],-t[0]]);z=top(*p) if callable(top) else top
   self.b.box([*p,(bottom+z)/2],(.065,.28,z-bottom),material,[[*t,0],[*n,0],[0,0,1]],label+f'/fin-{i}')
  self.features.append({'kind':'actual_separated_vertical_fins','label':label,'count':count,'draft_pitch_m':pitch,'transparent_gaps':True})
 def connector_deck(self,a,b,za,zb,width,label):
  a=np.array(a);b=np.array(b);v=b-a;v/=np.linalg.norm(v);n=np.array([-v[1],v[0]])*width/2
  points=[a-n,b-n,b+n,a+n];zs=[za,zb,zb,za];vs=[[float(q[0]),float(q[1]),z-.18] for q,z in zip(points,zs)]+[[float(q[0]),float(q[1]),z] for q,z in zip(points,zs)]
  self.b.add(vs,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],'white coping',label)
  for side in [-1,1]:
   aa=a+side*n;bb=b+side*n
   self.b.tube([[*aa,za+1.1],[*bb,zb+1.1]],.035,'dark metal',6,label+'/provisional-handrail')
 def build(self):
  topology=json.loads((HERE.parent/'roof-topology-v3a/roof-regions.json').read_text())
  roofs={name:shape(item['enu']).intersection(self.outer.buffer(-.25)) for name,item in topology['roof_regions'].items()}
  floor2=shape(topology['level2_connected_floor_enu']).intersection(self.outer.buffer(-.25));leafunion=unary_union(list(self.leaves.values()))
  floor3=shape(topology['level3_separate_floor_enu']).intersection(self.outer.buffer(-.25))
  # Three independent recessed glazed ground-level enclosures; no ground infill.
  for name,leaf in self.leaves.items():
   c=leaf.centroid;ground=scale(leaf,xfact=.86,yfact=.86,origin=(c.x,c.y));self.b.plan_prism(ground,0,.30,'light floor',name+'/ground-floor');self.wall_loop(ground,.30,5.15,'low iron glass',name+'/ground-curtain-wall',2.2)
   line=leaf.buffer(-1.15).exterior;n=round(line.length/7.5)
   for i in range(n):
    c0=line.interpolate((i+.3)/n,normalized=True).coords[0];self.b.lathe(c0,[(.0,.39),(5.15,.39)],'white structural',16,name+f'/white-ground-column-{i}')
  # Second floor is three bodies joined only by three short bridges. Third-floor
  # and planted-roof inner boundaries are independent of the coarse source mask.
  self.b.plan_prism(floor2,5.15,5.40,'white structural','level2/three-bodies-and-short-bridges')
  self.b.plan_prism(floor3,10.55,10.80,'white structural','level3/separate-bodies-no-full-envelope-fill')
  for name,leaf in self.leaves.items():
   self.wall_loop(leaf.buffer(-1.35),5.4,10.55,'low iron glass',name+'/level2-curtainwall',2.2)
   for j,piece in enumerate(pieces(roofs[name].buffer(-1.35))):self.wall_loop(piece,10.8,self.zroof,'low iron glass',name+f'/level3-recessed-glass-{j}',2.2)
  bridges={name:shape(q).difference(leafunion) for name,q in topology['level2_bridges'].items()}
  for name,p in bridges.items():
   for j,piece in enumerate(pieces(p)):
    self.b.plan_prism(piece,10.55,10.80,'white structural',name+f'/low-bridge-roof-{j}')
    self.wall_loop(piece,5.4,10.55,'low iron glass',name+f'/low-bridge-glazing-{j}',2.0)
  # Independent continuous external copper veil: source identity is the coarse
  # envelope, not a filled floor or green roof. Built facade photos show a
  # continuous wave even where the short internal bridge is substantially lower.
  def screen_top(x,y):
   d=Point(x,y).distance(leafunion);u=min(1.,d/7.0);u=u*u*(3-2*u)
   return self.zroof(x,y)-2.0*u
  self.fin_loop(self.outer.exterior,5.25,screen_top,.70,'copper fins','continuous-independent-copper-veil')
  # Narrow, separate outer path/coping follows the veil. This is not central
  # roof infill: only a1.25m perimeter strip bridges the external leaf gaps.
  strip=self.outer.difference(self.outer.buffer(-1.25))
  self.roof_surface(strip,'continuous-outer-roof-edge-path',lambda x,y:screen_top(x,y)+.03,'roof path',.18)
  edge=self.outer.exterior;points=[edge.interpolate(t,normalized=True).coords[0] for t in np.linspace(0,1,220)]
  self.b.tube([[x,y,screen_top(x,y)+.06] for x,y in points],.14,'white coping',8,'continuous-veil-top-coping')
  # Visible steel standoffs at the screen line; longer connecting members are
  # only exposed in the bridge sectors. Exact structural sections are unknown.
  line=self.outer.buffer(-.55).exterior;cnt=round(line.length/4.)
  for i in range(cnt):
   p=np.array(line.interpolate(i/cnt,normalized=True).coords[0]);q=np.array(line.interpolate((i/cnt+1e-4)%1,normalized=True).coords[0]);t=(q-p)/np.linalg.norm(q-p);n=np.array([t[1],-t[0]])
   outward=n if line.is_ccw else -n;mount=p-outward*.40
   for zz in [5.67,10.83]:
    if zz+.22<screen_top(*p):self.b.box([*mount,zz],(.12,1.5,.18),'dark metal',[[*t,0],[*n,0],[0,0,1]],f'external-screen-standoff-{i}-{zz}')
  self.features.append({'kind':'continuous_external_veil_independent_of_floor_cover','screen_top_separate_from_leaf_roof':True,'screen_top_approx_range_m':[13.,18.],'no_continuous_high_glass_shell':True,'perimeter_roof_path_width_m':1.25,'does_not_fill_central_court':True,'support_sections_not_measured':True})
  for name,poly in roofs.items():
   self.roof_surface(poly,name+'/separate-undulating-planted-roof')
   for j,piece in enumerate(pieces(poly)):
    edge=piece.exterior;points=[edge.interpolate(t,normalized=True).coords[0] for t in np.linspace(0,1,max(20,round(edge.length/.9)))]
    self.b.tube([[x,y,self.zroof(x,y)+.02] for x,y in points],.14,'white coping',8,name+f'/roof-coping-{j}')
  for name,(c,r) in self.recesses.items():
   circle=Point(c).buffer(r,resolution=40);deckz=topology['A_B_lower_white_platform_top_m']
   self.wall_loop(orient(circle,sign=-1),deckz,self.zroof,'low iron glass',name+'/round-recess-wall',1.9);self.ring(c,r-.08,deckz,.26,name+'/visible-lower-white-deck','white coping');self.railing(circle.exterior,self.zroof,name+'/round-recess-guard')
   self.features.append({'kind':'round_roof_recess','name':name,'only_roof_cut':True,'lower_white_deck_inferred_m':deckz,'not_ground_through':True})
  c=self.xy([363,290]);ro=54*self.s;ri=47*self.s;z=17.8;self.ring(c,ro,z,.40,'central-high-ring','dark roof walk',ri)
  self.railing(Point(c).buffer(ro,resolution=48).exterior,z,'ring-outer-guard');self.railing(Point(c).buffer(ri,resolution=48).exterior,z,'ring-inner-guard')
  # Narrow descending connections are observed, but exact grading/steps unknown.
  for name,(rc,rr) in self.recesses.items():
   direction=(rc-c)/np.linalg.norm(rc-c);start=c+direction*(ro+.05);end=rc-direction*.8
   self.connector_deck(start,end,z,13.8,1.8,name+'/estimated-descending-white-connector')
  dc=self.xy([388,293]);dr=23*self.s;dz=15.7;self.ring(dc,dr,dz,.42,'central-solid-disc','white coping');self.railing(Point(dc).buffer(dr,resolution=40).exterior,dz,'central-disc-guard')
  self.features.append({'kind':'independent_layer_topology','source':'roof-topology-v3a/roof-regions.json','source_mask_is_not_roof':True,'leaf_roof_count':3,'low_level2_bridge_count':3,'low_bridge_roof_m':10.8,'retained_A_green_tongue':True,'central_white_disc_has_exposed_underside':True,'all_new_inner_curves_and_elevations_estimated':True})
  # Large glazing drum has a real solid cap. Its top21m is a hypothesis.
  pc=self.xy([388,207]);pr=28*self.s;pz=self.zroof(*pc);pavilion=Point(pc).buffer(pr,resolution=48);self.wall_loop(pavilion,pz,20.78,'low iron glass','A-rooftop-pavilion',1.5);self.fin_loop(pavilion.exterior,pz,20.83,.75,'bronze roof screen','A-pavilion-fins');self.ring(pc,pr+.08,21.,.22,'A-pavilion-solid-roof','white coping')
  for name,p,r in [('B',[302,362],15),('C',[445,351],13)]:
   c0=self.xy(p);radius=r*self.s;zz=self.zroof(*c0)+.05;circle=Point(c0).buffer(radius,resolution=36);self.fin_loop(circle.exterior,zz,zz+1.8,.55,'bronze roof screen',name+'/small-roof-screen');self.ring(c0,radius+.05,zz,.12,name+'/screen-base','roof path',radius-.35)
  self.features.append({'kind':'stage_circular_types','closed_glazed_pavilion':1,'roof_recesses_with_lower_decks':2,'open_brown_roof_screens':2,'solid_central_suspended_disc':1,'true_high_annular_walkway':1,'all_dimensions_estimated':True})
  self.features.append({'kind':'visible_screen_cavity','nominal_front_glass_setback_m':1.35,'standoff_beams':True,'not_flat_brown_wall':True})
  # Consistent closed-part orientation; curved glass is an intentionally thin skin.
  for p in self.b.parts:
   v=np.array(p['vertices']);t=np.array(p['triangles']);vol=np.einsum('ij,ij->i',v[t[:,0]],np.cross(v[t[:,1]],v[t[:,2]])).sum()/6
   if vol<0:p['triangles']=[tuple(reversed(q)) for q in p['triangles']]
  return self
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();assert not a.out.exists();m=Museum().build();a.out.mkdir(parents=True)
 meta={'id':'fengxian-museum','name':'奉贤博物馆2019新馆','anchor':m.g['anchor'],'ground_base_m':0,'rotation_y':0,'stage':'SPATIAL DRAFT; not final detail or measured as-built','height_estimate_m':21,'height_is_trial_interpretation':True,'source_geometry_sha256':sha(HERE/'geometry-input.json'),'registration_sha256':sha(HERE.parent/'registration-v1/registration.json'),'topology_sha256':sha(HERE.parent/'roof-topology-v3a/roof-regions.json'),'textures_embedded':False,'copyright':'Authored draft geometry MIT; source footprint ©OpenStreetMap contributors / Overture ODbL-1.0; reference photographs not embedded; no private image pixels'}
 r=m.b.save(a.out/'fengxian-museum-draft.glb',meta);(a.out/'metadata.json').write_text(json.dumps({**meta,'raw':{k:r[k] for k in ['file','bytes','sha256','triangles','parts','bounds_glb']}},ensure_ascii=False,indent=2)+'\n');(a.out/'features.json').write_text(json.dumps(m.features,indent=2)+'\n');print(json.dumps({k:r[k] for k in ['file','bytes','sha256','triangles','parts','bounds_glb']}),flush=True)
if __name__=='__main__':main()
