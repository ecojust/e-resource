"""Shanghai Race Club east body and principal tower exterior candidate. MIT.
All unmeasured dimensions/grid/clock detail are design estimates, not a survey.
"""
import argparse,json,math
from pathlib import Path
import numpy as np
from shapely.geometry import box,Point
from shapely.ops import unary_union
from common.photo_architecture import Builder,facade_ring,opening
ID='huangpu-shanghai-race-club-east-building'
PALETTE={'brick':{'color':[.36,.21,.15],'roughness':.91},'stone':{'color':[.67,.62,.51],'roughness':.85},'pavilion stone':{'color':[.68,.63,.53],'roughness':.85},'carved pale stone':{'color':[.72,.68,.58],'roughness':.82},'tile':{'color':[.35,.105,.065],'roughness':.91},'tile edge':{'color':[.41,.14,.09],'roughness':.9},'floor':{'color':[.41,.40,.35],'roughness':.93},'frame':{'color':[.18,.19,.17],'roughness':.6},'glass':{'color':[.115,.16,.17],'roughness':.3,'metallic':.16},'dial':{'color':[.87,.84,.71],'roughness':.75},'clock iron':{'color':[.035,.04,.036],'roughness':.64,'metallic':.3}}
P={'body_length':104,'body_depth':20,'levels':[0,5,11,18,23],'tower_center':[-45,-6],'tower_width':10.4,'tower_top':53,'gallery_intervals':[[-33,-7],[7,43]],'gallery_depth':4.6,'gallery_front_y':-11.6,'gallery_rear_y':-7,'clock_center_height':41,'clock_radius':3.3}
def wall(f,prev,nxt,lo,hi,holes,mat,th=.4):
 t=f.t[:2];n=f.n[:2]
 def inner(pt,on):return np.linalg.solve(np.array([n,on]),np.array([n@pt-th,on@pt-th]))
 l=(inner(f.a[:2],prev.n[:2])-f.a[:2])@t/th;r=(inner(f.b[:2],nxt.n[:2])-f.b[:2])@t/th
 def mapper(u,z,d):return f.point(u-d*(l+(u+f.length/2)/f.length*(r-l)),z,d)
 shape=box(-f.length/2,lo,f.length/2,hi)
 if holes:shape=shape.difference(unary_union(holes))
 f.builder.prism(shape,-th,0,mapper,mat,f.label+'/closed-mitered-wall')
def window(f,shape,lod,label,cols=2,rows=2):
 if lod:
  f.prism(shape,-.30,-.27,'glass',label+'-glass')
  x0,z0,x1,z1=shape.bounds;f.box((x0+x1)/2,z0-.07,x1-x0+.30,.14,.60,.10,'carved pale stone',label+'-sill')
 else:f.window(shape,cols,rows,'frame',False,'glass',label)
def railing(b,x0,x1,y,z,lod,label):
 b.box(((x0+x1)/2,y,z+.1),(x1-x0,.32,.2),'stone',label=label+'-plinth')
 b.box(((x0+x1)/2,y,z+1.0),(x1-x0,.34,.16),'stone',label=label+'-rail')
 for x in np.arange(x0+.2,x1-.1,.8 if lod else .45):
  b.lathe((float(x),y),[(z+.2,.07),(z+.36,.11),(z+.72,.065),(z+.92,.075)],'stone',8 if lod else 12,label+'-baluster')
def hiproof(b,x0,x1,y0,y1,eave,ridge,lod,label):
 h=(y1-y0)/2;ym=(y0+y1)/2;inset=min(h,(x1-x0)/2-.12)
 v=[(x0,y0,eave),(x1,y0,eave),(x1,y1,eave),(x0,y1,eave),(x0+inset,ym,ridge),(x1-inset,ym,ridge)]
 b.add(v,[(0,3,2,1),(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)],'tile',label+'-closed-hip')
 def height(x,y):return eave+(ridge-eave)*min(1,(x-x0)/inset,(x1-x)/inset,(y-y0)/h,(y1-y)/h)
 for x in np.arange(x0+.12,x1-.1,1.1 if lod else .43):
  ys=np.linspace(y0+.08,y1-.08,9 if lod else 17);b.tube([(float(x),float(y),height(x,y)+.035) for y in ys],.035,'tile edge',5 if lod else 6,label+'-estimated-tile-row')
 b.tube([(x0+inset,ym,ridge+.035),(x1-inset,ym,ridge+.035)],.055,'tile edge',8,label+'-ridge')
