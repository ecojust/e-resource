"""Derive the freely placed arched porch from the same complete, registered source."""
from pathlib import Path
import argparse,sys,json
def run(project,out):
 src=project/'source/precise/xuhui-changle-325-garden-courtyard-and-arched-porch/source'
 sys.path.insert(0,str(src))
 import build_model as b
 for lod in [False,True]:
  builder=b.Builder(b.PALETTE);frame=b.PorchFrame()
  b.porch_stone.add_porch_stone(builder,frame,lod=lod)
  b.porch_tiles.add_porch_roof(builder,frame,lod=lod)
  b.porch_doors.add_porch_doors(builder,frame,lod=lod)
  anchor=json.loads((src.parent/'measurements/porch-frame.json').read_bytes())['frame_origin']
  for p in builder.parts:
   assert max(x for x,y,z in p['vertices'])<-7, p['label']
   p['vertices']=[(x-anchor[0],y-anchor[1],z) for x,y,z in p['vertices']]
  role='lod' if lod else 'full';meta={**b.META,'map_component':'stone entrance, flight and tiled roof','scope':'券廊、十级石阶与两侧栏杆和门；院中独立摆放。','city_source_owners_removed':[],'garden_to_map_anchor_local_xyz':anchor}
  builder.save(out/(role+'-source.glb'),meta)
if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('project',type=Path);a.add_argument('output',type=Path);c=a.parse_args();c.output.mkdir(parents=True,exist_ok=True);run(c.project,c.output)
