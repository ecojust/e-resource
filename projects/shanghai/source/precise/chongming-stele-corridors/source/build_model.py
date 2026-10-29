"""Two long-side stele corridor components; no invented short-side or courtyard plan. MIT."""
import argparse,copy,hashlib,json,struct
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from common.photo_architecture import Builder
ID='chongming-stele-corridors'
P={'length':30.5,'width':2.5,'base_top':.15,'bays':10,'column_radius':.10,'column_y':-1.05,'wall_y':1.12,'wall_thickness':.18,'wall_top':3.58,'eave':3.50,'ridge_roof':4.40,'total_height':4.60,'roof_half_depth':1.50,'roof_length':31.1,'display_y_centres':[-3.5,3.5]}
PALETTE={'plaster':{'color':[.82,.80,.73],'roughness':.96},'stone base':{'color':[.45,.46,.42],'roughness':.97},'stone foot':{'color':[.58,.54,.43],'roughness':.95},'timber':{'color':[.22,.055,.032],'roughness':.82},'timber edge':{'color':[.28,.085,.050],'roughness':.82},'tile0':{'color':[.27,.29,.27],'roughness':.96},'tile1':{'color':[.33,.34,.30],'roughness':.96},'roof bed':{'color':[.21,.23,.21],'roughness':.98},'blank stele0':{'color':[.23,.24,.21],'roughness':.96},'blank stele1':{'color':[.30,.29,.24],'roughness':.98}}
class SteleCorridor:
 def __init__(self,lod=False):self.b=Builder(PALETTE);self.lod=lod;self.features=[]
 def box(self,c,s,m,label):self.b.box(c,s,m,label=label)
 def roofz(self,y):
  t=abs(y)/P['roof_half_depth'];return P['ridge_roof']-(P['ridge_roof']-P['eave'])*(2*t-t*t)
 def finish(self):
  L=P['length'];half=L/2
  self.box((0,0,.075),(L,2.5,.15),'stone base','interpreted-30.5x2.5-base')
  # Original paving joints; not a survey of actual individual stones.
  for i in range(31):
   for j in range(2):self.box((-half+(i+.5)*L/31,-.57+j*1.1,.1625),(L/31-.012,1.08,.025),'stone base','estimated-paving-slab')
  self.box((0,P['wall_y'],(P['wall_top']+.15)/2),(L,.18,P['wall_top']-.15),'plaster','estimated-white-stele-wall')
  for i,x in enumerate(np.linspace(-half+.25,half-.25,11)):
   # Drum-profile stone foot is authored from visible form, not a traced measured section.
   for y in [P['column_y'],1.025]:
    self.box((x,y,.185),(.46,.46,.07),'stone foot','estimated-footing-pad')
    self.b.lathe((x,y),[(.22,.15),(.26,.20),(.33,.205),(.40,.15)],'stone foot',12 if self.lod else 24,'observed-drum-stone-foot')
    self.b.tube([(x,y,.39),(x,y,3.50)],.10 if y<0 else .085,'timber',10 if self.lod else 20,'open-round-column' if y<0 else 'wall-side-semi-exposed-column')
   self.box((x,-.01,3.42),(.17,2.32,.20),'timber','estimated-cross-beam')
   self.box((x,-.01,3.62),(.14,1.30,.11),'timber edge','estimated-upper-cross-member')
  for y in [-1.05,1.025]:self.box((0,y,3.40),(L,.15,.18),'timber','estimated-longitudinal-beam')
  # Twenty blank panels per long component; no mapping to the historical53 stones.
  for i in range(20):
   x=-half+(i+.5)*L/20;h=1.85 if i%3 else 2.12
   self.box((x,1.017,.72+h/2),(.94 if i%2 else 1.03,.025,h),f'blank stele{i%2}','estimated-blank-stele-panel')
  # Curved repeated rafters and closed roof slopes; the total exterior roof remains estimated.
  halfRoof=P['roof_length']/2
  for side in [-1,1]:
   ys=np.linspace(0,side*1.5,17 if not self.lod else 7);profile=[(float(y),self.roofz(y)) for y in ys]
   shell=Polygon(profile+[(y,z-.06) for y,z in reversed(profile)])
   self.b.prism(shell,-halfRoof,halfRoof,lambda y,z,x:(x,y,z),'roof bed','estimated-curved-roof-closed-shell')
   for i,x in enumerate(np.linspace(-halfRoof+.09,halfRoof-.09,111 if not self.lod else 51)):
    self.b.tube([(float(x),float(y),self.roofz(y)+.035) for y in ys],.045,f'tile{i%2}',6 if self.lod else 8,'estimated-tile-course')
    y=side*1.5;self.b.tube([(x,y-side*.02,self.roofz(y)+.035),(x,y+side*.045,self.roofz(y)+.035)],.059,'tile0',6 if self.lod else 8,'estimated-tile-end')
   self.box((0,side*1.42,3.39),(P['roof_length'],.12,.15),'timber','estimated-eave-fascia')
  for x in np.linspace(-halfRoof+.2,halfRoof-.2,82 if not self.lod else 42):
   ys=np.linspace(-1.5,1.5,33 if not self.lod else 13)
   self.b.tube([(float(x),float(y),self.roofz(y)-.16) for y in ys],.045,'timber',6 if self.lod else 8,'photo-guided-curved-rafter')
  self.box((0,0,4.51),(P['roof_length'],.19,.18),'tile0','estimated-plain-ridge-cap')
  self.features=[{'kind':'long-component-base','length_m':30.5,'width_m':2.5,'endpoint_interpretation':'base outer limits'},{'kind':'estimated-grid','bays':10,'column_groups':11,'chosen_column_pitch_m':3.0,'end_inset_m':.25,'full_grid_verified':False},{'kind':'blank-steles','count':20,'all_positions_and_sizes_estimated':True,'historical53_not_layout_inventory':True}]
  for part in self.b.parts:
   v=np.array(part['vertices']);t=np.array(part['triangles']);vol=np.einsum('ij,ij->i',v[t[:,0]],np.cross(v[t[:,1]],v[t[:,2]])).sum()/6
   assert abs(vol)>1e-10,part['label']
   if vol<0:part['triangles']=[(a,c,b) for a,b,c in t]
  return self

