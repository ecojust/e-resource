"""Measure the selected part of the named main compound and preserve its southern range."""
from argparse import ArgumentParser
from pathlib import Path
import runpy,subprocess,sys
import numpy as np
import shapely as geo
from shapely.geometry import MultiLineString

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
ID='huangpu-cixiu-nunnery-courtyard'
OWNER=448
solid_section=runpy.run_path(str(PROJECT/'data/audit/sino-french-school-v1/verify-placement.py'))['solid_section']


def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',required=True,type=Path)
    parser.add_argument('--work',required=True,type=Path)
    parser.add_argument('--out',default=HERE,type=Path)
    opts=parser.parse_args();opts.out.mkdir(parents=True,exist_ok=True)
    ref=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,opts.work,ref)
    assets,bounds,projection,_=site.decode_model(opts.manifest)
    source=site.footprints[OWNER]
    cut=geo.box(-7.78,-9.02,7.40,6.78)
    assert cut.covers(projection)
    interior=geo.union_all([geo.box(-6.84,1.22,7.15,6.05),geo.box(-6.84,-8.8,-5.78,.14),geo.box(5.78,-8.8,7.15,.14)])
    areas=[]
    for result in read(site.work/'delivered-decode.json'):
        triangles=np.fromfile(result['triangle_file'],np.float64).reshape(-1,3,3)[:,:,[0,2,1]]*[1,-1,1]
        areas.append(solid_section(triangles,.40))
    # Small window/door moulding gaps join to the solid room. Spaces between posts,
    # the covered gallery and the paved main court remain accessible.
    collision=geo.union_all([interior,*areas],grid_size=.001).buffer(.022,join_style='mitre').buffer(-.022,join_style='mitre').simplify(.007)
    assert collision.is_valid
    group=next(item for item in ref['near_tiles']if OWNER in item['feature_local_ids'])
    ids=group['feature_local_ids']
    ready=read(site.files['READY.json'])
    site.link('baseline-far.glb',site.files['far.glb'])
    site.link('baseline-near.glb.gz',site.files[Path(group['file']).name])
    site.link('macro-READY.json',site.files['READY.json'])
    write(site.work/'context-features.json',[{'localId':i}for i in ids])
    subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,stdout=subprocess.DEVNULL)
    variants={};seams={};tops={}
    for key in ('near','far'):
        tris=np.fromfile(site.work/f'baseline-{key}-triangles.f64',np.float64).reshape(-1,3,3)
        tris[:,:,:2]=tris[:,:,:2]@site.axes.T
        if key=='far':
            owners=np.fromfile(site.work/'baseline-far-owners.u32',np.uint32)
            assignment='Original _FEATURE_ID_0.'
        else:
            pts=geo.points(tris[:,:,:2].mean(axis=1))
            distances=np.stack([geo.distance(pts,site.footprints[i])for i in ids],axis=1)
            owners=np.asarray(ids)[distances.argmin(axis=1)]
            ordered=np.sort(distances[owners==OWNER],axis=1)
            if len(ids)>1:assert (ordered[:,1]-ordered[:,0]).min()>1.5
            assert ordered[:,0].max()<.40
            assignment='Actual triangle centroids nearest the named source polygon in the near group.'
        selected,context=tris[owners==OWNER],tris[owners!=OWNER]
        projected=site.project_faces(selected)
        remaining=projected.difference(cut)
        affected=geo.intersects(cut,geo.polygons(selected[:,:,:2]))
        assert len(selected)>0 and affected.any()
        roofs=selected[affected,:,2].max();tops[key]=float(roofs)
        assert abs(roofs-6.4)<.1
        context_distance=site.project_faces(context).distance(cut)if len(context) else None
        assert context_distance is None or context_distance>2
        fraction=remaining.area/projected.area
        assert .52<fraction<.65
        seam=geo.line_merge(cut.boundary.intersection(projected)).simplify(.011)
        assert seam.geom_type=='LineString' and len(seam.coords)==3
        seams[key]=seam
        variants[key]=dict(assignment=assignment,group=group['id'],original_source_triangles=len(selected),affected_source_triangles=int(affected.sum()),original_source_m2=projected.area,retained_m2=remaining.area,retained_percent=100*fraction,source_roof_m=tops[key],other_group_triangles=len(context),cut_to_other_group_faces_m=context_distance)
    agreement=seams['near'].hausdorff_distance(seams['far']);assert agreement<.15
    coords=list(seams['far'].coords);cap=MultiLineString([[coords[i],coords[i+1]]for i in range(2)])
    caps=dict(geometry=site.wgs(cap),base_m=0,roof_m=tops['far'],height_reference=[ready['origin_longitude'],ready['origin_latitude']],far_sha256=sha(site.files['far.glb']))
    neighbor=[]
    for i in ref['registration']['screened_other_local_ids']:
        q=site.footprints[i];assert q.distance(cut)>3
        neighbor.append(dict(local_id=i,cut_distance_m=q.distance(cut),model_distance_m=q.distance(projection)))
    tests=[]
    for y in [-8.18,-6.55,-4.39,-2.28,-1.23,-.27]:
        for x in [-5.07,-3.68,0,3.69,5.05]:
            tests.append(('paving or covered passage',[x,y],False,False))
    for x in [-4.55,4.55]:
        for y in [-8.8,-5.86,-2.92,.02]:tests.append(('red gallery post',[x,y],True,True))
    for t in [('north porch before closed door',[.53,.58],False,False),('north hall',[.53,2.48],True,True),('west range room',[-6.23,-3],True,True),('east range room',[6.29,-3],True,True),('preserved source at south gate hall',[0,-13.2],False,True),('preserved eastern range',[9.5,-3],False,True)]:
        tests.append(t)
    cases=[]
    for label,pt,solid,blocked in tests:
        p=geo.Point(pt); actual=collision.covers(p);walk_block=actual or source.covers(p)and not cut.covers(p)
        assert actual==solid and walk_block==blocked,(label,pt,actual,walk_block)
        cases.append(dict(name=label,xy=pt,model_obstacle=actual,source_cut=cut.covers(p),expected_map='building'if blocked else None))
    own=next(r for r in ref['owners']if r['local_id']==OWNER)
    record=dict(id=ID,owner=dict(macro_id=ref['frozen_macro'],feature_local_id=OWNER),source_feature_ids=dict(building=[own['key'][9:]],building_part=[]),
                replacement_geometry=site.wgs(cut),collision_geometry=site.wgs(collision),source_section_caps=caps,
                lng=site.lon,lat=site.lat,heading=ref['author_frame']['runtime_heading_deg'],scale=1,altitude=0,
                bounds_glb=bounds,model_geometry_sha256={k:v['sha256']for k,v in assets.items()},
                overviewBearing=341.99733539,overviewPitch=38,overviewZoom=19.6,maxDistance=525,lod_switch_in_m=540,lod_switch_out_m=700,
                navigation=dict(listed=False,status='从正院南侧向北望见北殿及两厢木廊。'),
                placement=dict(status='map-aligned',note='榛岭街15号原主院内的北厅与向院侧木廊，保留448南殿和东侧余部，方浜中路593号另院独立。'),
                partial_model=True,model_scope=read(opts.manifest)['scope'])
    checked_geometry(record['replacement_geometry'],'replacement');checked_geometry(record['collision_geometry'],'collision',collision=True)
    write(opts.out/'final-placement-contract.json',record)
    write(opts.out/'placement-geometry.json',dict(id=ID,assets=assets,manifest_sha256=sha(opts.manifest),source_m2=source.area,model_projection_m2=projection.area,
                collision_m2=collision.area,cut_m2=cut.area,variants=variants,cap_segments=2,seam_agreement_m=agreement,neighbors=neighbor,ground_probes=cases,
                checker_sha256=sha(Path(__file__)),decoder_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py')))

if __name__=='__main__':main()
