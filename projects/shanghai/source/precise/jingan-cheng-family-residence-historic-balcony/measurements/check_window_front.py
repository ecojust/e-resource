"""Intersect actual exported triangles at the five registered windows and the pierced east crown."""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from read_study import decode,hit,norm
import historic_window_front as facade

def check(asset):
    t,m,_=decode(asset);data=facade.DATA;faces=[facade.Face(None,q)for q in data['faces']]
    cameras=json.loads((HERE/'historic-balcony-cameras.json').read_bytes())
    P=np.asarray(cameras['gao2018']['P']);eye=-np.linalg.solve(P[:,:3],P[:,3]);checks=[]
    def probe(label,o,d,material,photo=None):
        r=hit(t,m,np.asarray(o),norm(d));a=None if r is None else r[0]
        checks.append(dict(feature=label,expected=material,actual=a,hit_m=None if r is None else r[1],photo_px=photo,passed=a==material))
    for w in data['windows']:
        f=faces[w['face']];k=w['key'];l,r,b,z=w['opening_m'];lo,ro,bo,zo=w['surround_m']
        def point(name,x,h,mat):
            o=f.point(x,h,-.11);d=np.r_[f.n,0.];probe(k+' '+name,o,d,mat)
        for x in [lo+.045,ro-.045]:
            for v in (.18,.48,.77):point('outer stone',x,b+(z-b)*v,facade.STONE)
        point('head',(l+r)/2,(zo+z)/2,facade.STONE)
        point('fixed stile',l+.043,z-.14,facade.WOOD)
        point('fixed stile',r-.047,z-.14,facade.WOOD)
        point('middle of opening',(l+r)/2,z-.40,facade.DARK_GLASS if k=='left_splay' else facade.WOOD)
        for i,kx in enumerate((.256,.747)):
            dark=k=='left_splay' or (k in ('balcony_right','right_splay') and i==0)
            surf=facade.DARK_GLASS if dark else facade.GLASS
            for row in (.518,.67,.787):
                hz=b+(z-b)*row
                trans=min(w.get('transom_z_m',z+1.),z-.074)
                inside_rail=trans-.022<=hz<=trans+.022
                near_leaf_head=k!='left_splay' and trans-.063<hz<trans-.022
                mat=facade.WOOD if inside_rail else (facade.DULL_PANEL if dark else facade.WOOD) if near_leaf_head else surf
                point('transom rail' if inside_rail else 'upper leaf rail' if near_leaf_head else 'inset sash field',l+(r-l)*kx,hz,mat)
            if k=='left_splay':
                point('upper shadow field',l+(r-l)*kx,z-.134,facade.DARK_GLASS)
            elif z-.062-trans>.06:
                point('transom light',l+(r-l)*kx,(trans+z-.062)/2,facade.DARK_GLASS)
            else:
                point('upper casement rail',l+(r-l)*kx,trans,facade.WOOD)
            if k=='right_front':point('painted lower field',l+(r-l)*kx,b+(z-b)*.25,facade.LIGHT_PANEL)
        if not k.startswith('balcony'):
            point('sloping sill surface',(lo+ro)/2,b-.092,facade.LIP)
            point('sill bed',(lo+ro)/2,b-.165,facade.STONE)
            point('sill apron',(lo+ro)/2,b-.255,facade.STONE)
    f=faces[3];c=data['right_bay_crown']
    for key in ['upper_light','lower_light','left_light','right_light']:
        q=np.array(c[key]['face_xz_m']);centre=q.mean(0);uv=np.asarray(c[key]['native_pixels']).mean(0)
        for fraction in (.0,.38):
            for edge in (q[0],q[2],q[-2]):
                pt=centre+fraction*(edge-centre)
                probe('openwork '+key,f.point(*pt,-.22),np.r_[f.n,0.],None)
        probe('photographic openwork '+key,eye,np.linalg.solve(P[:,:3],np.r_[uv,1]),None,uv.tolist())
    # Independent original image samples on the masonry between the four excavated apertures.
    for uv in [(2772,810),(2754,795),(2786,792),(2752,825),(2785,828),(2700,747),(2850,853)]:
        probe('photo crown material',eye,np.linalg.solve(P[:,:3],np.r_[uv,1]),facade.STONE,uv)
    return dict(asset_sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),triangles=len(t),rays=len(checks),passed=sum(x['passed']for x in checks),observations=checks)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('mesh',type=Path);a.add_argument('out',type=Path);q=a.parse_args();r=check(q.mesh)
    q.out.write_text(json.dumps(r,indent=1,ensure_ascii=False)+'\n')
    print(r['passed'],r['rays']);print([(row['feature'],row['expected'],row['actual'])for row in r['observations']if not row['passed']])
