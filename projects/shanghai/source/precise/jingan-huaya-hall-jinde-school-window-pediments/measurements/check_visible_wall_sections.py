"""Read the wall joints, cornice returns and storey openings from complete Huaya Hall GLBs."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
M=Path(__file__).resolve().parent
sys.path[:0]=[str(M.parent/'source'),str(M.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
import visible_wall_and_bay as walls
from glb_triangles import SerialScene

def check(path):
    scene=SerialScene(path);rows=[]
    for i in range(3):
        f=walls.Facade(None,i)
        def shot(x,z,wanted,label):
            origin=f.xyz(x,-.48,z);direction=np.r_[f.n,0.]
            hit=scene.ray(origin,direction,1.12)
            actual=hit['material'] if hit else None
            rows.append(dict(wall=i,feature=label,origin=origin,direction=list(direction),expected=wanted,actual=actual,nearest=hit,passed=actual in wanted))
        for a,b in [(0.,f.length),*(([(4.7,f.length)] if i==0 else [(0.,f.length)]))]:
            high=(4.397 if len([v for v in rows if v['wall']==i])==0 else 10.07);scale=(1. if high<6 else .89)
            for fract in [.16,.33,.54,.72,.89]:
                x=a+(b-a)*fract
                for h in (.03,.07,.184,.440):shot(x,high+h*scale,[walls.LIGHT],'horizontal moulded course')
            for pitch,w,h in [(.286,.129,.326),(.104,.053,.145)]:
                count=max(1,round((b-a)/pitch));step=(b-a)/count
                for j in sorted({0,count//3,count//2,count-1}):shot(a+step*(j+.5),high+h*scale,[walls.LIGHT],'dentil face')
        for pos in np.linspace(.13,f.length-.13,7):
            shot(pos,-1.502,[walls.BASE],'low red-grey stone course')
        for o in (r for r in walls.SLOTS if r['face']==i):
            l,r,b,t=(o[k]for k in ['left','right','bottom','top'])
            if o['level']=='upper':
                for x in np.linspace(l+.05,r-.05,4):shot(x,b-.062,[walls.LIGHT],'upper projecting sill')
                for x in (l-.12,r+.12):shot(x,b+(t-b)*.55,[walls.LIGHT],'pilaster of upper arched hood')
            else:
                for x in ((l+r)*.5,l+.07,r-.07):shot(x,b-.073,[walls.LIGHT],'lower projecting sill')
    return dict(asset_sha256=hashlib.file_digest(path.open('rb'),'sha256').hexdigest(),triangles=len(scene.tri),rays=len(rows),passed=sum(v['passed']for v in rows),observations=rows)
if __name__=='__main__':
    r=check(Path(sys.argv[1]));Path(sys.argv[2]).write_text(json.dumps(r,ensure_ascii=False,indent=1)+'\n');print(r['passed'],r['rays'],[(v['wall'],v['feature'],v['actual'])for v in r['observations']if not v['passed']])
