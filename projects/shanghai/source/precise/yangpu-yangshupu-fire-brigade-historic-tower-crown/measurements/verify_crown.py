"""Read actual first intersections from fixed historical-image pixels and save a model-only study."""
import argparse,hashlib,json,runpy,sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from build_model import PROJECT, GLASS,BAR,FLOOR,INNER,PANEL,SILL,EDGE,ROOF,WALL,SURVEY
SerialScene=runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
SAMPLES={
    'front roundel':([(572,161),(577,158),(580,165),(572,170)],{GLASS,BAR,SILL}),
    'return roundel':([(632,166),(636,173),(635,178)],{GLASS,BAR,SILL}),
    'recessed rectangular fields':([(555,264),(571,253),(590,267),(627,261),(638,271),(648,264)],{PANEL}),
    'shaft margins':([(541,264),(607,249),(611,213),(620,190),(658,260)],{WALL}),
    'east and return projecting cap':([(540,115),(565,102),(592,92),(627,95),(647,111),(662,123)],{ROOF,SILL,FLOOR,EDGE}),
    'historic crown roof':([(577,37),(588,30),(602,26),(616,29),(628,35)],{ROOF}),
    'lantern apron':([(588,75),(602,78),(610,74)],{WALL,SILL}),
    'dark lights between posts':([(585,50),(587,53),(607,47),(611,50)],{INNER,None}),
    'open sky':([(550,53),(646,35),(556,79),(650,72)],{None})}
MATRIX=np.array(SURVEY['matrix'])
def sha(path):
    with path.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def inspect(path):
    scene=SerialScene(path); eye=np.linalg.solve(MATRIX[:,:3],-MATRIX[:,3]);rows=[]
    for group,(points,kinds) in SAMPLES.items():
        for u,v in points:
            direction=np.linalg.solve(MATRIX[:,:3],[u,v,1]);hit=scene.ray(eye,direction,20)
            actual=hit['material'] if hit else None
            rows.append(dict(group=group,point=[u,v],expected=sorted(k or 'sky'for k in kinds),first_hit=actual,passed=actual in kinds))
    return {'mesh_sha256':sha(path),'reference_sha256':SURVEY['source_sha256'],'camera_reference':'historical-crown-camera.json',
        'rays':rows,'matched':sum(r['passed']for r in rows),'total':len(rows)}
def render(path,out):
    s=SerialScene(path)
    q=np.column_stack((s.tri.reshape(-1,3),np.ones(len(s.tri)*3)))@MATRIX.T
    q=q.reshape(-1,3,3);u=q[:,:,:2]/q[:,:,2,None];scale=1.74
    img=Image.new('RGB',(350,555),(231,231,223));draw=ImageDraw.Draw(img)
    colors={WALL:(191,190,181),ROOF:(99,100,98),EDGE:(209,208,200),SILL:(177,175,167),GLASS:(66,69,66),BAR:(114,115,107),FLOOR:(165,165,157),PANEL:(145,143,136),INNER:(90,90,85)}
    norms=np.cross(s.tri[:,1]-s.tri[:,0],s.tri[:,2]-s.tri[:,0]);norms/=np.linalg.norm(norms,axis=1)[:,None]
    sun=np.array([-.4,-.7,.75]);sun/=np.linalg.norm(sun)
    for i in np.argsort(-q[:,:,2].mean(axis=1)):
        xy=(u[i]-[499,6])*scale
        bright=.78+.26*max(0.,norms[i]@sun)
        draw.polygon([tuple(p) for p in xy],fill=tuple(round(c*bright) for c in colors[s.materials[s.mi[i]]]))
    img.save(out,quality=93)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('out',type=Path);parser.add_argument('models',nargs='+',type=Path)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True);rep=[inspect(p) for p in args.models]
    (args.out/'historical-image-rays.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2)+'\n')
    render(args.models[0],args.out/'historic-tower-crown.jpg')
    for item in rep:print(item['matched'],item['total'],[(r['point'],r['first_hit'])for r in item['rays']if not r['passed']],flush=True)
