"""Read the actual southern steelwork and glass triangles, with the six observed window patterns."""
from collections import Counter
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import first_hit, load_triangles, material_appearance

FIXED = 'Guanger | fixed dark steel'
SASH = 'Guanger | painted steel sash'
BLUE = 'Guanger | blue grey window glass'
PALE = 'Guanger | pale reflective window glass'
SHOP = 'Guanger | lower shop glass'
# From the orthogonal and oblique completion photographs. Count each fine pane
# distinctly in a wide second-floor window, including the two flanking lower sections.
PATTERNS = {
    'wide-upper': ([.20,.40,.60,.80], [[1/6,2/6,.5,4/6,5/6]]*5, BLUE),
    'wide-second': ([.385,.565,.715,.865], [[.30,.70]]+[[i/10 for i in range(1,10)]]*4, PALE),
    'central-upper': ([.25,.50,.75], [[1/3,2/3]]*4, BLUE),
    'central-second': ([.176,.460,.745], [[.25,.5,.75]]*4, PALE),
    'ground-mid': ([.61,.81], [[.5]]*3, SHOP),
    'ground-side': ([.61,.81], [[]]*3, SHOP),
}

def probes(o, far):
    l,r,b,t = [o[n] for n in ('x0','x1','z0','z1')]
    width,height=r-l,t-b
    fixed=min(.051,width*.055,height*.035)
    yield 'fixed jamb', l+fixed*.45, b+.38*height, 0, FIXED
    yield 'fixed head', l+.35*width, t-fixed*.45, 0, FIXED
    margin=fixed+.0015
    x0,x1,z0,z1=l+margin,r-margin,b+margin,t-margin
    heights,lights,glass=PATTERNS[o['family']]
    cuts=[z0,*[z0+h*(z1-z0) for h in heights],z1]
    for z in cuts[1:-1]:
        yield 'cross rail', x0+.413*(x1-x0), z, .010, SASH
    for row, verticals in enumerate(lights):
        z=cuts[row]+.48*(cuts[row+1]-cuts[row])
        xcuts=[x0,*[x0+f*(x1-x0) for f in verticals],x1]
        for x in xcuts[1:-1]:
            yield 'glazing bar', x,z,.010,SASH
        for left,right in zip(xcuts,xcuts[1:]):
            yield 'glass pane', (left+right)*.5,z,.061 if far else .036,glass

def photo_check(schedule):
    obs=json.loads((HERE/'southern-window-image-observations.json').read_bytes())
    openings={o['key']:o for o in schedule['openings']}
    records=[]
    keys=['W1-F4','W1-F3','Cc-F4','Cc-F3','Cc-F2','W1-F2']
    for key,o in zip(keys, obs['observed_windows'][:6]):
        shape=openings[key]
        edges=np.array(o['clear_opening_points_tl_tr_br_bl'],float)
        zs,xfrac,_=PATTERNS[shape['family']]
        # Estimate photographed rod/rail midpoints in the registered perimeter,
        # accounting for the fixed jamb offset between outside frame and moving leaves.
        u0,u1=edges[[0,3],0].mean(),edges[[1,2],0].mean()
        v0,v1=edges[[2,3],1].mean(),edges[[0,1],1].mean()
        w,h=shape['x1']-shape['x0'],shape['z1']-shape['z0']
        rim=min(.051,w*.055,h*.035)+.0015
        u=np.array([0,*[rim/w+(1-2*rim/w)*v for v in xfrac[-1]],1])
        v=np.array([0,*[rim/h+(1-2*rim/h)*f for f in zs],1])[::-1]
        observed_x=np.array(o['measured_rod_x_px']);observed_y=np.array(o['measured_rail_y_px'])
        assert len(u)==len(observed_x) and len(v)==len(observed_y)
        dx=(u0+(u1-u0)*u-observed_x).round(3)
        dy=(v0+(v1-v0)*v-observed_y).round(3)
        records.append(dict(key=key,original=o['source'],jamb_corners_px=edges.tolist(),
            predicted_minus_observed_vertical_x_px=dx.tolist(),predicted_minus_observed_rail_y_px=dy.tolist(),
            max_abs_px=float(np.abs(np.r_[dx,dy]).max())))
    return records

