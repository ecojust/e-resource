"""Disambiguate the unlabelled near triangles of the street block using far feature IDs and all near triangle vertices."""
import subprocess
from pathlib import Path
import numpy as np
import shapely
from candidate_placement_meshes import write


def house_meshes(ctx,group):
    owner=3240
    ids=group['feature_local_ids']
    ctx.link('baseline-far.glb',ctx.files['far.glb'])
    ctx.link('baseline-near.glb.gz',ctx.files[Path(group['file']).name])
    ctx.link('macro-READY.json',ctx.files['READY.json'])
    write(ctx.work/'context-features.json',[{'localId':i} for i in ids])
    subprocess.run(['node',ctx.decoders/'map-decode-source.mjs'],env=ctx.env,stdout=subprocess.DEVNULL,check=True)
    def triangles(role):
        tri=np.fromfile(ctx.work/('baseline-'+role+'-triangles.f64'),np.float64).reshape(-1,3,3)
        tri[:,:,:2]=tri[:,:,:2] @ ctx.axes.T
        return tri
    far=triangles('far')
    owners=np.fromfile(ctx.work/'baseline-far-owners.u32',np.uint32)
    assert set(owners.tolist())==set(ids)
    near=triangles('near')
    house=ctx.footprints[owner];peers=shapely.union_all([ctx.footprints[i]for i in ids if i!=owner])
    farhouse=ctx.project_faces(far[owners==owner]);farpeers=ctx.project_faces(far[owners!=owner])
    samples=np.concatenate((near[:,:,:2],near[:,:,:2].mean(1)[:,None]),axis=1)
    points=shapely.points(samples.reshape(-1,2))
    ds=shapely.distance(points,house).reshape(-1,4);others=shapely.distance(points,peers).reshape(-1,4)
    df=shapely.distance(points,farhouse).reshape(-1,4);fothers=shapely.distance(points,farpeers).reshape(-1,4)
    at_owner=ds[:,-1]<others[:,-1]
    # Independent distant ID surfaces must assign
    # every vertex and centroid identically, including the projecting near window surrounds.
    assert np.array_equal(ds<others,np.repeat(at_owner[:,None],4,axis=1))
    assert np.array_equal(df<fothers,np.repeat(at_owner[:,None],4,axis=1))
    own_edge=ds[at_owner].max();margin=(others-ds)[at_owner].min()
    assert own_edge<.25 and margin>1.0 and (~at_owner).any() and at_owner.any(),(own_edge,margin)
    proof={'method':'For each near triangle, all three vertices and centroid agree both with nearest frozen vector footprint and with the far surfaces decoded from per-vertex feature IDs.',
           'largest_own_vertex_or_centroid_distance_m':float(own_edge),'smallest_next_owner_margin_m':float(margin),
           'vector_gap_m':float(house.distance(peers)),'checked_near_points':int(samples.shape[0]*4)}
    return {'near':(near[at_owner],near[~at_owner],proof),
            'far':(far[owners==owner],far[owners!=owner],{'method':'per-vertex _FEATURE_ID_0'})}
