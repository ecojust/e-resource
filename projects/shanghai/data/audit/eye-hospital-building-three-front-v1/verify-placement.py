"""Register the southwest three-storey courtyard bay against the two original city meshes."""
import argparse
from pathlib import Path
import sys,os
from contextlib import ExitStack

import numpy as np
import shapely as geo
from shapely.geometry import Point, Polygon, box, shape, MultiLineString

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

ID='jingan-eye-hospital-building-three-front'
OWNER=712


def line_segments(cut,outline):
    result=[]
    for line in geo.get_parts(geo.line_merge(cut.boundary.intersection(outline))):
        for a,b in zip(line.coords,list(line.coords)[1:]):
            if np.linalg.norm(np.asarray(a)-b)>.007:result.append([a,b])
    assert result
    return MultiLineString(result)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',required=True,type=Path)
    parser.add_argument('--work',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args();args.out.mkdir(exist_ok=True,parents=True)
    review_path=PROJECT/'source/precise'/ID/'footprint-review.json'
    review=read(review_path);site=PlacementMeshes(PROJECT,args.work,review)
    site.env['NODE_OPTIONS']=(site.env.get('NODE_OPTIONS','')+' --require='+str(HERE.parent/'mitsui-bussan-pediment-front-v1/decode-texture.cjs')).strip()
    assets,bounds,form,ground=site.decode_model(args.manifest)
    cut=box(-3.61,-2.71,3.355,2.755)
    assert cut.covers(form),form.difference(cut).area
    group,=review['near_tiles']
    with ExitStack() as scratch:
        for role in ('near','far'):
            for suffix in ('triangles.f64','owners.u32'):
                name=args.work/f'baseline-{role}-{suffix}'
                assert not name.exists() and not name.is_symlink()
                fd=os.memfd_create('eye315-source-triangles');scratch.callback(os.close,fd)
                name.symlink_to(f'/proc/{os.getpid()}/fd/{fd}');scratch.callback(name.unlink)
        original=site.decode_group(group,OWNER)
    surfaces={};seams={};tops={}
    for role,(own,other,assignment)in original.items():
        old=site.project_faces(own);remaining=old.difference(cut)
        touches=geo.intersects(cut,geo.polygons(own[:,:,:2]))
        other_shape=site.project_faces(other)
        distance=other_shape.distance(cut)
        kept=remaining.area/old.area
        assert .95<kept<.985 and distance>0,(role,kept,distance)
        assert np.count_nonzero(touches)>0 and cut.intersection(other_shape).is_empty
        tops[role]=float(own[touches,:,2].max())
        assert 16.95<tops[role]<17.05,(role,tops[role])
        seams[role]=line_segments(cut,old)
        surfaces[role]=dict(assignment=assignment,source_triangles=len(own),affected_source_triangles=int(touches.sum()),unchanged_other_group_triangles=len(other),other_source_distance_m=distance,source_projected_m2=old.area,retained_m2=remaining.area,retained_percent=100*kept,source_roof_m=tops[role],mask_seam_m=seams[role].length)
    agreement=seams['far'].hausdorff_distance(seams['near'])
    write(args.out/'original-cut-seams.json',dict(seams={k:[list(a.coords) for a in v.geoms]for k,v in seams.items()},agreement=agreement,source=surfaces))
    assert agreement<1.0 and abs(tops['near']-tops['far'])<.1,(agreement,tops)
    ready=read(site.files['READY.json'])
    caps=dict(geometry=site.wgs(seams['far']),base_m=0,roof_m=tops['far'],height_reference=[ready['origin_longitude'],ready['origin_latitude']],far_sha256=sha(site.files['far.glb']))
    neighbors=[]
    for j in review['selection']['checked_neighbors']:
        outline=site.footprints[j];d=outline.distance(cut)
        assert d>0
        record=next(f for f in review['owners']if f['local_id']==j)
        neighbors.append(dict(owner=j,source_distance_m=d,model_distance_m=outline.distance(form),mask_distance_m=d,remaining=True,center_wgs84=list(shape(record['geometry_wgs84']).representative_point().coords[0])))
    # Ground slices include the closed ground-floor breast, both piers and their short returns.
    # The score does not infer a walkable opening from the dark glass of a sash.
    collide=geo.make_valid(ground).simplify(.019,preserve_topology=True)
    assert collide.is_valid and not collide.is_empty and form.buffer(.04).covers(collide)
    source=site.footprints[OWNER];probes=[]
    def probe(name,x,y,inside,mapblocked):
        pt=Point(x,y);obstacle=collide.covers(pt);blocked=obstacle or (not cut.covers(pt) and source.covers(pt))
        assert (obstacle,blocked)==(inside,mapblocked),(name,x,y,obstacle,blocked)
        probes.append(dict(name=name,xy=[x,y],wgs84=site.to_wgs(np.array([[x,y]]))[0].tolist(),model_obstacle=obstacle,source_cut=cut.covers(pt),expected_map='building' if blocked else None))
    for x in [-4.2,-3.22,-2.45,-1.65,0,1.65,2.45,3.22,4.2,7.0,17.0]:
        probe('Open courtyard in front of the selected bay',x,-3.55,False,False)
    for x in [-3.12,-2.7,-1.9,-.8,0,.8,1.9,2.7,3.12]:
        probe('Solid interior strip of the southwest bay',x,1.52,True,True)
    for x,y in [(0,-1.9),(-.8,-1.6),(.8,-1.6),(-1.7,-1.1),(1.7,-1.1)]:
        probe('Closed curved window breast',x,y,True,True)
    for x,y in [(0,-2.52),(-1.65,-2.12),(1.65,-2.12),(-2.75,-1.1),(2.75,-1.1)]:
        probe('Public approach outside the planted bay',x,y,False,False)
    for x,y in [(-1,3.4),(0,4.5),(2.1,4.5),(4.5,1.5),(8.6,1.5),(15.4,2),(18.1,2),(21.5,2.5)]:
        probe('Retained central three bays, northeast bay or rear body',x,y,False,True)
    contract=dict(id=ID,owner=dict(macro_id=review['frozen_macro'],feature_local_id=OWNER),source_feature_ids={'building':[review['owner']['source_key'][9:]],'building_part':[]},replacement_geometry=site.wgs(cut),collision_geometry=site.wgs(collide),source_section_caps=caps,lng=site.lon,lat=site.lat,heading=review['author_frame']['runtime_heading_deg'],scale=1,altitude=0,model_geometry_sha256={k:v['sha256']for k,v in assets.items()},bounds_glb=bounds,overviewBearing=-34.8,overviewPitch=38.,overviewZoom=19.0,maxDistance=710,lod_switch_in_m=810,lod_switch_out_m=980,navigation={'listed':False,'status':'自南侧院落查看三号楼西南弧窗、曲栏、山墙和原位3号字。'},placement={'status':'map-aligned','note':'以712号底图的西南单窗轴配准，保留同院东北端、中央三开间、雨篷及其他建筑。'},partial_model=True,model_scope=read(args.manifest)['scope'])
    checked_geometry(contract['collision_geometry'],'closed hospital bay',collision=True);checked_geometry(contract['replacement_geometry'],'southwest hospital bay')
    result=dict(id=ID,manifest_sha256=sha(args.manifest),source_sha256=sha(review_path),checker_sha256=sha(Path(__file__)),mesh_decoder_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py'),assets=assets,model_projected_m2=form.area,collision_m2=collide.area,mask_m2=cut.area,source_variants=surfaces,seam_agreement_m=agreement,cap_segments=len(seams['far'].geoms),neighbors=neighbors,ground_probes=probes)
    write(args.out/'final-placement-contract.json',contract);write(args.out/'placement-geometry.json',result)
    print('Source meshes retained',[(k,v['retained_percent'])for k,v in surfaces.items()],'mask and model areas',cut.area,form.area,'seam agreement',agreement,'ground probes',len(probes),flush=True)

if __name__=='__main__':main()
