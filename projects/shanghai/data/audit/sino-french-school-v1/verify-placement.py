"""Check the actual teaching block, its open galleries and its two independent school neighbours."""
from argparse import ArgumentParser
from pathlib import Path
import sys
import numpy as np
import shapely as geo

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes, read, write, sha
from build_candidate_city_integrations import checked_geometry

ID = 'huangpu-sino-french-school-teaching-building'
OWNER = 1709
GALLERIES = [
    ('west recess',(-34.03,9.79),(-14.65,9.41),[.50,1.02,1.36,1.02,.50]),
    ('central court projection',(-7.330,.0255),(7.330,-.0255),[1,1.5,1]),
    ('east recess',(13.43,10.23),(34.65,10.05),[.50,1.02,1.36,1.02,.50]),
]


def gallery_floor_and_probes():
    areas,tests=[],[]
    for name,start,end,ratios in GALLERIES:
        a,b=np.array(start),np.array(end)
        span=np.linalg.norm(b-a)
        tang=(b-a)/span
        normal=np.array([-tang[1],tang[0]])
        def xy(u,depth):return a+u*tang+depth*normal
        areas.append(geo.Polygon([xy(0,-.9),xy(span,-.9),xy(span,2.82),xy(0,2.82)]))
        edges=np.r_[0,np.cumsum(ratios)/sum(ratios)]*span
        for i,(l,r) in enumerate(zip(edges,edges[1:])):
            u=(l+r)/2+.19
            for depth in (-.46,.52,1.75):
                tests.append((f'{name} opening {i+1} at {depth} m',xy(u,depth),False))
            tests.append((f'{name} room behind opening {i+1}',xy(u,3.08),True))
        for i,u in enumerate(edges[1:-1]):
            tests.append((f'{name} masonry pier {i+1}',xy(u,.14),True))
    return geo.union_all(areas),tests


def solid_section(triangles, altitude):
    """Fill the horizontal slice of the watertight solids just above the terrace."""
    z = triangles[:, :, 2]
    cut = triangles[(z.min(axis=1) < altitude) & (z.max(axis=1) > altitude)]
    edges = []
    for face in cut:
        ends = []
        for a, b in zip(face, np.roll(face, -1, axis=0)):
            if (a[2] < altitude) != (b[2] < altitude):
                ends.append(a[:2] + (altitude-a[2])/(b[2]-a[2]) * (b[:2]-a[:2]))
        if len(ends) == 2:
            # Orient all lines using the outward face normal. Winding also
            # distinguishes an opening in a wall from the solid wall itself.
            normal = np.cross(face[1]-face[0], face[2]-face[0])
            if np.dot(ends[1]-ends[0], [-normal[1], normal[0]]) < 0:
                ends.reverse()
            edges.append(ends)
    edges = np.round(edges, 5)
    segments = geo.get_parts(geo.union_all(geo.linestrings(edges), grid_size=.00001))
    faces = geo.get_parts(geo.polygonize(segments))
    a, b = edges[:, 0], edges[:, 1]
    filled = []
    for face in faces:
        x, y = face.representative_point().coords[0]
        crossing = (a[:, 1] > y) != (b[:, 1] > y)
        first, last = a[crossing], b[crossing]
        delta = last-first
        to_right = first[:, 0] + delta[:, 0]*(y-first[:, 1])/delta[:, 1] > x
        if np.sign(delta[to_right, 1]).sum():
            filled.append(face)
    return geo.union_all(filled, grid_size=.00001)


