"""Intersect first surfaces in the street displays, modelled relief and documented open passage."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from shapely.geometry import Polygon
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
import street_shops_and_roof as shell
def check(path):
    mesh=SerialScene(path);q=json.loads((HERE/'street-frontage-layout.json').read_text());pts=np.asarray(q['pier_tip_axes_m'])
    obs=json.loads((HERE/'street-shops-roof-and-passages.json').read_text());results=[]
    def shot(tag,p,delta,length,expected):
        hit=mesh.ray(p,delta,length);actual=hit['material'] if hit else None
        results.append(dict(feature=tag,origin_m=list(p),direction=list(delta),length_m=length,expected=expected,actual=actual,nearest_surface=hit,passed=actual==expected))
    for i,row in enumerate(obs['ground_bays']):
        f=shell.Face(None,pts[i],pts[i+1],str(i));l,r=np.multiply(row['opening_proportions'],f.length);lower=.09 if i in [5,8]else .23
        for j,frac in enumerate((.10,.25,.45,.71,.87)):
            for z in (.96,2.24):
                x=l+(r-l)*frac;wanted=shell.GLASS
                if i==8 and .325<frac<.64:wanted=shell.BAND
                shot(f'Bay {i+1} display {j+1} at {z:.2f}',f.xyz(x,z,-.37),np.r_[f.n,0],2.4,wanted)
        shot(f'Bay {i+1} lintel',f.xyz((l+r)/2,3.58,-.37),np.r_[f.n,0],1.6,shell.BRONZE if i<3 else shell.SIGN)
    f=shell.Face(None,pts[-2],pts[-1],'204')
    photo=json.loads((HERE/'204-front-metric-camera.json').read_text());ratio=f.length/photo['width_m']
    for key,raw in [('ogee '+str(i+1),x)for i,x in enumerate(photo['crown_relief']['ogees'])]+[('central cartouche',photo['crown_relief']['centre'])]:
        poly=Polygon(np.asarray(raw)*ratio);c=poly.representative_point()
        for point in [c,poly.centroid]:
            shot(key,f.xyz(point.x,point.y,-.25),np.r_[f.n,0],2.4,shell.SHADOW)
    plaque=np.array(photo['local_P'])[:,[0,2,3]]
    for u,v,expected in [(1469,2277,shell.GREEN),(1514,2305,shell.GREEN),(1462,2395,shell.PLAQUE),(1542,2445,shell.PLAQUE)]:
        a=np.linalg.solve(plaque,[u,v,1]);x,z=a[:2]/a[2]*ratio;shot('number or municipal plaque',f.xyz(x,z,-.34),np.r_[f.n,0],1.3,expected)
    for x in (1.02,1.87,2.77,3.57,4.14):
        for z in (.5,1.46,2.31):
            shot('open street entrance',f.xyz(x,z,-.50),np.r_[f.n,0],2.15,None)
    rear=json.loads((HERE/'street-shops-roof-and-passages.json').read_text())['rear_ring_N_to_S']
    back=shell.Face(None,rear[3],rear[2],'rear')
    for x in (.62,1.74,3.04):
        for z in (.9,1.72):shot('open rear return',back.xyz(x,z,-.50),np.r_[back.n,0],2.15,None)
    for x in (-5.0,-3.,0.,3.):
        for y in (-7.,-3.,1.,5.):
            plan=Polygon([*pts,*np.array(rear)[::-1]])
            from shapely.geometry import Point
            if plan.buffer(-1.5).contains(Point(x,y)):shot('flat roof',(x,y,18.30),(0,0,-1),3.0,shell.ROOF)
    return dict(asset_sha256=hashlib.file_digest(path.open('rb'),'sha256').hexdigest(),triangles=len(mesh.tri),rays=len(results),passed=sum(q['passed']for q in results),observations=results)
if __name__=='__main__':
    r=check(Path(sys.argv[1]));Path(sys.argv[2]).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(r['passed'],r['rays'],[(q['feature'],q['actual'])for q in r['observations']if not q['passed']])
