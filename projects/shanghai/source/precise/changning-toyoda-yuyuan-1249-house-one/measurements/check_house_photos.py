"""Trace pre-registered pixels from the two independently dated photographs into delivered GLBs."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
M=Path(__file__).absolute().parent
S=M.parent/'source'
project=next(r for r in M.parents if (r/'tools/package_architectural_model.py').is_file())
sys.path[:0]=[str(M),str(S),str(project/'source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact')]
from glb_triangles import SerialScene
from check_triple_windows import camera
# 2018 points on the full image resampled to width 850. 2013 resampled to 650.
REFS={
 'commons2018':{
 'arc brick':[(129,272),(152,255),(175,229),(204,203)],
 'round column':[(137,313),(158,303),(185,287)],
 'glass or joinery':[(127,310),(150,290),(177,263),(204,250),(260,247),(271,225),(449,228),(451,245),(565,223),(591,228),(668,218)],
 'grey masonry':[(228,244),(279,288),(340,192),(476,199),(493,267),(631,189),(503,143)],
 'red floor band':[(257,321),(279,311),(425,304),(510,310)],
 'porch parapet':[(608,299),(662,310),(735,305),(783,319)],
 'porch brick arch':[(612,366),(652,357),(748,353),(784,355)],
 'roof or eave':[(125,211),(151,181),(240,19),(271,40),(476,74),(657,123)]},
 'gao05':{
 'grey masonry':[(177,87),(185,116),(314,89),(401,126)],
 'glass or joinery':[(74,79),(91,89),(248,97),(265,90),(371,101)],
 'red floor band':[(108,172),(161,182),(195,184)],
 'porch parapet':[(265,167),(317,163),(376,171),(432,179),(478,193)],
 'porch brick arch':[(245,234),(264,219),(345,235),(378,228),(428,229),(467,247)],
 'porch inner plaster':[(412,284),(425,323),(401,366)],
 'porch dark door':[(366,296),(376,361)],
 'porch raised floor':[(392,397),(420,402)]}}
EXPECTED={'arc brick':['radial red brick','russet brick','buff joint'],'round column':['pale carved stone'],
 'glass or joinery':['crimson joinery','shaded courtyard glass','pale reflected glass'],'grey masonry':['blue-grey running bond'],
 'red floor band':['radial red brick','russet brick'],'porch parapet':['weathered terrace render','grey concrete'],
 'porch brick arch':['radial red brick','russet brick','buff joint'],'roof or eave':['dark red roof tile','ridge clay','weathered red fascia'],
 'porch inner plaster':['recessed porch plaster'],'porch dark door':['dark red door'],'porch raised floor':['grey concrete','pale carved stone']}
def run(mesh):
 scene=SerialScene(mesh);layout=json.loads((S/'house-layout.json').read_bytes());cal=json.loads((M/'triple-window-calibration.json').read_bytes())
 results=[]
 for key,points in REFS.items():
  if key=='commons2018':
   P=np.array(json.loads((M/'commons-corner-camera.json').read_bytes())['P']);m=P[:,:3];o=-np.linalg.solve(m,P[:,3])
  else:
   m,o=camera(cal['views']['gao05'],layout);m=np.diag([650/850,650/850,1])@m
  obs=[]
  for feature,coords in points.items():
   for u,v in coords:
    hit=scene.ray(o,np.linalg.solve(m,[u,v,1]),100)
    expected=EXPECTED[feature];passed=hit is not None and hit['material'].split(' | ')[-1] in expected
    obs.append(dict(feature=feature,source_pixel=[u,v],expected_materials=expected,passed=passed,first_hit=hit))
  results.append(dict(source=key,working_width=850 if key=='commons2018' else 650,passed=sum(r['passed'] for r in obs),count=len(obs),points=obs))
 return dict(file=scene.asset,views=results)
if __name__=='__main__':
 cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('out',type=Path);cli.add_argument('models',nargs='+',type=Path);args=cli.parse_args()
 data=[run(model)for model in args.models];args.out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 for role in data:
  print(role['file']['file'],[(v['source'],v['passed'],v['count'])for v in role['views']])
