"""Check the retained V5 main building against the annex strip using the actual shipped surfaces."""
from argparse import ArgumentParser
import json
import mmap
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

import numpy as np
import shapely as geo
from shapely.geometry import box,shape

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha

def compare(file,site,origin,mask):
    # The published V5 package consists of one identity node and one mesh with per-material primitives.
    # Traverse every primitive, discard triangles with bounding boxes farther than the current minimum
    # and measure the rest against the annex's actual site cut. The rear and upper parts remain included.
    with file.open('rb') as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ) as raw:
        assert raw[:4]==b'glTF'
        length,kind=struct.unpack_from('<II',raw,12)
        assert kind==0x4e4f534a
        doc=json.loads(raw[20:20+length]);binary=28+length
        assert len(doc['nodes'])==len(doc['meshes'])==1 and set(doc['nodes'][0]).issubset({'name','mesh','extras'})
        offsets=site.to_xy(np.array([origin]))[0];mask_bounds=mask.bounds
        def accessor(key,count):
            a=doc['accessors'][key];v=doc['bufferViews'][a['bufferView']]
            fmt={5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
            dtype=np.dtype(fmt);size=dtype.itemsize;start=binary+v.get('byteOffset',0)+a.get('byteOffset',0)
            return np.ndarray((a['count'],count),dtype=dtype,buffer=raw,offset=start,strides=(v.get('byteStride',size*count),size)).copy()
        total=0;nearest=2.;tested=0;intersected=0;approx_area=0.
        for p in doc['meshes'][0]['primitives']:
            vertices=accessor(p['attributes']['POSITION'],3)[:,[0,2]].astype('f8')*[1,-1]
            v=vertices@site.axes.T+offsets
            t=v[accessor(p['indices'],1).reshape(-1,3)]
            total+=len(t);lo=t.min(1);hi=t.max(1)
            t=t[(hi[:,0]>=mask_bounds[0]-nearest)&(lo[:,0]<=mask_bounds[2]+nearest)&(hi[:,1]>=mask_bounds[1]-nearest)&(lo[:,1]<=mask_bounds[3]+nearest)]
            if not len(t):continue
            # A convex hull correctly represents the plan segment of a vertical wall as well as any triangular face.
            surfaces=geo.convex_hull(geo.multipoints(t));tested+=len(t)
            nearest=min(nearest,float(geo.distance(surfaces,mask).min()))
            hits=surfaces[geo.intersects(surfaces,mask)];intersected+=len(hits)
            if len(hits):approx_area+=float(geo.area(geo.intersection(geo.union_all(hits),mask)))
        assert tested>0 and total>10000
        return dict(triangles=total,triangles_in_search_neighborhood=tested,intersecting_triangles=intersected,
                    nearest_clipping_boundary_m=nearest,summed_per_material_overlap_m2=approx_area)

def main():
    cli=ArgumentParser(description=__doc__);cli.add_argument('--work',required=True,type=Path);cli.add_argument('--contract',type=Path,default=HERE/'final-placement-contract.json');cli.add_argument('--out',type=Path,default=HERE/'main-building-preservation.json')
    args=cli.parse_args();review=read(PROJECT/'source/precise/xuhui-wukang-mansion-east-annex/footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,review);contract=read(args.contract);mask=geo.transform(shape(contract['replacement_geometry']),site.to_xy)
    main=next(r for r in read(PROJECT/'data/landmarks.json')if r['id']=='xuhui-wukang-mansion')
    assert main['owner']['feature_local_id']==1235 and contract['owner']['feature_local_id']==320
    origin=main['anchor'];decoder=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
    rows={}
    for key in ['raw','web','lod']:
        a=main['assets'][key];f=PROJECT/a['file'];assert sha(f)==a['sha256'] and f.stat().st_size==a['bytes']
        if key!='raw':
            with tempfile.TemporaryDirectory(dir=args.work) as directory:
                dec=Path(directory)/'old.glb'
                subprocess.run(['node',decoder,f,dec,PROJECT/'vendor/meshopt_decoder.module.js'],check=True,stdout=subprocess.DEVNULL)
                stats=compare(dec,site,origin,mask)
        else:stats=compare(f,site,origin,mask)
        rows[key]=dict(sha256=a['sha256'],bytes=a['bytes'],**stats)
    result=dict(ordinary_model=main['id'],ordinary_owner=1235,annex_owner=320,main_anchor=origin,
                ordinary_public_assets=rows,contract_sha256=sha(args.contract),checker_sha256=sha(Path(__file__)),
                passed=all(v['intersecting_triangles']==0 for v in rows.values()))
    write(args.out,result);print(rows);assert result['passed']
if __name__=='__main__':main()
