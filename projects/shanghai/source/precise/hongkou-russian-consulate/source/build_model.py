"""Public historical exterior candidate, no interior or inferred site facilities. MIT.
Body dimensions and tower geometry are explicitly unmeasured design estimates.
"""
import argparse,json,math
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box
from common.photo_architecture import Builder,Facade,facade_ring,opening
ID='hongkou-russian-consulate'
PALETTE={'pale plaster':{'color':[.76,.75,.69],'roughness':.87},'carved pale stone':{'color':[.79,.78,.72],'roughness':.80},'red roof':{'color':[.41,.105,.062],'roughness':.87},'green copper':{'color':[.12,.24,.19],'roughness':.75,'metallic':.3},'window frame':{'color':[.27,.25,.20],'roughness':.65},'glass':{'color':[.16,.22,.21],'roughness':.3,'metallic':.12}}
P={'body_width':44,'body_depth':24,'body_eave':12.6,'roof_break':16.8,'roof_ridge':18.6,'tower_top':30.8,'floor_heights':[0,4.2,8.4,12.6],'balcony_width':10,'balcony_projection':2}
def balustrade(b,y,z,x0,x1,lod,label):
 b.box(((x0+x1)/2,y,z+.12),(x1-x0,.32,.24),'carved pale stone',label=label+'-plinth')
 b.box(((x0+x1)/2,y,z+1.03),(x1-x0,.34,.18),'carved pale stone',label=label+'-handrail')
 for x in np.arange(x0+.22,x1-.1,.75 if lod else .46):
  b.lathe((float(x),y),[(z+.24,.075),(z+.4,.12),(z+.7,.065),(z+.94,.075)],'carved pale stone',8 if lod else 12,label+'-estimated-baluster')
