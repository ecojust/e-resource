"""Register the two street wings and protect the masonry adjoining the rear wall."""
import argparse
import math
from pathlib import Path
import subprocess
import sys

import numpy as np
import shapely as geo
from shapely.geometry import shape

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT / 'tools'))
from candidate_placement_meshes import PlacementMeshes, read, write, sha

ID = 'hongkou-new-asia-hotel'
OWNER = 3209
REAR = 123


def inspect_source(site, group, mask):
    ids = group['feature_local_ids']
    site.link('baseline-far.glb', site.files['far.glb'])
    site.link('baseline-near.glb.gz', site.files[Path(group['file']).name])
    site.link('macro-READY.json', site.files['READY.json'])
    write(site.work/'context-features.json', [{'localId': i} for i in ids])
    subprocess.run(['node', site.decoders/'map-decode-source.mjs'], env=site.env,
                   check=True, stdout=subprocess.DEVNULL)
    results = {}
    for variant in ['near', 'far']:
        tris = np.fromfile(site.work/f'baseline-{variant}-triangles.f64', np.float64).reshape(-1,3,3)
        tris[:, :, :2] = tris[:, :, :2] @ site.axes.T
        centroids = geo.points(tris[:, :, :2].mean(1))
        distances = np.stack([geo.distance(centroids, site.footprints[i]) for i in ids], axis=1)
        owners = np.asarray(ids)[distances.argmin(1)] if variant == 'near' else np.fromfile(site.work/'baseline-far-owners.u32', np.uint32)
        hotel = site.project_faces(tris[owners == OWNER])
        context = site.project_faces(tris[owners != OWNER])
        rear = site.project_faces(tris[owners == REAR])
        # Near GLBs have group-level IDs. Both adjacent buildings can have coplanar
        # wall triangles, so their shared edge cannot be classified from a centroid.
        # Include uncertain vertical faces (zero plan area) in a separate test.
        rear_index, hotel_index = ids.index(REAR), ids.index(OWNER)
        possible_shared_wall = ((distances[:,rear_index] < .12) &
                                (distances[:,hotel_index] < .12) &
                                (np.ptp(tris[:,:,2], axis=1) > .002))
        uncertain = tris[possible_shared_wall]
        lines = geo.linestrings(uncertain[:,:, :2])
        wall_clearance = float(geo.distance(lines, mask).min()) if len(lines) else None
        assert wall_clearance is None or wall_clearance > .13, (variant, wall_clearance)
        assert context.distance(mask) > .24 and mask.intersection(rear).area == 0
        residual = hotel.difference(mask)
        assert 42 < residual.area < 46
        results[variant] = dict(group=group['id'], group_owners=ids, source_faces=len(tris),
            hotel_assigned_faces=int(np.sum(owners==OWNER)), rear_assigned_faces=int(np.sum(owners==REAR)),
            assignment='group centroid and separate ambiguous shared-wall clearance' if variant=='near' else 'per-vertex _FEATURE_ID_0',
            all_neighbor_clearance_m=mask.distance(context), adjacent_roof_clearance_m=mask.distance(rear),
            potential_coplanar_faces=len(uncertain), potential_wall_clearance_m=wall_clearance,
            projected_hotel_m2=hotel.area, retained_rear_strip_m2=residual.area,
            retained_fraction=residual.area/hotel.area, rear_overlap_m2=mask.intersection(rear).area)
    return results


