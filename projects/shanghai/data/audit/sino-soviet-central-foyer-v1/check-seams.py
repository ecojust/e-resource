"""Measure roof continuity and check the open court against both original detail meshes."""
from pathlib import Path
import argparse
import sys
import numpy as np
import shapely as geo
from shapely.geometry import Point, Polygon

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT / 'tools'))
from candidate_placement_meshes import PlacementMeshes, read, sha, write

ID = 'jingan-sino-soviet-central-foyer'


def measure(work, contract, output):
    review = read(PROJECT / 'source/precise' / ID / 'footprint-review.json')
    site = PlacementMeshes(PROJECT, work, review)
    navigation = read(contract)
    cut = geo.transform(geo.geometry.shape(navigation['replacement_geometry']), site.to_xy)
    caps = geo.transform(geo.geometry.shape(navigation['source_section_caps']['geometry']), site.to_xy)
    owner = navigation['owner']['feature_local_id']
    ids = np.array(review['near_tiles'][0]['feature_local_ids'])
    assert owner == 969 and set(ids) == {969, 1650}
    summaries = {}
    for variant in ('near', 'far'):
        data = work / f'baseline-{variant}-triangles.f64'
        tris = np.fromfile(data, np.float64).reshape(-1, 3, 3)
        tris[:, :, :2] = tris[:, :, :2] @ site.axes.T
        if variant == 'far':
            owners = np.fromfile(work / 'baseline-far-owners.u32', np.uint32)
        else:
            centers = geo.points(tris[:, :, :2].mean(1))
            distance = np.stack([geo.distance(centers, site.footprints[int(i)]) for i in ids], axis=1)
            owners = ids[distance.argmin(axis=1)]
        source = tris[owners == owner]
        roof_height = float(source[:, :, 2].max())
        roof_faces = source[source[:, :, 2].min(axis=1) >= roof_height - .04]
        assert 16.65 < roof_height < 16.75 and len(roof_faces) >= 35
        roof = site.project_faces(roof_faces)
        retained = roof.difference(cut)
        probes = []
        for sign in (-1, 1):
            for y in (2., 16., 32., 44.):
                for d in (-.18, .18, .55):
                    xy = (sign * (23. + d), y)
                    is_source = roof.covers(Point(*xy))
                    is_retained = retained.covers(Point(*xy))
                    assert is_source and is_retained == (d > 0)
                    probes.append(dict(xy=xy, z_m=roof_height, source=is_source, retained=is_retained))
                assert caps.distance(Point(sign * 23, y)) < .002
        for x in (-21., -10., 0., 10., 21.):
            for d in (-.18, .18, .55):
                xy = (x, 46 + d)
                assert roof.covers(Point(*xy)) and retained.covers(Point(*xy)) == (d > 0)
                probes.append(dict(xy=xy, z_m=roof_height, source=True, retained=d > 0))
            assert caps.distance(Point(x, 46)) < .002
        # A narrow strip of near roof projects beyond the survey line. Test it
        # explicitly at the thresholds and both ends of the court frontage.
        band = Polygon([(-22.99,-.14), (22.99,-.14), (22.99,.01), (-22.99,.01)])
        before = float(roof.intersection(band).area)
        after = float(retained.intersection(band).area)
        assert after < .00001 and (before > 2.0 if variant == 'near' else before < .5)
        for x in (-20.,-8.,-3.6,0.,3.6,8.,20.):
            for y in (-.18,-.05,.006):
                xy = (x,y)
                assert not retained.covers(Point(*xy)) and caps.distance(Point(*xy)) > 2.0
                probes.append(dict(xy=xy, z_m=roof_height, source=roof.covers(Point(*xy)), retained=False))
        summaries[variant] = dict(roof_m=roof_height, before_m2_in_front_band=before,
                                  after_m2_in_front_band=after, original_triangles_sha256=sha(data),
                                  roof_faces=len(roof_faces), probes=probes)
    write(output, dict(id=ID, passed=True, contract_sha256=sha(contract), checker_sha256=sha(Path(__file__)),
                       variants=summaries, front_cap_count=0, source_section_count=len(caps.geoms)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--contract', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    measure(args.work, args.contract, args.out)