def build(lod=False):
 b=Builder(PALETTE);count=0
 body=box(-52,-7,52,13);fs=facade_ring(b,body,'body')
 for floor,(lo,hi) in enumerate(zip(P['levels'],P['levels'][1:])):
  b.plan_prism(body.buffer(-.42,join_style=2),lo,lo+.18,'floor','body-floor')
  b.plan_prism(body,hi-.18,hi,'floor','body-ceiling')
  for j,f in enumerate(fs):
   n=23 if f.length>90 else 4;pitch=(f.length-2)/n;holes=[]
   for k in range(n):
    u=-f.length/2+1+(k+.5)*pitch;sh=opening(u,lo+1.0,min(2.2,pitch-.7),min(3.2,hi-lo-1.5));holes.append(sh);window(f,sh,lod,'estimated-body-window');count+=1
   wall(f,fs[j-1],fs[(j+1)%len(fs)],lo,hi,holes,'brick')
   f.beam(hi-.15,.3,.20,'stone',label='photo-guided-storey-band')
 # Two deep, genuinely open gallery stretches. Back walls stay atY-7.
 for g,(x0,x1) in enumerate(P['gallery_intervals']):
  bay_count=6 if g==0 else 8;xs=np.linspace(x0+.25,x1-.25,bay_count+1)
  for z in [0,5,18,23]:b.box(((x0+x1)/2,-9.4,z+.09),(x1-x0,4.8,.18),'floor',label='open-gallery-slab')
  for lo,hi in [(5,18),(18,23)]:
   b.box(((x0+x1)/2,-11.6,hi-.25),(x1-x0,.6,.7),'stone',label='open-gallery-front-beam')
   for x in xs:
    radius=.43 if lo==5 else .19
    b.lathe((float(x),-11.4),[(lo+.18,radius*1.2),(lo+.42,radius*1.3),(lo+.65,radius),(hi-.75,radius),(hi-.60,radius*1.25),(hi-.40,radius*1.25)],'stone' if lo==5 else 'brick',12 if lod else 20,'tall-lower-gallery-column' if lo==5 else 'slender-upper-gallery-column')
   railing(b,x0+.1,x1-.1,-11.65,lo+.18,lod,'gallery')
  b.box(((x0+x1)/2,-11.65,23.65),(x1-x0,.38,.94),'stone',label='solid-roof-terrace-parapet')
  b.box(((x0+x1)/2,-11.65,24.16),(x1-x0,.5,.12),'carved pale stone',label='terrace-parapet-cap')
 # Projecting pavilions divide the galleries; corners have independent mitred walls.
 for cx,w in [(-36,6),(0,12),(48,8)]:
  plan=box(cx-w/2,-13.0,cx+w/2,-6.8);es=facade_ring(b,plan,f'pavilion-{cx}')
  for lo,hi in [(0,5),(5,11),(11,17),(17,25)]:
   for j,f in enumerate(es):
    holes=[];n=max(1,int((f.length-1.2)/2.8))
    for k in range(n):
     u=-f.length/2+.6+(k+.5)*(f.length-1.2)/n;sh=opening(u,lo+1.0,min(1.6,(f.length-1.2)/n-.4),min(3.6,hi-lo-1.5),arch=.5 if lo==17 else 0);holes.append(sh);window(f,sh,lod,'pavilion-window');count+=1
    wall(f,es[j-1],es[(j+1)%len(es)],lo,hi,holes,'pavilion stone')
    f.beam(hi-.15,.3,.22,'carved pale stone',label='pavilion-band')
   b.plan_prism(plan.buffer(-.42,join_style=2),hi-.17,hi,'floor','pavilion-floor')
  hiproof(b,cx-w/2-.45,cx+w/2+.45,-13.45,-6.4,25,28,lod,'pavilion-roof')
 hiproof(b,-33,51,3.3,13.5,23.4,27.4,lod,'long-rear-roof')
 # Principal square tower, not duplicated at the far end.
 tx,ty=P['tower_center'];tw=P['tower_width'];tp=box(tx-tw/2,ty-tw/2,tx+tw/2,ty+tw/2);es=facade_ring(b,tp,'principal-tower');clock_faces=[]
 for j,f in enumerate(es):
  holes=[]
  for z in [2,7,13,19]:
   for u in [-2.0,2.0]:
    sh=opening(u,z,1.25,3.5);holes.append(sh);window(f,sh,lod,'tower-slit');count+=1
  for u in [-2.0,2.0]:
   sh=opening(u,24.5,1.25,12,arch=.625);holes.append(sh);window(f,sh,lod,'tower-long-recess',1,3);count+=1
  clock_visible=f.n[1]<-.5 or f.n[0]<-.5
  if clock_visible:holes.append(Point(0,41).buffer(3.3,quad_segs=16 if lod else 32))
  wall(f,es[j-1],es[(j+1)%len(es)],0,45.2,holes,'stone',.5)
  for u in [-4.7,-3.4,3.4,4.7]:f.box(u,22,.4,43.8,.35,.10,'carved pale stone','tower-vertical-frame')
  for z in [5,23,45.2]:f.beam(z,.35,.3,'carved pale stone',label='tower-cornice')
  if clock_visible:
   circle=Point(0,41).buffer(3.3,quad_segs=16 if lod else 48);rim=Point(0,41).buffer(3.7,quad_segs=16 if lod else 48).difference(circle)
   f.prism(circle,-.03,.06,'dial','clock-face');f.prism(rim,-.10,.28,'carved pale stone','clock-stone-ring')
   arch=Point(0,41).buffer(4.2,quad_segs=16 if lod else 48).intersection(box(-4.2,41,4.2,45.3)).difference(Point(0,41).buffer(3.75,quad_segs=16 if lod else 48))
   f.prism(arch,.15,.48,'carved pale stone','clock-arched-crown')
   for u in [-3.975,3.975]:f.box(u,40,.45,2,.5,.35,'carved pale stone','clock-arch-shoulder')
   for k in range(12):
    ang=k*math.tau/12;f.line((2.75*math.sin(ang),41+2.75*math.cos(ang),.14),(3.06*math.sin(ang),41+3.06*math.cos(ang),.14),.055,'clock iron',6,'estimated-clock-tick')
   # Display-only10:10, not a historic photographed time or working mechanism.
   for ang,length in [(-math.pi/3,1.8),(math.pi/3,2.55)]:f.line((0,41,.19),(length*math.sin(ang),41+length*math.cos(ang),.19),.09,'clock iron',8,'illustrative-clock-hand')
   f.prism(Point(0,41).buffer(.19,quad_segs=12),.15,.25,'clock iron','clock-hub');clock_faces.append(f.n.tolist())
 # Open upper lantern with eight rectangular piers, terrace rail and tiled cap.
 b.plan_prism(tp.buffer(.4,join_style=2),45.25,45.6,'floor','lantern-base')
 for dx,dy in [(-4.3,-4.3),(0,-4.3),(4.3,-4.3),(4.3,0),(4.3,4.3),(0,4.3),(-4.3,4.3),(-4.3,0)]:
  b.box((tx+dx,ty+dy,47.5),(.6,.6,3.8),'stone',label='open-lantern-pier')
 for y in [ty-4.7,ty+4.7]:railing(b,tx-4.7,tx+4.7,y,45.6,lod,'lantern')
 for x in [tx-4.7,tx+4.7]:
  b.box((x,ty,46.6),(.3,9.4,.18),'stone',label='lantern-side-rail')
 hiproof(b,tx-6,tx+6,ty-6,ty+6,49.4,52.8,lod,'tower-cap')
 b.box((tx,ty,52.95),(.18,.18,.10),'clock iron',label='estimated-top-finial')
 for part in b.parts:
  v=np.array(part['vertices']);t=np.array(part['triangles']);vol=np.einsum('ij,ij->i',v[t[:,0]],np.cross(v[t[:,1]],v[t[:,2]])).sum()/6
  assert abs(vol)>1e-9,part['label']
  if vol<0:part['triangles']=[(int(a),int(c),int(b)) for a,b,c in t]
 meta={'id':ID,'status':'standalone-exterior-candidate-not-geographically-registered','tower_height_secondary_reference_m':53,'all_plan_dimensions_estimated':True,'height_endpoints_verified':False,'photo_period':'2013-12-22','east_body_only':True,'west_building_modeled':False,'secondary_clock_tower_modeled':False,'map_replacement':False,'photos_embedded':False,'clock_dials_modeled':2,'clock_time_illustrative':'10:10','copyright':'Original code and geometry MIT; reference photographs not embedded'}
 return b,meta,{'parameters':P,'estimated_window_openings':count,'author_parts':len(b.parts),'clock_face_normals':clock_faces,'gallery_bays_design_estimate':[6,8],'gallery_height_intervals_estimated':[[5,18],[18,23]],'lantern_piers_design_estimate':8,'clock_face_count':2,'unseen_faces_and_roof_junctions_estimated':True}
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args();b,m,f=build(a.lod);a.out.mkdir(parents=True,exist_ok=True);stem=ID+('-lod' if a.lod else '-raw');r=b.save(a.out/(stem+'.glb'),m);(a.out/(stem+'-features.json')).write_text(json.dumps(f,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='part_summary'}))
if __name__=='__main__':main()
