"""Build two source-scoped cuts for the north block and its connecting roof.

Run with the production manifest and a scratch directory outside Git. Inputs are
read from the exact Git revision bound by the north block footprint review.
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess

import numpy as np
import shapely as geo
from shapely.geometry import box, mapping, shape

MODEL = 'jingan-country-hospital-north-block'


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--manifest', type=Path, required=True)
    cli.add_argument('--work', type=Path, required=True)
    cli.add_argument('--out', type=Path, default=Path(__file__).resolve().parent)
    args = cli.parse_args()
    audit = Path(__file__).resolve().parent
    project = audit.parents[2]
    repo = project.parents[1]
    work = args.work.resolve()
    work.mkdir(exist_ok=True, parents=True)
    args.out.mkdir(exist_ok=True, parents=True)
    source_path = project / 'source/precise' / MODEL / 'footprint-review.json'
    src = read(source_path)
    pose = src['author_frame']
    lon, lat = pose['anchor']['lng'], pose['anchor']['lat']
    c, s = math.cos(math.radians(15)), math.sin(math.radians(15))
    axes = np.array([[-c,-s],[s,-c]])
    k = 6371008.8 * math.cos(math.radians(lat))
    loglat = math.asinh(math.tan(math.radians(lat)))
    def to_xy(points):
        east = np.radians(points[:,0]-lon)*k
        north = (np.arcsinh(np.tan(np.radians(points[:,1])))-loglat)*k
        return np.column_stack((east,north)) @ axes.T
    def to_wgs(points):
        east, north = (points @ axes).T
        return np.column_stack((lon+np.degrees(east/k),
            np.degrees(np.arctan(np.sinh(loglat+north/k)))))
    def wgs(poly):
        return mapping(geo.transform(poly, to_wgs))

    tools = project/'data/audit/postal-office-v1'
    garden = project/'data/audit/country-hospital-v1/verify-placement.py'
    loader = importlib.util.spec_from_file_location('garden_mesh_qa',garden)
    helpers = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(helpers)
    decoders = [tools/'map-decode-delivered.mjs',tools/'map-decode-source.mjs']
    import os
    env=dict(os.environ, POSTAL_REPO=str(repo), POSTAL_MAPPING_WORK=str(work), POSTAL_ASSET_PREFIX='')
    manifest = read(args.manifest)
    assert manifest['id']==MODEL
    assets = {}
    for role, variant in [('raw','raw'),('full','web'),('lod','lod')]:
        asset=manifest['assets'][role]
        file=(args.manifest.parent/asset['file']).resolve()
        assert file.stat().st_size==asset['bytes'] and sha(file)==asset['sha256']
        link=work/(variant+'.glb')
        link.unlink(missing_ok=True)
        link.symlink_to(file)
        assets[variant]={k:asset[k] for k in ('bytes','sha256','triangles')}
    subprocess.run(['node',decoders[0],work],env=env,check=True,stdout=subprocess.DEVNULL)
    bounds,profiles,ground=[],[],[]
    for receipt in read(work/'delivered-decode.json'):
        triangles=np.fromfile(receipt['triangle_file'],np.float64).reshape(-1,3,3)
        assert len(triangles)==assets[receipt['variant']]['triangles'] and np.isfinite(triangles).all()
        bounds.append([triangles.min((0,1)),triangles.max((0,1))])
        local=triangles[:,:,[0,2,1]] * [1,-1,1]
        profiles.append(helpers.project_triangles(local))
        ground.append(helpers.ground_projection(local))
    model=geo.union_all(profiles)
    collision=geo.union_all(ground,grid_size=.001).simplify(.025, preserve_topology=True)
    assert collision.is_valid and not collision.is_empty
    b=np.array(bounds)
    # The long coarse block continues east of the documented north bar.
    # The alley behind the main wing is open in the dated overhead views.
    # The separate cut at the other owner follows only the stem connection.
    parts = {row['local_id']:row for row in src['owners']}
    stems=src['model_envelopes']['central_link_envelope']['xy_limits_m']
    cuts={848:box(model.bounds[0]-.015,-4,16.6,20),
          2764:box(stems[0]-.18,24,stems[2]+.18,model.bounds[3]+.015)}
    files={}
    for entry in src['frozen_bindings']:
        p=entry['repository_path']
        file=work/Path(p).name
        if not file.exists() or sha(file)!=entry['sha256']:
            file.write_bytes(subprocess.check_output(['git','show',src['baseline_commit']+':'+p],cwd=repo))
        assert file.stat().st_size==entry['bytes'] and sha(file)==entry['sha256']
        files[Path(p).name]=file
    table=json.loads(gzip.decompress(files['feature-table.json.gz'].read_bytes()))
    rows={r['localId']:r for r in table['features']}
    polygons={i:geo.transform(shape(r['geometry']),to_xy) for i,r in rows.items()
              if shape(r['geometry']).distance(geo.Point(lon,lat))<.003}
    ready=read(files['READY.json'])
    data={}; contracts={}
    for local_id,clip in cuts.items():
        row=parts[local_id]
        grp=next(n for n in src['near_tiles'] if local_id in n['feature_local_ids'])
        ids=grp['feature_local_ids']
        distant=files['far.glb']; near=files[Path(grp['file']).name]
        for name,target in [('baseline-near.glb.gz',near),('baseline-far.glb',distant),('macro-READY.json',files['READY.json'])]:
            link=work/name
            link.unlink(missing_ok=True)
            link.symlink_to(target)
        write(work/'initial-local-frame.json',{'anchor':pose['anchor']})
        write(work/'context-features.json',[{'localId':i}for i in ids])
        subprocess.run(['node',decoders[1]],env=env,check=True,stdout=subprocess.DEVNULL)
        variants={}; seams={}
        for variant in ('near','far'):
            tris=np.fromfile(work/('baseline-'+variant+'-triangles.f64'),np.float64).reshape(-1,3,3)
            tris[:,:,:2]=tris[:,:,:2] @ axes.T
            if variant=='far':
                owners=np.fromfile(work/'baseline-far-owners.u32',np.uint32)
            else:
                points=geo.points(tris[:,:,:2].mean(axis=1))
                distances=np.stack([geo.distance(points,geo.transform(shape(rows[i]['geometry']),to_xy))for i in ids],axis=1)
                owners=np.asarray(ids)[distances.argmin(axis=1)]
                target_d=np.sort(distances[owners==local_id],axis=1)
                assert target_d[:,0].max()<.3 and (target_d[:,1]-target_d[:,0]).min()>2
            target=tris[owners==local_id]; others=tris[owners!=local_id]
            assert set(owners)==set(ids)
            profile=helpers.project_triangles(target); neighbors=helpers.project_triangles(others)
            assert clip.disjoint(neighbors),('shared neighbor',local_id,variant)
            projected=model.intersection(profile)
            assert projected.difference(clip).area<.001,(local_id,variant,projected.difference(clip).area)
            seam=geo.line_merge(clip.boundary.intersection(profile)).simplify(.001)
            assert seam.geom_type=='LineString' and not seam.is_ring,(local_id,variant,seam.geom_type)
            seams[variant]=seam
            variants[variant]={'source_area_m2':profile.area,'cut_m2':clip.intersection(profile).area,
               'retained_m2':profile.difference(clip).area,'other_group_owner_ids':[i for i in ids if i!=local_id],
               'other_near_far_clearance_m':clip.distance(neighbors),'other_owner_overlap_m2':0,
               'all_model_overlap_with_target_covered':True,'highest_source_vertex_m':float(target[:,:,2].max()),
               'input_file':grp['file'] if variant=='near' else 'far.glb'}
        other_source_distance=min(clip.distance(p) for i,p in polygons.items() if i!=local_id)
        assert other_source_distance>.35,(local_id,other_source_distance)
        assert abs(variants['near']['highest_source_vertex_m']-variants['far']['highest_source_vertex_m'])<.03
        assert seams['far'].hausdorff_distance(seams['near'])<.2
        cap={'geometry':wgs(geo.MultiLineString([seams['far']])), 'base_m':0,
             'roof_m':variants['far']['highest_source_vertex_m'],'height_reference':[ready['origin_longitude'],ready['origin_latitude']],
             'far_sha256':sha(distant)}
        contracts[local_id]={'owner':{'macro_id':src['frozen_macro'],'feature_local_id':local_id},
          'source_feature_ids':{'building':[row['key'].split(':')[1]],'building_part':[]},
          'geometry':wgs(clip),'source_section_caps':cap}
        data[local_id]={'near_group':grp,'original_bytes':{'far':sha(distant),'near':sha(near)},
          'variants':variants,'seam_segments':len(seams['far'].coords)-1,'other_source_footprint_clearance_m':other_source_distance,
          'nominal_mask_xy_bounds_m':clip.bounds}
    garden_row=next(i for i in read(project/'data/candidate-city-integrations.json')['models']if i['id']=='jingan-country-hospital')
    old=geo.transform(shape(garden_row['replacement_geometry']),to_xy)
    assert all(mask.disjoint(old)for mask in cuts.values())
    base=contracts[848]; mask=base.pop('geometry')
    stem_id=MODEL+'-spine'
    contract={'id':MODEL,**base,'replacement_geometry':mask,'site_replacement':{'id':stem_id,**contracts[2764]},
     'lng':lon,'lat':lat,'heading':165,'scale':1,'altitude':0,
     'bounds_glb':{'min':b[:,0].min(0).tolist(),'max':b[:,1].max(0).tolist()},
     'collision_geometry':wgs(collision),'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},
     'overviewBearing':165,'overviewPitch':58,'overviewZoom':18.5,'maxDistance':480,'lod_switch_in_m':550,'lod_switch_out_m':700,
     'navigation':{'listed':False,'status':'历史北横翼及中间连接体外观俯瞰。'},
     'placement':{'status':'estimated','note':'两支地图源按已见范围分别裁剪；北体东侧余段、连接体南侧余段和邻楼保留。'},
     'partial_model':True,'model_scope':'宏恩医院历史工字建筑的北横翼和中央连接体外观；南翼花园立面沿用既有入口，南翼其他外墙不计入本栋。'}
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',{'id':MODEL,'model_variants':assets,'model_xy_bounds_m':model.bounds,
          'collision_m2':collision.area,'source_geometry':data,'distance_from_existing_garden_cut_m':min(c.distance(old)for c in cuts.values()),
          'method':'All variants decoded with the repository GLTFLoader. Ground projection below 2m, with triangle-edge intersections. Near triangle IDs inferred from their actual tile member footprints, far IDs read from vertex attribute. Source cap seams are intersections with actual far roof projections. The two rectangular cuts consume four shader triangles.',
          'script_sha256':sha(Path(__file__)),'decoder_sha256':{str(f.relative_to(project)):sha(f)for f in decoders+[garden]},
          'footprint_review_sha256':sha(source_path),'contract_sha256':sha(args.out/'final-placement-contract.json')})
    print('verified',MODEL,data[848]['seam_segments'],data[2764]['seam_segments'])


if __name__=='__main__':
    main()
