"""Test the two street-camera rays and the 1934 front-plane controls against a GLB."""
from pathlib import Path
import argparse, json, sys
import numpy as np
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene
C,STONE,GL,J,IR='ivory cement','grey cast','grey-green glazing','warm plaster','dark metal'
samples={
 'commons2015':[
 (512,1644,C),(864,1644,C),(691,1653,STONE),(543,1370,C),(865,1371,C),(694,1375,STONE),
 (526,1118,C),(850,1121,C),(692,1117,STONE),(551,857,C),(850,847,C),(693,862,STONE),
 (565,1504,GL),(808,1506,GL),(558,1245,GL),(821,1239,GL),(556,1002,GL),(808,1003,GL),
 (570,749,GL),(819,750,GL),(460,1462,J),(478,936,J),(490,746,J),
 (729,1779,IR),(642,1774,GL),(490,1781,C),(890,1769,C)],
 'housing2023':[
 (497,582,C),(589,582,C),(542,590,STONE),(496,503,C),(590,503,C),(541,506,STONE),
 (497,415,C),(587,416,C),(542,419,STONE),(496,326,C),(592,324,C),(542,325,STONE),
 (493,548,GL),(590,546,GL),(495,454,GL),(588,457,GL),(497,365,GL),(586,362,GL),
 (496,286,GL),(586,284,GL),(476,565,J),(481,372,J),(605,285,J),
 (548,632,IR),(531,634,GL),(490,625,C),(590,629,C)]}
# Coordinates of tangible front surfaces in the photograph published by Le Journal de Shanghai.
historical=[(248,755,C),(465,753,C),(347,751,STONE),(241,603,C),(471,607,C),(355,604,STONE),
            (246,459,C),(467,457,C),(355,457,STONE),(245,305,C),(463,308,C),(347,305,STONE)]
def inspect(mesh):
 data=json.loads((HERE/'corner-camera-and-levels.json').read_bytes());s=SerialScene(mesh);stations={}
 for name,points in samples.items():
  p=np.array(data['cameras'][name]['P']);inv=np.linalg.inv(p[:,:3]);eye=-inv@p[:,3]
  rows=[]
  for u,v,w in points:
   hit=s.ray(eye,inv@[u,v,1],130)
   rows.append({'native_pixels':[u,v],'expected_material_contains':w,'hit':hit,'matched':bool(hit and w in hit['material'])})
  stations[name]={'matched':sum(t['matched'] for t in rows),'count':len(rows),'rays':rows}
 H=np.linalg.inv(data['press_1934_front_plane']['H_XZ_to_uv']);rows=[]
 for u,v,w in historical:
  p=H@[u,v,1];x,z=p[:2]/p[2];hit=s.ray([x,-20,z],[0,1,0],60)
  rows.append({'native_pixels':[u,v],'front_XZ_m':[x,z],'expected_material_contains':w,'hit':hit,'matched':bool(hit and w in hit['material'])})
 stations['press1934_coplanar_normal']={'matched':sum(t['matched'] for t in rows),'count':len(rows),'rays':rows}
 return {'mesh':s.asset,'stations':stations,'method':'2015及2023沿各自拟合针孔相机实射。1934报纸图经过裁切，用栏板立面单应性将原像映到XZ，沿立面法线实射。电线、行人及室外机没有作为栏板控制点。'}
if __name__=='__main__':
 cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('glb',type=Path);cli.add_argument('output',type=Path);args=cli.parse_args()
 d=inspect(args.glb);args.output.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
 for k,v in d['stations'].items():
  print(k,v['matched'],v['count'],[(r['native_pixels'],r['hit']['material'] if r['hit'] else None) for r in v['rays'] if not r['matched']])