def main():
    cli=ArgumentParser(description=__doc__)
    cli.add_argument('--manifest',required=True,type=Path)
    cli.add_argument('--work',required=True,type=Path)
    cli.add_argument('--out',default=HERE,type=Path)
    args=cli.parse_args()
    args.out.mkdir(exist_ok=True,parents=True)
    ref=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,ref)
    assets,bounds,model,ground=site.decode_model(args.manifest)
    source=site.footprints[OWNER]
    cut=source.buffer(.40,join_style='mitre')
    galleries,tests=gallery_floor_and_probes()
    ground_above_paving=[]
    for d in read(site.work/'delivered-decode.json'):
        tri=np.fromfile(d['triangle_file'],np.float64).reshape(-1,3,3)
        local=tri[:,:,[0,2,1]]*[1,-1,1]
        # Ground and terrace finishes are at or below 2.6 cm. The pillars,
        # plinths, barriers and closed rooms remain solid above this finish.
        stand=local[local[:,:,2].max(axis=1)>.048]
        ground_above_paving.extend([site.ground_faces(stand), solid_section(local, .119)])
    hard=geo.union_all(ground_above_paving,grid_size=.001)
    structural=ground.difference(galleries).union(hard.intersection(galleries))
    # A 25 mm pedestrian clearance joins nearly coincident returns and plinth
    # faces. The arcades and the courtyard retain their metre-wide openings.
    clearance=structural.buffer(.025,join_style='mitre',mitre_limit=2)
    # Close shallow notches between closely spaced window and plinth mouldings.
    # Every resulting point lies within 20 cm of solid geometry. Courtyard
    # returns, ten detached piers and every floor-level passage remain distinct.
    collision=clearance.buffer(.50,join_style='mitre').buffer(-.50,join_style='mitre').simplify(.025,preserve_topology=True)
    (site.work/'structural-plan.wkb').write_bytes(geo.to_wkb(structural))
    (site.work/'pedestrian-plan.wkb').write_bytes(geo.to_wkb(collision))
    assert collision.difference(structural.buffer(.20)).area < .001
    assert structural.difference(collision.buffer(.001)).area < .001
    assert collision.is_valid and not collision.is_empty
    tests += [('playing court',(0,-3),False),('west court beyond gallery',(-24,5),False),
              ('east court beyond gallery',(23,3),False),('classroom interior',(0,13),True),
              ('west wing interior',(-38,5),True),('east wing interior',(38,6),True),
              ('north of old block',(0,27),False)]
    probes=[]
    for label,point,expected in tests:
        actual=collision.covers(geo.Point(point))
        assert actual==expected,(label,point,actual)
        probes.append(dict(name=label,xy=list(point),expected_solid=expected,actual_solid=actual,source_cut=cut.covers(geo.Point(point))))
    group=next(g for g in ref['near_tiles'] if OWNER in g['feature_local_ids'])
    variants={}
    for variant,(own,context,classification) in site.decode_group(group,OWNER).items():
        original,neighbors=(site.project_faces(mesh) for mesh in (own,context))
        assert original.difference(cut).area<1e-7
        assert model.distance(neighbors)>6 and cut.distance(neighbors)>6
        variants[variant]=dict(group=group['id'],owner_faces=len(own),other_faces=len(context),
            area_m2=original.area,original_remaining_m2=original.difference(cut).area,
            mesh_to_other_m=model.distance(neighbors),mask_to_other_m=cut.distance(neighbors),
            source_roof_m=float(own[:,:,2].max()),assignment=classification)
    retained=[]
    for lid in [1071,1911,2306]:
        fp=site.footprints[lid]
        assert min(cut.distance(fp),model.distance(fp))>6
        retained.append(dict(local_id=lid,cut_to_footprint_m=cut.distance(fp),model_to_footprint_m=model.distance(fp)))
    record=next(r for r in ref['owners'] if r['local_id']==OWNER)
    contract=dict(id=ID,owner=dict(macro_id=ref['frozen_macro'],feature_local_id=OWNER),
        source_feature_ids=dict(building=[record['key'][9:]],building_part=[]),
        replacement_geometry=site.wgs(cut),collision_geometry=site.wgs(collision),lng=site.lon,lat=site.lat,
        heading=ref['author_frame']['runtime_heading_deg'],scale=1,altitude=0,bounds_glb=bounds,
        model_geometry_sha256={k:v['sha256'] for k,v in assets.items()},
        overviewBearing=334,overviewPitch=45,overviewZoom=18.74,maxDistance=730,lod_switch_in_m=610,lod_switch_out_m=700,
        navigation=dict(listed=False,status='操场一侧可观察中央曲匾、两段开廊和三处凸出的教学翼。'),
        placement=dict(status='map-aligned',note='淮海东路70号地图点为学校入口，老教学楼主体落在院内1709号地块。其余教学楼独立保留。'),
        partial_model=True,model_scope=read(args.manifest)['scope'])
    checked_geometry(contract['replacement_geometry'],'replacement')
    checked_geometry(contract['collision_geometry'],'collision',collision=True)
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=ID,assets=assets,manifest_sha256=sha(args.manifest),source_area_m2=source.area,
        model_m2=model.area,structural_ground_m2=structural.area,pedestrian_clearance_m=.025,shallow_notch_closing_radius_m=.50,maximum_solid_separation_bound_m=.20,ground_m2=collision.area,mask_m2=cut.area,variants=variants,retained=retained,ground_probes=probes,
        checker_sha256=sha(Path(__file__)),decoder_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py')))
    print('Verified source, nearby blocks and',len(probes),'outdoor/solid witnesses.')


if __name__=='__main__':
    main()