def add_components(path,metadata,source_result):
 raw=path.read_bytes();oldlen=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+oldlen]);tail=raw[20+oldlen:]
 doc['meshes']=[copy.deepcopy(doc['meshes'][0]),copy.deepcopy(doc['meshes'][0])]
 doc['meshes'][0]['name']='East_long_component_geometry';doc['meshes'][1]['name']='West_long_component_geometry'
 doc['nodes']=[{'name':label,'mesh':i,'translation':[0,0,-float(y)],'extras':{'identity':label,'display_placement_only':True,'not_measured_courtyard_spacing':True}} for i,(label,y) in enumerate(zip(['East_long_component','West_long_component'],P['display_y_centres']))]
 doc['scenes']=[{'nodes':[0,1]}];doc['extras']=metadata
 data=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();data+=b' '*((-len(data))%4)
 path.write_bytes(struct.pack('<4sII',b'glTF',2,20+len(data)+len(tail))+struct.pack('<II',len(data),0x4e4f534a)+data+tail)
 result={**source_result,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'triangles':source_result['triangles']*2,'parts':source_result['parts']*2,'component_count':2,'each_component_triangles':source_result['triangles'],'component_base_m':[30.5,2.5],'display_only_y_centres_m':P['display_y_centres']}
 # The combined report deliberately does not reuse the single-component bounds.
 result.pop('bounds_glb',None);path.with_suffix('.geometry.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return result
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--out',type=Path,required=True);a.add_argument('--lod',action='store_true');args=a.parse_args();args.out.mkdir(parents=True,exist_ok=True);m=SteleCorridor(args.lod).finish();role='lod' if args.lod else 'raw';path=args.out/f'{ID}-{role}.glb'
 metadata={'id':ID,'name':'崇明学宫碑廊（两长边分段候选）','status':'Two long-side components only; no full courtyard plan or geographic acceptance','documented':'Total76.7m,width2.5m; interpretation2x30.5+15.7=76.7; reportedarea191.75m2. Repair2001.','modeled_components':{'count':2,'each_base_length_m':30.5,'each_base_width_m':2.5,'total_modeled_baseline_length_m':61.0,'estimated_height_m':4.6},'north_south_pending':{'combined_length_budget_m':15.7,'physical_segments_created':False,'individual_lengths_unknown':True},'display':'Components parallel and same-facing at localY-3.5/+3.5 solely for display;7m centre separation is not measured courtyard width or geographic placement.','common_geometry':'Both long components reuse explicit common structural assumptions, not independent evidence of identical east/west details. Photo side identities unknown.','observed':'Open round columns, stone drum feet, white wall/blank stele type, exposed timber beams and repeated curved rafters, stone paving concept.','estimated':'Column spacing/height/diameter,10 divisions, complete roof form/height/curvature,40 blank panels overall and all positions, paving and hidden rear.','historical_collection_count':53,'inscription_reconstruction':False,'photo_pixels_embedded':False,'photo_scale_accepted':False,'full_layout_accepted':False,'walk_scope':'Geometry has clear open corridors, but viewer walk is limited to the entire display envelope exterior, not passage through the galleries.'}
 result=m.b.save(path,metadata=metadata);result=add_components(path,metadata,result)
 (args.out/f'{role}-features.json').write_text(json.dumps({'features':m.features,'component_count':2,'shared_assumptions':True,'parameters':P},ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='part_summary'}))