def inspect_vector(site, pbf, mask):
    import mapbox_vector_tile
    layer=mapbox_vector_tile.decode(pbf.read_bytes(),default_options={'y_coord_down':True})['building']
    extent=layer['extent']
    def to_local(points):
        x, y = points.T / extent
        lng=(13720+x)/16384*360-180
        lat=np.degrees(np.arctan(np.sinh(np.pi*(1-2*(6693+y)/16384))))
        return site.to_xy(np.column_stack((lng,lat)))
    result=[]
    for item in layer['features']:
        poly=geo.transform(shape(item['geometry']),to_local)
        if poly.distance(mask)>16:
            continue
        overlap=poly.intersection(mask).area
        result.append(dict(id=item['id'],height_m=item['properties'].get('render_height'),
            before_m2=poly.area,cut_m2=overlap,remaining_m2=poly.area-overlap))
    merged=next(row for row in result if row['id']==116367720)
    assert merged['remaining_m2']>19800 and 2400<merged['cut_m2']<2550
    post=next(row for row in result if row['id']==116293700)
    assert post['cut_m2']==0
    return result


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--work',type=Path,required=True)
    cli.add_argument('--pbf',type=Path,required=True)
    cli.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    cli.add_argument('--out',type=Path,default=Path(__file__).resolve().parent)
    args=cli.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    src=PROJECT/'source/precise'/ID
    review=read(src/'footprint-review.json')
    manifest=args.manifest
    site=PlacementMeshes(PROJECT,args.work,review)
    assets,bounds,model,ground=site.decode_model(manifest)
    target=site.footprints[OWNER]
    peer=site.footprints[REAR]
    mask=target.buffer(.40,join_style='mitre').difference(peer.buffer(.35,join_style='mitre'))
    assert mask.geom_type=='Polygon' and mask.is_valid
    group=next(g for g in review['near_tiles'] if OWNER in g['feature_local_ids'])
    source_checks=inspect_source(site,group,mask)
    pbf_sha=sha(args.pbf)
    assert pbf_sha=='e6a2578dd38fdc6ef28737b68ea1e59181efe7d2fbde1d812f76f0a555833495'
    vector=inspect_vector(site,args.pbf,mask)
    print('Projected neighboring area',model.intersection(peer).area,ground.intersection(peer).area, flush=True)
    assert model.intersection(peer).area<.00001 and ground.intersection(peer).area<.00001
    # Main corner's recessed threshold. Derive its line independently from the five published facets.
    angle=1.225/2
    nx,ny=math.sin(angle),-math.cos(angle)
    door=np.array([46.298,12])+np.array([nx,ny])*12*math.cos(1.225/10)
    probe=lambda depth:geo.Point(door-depth*np.array([nx,ny]))
    # The stone threshold rises 7 cm. Check its entire entry strip at pedestrian
    # body height in three decoded files before removing only its low sill from collision.
    tangent=np.array([math.cos(angle),math.sin(angle)])
    normal=np.array([nx,ny])
    pocket=geo.Polygon([door+u*tangent-depth*normal for u,depth in
        [(-.94,-.015),(.94,-.015),(.94,.385),(-.94,.385)]])
    walk_proofs={}
    for role in ['raw','web','lod']:
        file=site.work/f'delivered-{role}-triangles.f64'
        t=np.fromfile(file,np.float64).reshape(-1,3,3)[:,:,[0,2,1]]*[1,-1,1]
        lo,hi=t.min(1),t.max(1);x0,y0,x1,y1=pocket.bounds
        near=t[(lo[:,0]<=x1)&(hi[:,0]>=x0)&(lo[:,1]<=y1)&(hi[:,1]>=y0)&(hi[:,2]>=.11)&(lo[:,2]<=1.85)]
        faces=[]
        for tri in near:
            vertices=list(tri)
            for level,above in [(.11,True),(1.85,False)]:
                clipped=[]
                for a,b in zip(vertices,vertices[1:]+vertices[:1]):
                    inside=(a[2]>=level) if above else (a[2]<=level)
                    if inside:clipped.append(a)
                    if min(a[2],b[2])<level<max(a[2],b[2]):
                        clipped.append(a+(b-a)*(level-a[2])/(b[2]-a[2]))
                vertices=clipped
            if len(vertices)>=3:
                coords=[point[:2] for point in vertices]
                h=geo.Polygon(coords)
                if h.area>1e-10:faces.append(h)
                else:faces.append(geo.LineString(coords))
        occupied=geo.union_all(faces)
        assert occupied.disjoint(pocket), (role,occupied.intersection(pocket).wkt[:320])
        walk_proofs[role]=dict(checked_triangles=len(near),clear_m=occupied.distance(pocket))
    ground=ground.difference(pocket)
    # Separately extruded 12 mm mortar joints lie millimetres from the bonded
    # wall. Use the connected podium for pedestrian collision. Retain and bound
    # the discarded geometric detail quantitatively in the audit.
    aggregate=ground
    parts=sorted(geo.get_parts(aggregate),key=lambda part:-part.area)
    ground=parts[0]
    extras=parts[1:]
    farthest=max(float(geo.distance(geo.points(geo.get_coordinates(q)),ground).max()) for q in extras)
    omission=dict(components=len(extras),total_m2=aggregate.area-ground.area,
                  largest_component_m2=max(q.area for q in extras),furthest_vertex_from_body_m=farthest)
    assert omission['total_m2']<.6 and omission['largest_component_m2']<.03 and farthest<.05
    assert target.contains(probe(.28)) and mask.contains(probe(.28))
    assert not ground.intersects(probe(.28)) and ground.contains(probe(.75))
    neighbors=sorted((poly.distance(mask),i) for i,poly in site.footprints.items() if i!=OWNER)
    actual_peers=[dict(local_id=i,mask_clearance_m=d,collision_overlap_m2=ground.intersection(site.footprints[i]).area,
                       geometry_overlap_m2=model.intersection(site.footprints[i]).area) for d,i in neighbors[:8]]
    assert all(r['collision_overlap_m2']<.0001 and r['geometry_overlap_m2']<.0001 for r in actual_peers)
    source=next(r for r in review['owners'] if r['local_id']==OWNER)
    contract=dict(id=ID,owner=dict(macro_id=review['frozen_macro'],feature_local_id=OWNER),
        source_feature_ids=dict(building=[source['key'].removeprefix('building:')],building_part=[]),
        replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(ground),lng=site.lon,lat=site.lat,
        heading=review['author_frame']['runtime_heading_deg'],scale=1,altitude=0,
        bounds_glb=bounds,model_geometry_sha256={k:v['sha256'] for k,v in assets.items()},
        overviewBearing=298.86,overviewPitch=55,overviewZoom=18.33,maxDistance=650,
        lod_switch_in_m=660,lod_switch_out_m=820,navigation=dict(listed=False,status='沿天潼路看向四川北路街角的主入口。'),
        placement=dict(status='map-aligned',note='按具名道路、三期航片和单体3209的街墙定位；后方共墙内保留窄边，邻栋123与上海邮政总局独立。'),
        partial_model=True,model_scope=read(manifest)['scope'])
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(manifest),assets=assets,
        geometry_m2=model.area,collision_m2=ground.area,source_area_m2=target.area,mask_area_m2=mask.area,
        source_checks=source_checks,neighbor_clearances=actual_peers,door_line_center_xy_m=door.tolist(),
        subcentimetric_masonry_joints=omission,threshold=dict(sill_height_m=.07,checked_height_range_m=[.11,1.85],walkable_pocket_xy=list(pocket.exterior.coords),results=walk_proofs),
        outside_door_xy_m=list(probe(.28).coords[0]),inside_door_xy_m=list(probe(.75).coords[0]),
        fallback=dict(url='https://tiles.openfreemap.org/planet/20261115_080022_pt/14/13720/6693.pbf',
            sha256=pbf_sha,features=vector),checker_sha256=sha(Path(__file__)),
        shared_checker_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py')))
    print('Projected survey surfaces, site polygon and threshold verified',flush=True)

if __name__=='__main__':
    main()
