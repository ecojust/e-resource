#!/usr/bin/env python3
"""Small deterministic geometry/GLB audits; no Blender, renderer or browser."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct
import tempfile

import numpy as np
from shapely.geometry import GeometryCollection, LineString, MultiPolygon, Point, Polygon, box
from shapely.ops import unary_union

from photo_architecture import Builder, Facade, opening, pieces


CASES = []


def mesh_audit(vertices, triangles, label, expected_volume=None):
    vertices = np.asarray(vertices, dtype=float)
    triangles = np.asarray(triangles, dtype=int)
    assert np.isfinite(vertices).all() and len(triangles)
    weld = {}; remap = []
    for point in vertices:
        key = tuple(point)
        weld.setdefault(key, len(weld)); remap.append(weld[key])
    remapped = np.asarray(remap)[triangles]
    undirected = Counter(); directed = Counter(); triangle_keys = Counter()
    for tri in remapped:
        assert len(set(tri)) == 3, (label, 'collapsed triangle')
        triangle_keys[tuple(sorted(tri))] += 1
        for a, b in zip(tri, np.roll(tri, -1)):
            undirected[tuple(sorted((int(a), int(b))))] += 1
            directed[int(a), int(b)] += 1
    assert all(n == 1 for n in triangle_keys.values()), (label, 'duplicate face')
    assert all(n == 2 for n in undirected.values()), (label, 'boundary/nonmanifold edge', Counter(undirected.values()))
    assert all(directed[a, b] == directed[b, a] == 1 for a, b in undirected), (label, 'inconsistent winding')
    shifted = vertices - vertices.mean(axis=0)
    tri = shifted[triangles]
    areas = np.linalg.norm(np.cross(tri[:,1]-tri[:,0], tri[:,2]-tri[:,0]), axis=1) / 2
    assert np.all(areas > 1e-12), (label, 'zero area')
    volume = np.einsum('ij,ij->i', tri[:,0], np.cross(tri[:,1], tri[:,2])).sum() / 6
    assert volume > 0, (label, 'inside-out/nonpositive solid')
    if expected_volume is not None:
        assert math.isclose(volume, expected_volume, rel_tol=1e-8, abs_tol=1e-8), (label, volume, expected_volume)
    report = {'case': label, 'vertices_welded': len(weld), 'triangles': len(triangles),
              'edges': len(undirected), 'boundary_edges': 0, 'nonmanifold_edges': 0,
              'duplicate_faces': 0, 'inconsistent_winding_edges': 0, 'signed_volume_m3': float(volume),
              'expected_volume_m3': expected_volume, 'euler_characteristic': len(weld)-len(undirected)+len(triangles)}
    CASES.append(report)
    return report


def audit_builder(builder, label, expected_volumes=None):
    return [mesh_audit(p['vertices'], p['triangles'], label+'/'+p['label'],
                      None if expected_volumes is None else expected_volumes[i]) for i,p in enumerate(builder.parts)]


def glb_arrays(path):
    data = path.read_bytes()
    magic, version, size = struct.unpack_from('<4sII', data)
    assert (magic, version, size) == (b'glTF', 2, len(data))
    json_size, json_type = struct.unpack_from('<II', data, 12)
    assert json_type == 0x4E4F534A
    doc = json.loads(data[20:20+json_size])
    binary_size, binary_type = struct.unpack_from('<II', data, 20+json_size)
    assert binary_type == 0x004E4942
    binary = data[28+json_size:]
    assert len(binary) == binary_size == doc['buffers'][0]['byteLength']
    def accessor(index):
        item = doc['accessors'][index]; view = doc['bufferViews'][item['bufferView']]
        dtype = {5126:'<f4', 5125:'<u4'}[item['componentType']]
        width = {'SCALAR':1, 'VEC3':3}[item['type']]
        return np.frombuffer(binary, dtype=dtype, count=item['count']*width,
            offset=view.get('byteOffset',0)+item.get('byteOffset',0)).reshape(item['count'], width)
    return [(accessor(p['attributes']['POSITION']), accessor(p['attributes']['NORMAL']),
             accessor(p['indices']).reshape(-1,3)) for p in doc['meshes'][0]['primitives']]


def must_reject(label, operation):
    try:
        operation()
    except ValueError:
        CASES.append({'case':label, 'invalid_input_rejected':True})
    else:
        raise AssertionError('Invalid input accepted: '+label)


def main():
    # A continuous wall, two internal openings and a door notch reaching ground.
    holes = [opening(-3,1,1.4,2.8), opening(0,0,1.8,3.2,.9), opening(3,4,1.8,3,1.1)]
    for angle, offset in [(0,(0,0)), (.419,(1234.678912,-876.543219))]:
        builder=Builder(); t=np.array([math.cos(angle),math.sin(angle)]); a=np.array(offset)
        facade=Facade(builder,a,a+t*12); surface=facade.wall(0,9,holes)
        audit_builder(builder,f'continuous-wall-angle{angle}',[surface.area*.48])
        front_area=0.; hole_overlap=0.
        for part in builder.parts:
            vv=np.asarray(part['vertices'])
            for tri in part['triangles']:
                points=vv[list(tri)]
                depths=(points-facade.center)@facade.n
                if np.max(np.abs(depths))<1e-9:
                    normal=np.cross(points[1]-points[0],points[2]-points[0])
                    assert np.dot(normal,facade.n)>0
                    shape=Polygon([((p-facade.center)@facade.t,p[2]) for p in points])
                    front_area+=shape.area
                    hole_overlap+=shape.intersection(unary_union(holes)).area
        assert math.isclose(front_area,surface.area,abs_tol=1e-9) and hole_overlap<1e-9
        CASES.append({'case':f'front-area-and-open-holes-angle{angle}', 'front_area_m2':front_area,
                      'expected_area_m2':surface.area,'triangles_in_openings_area_m2':hole_overlap})
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'wall.glb'; builder.save(path)
            for positions,normals,triangles in glb_arrays(path):
                mesh_audit(positions,triangles,f'actual-glb-float32-wall-angle{angle}')
                actual=np.cross(positions[triangles[:,1]].astype(float)-positions[triangles[:,0]],
                                positions[triangles[:,2]].astype(float)-positions[triangles[:,0]])
                actual/=np.linalg.norm(actual,axis=1)[:,None]
                assert np.all(np.einsum('ij,ij->i',actual,normals[triangles[:,0]])>.999999)

    # Both ordinary and reflected bases must have exterior-facing winding.
    for basis in [None,[[1,0,0],[0,-1,0],[0,0,1]]]:
        builder=Builder(); builder.box((3,7,13),(2,4,6),basis=basis)
        audit_builder(builder,'box-'+('right' if basis is None else 'left'),[48.])
    builder=Builder(); facade=Facade(builder,(0,0),(0,10)); facade.box(0,5,2,3,.4)
    audit_builder(builder,'facade-left-handed-box',[2*3*.4])

    # Roof/plan prisms preserve interior courtyard holes and multiple islands.
    courtyard=box(-5,-4,5,4).difference(box(-2,-1,2,1))
    builder=Builder(); builder.plan_prism(courtyard,6,6.3)
    audit_builder(builder,'courtyard-prism',[courtyard.area*.3])
    builder=Builder(); builder.plan_prism(MultiPolygon([box(0,0,1,1),box(2,0,3,1)]),0,2)
    audit_builder(builder,'multi-island-prism',[2.,2.])
    assert len(pieces(GeometryCollection([box(0,0,1,1),LineString([(2,0),(3,0)]),Point(4,0)])))==1

    # Unioned frame grids have no crossing/coplanar duplicates or open ends.
    for arch in [0.,.85]:
        builder=Builder(); facade=Facade(builder,(0,0),(0,10)); shape=opening(0,1,2.4,3.4,arch)
        facade.window(shape,columns=3,rows=4)
        audit_builder(builder,'window-grid-'+str(arch))
        grid=[p for p in builder.parts if p['label'].endswith('-frame-grid')]
        assert len(grid)==1 and not any(p['label'].endswith(('-mullion','-transom')) for p in builder.parts)

    for points,label in [([(0,0,0),(0,0,3)],'vertical'),([(0,0,0),(3,0,0)],'horizontal'),
                         ([(0,0,0),(1,2,3)],'diagonal'),([(0,0,0),(0,0,2),(1,0,3)],'bend')]:
        builder=Builder(); builder.tube(points,.3,sides=12)
        expected=None if len(points)>2 else 12*.3**2*math.sin(math.tau/12)/2*math.dist(*points)
        audit_builder(builder,'tube-'+label,None if expected is None else [expected])
    for profile,label in [([(0,.5),(3,.5)],'cylinder'), ([(0,0),(0,.5),(3,.5),(3,0)],'zero-radius-caps'),
                          ([(0,0),(3,.5)],'cone'), ([(0,.7),(.2,.7),(.2,.5),(2.8,.5),(2.8,.7),(3,.7)],'stepped-column')]:
        builder=Builder(); builder.lathe((0,0),profile,segments=24)
        audit_builder(builder,'lathe-'+label)

    # The axis permutation is a proper rotation, retaining signed volume.
    builder=Builder(); builder.box((3,7,13),(2,4,6))
    with tempfile.TemporaryDirectory() as directory:
        path=Path(directory)/'axes.glb'; builder.save(path)
        positions,normals,triangles=glb_arrays(path)[0]
        assert np.array_equal(positions.min(0),[2,10,-9])
        assert np.array_equal(positions.max(0),[4,16,-5])
        mesh_audit(positions,triangles,'glb-east-up-minus-north',[48.][0])
        for n in normals:
            assert math.isclose(float(np.linalg.norm(n)),1.,abs_tol=1e-7)
        bad=Builder(); bad.box((1e8,1e8,1e8),(.1,.1,.1))
        must_reject('float32-collapsed-solid',lambda:bad.save(Path(directory)/'invalid.glb'))

    must_reject('zero-facade',lambda:Facade(Builder(),(0,0),(0,0)))
    must_reject('left-handed-prism',lambda:Builder().prism(box(0,0,1,1),0,1,lambda u,z,d:(u,d,z)))
    must_reject('repeated-tube-points',lambda:Builder().tube([(0,0,0),(0,0,0)],.1))
    must_reject('reversing-tube-tangent',lambda:Builder().tube([(0,0,0),(1,0,0),(0,0,0)],.1))
    must_reject('negative-tube-radius',lambda:Builder().tube([(0,0,0),(0,0,1)],-.1))
    must_reject('descending-lathe',lambda:Builder().lathe((0,0),[(2,.5),(0,.5)]))
    must_reject('invalid-arch-segments',lambda:opening(0,0,1,2,1,segments=0))
    must_reject('singular-box-basis',lambda:Builder().box((0,0,0),(1,1,1),basis=[[1,0,0],[1,0,0],[0,0,1]]))
    for filename in ['photo_architecture.py','blender_finish.py']:
        compile(Path(__file__).with_name(filename).read_text(),filename,'exec')
    report={'passed':True,'browser_or_blender_or_render_executed':False,'case_count':len(CASES),'cases':CASES,
        'source_sha256':{name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                         for name in ['photo_architecture.py','blender_finish.py','test_photo_architecture.py']},
        'blender_finish_review':{'syntax':'passed','axis_contract':'Blender glTF importer rotates east/up/south back to east/north/up; no additional axis transform is applied by the finish script.',
            'no_renderer_execution':'Native import/render was not run; shader, visual quality and actual Blender importer execution remain separate checks.'}}
    output=Path(__file__).with_name('geometry-api-audit.json');output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':True,'cases':len(CASES),'report':str(output),'source_sha256':report['source_sha256']},indent=2))


if __name__=='__main__':main()
