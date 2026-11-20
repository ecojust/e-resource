"""Bind the south-facing part of the No. 93 rowhouse to its existing, shared terrace source."""
from argparse import ArgumentParser
from pathlib import Path
import subprocess
import sys

import numpy as np
import shapely as geo
from shapely.geometry import LineString, MultiLineString

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes, read, sha, write
from build_candidate_city_integrations import checked_geometry

ID='huangpu-feng-zikai-riyue-lou'
OWNER=1452


def cap_segments(mask,footprint):
    result=[]
    for a,b in zip(mask.exterior.coords,list(mask.exterior.coords)[1:]):
        segments=LineString([a,b]).intersection(footprint)
        for line in geo.get_parts(segments):
            if line.geom_type=='LineString' and line.length>.012:
                coordinates=list(line.coords)
                result.append([coordinates[0],coordinates[-1]])
    return MultiLineString(result)


def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',required=True,type=Path)
    parser.add_argument('--work',required=True,type=Path)
    parser.add_argument('--out',default=HERE,type=Path)
    a=parser.parse_args();a.out.mkdir(exist_ok=True,parents=True)
    ref=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,a.work,ref)
    assets,bounds,projection,ground=site.decode_model(a.manifest)
    cut=geo.box(-3.12,-2.35,3.12,5.24)
    assert cut.covers(projection)
    # The flat approach and short steps are walkable. The railing has horizontal
    # connecting bars; each side is one obstacle, while the middle opening remains free.
    doorhouse=geo.box(-3.025,-.025,3.025,5.17)
    left=geo.line_merge(MultiLineString([[(-2.70,-2.18),(-1.18,-2.18)],[(-1.18,-2.18),(-1.34,-1.13)]]))
    right=geo.line_merge(MultiLineString([[(2.70,-2.18),(1.18,-2.18)],[(1.18,-2.18),(1.34,-1.13)]]))
    collision=geo.union_all([doorhouse,left.buffer(.042,join_style='mitre',cap_style='flat'),
                             right.buffer(.042,join_style='mitre',cap_style='flat'),
                             LineString([(.85,-.81),(.85,-.10)]).buffer(.035,cap_style='flat')])
    assert cut.covers(collision)
    grp,=ref['near_tiles'];members=grp['feature_local_ids']
    assert OWNER in members
    ready=read(site.files['READY.json'])
    for alias,filename in [('baseline-far.glb','far.glb'),('baseline-near.glb.gz',Path(grp['file']).name),('macro-READY.json','READY.json')]:
        site.link(alias,site.files[filename])
    write(site.work/'context-features.json',[{'localId':i} for i in members])
    subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,stdout=subprocess.DEVNULL)
    variants={};seams={};heights={}
    for name in ('near','far'):
        ts=np.fromfile(site.work/f'baseline-{name}-triangles.f64',np.float64).reshape(-1,3,3)
        ts[:,:,:2]=ts[:,:,:2]@site.axes.T
        if name=='far':
            owners=np.fromfile(site.work/'baseline-far-owners.u32',np.uint32)
        else:
            samples=geo.points(ts[:,:,:2].mean(axis=1));dist=np.stack([geo.distance(samples,site.footprints[i])for i in members],axis=1)
            owners=np.asarray(members)[dist.argmin(axis=1)]
            values=np.sort(dist[owners==OWNER],axis=1)
            assert (values[:,1]-values[:,0]).min()>3 and values[:,0].max()<.60
        selected=ts[owners==OWNER];native=site.project_faces(selected);remainder=native.difference(cut)
        assert .92<remainder.area/native.area<.99
        affected=geo.intersects(geo.polygons(selected[:,:,:2]),cut)
        assert affected.any()
        heights[name]=float(selected[affected,:,2].max())
        assert 5<heights[name]<25
        others=ts[owners!=OWNER]
        close=others[(np.abs(others[:,:,:2].mean(axis=1))<65).all(axis=1)]
        peer_distance=site.project_faces(close).distance(cut)
        assert peer_distance>3
        seam=cap_segments(cut,native);assert len(seam.geoms)==3
        seams[name]=seam
        variants[name]=dict(native_triangles=len(selected),hit_triangles=int(affected.sum()),native_area_m2=native.area,
                            preserved_area_m2=remainder.area,preserved_fraction=remainder.area/native.area,
                            section_height_m=heights[name],neighbor_clearance_m=peer_distance)
    gap=seams['far'].hausdorff_distance(seams['near']);assert gap<.5
    caps={'geometry':site.wgs(seams['far']),'base_m':0,'roof_m':heights['far'],
          'height_reference':[ready['origin_longitude'],ready['origin_latitude']],'far_sha256':sha(site.files['far.glb'])}
    from shapely.geometry import shape
    assert shape(site.wgs(cut)).boundary.buffer(1e-8).covers(shape(caps['geometry']))
    probes=[]
    for label,xy,blocked in [('entrance path',[0,-2.18],False),('garden approach',[0,-1.35],False),('steps',[0,-.46],False),
                            ('left railing',[-1.96,-2.18],True),('right railing',[1.98,-2.18],True),('open gate leaf',[-1.26,-1.66],True),
                            ('closed door',[0,.20],True),('left room',[-2.24,1.38],True),('right room',[2.20,1.38],True),
                            ('upper room footprint',[0,4.53],True),('west household',[-5.40,2.],False),('back of row',[0,7.2],False)]:
        point=geo.Point(*xy);inside=collision.covers(point);assert inside==blocked
        kept=site.footprints[OWNER].covers(point) and not cut.covers(point)
        probes.append(dict(name=label,xy=xy,modelObstacle=inside,cut=cut.covers(point),expected='building'if inside or kept else None))
    owner,=(item for item in ref['owners'] if item['local_id']==OWNER);heading=ref['author_frame']['runtime_heading_deg']
    record=dict(id=ID,owner=dict(macro_id=ref['frozen_macro'],feature_local_id=OWNER),
                source_feature_ids=dict(building=[owner['key'].removeprefix('building:')],building_part=[]),
                replacement_geometry=site.wgs(cut),collision_geometry=site.wgs(collision),source_section_caps=caps,
                lng=site.lon,lat=site.lat,heading=heading,scale=1,altitude=0,bounds_glb=bounds,
                model_geometry_sha256={key:value['sha256'] for key,value in assets.items()},
                overviewBearing=heading,overviewPitch=48,overviewZoom=20.75,maxDistance=470,lod_switch_in_m=500,lod_switch_out_m=630,
                navigation=dict(listed=False,status='庭院正面展示93号与采光窗。'),placement=dict(status='estimated',note='具名93号地址点投影至整排1452朝南边界，保留其余住宅与本单元后段。'),partial_model=True,model_scope=read(a.manifest)['scope'])
    checked_geometry(record['collision_geometry'],'93 garden',collision=True)
    checked_geometry(record['replacement_geometry'],'93 front unit')
    write(a.out/'final-placement-contract.json',record)
    neighbors={}
    for i in ref['registration']['screened_other_local_ids']:
        poly=site.footprints[i];assert poly.distance(cut)>4
        pt=poly.representative_point();neighbors[str(i)]=list(site.to_wgs(np.array([[pt.x,pt.y]]))[0])
    write(a.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(a.manifest),source_sha256=sha(PROJECT/'source/precise'/ID/'footprint-review.json'),
          checker_sha256=sha(Path(__file__)),assets=assets,model_projection_m2=projection.area,collision_m2=collision.area,cut_m2=cut.area,
          variants=variants,cap_segments=3,cap_agreement_m=gap,ground_probes=probes,neighbor_points_wgs84=neighbors))
    print('Verified',variants,flush=True)

if __name__=='__main__':main()
