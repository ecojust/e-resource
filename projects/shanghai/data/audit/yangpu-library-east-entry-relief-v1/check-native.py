"""Read the reopened Blender polygons and compare actual material-sorted triangle surfaces."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace
import bpy
import numpy as np

cli=argparse.ArgumentParser(description=__doc__)
cli.add_argument('--project',type=Path,required=True);cli.add_argument('--raw',type=Path,required=True)
cli.add_argument('--out',type=Path,required=True);args=cli.parse_args(sys.argv[sys.argv.index('--')+1:])
helper=runpy.run_path(str(args.project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
full=helper(args.raw);expected=full.surface_digest();del full
parts=[];indices=[];names=[];recognized=[]
for obj in bpy.data.collections['Yangpu Library, complete exterior'].objects:
    if obj.type!='MESH':continue
    mesh=obj.data;mesh.calc_loop_triangles()
    vertices=np.empty(len(mesh.vertices)*3,np.float32);mesh.vertices.foreach_get('co',vertices)
    transform=np.array(obj.matrix_world,dtype=np.float64);coordinates=vertices.reshape(-1,3)@transform[:3,:3].T+transform[:3,3]
    triangles=np.empty(len(mesh.loop_triangles)*3,np.int32);mesh.loop_triangles.foreach_get('vertices',triangles)
    mi=np.empty(len(mesh.loop_triangles),np.int32);mesh.loop_triangles.foreach_get('material_index',mi)
    mapping=np.empty(len(mesh.materials),np.int32)
    for i,m in enumerate(mesh.materials):
        if m.name not in names:names.append(m.name)
        mapping[i]=names.index(m.name)
    parts.append(coordinates[triangles.reshape(-1,3)]);indices.append(mapping[mi])
    recognized.extend(g.name for g in obj.vertex_groups)
scene=SimpleNamespace(tri=np.concatenate(parts),mi=np.concatenate(indices),materials=names)
got=helper.surface_digest(scene)
assert expected==got,[(n,expected[n],got.get(n))for n in expected if expected[n]!=got.get(n)]
assert len(set(recognized))==4
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
args.out.write_text(json.dumps(dict(passed=True,raw_sha256=sha(args.raw),native_sha256=sha(Path(bpy.data.filepath)),
    vertex_groups=recognized,reopened_blender=bpy.app.version_string,triangles=len(scene.tri),
    oriented_material_surfaces=got,checker_sha256=sha(Path(__file__))),indent=2)+'\n')
