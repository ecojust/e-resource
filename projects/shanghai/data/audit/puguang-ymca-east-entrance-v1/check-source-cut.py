"""Measure the two limited-height cuts against the six buildings in the frozen draw group."""
from argparse import ArgumentParser
from pathlib import Path
import subprocess,sys
import numpy as np
import shapely as geo
from shapely.geometry import box
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,sha,write
ID='huangpu-puguang-ymca-east-entrance'
OWNER=2382
GROUP={2187,1222,2490,3197,2382,379}
FRONT=-1.13
BACK=1.47

def inside_volume(triangle,limits):
    """Clip the actual 3D triangle against all six faces, including zero-area wall projections."""
    points=list(triangle)
    for axis,limit,keep_above in limits:
        clipped=[]
        for a,b in zip(points,points[1:]+points[:1]):
            va=a[axis]-limit;vb=b[axis]-limit
            a_inside=va>=0 if keep_above else va<=0
            b_inside=vb>=0 if keep_above else vb<=0
            if a_inside:clipped.append(a)
            if a_inside!=b_inside:clipped.append(a+va/(va-vb)*(b-a))
        if not clipped:return False
        points=clipped
    return len(points)>=3

def main(work,out):
    source=PROJECT/'source/precise'/ID
    review=read(source/'footprint-review.json');site=PlacementMeshes(PROJECT,work,review)
    bands=read(source/'source/frontage-registration.json')['height_bands'];group,=review['near_tiles']
    ids=group['feature_local_ids'];assert set(ids)==GROUP
    site.link('baseline-far.glb',site.files['far.glb'])
    site.link('baseline-near.glb.gz',site.files[Path(group['file']).name])
    site.link('macro-READY.json',site.files['READY.json'])
    write(work/'context-features.json',[dict(localId=i)for i in ids])
    subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,stdout=subprocess.DEVNULL)
    rings=[site.footprints[i]for i in ids];own=ids.index(OWNER);src=site.footprints[OWNER]
    results={}
    for variant in ('near','far'):
        arr=np.fromfile(work/f'baseline-{variant}-triangles.f64',np.float64).reshape(-1,3,3)
        arr[:,:,:2]=arr[:,:,:2]@site.axes.T
        low=arr.min(axis=1);high=arr.max(axis=1)
        typed=np.fromfile(work/'baseline-far-owners.u32',np.uint32) if variant=='far' else None
        if typed is not None:assert len(typed)==len(arr)and set(typed)==GROUP
        outputs=[]
        for band in bands:
            width_min,width_max=band['left'],band['right']
            lo=np.array([width_min,FRONT,band['base']]);hi=np.array([width_max,BACK,band['top']])
            limits=[(axis,which[axis],above)for axis in range(3)for which,above in ((lo,True),(hi,False))]
            halo_mask=np.all((high[:,:2]>=lo[:2]-.5)&(low[:,:2]<=hi[:2]+.5),axis=1)
            rows=np.flatnonzero(halo_mask)
            distances=np.stack([geo.distance(geo.points(arr[rows,:,:2].mean(axis=1)),r)for r in rings],axis=1)
            assigned=np.argmin(distances,axis=1)
            # Roof fans may have distant vertices. Recheck true material surfaces before assigning them.
            cached={};margin=[];observed_owners=[]
            for k,idx in enumerate(rows):
                hit=inside_volume(arr[idx],limits)
                if not hit:continue
                if variant=='far':
                    actual=typed[idx]
                else:
                    actual=ids[assigned[k]]
                observed_owners.append(int(actual))
                assert actual==OWNER,(variant,idx,actual)
                margin.append(float(np.delete(distances[k],own).min()-distances[k,own]))
                assert margin[-1]>1.5 and distances[k,own]<.40,(variant,idx,distances[k])
                cached[int(idx)]=True
            assert cached and min(margin)>1.5
            # Determine the surface area actually retained in plan from the signed source ring.
            footprint=box(width_min,FRONT,width_max,BACK)
            peers=[dict(local_id=r['local_id'],distance_m=float(site.footprints[r['local_id']].distance(footprint)))for r in review['owners']if r['local_id']!=OWNER]
            assert min(o['distance_m']for o in peers)>.65
            above=rows[(low[rows,2]>band['top']+.01)&(assigned==own)]
            heights=high[rows[assigned==own],2]
            assert 22.35<max(heights)<22.45 and len(above)>0
            outputs.append(dict(range_xyz_m=[lo.tolist(),hi.tolist()],mask_local_m=list(footprint.exterior.coords),hit_triangles=len(cached),
                      foreign_hits=sum(i!=OWNER for i in observed_owners),minimum_inter_owner_margin_m=min(margin),lowest_other_footprint_m=min(o['distance_m']for o in peers),
                      preserved_above_band=len(above),native_top_m=float(max(heights)),retained_outside_mask_m2=src.difference(footprint).area,
                      fraction_retained_outside_mask=src.difference(footprint).area/src.area,neighbors=peers))
        results[variant]=dict(source_triangles=len(arr),heights=outputs,attribution='explicit far feature indices' if typed is not None else 'nearest of all six source rings with per-hit margin')
    write(out,dict(id=ID,passed=True,source_review_sha256=sha(source/'footprint-review.json'),source_check_sha256=sha(Path(__file__)),source_levels=results,
                   check='3D polygon clipping against six planes per window, signed height limits and individual near/far original triangles.'))
if __name__=='__main__':
    parser=ArgumentParser(description=__doc__);parser.add_argument('--work',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    main(args.work,args.out)