def read(path,layout,far):
    tri,mi,labels,asset=load_triangles(path)
    appearance=material_appearance(path)['materials']
    for label in (BLUE,PALE,SHOP):
        assert 'baseColorTexture' in appearance[label]['textures']
    mn,mx=tri.min(1),tri.max(1)
    bays={b['bay']:b for b in layout['bays']}
    results=[];by_key={};first_occlusions=Counter()
    for o in layout['openings']:
        key=o['key'];bay=bays.get(o['bay'])
        # Include all geometry crossing the rays' XZ envelope (including masonry).
        region=(mn[:,0]<o['x1'])&(mx[:,0]>o['x0'])&(mn[:,2]<o['z1'])&(mx[:,2]>o['z0'])
        ids=np.where(region)[0]
        low,high=mn[ids],mx[ids]
        local=[]
        for tag,x,z,offset,material in probes(o,far):
            if bay:
                surface=bay['y0']+(x-bay['x0'])*(bay['y1']-bay['y0'])/(bay['x1']-bay['x0'])+.17
            else:
                surface=.11
            expected_y=surface+offset
            use=ids[(low[:,0]<=x)&(high[:,0]>=x)&(low[:,2]<=z)&(high[:,2]>=z)]
            start=[x,surface-5,z]
            head=None;match=None;normal=None
            if len(use):
                idx,distance,point=first_hit(tri[use],start,[0,1,0])
                if np.isfinite(distance):
                    head=[labels[mi[use[idx]]],round(float(point[1]),5)]
                targets=use[mi[use]==labels.index(material)]
                if len(targets):
                    idx,distance,point=first_hit(tri[targets],start,[0,1,0])
                    if np.isfinite(distance):
                        match=round(float(point[1]-expected_y),6)
                        a,c,d=tri[targets[idx]]
                        n=np.cross(c-a,d-a)
                        normal=round(float(n[1]/np.linalg.norm(n)),5)
            passed=bool(match is not None and abs(match)<.006 and normal<-.93)
            visible=bool(head and head[0]==material and abs(head[1]-expected_y)<.006)
            if not visible:first_occlusions[(key,head[0] if head else None)]+=1
            local.append([tag,round(x,5),round(z,5),round(expected_y,5),material,head,match,normal,passed,visible])
        by_key[key]=dict(family=o['family'],tested=len(local),geometry=sum(r[-2]for r in local),
                         first_surface=sum(r[-1]for r in local),pane_centres=sum(r[0]=='glass pane' for r in local))
        results.extend([[key,*r]for r in local])
    return dict(asset=asset,window_count=len(by_key),rays=len(results),matched=sum(r[-2]for r in results),
                visible=sum(r[-1]for r in results),first_occlusions=[[a,b,n]for (a,b),n in first_occlusions.items()],
                glass_materials=[BLUE,PALE,SHOP],windows=by_key),results

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('output',type=Path)
    parser.add_argument('files',nargs='+',type=Path)
    args=parser.parse_args()
    layout_path=HERE/'riverfront-layout.json'
    layout=json.loads(layout_path.read_bytes())
    assert len(layout['openings'])==69 and len({o['key']for o in layout['openings']})==69
    args.output.mkdir(exist_ok=True,parents=True)
    overview=[];payload=[]
    for p in args.files:
        stats,rows=read(p,layout,'lod' in p.name)
        overview.append(stats);payload.append(dict(sha256=stats['asset']['sha256'],rows=rows))
    packed=gzip.compress(json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode(),mtime=0)
    (args.output/'warehouse-window-rays.json.gz').write_bytes(packed)
    photo=photo_check(layout)
    result=dict(layout_sha256=hashlib.sha256(layout_path.read_bytes()).hexdigest(),
        photo_observations=photo,photo_register='Each original photographed aperture sets its own four-sided picture frame. Internal bars and transoms are the independent checks.',
        ray_columns=['window','test','x','z','expected_y','material','first_surface_and_y','matching_surface_error_m','normal_y','geometry_matches','visible_first'],
        rays_sha256=hashlib.sha256(packed).hexdigest(),meshes=overview)
    (args.output/'warehouse-window-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print([(r['asset']['file'],r['rays'],r['matched'],r['visible'])for r in overview], max(i['max_abs_px']for i in photo))
    assert all(x['rays']==x['matched'] for x in overview)
    assert max(i['max_abs_px'] for i in photo)<4

if __name__=='__main__':main()
