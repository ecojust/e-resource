"""Broadway Mansions exterior candidate; documented height, estimated vertical division.
Original geometry MIT; map-derived footprint © OpenStreetMap contributors ODbL-1.0.
"""
import argparse,json,math
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box
from shapely.geometry.polygon import orient
from common.photo_architecture import Builder,facade_ring,opening
ID='hongkou-broadway-mansions'
ROOT=Path(__file__).resolve().parents[6]
REVIEW=ROOT/'projects/shanghai/data/model-todo/heritage-next-footprint-review.json'
PALETTE={'carved pale stone':{'color':[.38,.29,.20],'roughness':.9},'coffee brick':{'color':[.37,.25,.16],'roughness':.93},'brick trim':{'color':[.30,.20,.13],'roughness':.90},'pale base':{'color':[.57,.55,.49],'roughness':.82},'window frame':{'color':[.28,.28,.25],'roughness':.6},'glass':{'color':[.14,.19,.21],'roughness':.3,'metallic':.15}}
def build(lod=False):
 review=json.loads(REVIEW.read_text());record=next(r for r in review['records'] if r['id']=='582fd5f8-2a90-3eba-9fce-81b358492d0b')
 plan=orient(Polygon(record['local_exterior_enu_m']),sign=1)
 b=Builder(PALETTE);floors=[];windows=0
 # Every cutoff, layer height, opening grid and hidden facade is a design estimate.
 # The frozen map H-like footprint guides form, not verified historical wall lines.
 levels=[0,4.8,8.6]+[8.6+i*3.32 for i in range(1,20)]+[75.7]
 assert len(levels)==23
 for i,(bottom,top) in enumerate(zip(levels,levels[1:])):
  cutoff=40 if i<10 else [33,33,29,29,23,23,18,18,12,12,12,12][i-10]
  poly=orient(plan.intersection(box(-cutoff,-50,cutoff,50)),sign=1)
  assert poly.is_valid and not poly.is_empty
  fs=facade_ring(b,poly,f'estimated-storey-{i+1}')
  b.plan_prism(poly.buffer(-.20,join_style=2),bottom,bottom+.18,'roof zinc','estimated-floor-slab')
  b.plan_prism(poly,top-.16,top,'roof zinc','estimated-flat-roof-or-ceiling')
  for edge in fs:
   margin=.65;n=max(1,int((edge.length-2*margin)/3.4));pitch=(edge.length-2*margin)/n
   holes=[]
   for j in range(n):
    u=-edge.length/2+margin+(j+.5)*pitch;w=min(2.15 if i>1 else 2.5,pitch-.5)
    if w<.5:continue
    h=2.08 if i>1 else 2.65;z=bottom+(.76 if i>1 else .85)
    sh=opening(u,z,w,h);holes.append(sh);windows+=1
    if lod:
     edge.prism(sh,-.30,-.27,'glass','estimated-recessed-glazing')
     edge.box(u,z-.06,w+.12,.12,.42,-.06,'brick trim','estimated-sill')
    else:
     edge.window(sh,columns=3 if w>1.6 else 2,rows=2,frame='window frame',trim=False,glass='glass',label='estimated-window')
   edge.wall(bottom,top,holes,thickness=.40,material='pale base' if i==0 else 'coffee brick')
   edge.beam(top-.10,.20,.08,'brick trim',label='estimated-brick-storey-band')
   if not lod and edge.length>4:
    # Narrow vertical brick ribs between openings, bounded within each storey.
    for j in range(n+1):
     u=-edge.length/2+margin+j*pitch
     if abs(u)<edge.length/2-.25:edge.box(u,(bottom+top)/2,.22,top-bottom-.25,.16,.04,'brick trim','estimated-brick-rib')
  floors.append({'layer':i+1,'bottom_m':bottom,'top_m':top,'x_cutoff_m':cutoff,'window_grid_estimated':True,'plan_area_m2':poly.area})
 # Roof parapets keep the actual maximum at the chosen historical 76.7m.
 for edge in facade_ring(b,poly,'estimated-crown'):
  edge.wall(75.7,76.7,thickness=.35,material='coffee brick');edge.beam(76.56,.28,.14,'brick trim',label='estimated-crown-coping')
 # Lower entrance canopy is only an exterior interpretation, no false signage.
 edge=max(facade_ring(b,plan),key=lambda f:f.length)
 edge.box(0,3.5,7,.25,2.5,1.05,'dark stone','estimated-entry-canopy')
 metadata={'id':ID,'status':'standalone-exterior-candidate-not-geographically-registered','height_reference_m':76.7,'secondary_height_m':77,'documentary_floor_counts':[22,21],'map_floor_count':19,'floor_conflict_resolved':False,'layers_are_design_divisions':True,'footprint_source_id':record['id'],'footprint_historical_wall_verified':False,'map_replacement':False,'photos_embedded':False,'estimated':'Floor divisions, x clipping setbacks, windows, ribs, roof/parapets, canopy, all hidden elevations; map footprint not surveyed historic wall','copyright':'Original code and geometry MIT; map-derived footprint © OpenStreetMap contributors ODbL-1.0; photograph not embedded'}
 # Closed author parts and positive volumes before export.
 for p in b.parts:
  v=np.array(p['vertices']);t=np.array(p['triangles']);volume=np.einsum('ij,ij->i',v[t[:,0]],np.cross(v[t[:,1]],v[t[:,2]])).sum()/6
  assert abs(volume)>1e-9,p['label']
  if volume<0:p['triangles']=[(int(a),int(c),int(b)) for a,b,c in t]
 return b,metadata,{'floors':floors,'estimated_window_openings':windows,'author_parts':len(b.parts)}
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args()
 b,meta,features=build(a.lod);a.out.mkdir(parents=True,exist_ok=True);name=ID+('-lod' if a.lod else '-raw')
 report=b.save(a.out/(name+'.glb'),meta);(a.out/(name+'-features.json')).write_text(json.dumps(features,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='part_summary'}))
if __name__=='__main__':main()
