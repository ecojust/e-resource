#!/usr/bin/env python3
"""Detailed exterior, with authored LOD and explicit source uncertainty."""
from pathlib import Path
import argparse,json,math,hashlib
import numpy as np
from shapely.geometry import Point,Polygon,shape
from shapely.ops import nearest_points
from build_envelope import Museum,Builder,Facade,HERE,sha

class DetailedBuilder(Builder):
 def __init__(self,palette,lod):super().__init__(palette);self.lod=lod
 def lathe(self,center,profile,material='carved pale stone',segments=32,label='column'):
  if 'white-ground-column' in label:segments=16 if self.lod else 28
  return super().lathe(center,profile,material,segments,label)

class DetailedMuseum(Museum):
 def __init__(self,lod=False):
  super().__init__();self.lod=lod;self.b=DetailedBuilder(self.b.palette,lod)
  self.b.palette.update({'copper muted':{'color':[.30,.115,.058],'roughness':.49,'metallic':.62},'copper warm':{'color':[.39,.165,.080],'roughness':.53,'metallic':.57},'steel framing':{'color':[.42,.45,.43],'roughness':.53,'metallic':.42},'door glass':{'color':[.17,.27,.30],'roughness':.18,'metallic':.02,'alpha':.30},'door stainless':{'color':[.52,.55,.54],'roughness':.3,'metallic':.8}})
  self.controls=json.loads((HERE/'facade-detail-controls.json').read_text());line=self.outer.exterior
  for h in self.controls['cutouts']:h['arc_m']=line.project(Point(self.xy(h['plan_px'])))
  self.entries={'A':self.xy([422,212]),'B':self.xy([281,391]),'C':self.xy([471,354])}
 def beam(self,a,b,w,h,mat,label):
  a=np.array(a,float);b=np.array(b,float);u=b-a;L=np.linalg.norm(u)
  if L<.001:return
  u/=L;v=np.cross([0,0,1],u)
  if np.linalg.norm(v)<.01:v=np.array([1.,0,0])
  v/=np.linalg.norm(v);n=np.cross(u,v);self.b.box((a+b)/2,(L,w,h),mat,[u,v,n],label)
 def fin_loop(self,line,bottom,top,pitch,material,label):
  principal=label=='continuous-independent-copper-veil';fullpitch=.25 if principal else .31;pitch=fullpitch*2 if self.lod else fullpitch;coverage_ratio=2. if self.lod else 1.;finwidth=.040*coverage_ratio;findepth=.24*coverage_ratio
  count=max(12,round(line.length/pitch));cuts=0
  for i in range(count):
   arc=i/count*line.length;p=np.array(line.interpolate(arc).coords[0]);q=np.array(line.interpolate((arc+.025)%line.length).coords[0]);t=(q-p)/np.linalg.norm(q-p);n=np.array([t[1],-t[0]]);z=top(*p) if callable(top) else top;intervals=[(bottom,z)]
   if principal:
    for h in self.controls['cutouts']:
     d=abs(arc-h['arc_m']);d=min(d,line.length-d)
     if d<=h['width_m']/2:
      new=[]
      for low,high in intervals:
       if h['top_m']<=low or h['bottom_m']>=high:new.append((low,high))
       else:
        if h['bottom_m']>low:new.append((low,h['bottom_m']))
        if h['top_m']<high:new.append((h['top_m'],high))
        cuts+=1
      intervals=new
   mat=material if not principal else ['copper fins','copper fins','copper muted','copper fins','copper warm'][i%5]
   outward=n if getattr(line,'is_ccw',True) else -n;finpoint=p-outward*(findepth-.24)/2
   for j,(lo,hi) in enumerate(intervals):self.b.box([*finpoint,(lo+hi)/2],(finwidth,findepth,hi-lo),mat,[[*t,0],[*n,0],[0,0,1]],label+f'/fin-{i}-{j}')
  if principal:
   for h in self.controls['cutouts']:
    p=np.array(line.interpolate(h['arc_m']).coords[0]);q=np.array(line.interpolate((h['arc_m']+.02)%line.length).coords[0]);t=(q-p)/np.linalg.norm(q-p);n=np.array([t[1],-t[0]])
    f=Facade(self.b,p-t*h['width_m']/2,p+t*h['width_m']/2,h['id'])
    for z in [h['bottom_m'],h['top_m']]:f.box(0,z,h['width_m']+.10,.055,.08,-.12,'dark metal','real-cutout-cross-frame')
    for u in [-h['width_m']/2,h['width_m']/2]:f.box(u,(h['bottom_m']+h['top_m'])/2,.055,h['top_m']-h['bottom_m'],.08,-.12,'dark metal','real-cutout-jamb')
  self.features.append({'kind':'authored_separated_louvers','label':label,'count':count,'pitch_m':line.length/count,'width_m':finwidth,'depth_m':findepth,'removed_intervals':cuts,'lod':self.lod,'lod_coverage_compensation':'width and depth scale with doubled pitch; extra depth extends inward, preserving external silhouette' if self.lod else None})
 def wall_loop(self,poly,bottom,top,material,label,pitch=3.0):
  pts=list(poly.exterior.coords);line=poly.exterior;ground='/ground-curtain-wall' in label;name=label.split('/')[0];entryarc=line.project(Point(self.entries[name])) if ground else None;doorwidth=3.2;doorz=2.95
  for i,(a,b) in enumerate(zip(pts,pts[1:])):
   za=top(*a) if callable(top) else top;zb=top(*b) if callable(top) else top;f=Facade(self.b,a,b,label+f'/panel-{i}');low=bottom;isdoor=False
   if ground:
    arc=line.project(Point((np.array(a)+b)/2));delta=abs(arc-entryarc);delta=min(delta,line.length-delta);isdoor=delta<doorwidth/2
    if isdoor:low=doorz+.06
   profile=Polygon([(-f.length/2,low),(f.length/2,low),(f.length/2,zb),(-f.length/2,za)])
   f.prism(profile,-.055,0,material,'true-curved-glass-with-door-opening' if isdoor else 'true-curved-glass')
   if isdoor:
    pane=Polygon([(-f.length/2,bottom+.025),(f.length/2,bottom+.025),(f.length/2,doorz),(-f.length/2,doorz)])
    f.prism(pane,-.040,-.012,'door glass','closed-door-glass-leaf')
   levels=[bottom+.07]
   if ground:levels+=[doorz+.03,5.09]
   elif bottom<6:levels +=[8.05,10.49]
   elif bottom<12:levels +=[13.45]
   else:levels +=[(bottom+min(za,zb))/2]
   for z in levels:
    if bottom+.03<z<min(za,zb)-.02:f.box(0,z,f.length,.06,.085,-.025,'dark metal','horizontal-curtain-transom')
  if pitch:
   pitch=2.4 if self.lod else 1.5;count=max(3,round(line.length/pitch))
   for j in range(count):
    arc=j/count*line.length;p=np.array(line.interpolate(arc).coords[0]);q=np.array(line.interpolate((arc+.025)%line.length).coords[0]);t=(q-p)/np.linalg.norm(q-p);n=np.array([t[1],-t[0]]);h=(top(*p) if callable(top) else top)-bottom
    if ground:
     d=abs(arc-entryarc);d=min(d,line.length-d)
     if d<doorwidth/2:continue
    self.b.box([*p,bottom+h/2],(.055,.10,h),'dark metal',[[*t,0],[*n,0],[0,0,1]],label+f'/mullion-{j}')
  if ground:
   for d in [-doorwidth/2,0,doorwidth/2]:
    p=np.array(line.interpolate((entryarc+d)%line.length).coords[0]);q=np.array(line.interpolate((entryarc+d+.025)%line.length).coords[0]);t=(q-p)/np.linalg.norm(q-p);n=np.array([t[1],-t[0]])
    self.b.box([*p,(bottom+doorz)/2],(.075,.14,doorz-bottom),'door stainless',[[*t,0],[*n,0],[0,0,1]],label+'/entrance-jamb')
   if not self.lod:
    for d in [-.35,.35]:
     p=np.array(line.interpolate((entryarc+d)%line.length).coords[0]);q=np.array(line.interpolate((entryarc+d+.025)%line.length).coords[0]);t=(q-p)/np.linalg.norm(q-p);n=np.array([t[1],-t[0]]);p+=n*.18
     self.b.tube([[*p,1.03],[*p,1.53]],.022,'door stainless',8,label+'/door-pull')
   self.features.append({'kind':'framed_recessed_glass_entrance','leaf':name,'closed_glass_separate_from_cut_wall':True,'estimated_location':True,'door_operation_not_simulated':True})
 def railing(self,line,z,label):
  count=max(6,round(line.length/(2.4 if self.lod else 1.25)));points=[np.array(line.interpolate(j/count,normalized=True).coords[0]) for j in range(count+1)]
  for i,(a,b) in enumerate(zip(points,points[1:])):
   za=z(*a) if callable(z) else z;zb=z(*b) if callable(z) else z;f=Facade(self.b,a,b,label+f'/{i}');f.prism(Polygon([(-f.length/2,za+.10),(f.length/2,zb+.10),(f.length/2,zb+1.10),(-f.length/2,za+1.10)]),-.008,.008,'glass guard','separate-glass-panel')
   self.beam([*a,za+1.12],[*b,zb+1.12],.045,.045,'dark metal',label+'/cap-rail');self.b.tube([[*a,za],[*a,za+1.12]],.023,'dark metal',6 if self.lod else 8,label+'/fine-post')
   self.beam([*a,za+.05],[*b,zb+.05],.045,.08,'dark metal',label+'/shoe-channel')
 def connector_deck(self,a,b,za,zb,width,label):
  super().connector_deck(a,b,za,zb,width,label);a=np.array(a);b=np.array(b);u=(b-a)/np.linalg.norm(b-a);n=np.array([-u[1],u[0]])
  count=max(1,round(abs(za-zb)/.17));L=np.linalg.norm(b-a)
  if not self.lod:
   for i in range(count):
    t=(i+.5)/count;p=a+(b-a)*t;z=za+(zb-za)*t+.045
    self.b.box([*p,z],(L/count-.012,width,.045),'white coping',[[*u,0],[*n,0],[0,0,1]],label+f'/visible-step-{i}')
  count=max(2,round(L/(2.4 if self.lod else 1.25)))
  for side in [-1,1]:
   for i in range(count):
    t=i/count;tt=(i+1)/count;p=a+(b-a)*t+n*width/2*side;q=a+(b-a)*tt+n*width/2*side;zp=za+(zb-za)*t;zq=za+(zb-za)*tt;f=Facade(self.b,p,q,label+'/connector-guard')
    f.prism(Polygon([(-f.length/2,zp+.12),(f.length/2,zq+.12),(f.length/2,zq+1.03),(-f.length/2,zp+1.03)]),-.008,.008,'glass guard','descending-panel');self.b.tube([[*p,zp],[*p,zp+1.1]],.023,'dark metal',6,label+'/connector-post')
 def add_structure(self):
  from shapely.ops import unary_union
  union=unary_union(list(self.leaves.values()));inner=union.buffer(-1.2);line=self.outer.exterior
  def top(x,y):
   d=Point(x,y).distance(union);u=min(1.,d/7.);u=u*u*(3-2*u);return self.zroof(x,y)-2*u
  count=round(line.length/(6 if self.lod else 3.2))
  for i in range(count):
   p=np.array(line.interpolate((i+.35)/count,normalized=True).coords[0]);q=np.array(nearest_points(inner,Point(p))[0].coords[0]);direction=q-p;direction/=np.linalg.norm(direction);p=p+direction*.24;span=np.linalg.norm(q-p)
   if span<.3:continue
   # Actual connected members reach the host frame; no floating short stubs.
   z1=top(*p)-.30;z2=min(self.zroof(*q)-.30,z1+.75);self.beam([*p,z1],[*q,z2],.16,.24,'steel framing',f'outer-path-connected-beam-{i}')
   for z in [5.35,10.65]:self.beam([*p,z],[*q,z],.16,.26,'steel framing',f'outer-screen-floor-tie-{i}-{z}')
   if span>3.0:self.beam([*p,10.65],[*q,13.0],.12,.18,'steel framing',f'outer-screen-inclined-brace-{i}')
  self.railing(line,lambda x,y:top(x,y)+.03,'continuous-outer-path-guard')
  self.features.append({'kind':'continuous_veil_and_roof_path_connected_to_host_frames','connections':count,'member_sections_approximate':True,'no_full_court_infill':True})
 def build(self):
  super().build();self.add_structure();top=json.loads((HERE.parent/'roof-topology-v3a/roof-regions.json').read_text());roofs={n:shape(v['enu']).intersection(self.outer.buffer(-.25)) for n,v in top['roof_regions'].items()}
  from roof_details import add_roof_details
  add_roof_details(self,roofs,lod=self.lod)
  for p in self.b.parts:
   v=np.array(p['vertices']);t=np.array(p['triangles']);vol=np.einsum('ij,ij->i',v[t[:,0]],np.cross(v[t[:,1]],v[t[:,2]])).sum()/6
   if vol<0:p['triangles']=[tuple(reversed(q)) for q in p['triangles']]
  return self

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args();assert not a.out.exists();m=DetailedMuseum(a.lod).build();a.out.mkdir(parents=True)
 meta={'id':'fengxian-museum','name':'奉贤博物馆2019新馆','anchor':m.g['anchor'],'ground_base_m':0,'rotation_y':0,'stage':'Authored exterior LOD' if a.lod else 'Detailed exterior awaiting independent review','source_geometry_sha256':sha(HERE/'geometry-input.json'),'registration_sha256':sha(HERE.parent/'registration-v1/registration.json'),'topology_sha256':sha(HERE.parent/'roof-topology-v3a/roof-regions.json'),'textures_embedded':False,'height_nominal_m':21,'uncertainty':['The source footprint is an approximate ownership mask, not a surveyed wall outline; plan registration boundary RMS2.09m, max9.57m.','2018 construction table18m and2020 built-project15–21m have different or unspecified boundaries. Rounded model levels and roof shapes are documentary/photo-derived estimates.','Inner roof curves, circular platforms, facade interruptions, entrance positions and roof equipment dimensions are approximate; hidden interior exhibitions are not recreated.','PBR surfaces and planted areas are authored approximations, not photographic scans.','Geometry paths and stairs do not assert browser collision or accessible roof navigation.'],'copyright':'Authored geometry and code by agent, MIT; source footprint ©OpenStreetMap contributors / Overture Maps Foundation, ODbL-1.0; building reference Stevenliuyi, CC-BY-SA-4.0 (not embedded); private reference image pixels not embedded or published.'}
 r=m.b.save(a.out/'fengxian-museum.glb',meta);(a.out/'metadata.json').write_text(json.dumps({**meta,'raw':{k:r[k] for k in ['file','bytes','sha256','triangles','parts','bounds_glb']}},ensure_ascii=False,indent=2)+'\n');(a.out/'features.json').write_text(json.dumps(m.features,indent=2)+'\n');print(json.dumps({k:r[k] for k in ['file','bytes','sha256','triangles','parts','bounds_glb']}),flush=True)
if __name__=='__main__':main()
