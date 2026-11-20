"""Fit the freestanding tower and short linking arcade to part of source 616."""
import argparse
from pathlib import Path
import subprocess
import sys

import numpy as np
import shapely as geo

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tools'))
from candidate_placement_meshes import PlacementMeshes, read, write, sha


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--out',type=Path,default=Path(__file__).resolve().parent)
    args=parser.parse_args()
    project=Path(__file__).resolve().parents[3]
    model_id='huangpu-holy-trinity-bell-tower'
    doc=read(project/'source/precise'/model_id/'footprint-review.json')
    site=PlacementMeshes(project,args.work,doc)
    assets,bounds,model,ground=site.decode_model(args.manifest)
    projected_ground = ground.area
    structural = []
    for f in read(site.work/'delivered-decode.json'):
        positions=np.fromfile(f['triangle_file'],np.float64).reshape(-1,3,3)[:, :, [0,2,1]]*[1,-1,1]
        materials=np.fromfile(f['triangle_material_ids_file'],np.uint16)
        pavement=f['material_names'].index('porch pavement')
        structural.append(site.ground_faces(positions[materials!=pavement]))
    ground=geo.union_all(structural,grid_size=.001).simplify(.022,preserve_topology=True)
    assert ground.contains(geo.Point(0,0)), 'Tower floor must remain blocked'
    assert ground.disjoint(geo.Point(-7.5,-.9)), 'Arcade floor must stay open'
    owner=616
    group=next(g for g in doc['near_tiles'] if owner in g['feature_local_ids'])
    ids=group['feature_local_ids']
    source=site.footprints[owner]
    assert source.contains(geo.Point(0,0)) and source.area>140
    # The church connects across open ground. Clip only a transverse section
    # of 616 at the tower, retaining its two longer ends and the tall north school.
    lo_x,lo_y,hi_x,hi_y=source.bounds
    mask=geo.box(lo_x-.20,model.bounds[1]-.055,hi_x+.20,model.bounds[3]+.055)
    assert model.bounds[1]>lo_y and model.bounds[3]<hi_y
    assert source.difference(mask).geom_type=='MultiPolygon'
    site.link('baseline-far.glb',site.files['far.glb'])
    site.link('baseline-near.glb.gz',site.files[Path(group['file']).name])
    site.link('macro-READY.json',site.files['READY.json'])
    write(site.work/'context-features.json',[{'localId':i}for i in ids])
    subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,stdout=subprocess.DEVNULL)
    results={}; seams={}; tops={}
    for variant in ('near','far'):
        tris=np.fromfile(site.work/('baseline-'+variant+'-triangles.f64'),np.float64).reshape(-1,3,3)
        tris[:,:,:2]=tris[:,:,:2]@site.axes.T
        if variant=='far':
            owners=np.fromfile(site.work/'baseline-far-owners.u32',np.uint32)
            assignment={'method':'per-vertex _FEATURE_ID_0'}
        else:
            points=geo.points(tris[:,:,:2].mean(1))
            distances=np.stack([geo.distance(points,site.footprints[i])for i in ids],axis=1)
            owners=np.asarray(ids)[distances.argmin(1)]
            near=np.sort(distances[owners==owner],axis=1)
            # The eastern corner of 616 is close to another building, well
            # outside the cut. Report the weaker whole-group separation as well.
            region=geo.intersects(mask.buffer(.5),geo.points(tris[owners==owner,:,:2].mean(1)))
            margins=near[:,1]-near[:,0]
            assert near[:,0].max()<.18 and margins.min()>.13 and margins[region].min()>2.0
            assignment={'method':'nearest source polygon within the verified group',
                'largest_own_distance_m':float(near[:,0].max()),'all_target_margin_m':float(margins.min()),
                'margin_inside_or_within_0_5m_of_cut_m':float(margins[region].min())}
        target=tris[owners==owner];others=tris[owners!=owner]
        projected=site.project_faces(target);neighbors=site.project_faces(others)
        assert mask.disjoint(neighbors),variant
        assert model.intersection(projected).difference(mask).area<.0001
        retained=projected.difference(mask)
        assert retained.area>.40*projected.area and retained.geom_type=='MultiPolygon'
        seam=geo.line_merge(mask.boundary.intersection(projected)).simplify(.001)
        assert seam.geom_type=='MultiLineString' and len(seam.geoms)==2 and not any(s.is_ring for s in seam.geoms)
        seams[variant]=seam;tops[variant]=float(target[:,:,2].max())
        results[variant]={'target_triangles':len(target),'other_triangles':len(others),'assignment':assignment,
            'original_source_projection_m2':projected.area,'retained_source_m2':retained.area,
            'retained_percent':100*retained.area/projected.area,'cut_m2':projected.intersection(mask).area,
            'cut_to_nearest_other_decoded_geometry_m':mask.distance(neighbors),'other_owner_cut_m2':0,
            'source_native_roof_m':tops[variant]}
    assert seams['near'].hausdorff_distance(seams['far'])<.2
    assert abs(tops['far']-tops['near'])<.03
    nearest=min((mask.distance(poly),key)for key,poly in site.footprints.items()if key!=owner)
    assert nearest[0]>1
    ready=read(site.files['READY.json'])
    ident={'macro_id':doc['frozen_macro'],'feature_local_id':owner}
    source_row=next(r for r in doc['owners']if r['local_id']==owner)
    contract={'id':model_id,'owner':ident,'source_feature_ids':{'building':[source_row['key'][9:]],'building_part':[]},
        'replacement_geometry':site.wgs(mask),'source_section_caps':{'geometry':site.wgs(seams['far']),
            'base_m':0,'roof_m':tops['far'],'height_reference':[ready['origin_longitude'],ready['origin_latitude']],
            'far_sha256':sha(site.files['far.glb'])},
        'lng':site.lon,'lat':site.lat,'heading':doc['author_frame']['runtime_heading_deg'],'scale':1,'altitude':0,
        'bounds_glb':bounds,'collision_geometry':site.wgs(ground),
        'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},
        'overviewBearing':315,'overviewPitch':22,'overviewZoom':18.6,
        'maxDistance':520,'lod_switch_in_m':590,'lod_switch_out_m':750,
        'navigation':{'listed':False,'status':'钟塔与连接廊外观俯瞰。'},
        'placement':{'status':'estimated','note':'塔与主堂独立锚定；原616长体两端保留，切口按原屋顶高度补面。'},
        'partial_model':True,'model_scope':read(args.manifest)['scope']}
    args.out.mkdir(exist_ok=True,parents=True)
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',{'id':model_id,'manifest_sha256':sha(args.manifest),'assets':assets,
        'group':group,'owner':owner,'ground_m2':ground.area,'ground_projection_before_pavement_exclusion_m2':projected_ground,
        'ground_method':'逐档剔除独立廊道的可行走铺地，仅投影两米以下的砌体、栏墩与塔内封闭地板。','model_projection_m2':model.area,
        'source_checks':results,'source_cap_segments':sum(len(s.coords)-1 for s in seams['far'].geoms),
        'nearest_other_vector_geometry':{'local_id':nearest[1],'clearance_m':nearest[0]},
        'checker_sha256':sha(Path(__file__)),'shared_checker_sha256':sha(project/'tools/candidate_placement_meshes.py')})


if __name__=='__main__':
    main()