def build(lod=False):
 b=Builder(PALETTE);plan=box(-22,-12,22,12);windows=0
 for edge in facade_ring(b,plan,'estimated-body'):
  n=12 if edge.length>40 else 6;pitch=(edge.length-2)/n
  for floor in range(3):
   lo,hi=P['floor_heights'][floor:floor+2];holes=[]
   for i in range(n):
    u=-edge.length/2+1+(i+.5)*pitch;sh=opening(u,lo+.8,2.1,2.7,arch=1.05 if floor==1 else 0,segments=12 if lod else 24)
    holes.append(sh);windows+=1
    if lod:edge.prism(sh,-.32,-.29,'glass','estimated-window-glass')
    else:edge.window(sh,columns=2,rows=2,frame='window frame',trim=True,glass='glass',label='estimated-window')
   edge.wall(lo,hi,holes,thickness=.45,material='pale plaster',outline=box(-edge.length/2+.45,lo,edge.length/2-.45,hi))
   edge.beam(hi-.08,.25,.22,'carved pale stone',label='photo-guided-stringcourse')
  for i in range(n+1):
   u=-edge.length/2+1+i*pitch
   edge.box(u,6.3,.24,12.35,.20,.07,'carved pale stone','estimated-pilaster')
  edge.beam(12.48,.38,.45,'carved pale stone',label='photo-guided-cornice')
 # Closed corner piers replace overlapping butt-ended facade caps.
 for x in [-21.775,21.775]:
  for y in [-11.775,11.775]:b.box((x,y,6.3),(.45,.45,12.6),'pale plaster',label='estimated-joined-corner-pier')
 for z in [.0,4.2,8.4,12.6]:b.plan_prism(plan.buffer(-.2,join_style=2),z,z+.14,'pale plaster','estimated-floor-or-roof-slab')
 # Front and rear steep roof slopes. Openings cut into the actual skin.
 dormer_positions=[-17,-11,-5,1,7,13,19]
 for side in [-1,1]:
  holes=[opening(x,13.6,1.65,2.35,.8,12 if lod else 24) for x in dormer_positions]
  # x cross height points outward: front uses x forward; rear reverses x.
  mapper=(lambda u,z,d:(u,-12+(z-12.6)*3/4.2-d,z)) if side==-1 else (lambda u,z,d:(-u,12-(z-12.6)*3/4.2+d,z))
  surface=box(-22.3,12.6,22.3,16.8)
  from shapely.ops import unary_union
  b.prism(surface.difference(unary_union(holes)),-.12,0,mapper,'red roof','estimated-open-mansard-slope')
  for x,sh in zip(dormer_positions,holes):
   # Local front/back composition only; all numbers and hidden dormer geometry estimated.
   f=Facade(b,(x-1.4,side*11.6),(x+1.4,side*11.6),'estimated-dormer') if side==-1 else Facade(b,(-x+1.4,side*11.6),(-x-1.4,side*11.6),'estimated-dormer')
   local=opening(0,13.6,1.65,2.35,.8,12 if lod else 24)
   f.prism(local.buffer(.18,join_style=2).difference(local),-2.5,.06,'red roof','arched-dormer-surround')
   if lod:f.prism(local,-.23,-.20,'glass','dormer-glass')
   else:f.window(local,columns=2,rows=2,frame='window frame',trim=False,glass='glass',label='photo-guided-arched-dormer')
   windows+=1
 # Closed shallow upper roof above the steep window-bearing face.
 profile=Polygon([(-9.3,16.8),(0,18.6),(9.3,16.8),(9.3,16.64),(0,18.44),(-9.3,16.64)])
 b.prism(profile,-22.3,22.3,lambda y,z,x:(x,y,z),'red roof','estimated-upper-roof-shell')
 for x in [-22,22]:
  # End slopes are closed triangles, not measured historical gable sections.
  b.prism(Polygon([(-12,12.6),(12,12.6),(9.3,16.8),(0,18.6),(-9.3,16.8)]),x-.12,x+.12,lambda y,z,x:(x,y,z),'red roof','estimated-roof-end')
 # Visible balcony/bay arrangement refers to the photographed side, not assigned a compass bearing.
 for x in [-9]:
  for z in [4.2,8.4,12.6]:
   b.box((x,-12.9,z+.1),(10,2,.2),'carved pale stone',label='documentary-approx-10x2-balcony-slab')
   balustrade(b,-13.8,z+.2,x-4.8,x+4.8,lod,'estimated-balcony')
  for dx in [-4.65,4.65]:
   b.lathe((x+dx,-13.6),[(8.6,.32),(8.8,.36),(9,.23),(12.25,.23),(12.45,.38)],'carved pale stone',12 if lod else 24,'photo-guided-balcony-column')
 # Curving central gable silhouette as a filled, thin, original polygon.
 gable=[(-5.1,12.8),(-5.1,13.5),(-4.2,14.4),(-3.4,16.2),(-2.3,17.6),(-1.2,18.2),(0,18.5),(1.2,18.2),(2.3,17.6),(3.4,16.2),(4.2,14.4),(5.1,13.5),(5.1,12.8)]
 f=Facade(b,(-14.2,-12.1),(-3.8,-12.1),'photo-guided-curved-gable');shape=Polygon(gable)
 sh=opening(0,14.0,2.4,2.5)
 f.prism(shape.difference(sh),-.25,0,'pale plaster','estimated-curved-gable-wall');f.window(sh,2,2,'window frame',True,'glass','gable-window');windows+=1
 if not lod:
  points=[f.point(u,z,.06) for u,z in gable[1:-1]];b.tube(points,.11,'carved pale stone',8,'photo-guided-gable-outline')
 # Photo tower is kept distinct from the unverified garden pavilion.
 tx,ty=-13,4
 b.box((tx,ty,20.7),(6.3,6.3,8.4),'pale plaster',label='estimated-tower-shaft')
 for z in [24.6,25.0]:b.box((tx,ty,z),(7,7,.22),'carved pale stone',label='estimated-tower-cornice')
 for angle in np.linspace(0,2*math.pi,8,endpoint=False):
  x,y=tx+2.35*math.cos(angle),ty+2.35*math.sin(angle)
  b.lathe((x,y),[(25.0,.24),(25.2,.28),(27.5,.22),(27.7,.3)],'carved pale stone',8 if lod else 16,'estimated-lantern-column')
 lantern=Polygon([(tx+2.35*math.cos(a),ty+2.35*math.sin(a)) for a in np.linspace(0,2*math.pi,8,endpoint=False)])
 for edge in facade_ring(b,lantern,'estimated-octagonal-lantern'):
  sh=opening(0,25.35,.85,1.95,.4,12 if lod else 24);edge.wall(25,27.7,[sh],.22,'pale plaster')
  if lod:edge.prism(sh,-.18,-.15,'glass','estimated-lantern-glass')
  else:edge.window(sh,1,2,'window frame',False,'glass','estimated-lantern-window')
  windows+=1
 b.plan_prism(lantern,27.7,27.9,'carved pale stone','estimated-lantern-cap')
 b.lathe((tx,ty),[(27.85,2.9),(28.3,2.6),(28.8,2.25),(29.25,1.8),(29.7,1.1),(30.1,.45),(30.45,.20),(30.8,.02)],'green copper',12 if lod else 40,'photo-guided-green-curve-cupola')
 # Shaft slit windows are visible-referenced shallow dark insets; rear details estimated.
 for side in [-1,1]:
  for x in [-1.5,0,1.5]:b.box((tx+x,ty+side*3.16,22.6),(.22,.035,1.4),'glass',label='estimated-tower-slit-inset')
 for x in [-18,-3,7,17]:
  b.box((x,0,18.8),(.7,.8,2.5),'pale plaster',label='estimated-roof-chimney');b.box((x,0,20.1),(.9,1,.18),'red roof',label='estimated-chimney-cap')
 for p in b.parts:
  v=np.array(p['vertices']);t=np.array(p['triangles']);vol=np.einsum('ij,ij->i',v[t[:,0]],np.cross(v[t[:,1]],v[t[:,2]])).sum()/6
  assert abs(vol)>1e-9,p['label']
  if vol<0:p['triangles']=[(int(a),int(c),int(b)) for a,b,c in t]
 meta={'id':ID,'status':'standalone-public-historic-exterior-candidate','dimensions_all_estimated':True,'four_storeys_text_reference':True,'model_interpretation':'Three facade levels plus inhabited mansard; not a verified floor-by-floor mapping','height_estimated_m':30.8,'photograph_period':'2010-05','chronology_unresolved':[1916,1917],'garden_pavilion_modeled':False,'photos_embedded':False,'map_replacement':False,'geographic_registration':False,'copyright':'Original geometry and code MIT; photograph referenced only, no third-party image pixels'}
 return b,meta,{'parameters':P,'window_count_estimated':windows,'author_parts':len(b.parts),'lantern_column_count_design_estimate':8,'garden_pavilion_created':False,'back_and_hidden_faces_estimated':True}
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args();b,m,f=build(a.lod);a.out.mkdir(parents=True,exist_ok=True);name=ID+('-lod' if a.lod else '-raw');r=b.save(a.out/(name+'.glb'),m);(a.out/(name+'-features.json')).write_text(json.dumps(f,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='part_summary'}))
if __name__=='__main__':main()
