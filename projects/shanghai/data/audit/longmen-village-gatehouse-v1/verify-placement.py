"""Read three gate meshes, their actual open archway and all nearby original city meshes."""
from argparse import ArgumentParser
from pathlib import Path
import runpy
import subprocess
import sys
import numpy as np
import shapely as geo
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
section=runpy.run_path(str(PROJECT/'data/audit/sino-french-school-v1/verify-placement.py'))['solid_section']
ID='huangpu-longmen-village-gatehouse'

def native_clearance(site,ref,roof_envelope):
    results=[]
    for group in ref['near_tiles']:
        site.link('baseline-far.glb',site.files['far.glb'])
        site.link('baseline-near.glb.gz',site.files[Path(group['file']).name])
        site.link('macro-READY.json',site.files['READY.json'])
        write(site.work/'context-features.json',[{'localId':n}for n in group['feature_local_ids']])
        subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,stdout=subprocess.DEVNULL)
        for variant in ('near','far'):
            tris=np.fromfile(site.work/f'baseline-{variant}-triangles.f64',np.float64).reshape(-1,3,3)
            xy=tris[:,:,:2]@site.axes.T
            near=(xy[:,:,0].max(1)>-35)&(xy[:,:,0].min(1)<35)&(xy[:,:,1].max(1)>-35)&(xy[:,:,1].min(1)<35)
            local=xy[near]
            assert len(local)>0
            footprints=geo.convex_hull(geo.multipoints(local))
            distance=float(geo.distance(footprints,roof_envelope).min())
            assert distance>.12,(ref['frozen_macro'],group['id'],variant,distance)
            results.append(dict(macro=ref['frozen_macro'],group=group['id'],variant=variant,
                original_triangles=len(tris),window_triangles=len(local),nearest_projected_triangle_m=distance,
                clipped_original_triangles=0))
    return results

def walking_samples():
    points=[]
    for y in [-1.20,.10,1.03,2.07,3.15,4.04,4.68]:
        for x in [-1.64,-.79,.06,.79,1.64]:
            points.append(dict(name=f'open passage {x},{y}',x=x,y=y,blocked=False))
    for x in [-2.83,-2.16,2.16,2.83]:
        for y in [.14,2.07,3.98]:
            points.append(dict(name=f'side pier {x},{y}',x=x,y=y,blocked=True))
    for x in [-2.62,2.62,-3.42,3.42]:
        points.append(dict(name=f'street pavement {x}',x=x,y=-.63,blocked=False))
    return points

def main():
    cli=ArgumentParser(description=__doc__)
    cli.add_argument('--manifest',required=True,type=Path)
    cli.add_argument('--work',required=True,type=Path)
    cli.add_argument('--out',default=HERE,type=Path)
    args=cli.parse_args();args.out.mkdir(exist_ok=True,parents=True)
    ref=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,ref)
    decoder=HERE.parent/'mitsui-bussan-pediment-front-v1/decode-texture.cjs'
    site.env['NODE_OPTIONS']=(site.env.get('NODE_OPTIONS','')+' --require='+str(decoder)).strip()
    assets,bounds,projected,low=site.decode_model(args.manifest)
    samples=walking_samples()
    slices=[]
    for row in read(site.work/'delivered-decode.json'):
        tri=np.fromfile(row['triangle_file'],np.float64).reshape(-1,3,3)[:,:,[0,2,1]]*[1,-1,1]
        for z in [.313,1.711]:
            cross=section(tri,z).simplify(.001)
            assert cross.geom_type=='MultiPolygon' and len(cross.geoms)==2,(row['variant'],cross)
            for p in samples:assert cross.covers(geo.Point(p['x'],p['y']))==p['blocked'],(row['variant'],z,p)
            slices.append(cross)
    collision=geo.union_all(slices,grid_size=.0001).simplify(.002,preserve_topology=True)
    for p in samples:assert collision.covers(geo.Point(p['x'],p['y']))==p['blocked'],p
    native=native_clearance(site,ref,projected)
    adj={**ref,**ref['adjacent_macro']}
    second=PlacementMeshes(PROJECT,args.work/adj['frozen_macro'],adj)
    native.extend(native_clearance(second,adj,projected))
    neighbors=[]
    for context,rg in [(site,ref),(second,adj)]:
        for n in rg['closest_neighbors']:
            d=float(projected.distance(context.footprints[n]))
            assert d>.12,(n,d)
            neighbors.append(dict(macro=rg['frozen_macro'],local_id=n,closest_distance_m=d))
    manifest=read(args.manifest)
    contract=dict(id=ID,replacement_geometry=None,source_feature_ids={'building':[],'building_part':[]},
        collision_geometry=site.wgs(collision),lng=site.lon,lat=site.lat,altitude=0,scale=1,
        heading=ref['author_frame']['runtime_heading_deg'],bounds_glb=bounds,model_geometry_sha256={k:v['sha256']for k,v in assets.items()},
        overviewBearing=ref['author_frame']['runtime_heading_deg'],overviewPitch=43,overviewZoom=20.75,
        maxDistance=440,lod_switch_in_m=202,lod_switch_out_m=285,partial_model=True,model_scope=manifest['model_scope_zh'],
        navigation={'listed':False,'status':'从尚文路进入133弄，可穿过过街楼下的拱洞。'},
        placement={'status':'estimated','note':'以南门公开地图点和2017年带相机朝向的街照定位，沿尚文路排布。过街楼单独加入，邻屋和弄内各房保持原状。'})
    checked_geometry(contract['collision_geometry'],ID,collision=True)
    assert bounds['min'][0]<-3.7 and bounds['max'][0]>3.7 and bounds['max'][1]>15.3, bounds
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(args.manifest),checker_sha256=sha(Path(__file__)),
        assets=assets,collision_cross_section_m=[.313,1.711],collision_m2=collision.area,ground_samples=samples,
        source_mesh_clearance=native,neighbor_polygons=neighbors,source_clipped_triangles=0,source_feature_ids=[],
        city_source_decoding_inputs=ref['frozen_bindings']+adj['frozen_bindings']))
    print('Original triangle checks',native,'ground probes',len(samples),'collision',collision.area,flush=True)
if __name__=='__main__':main()
