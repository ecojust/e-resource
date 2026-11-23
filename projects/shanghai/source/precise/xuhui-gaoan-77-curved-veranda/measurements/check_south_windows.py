"""Read the visible materials of the three garden windows in the original photographs."""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
sys.path.insert(0,str(HERE.parents[1]/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene
from materials import PLASTER,BRICK,FRAME,GLASS
from photo_cameras import projection
SAMPLES={
 'sina-37':[(181,249,GLASS),(192,273,GLASS),(220,244,GLASS),(231,272,GLASS),(245,270,GLASS),(253,246,GLASS),(208,264,BRICK),(207,277,BRICK),(173,221,PLASTER),(239,229,PLASTER)],
 'sina-35':[(98,249,GLASS),(105,270,GLASS),(129,240,GLASS),(147,253,GLASS),(180,238,GLASS),(187,266,GLASS),(116,264,BRICK),(169,252,BRICK),(166,216,PLASTER),(83,284,PLASTER)],
 'paper-25':[(305,151,GLASS),(308,166,GLASS),(327,152,GLASS),(342,167,GLASS),(363,159,GLASS),(366,171,GLASS),(318,159,BRICK),(355,157,BRICK),(290,175,PLASTER),(321,192,PLASTER)]}
def check(file):
    scene=SerialScene(file);rows=[]
    for name,samples in SAMPLES.items():
        P=projection(name);inv=np.linalg.inv(P[:,:3]);eye=-inv@P[:,3]
        for x,y,mat in samples:
            hit=scene.ray(eye,inv@[x,y,1],130);m=hit['material']if hit else None
            rows.append({'photo':name,'pixel':[x,y],'expected':mat,'actual':m,'matched':m==mat})
    return {'file':file.name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'matched':sum(r['matched']for r in rows),'samples':len(rows),'readings':rows}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('output',type=Path);a=p.parse_args();r=check(a.mesh);a.output.write_text(json.dumps(r,indent=2)+'\n');print(r['matched'],r['samples'],[(v['photo'],v['pixel'],v['actual'])for v in r['readings'] if not v['matched']])
