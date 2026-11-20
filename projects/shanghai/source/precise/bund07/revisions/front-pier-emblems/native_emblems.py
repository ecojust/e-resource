"""Add two open gilt emblems to the signed native Bund 7 baseline and verify the original scene."""
from pathlib import Path
from hashlib import sha256
import json,sys
import bpy
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(HERE.parents[2]/'bund17/revisions/street-wing-doors'))
from build_wing_doors import chunks
import numpy as np
from native_doors import signature,images

prior,raw,out,receipt=map(Path,sys.argv[sys.argv.index('--')+1:])
reference=json.loads((HERE/'baseline.json').read_bytes())['assets']['native']
assert sha256(prior.read_bytes()).hexdigest()==reference['sha256']
bpy.ops.wm.open_mainfile(filepath=str(prior))
old_objects=set(bpy.data.objects.keys())
originals={o.name:signature(o)for o in bpy.data.objects if o.type=='MESH'}
old_images=images()
group=bpy.data.collections.new('Bund 7 - street-pier lotus emblems')
bpy.context.scene.collection.children.link(group)
doc,blob=chunks(raw)
def unpack(i):
    acc=doc['accessors'][i];view=doc['bufferViews'][acc['bufferView']]
    dimensions={'VEC3':3,'SCALAR':1}[acc['type']]
    dtype={5123:'<u2',5126:'<f4'}[acc['componentType']]
    return np.frombuffer(blob,dtype=dtype,count=acc['count']*dimensions,offset=view.get('byteOffset',0)+acc.get('byteOffset',0)).reshape(-1,dimensions)
def assemblies():
    for mesh in doc['meshes'][-2:]:
        assert mesh['name'].startswith('Bund07 | ') and mesh['name'].endswith('open lotus')
        groups={}
        for prim in mesh['primitives']:
            a=prim['attributes'];material=doc['materials'][prim['material']]['name']
            groups[material]=unpack(a['POSITION']),unpack(a['NORMAL']),unpack(prim['indices']).reshape(-1,3)
        yield mesh['name'],groups
mats={}
for row in doc['materials'][-2:]:
    name=row['name'];material=row['pbrMetallicRoughness']
    rgba,metal,rough=material['baseColorFactor'],material['metallicFactor'],material['roughnessFactor']
    assert name not in bpy.data.materials
    mat=bpy.data.materials.new(name);mat.diffuse_color=rgba;mat.use_nodes=True
    shader=mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value=rgba;shader.inputs['Roughness'].default_value=rough
    shader.inputs['Metallic'].default_value=metal;mats[name]=mat
new={}
for name,groups in assemblies():
    mesh=bpy.data.meshes.new(name);verts=[];normals=[];faces=[];slots=[]
    for slot,(material,(points,directions,indices)) in enumerate(groups.items()):
        mesh.materials.append(mats[material]);base=len(verts)
        verts.extend((x,-z,y)for x,y,z in points);normals.extend((x,-z,y)for x,y,z in directions)
        faces.extend(tuple(base+int(j)for j in tri)for tri in indices);slots.extend([slot]*len(indices))
    mesh.from_pydata(verts,[],faces);mesh.update()
    mesh.polygons.foreach_set('material_index',slots);mesh.polygons.foreach_set('use_smooth',[True]*len(faces))
    mesh.normals_split_custom_set_from_vertices(normals)
    obj=bpy.data.objects.new(name,mesh);group.objects.link(obj);new[name]=len(faces)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(out))
assert {k:signature(bpy.data.objects[k])for k in originals}==originals and images()==old_images
assert set(bpy.data.objects.keys())-old_objects==set(new) and len(new)==2
assert all(len(bpy.data.objects[k].data.polygons)==v for k,v in new.items())
receipt.write_text(json.dumps({'blender':bpy.app.version_string,'baseline_native_sha256':reference['sha256'],
    'reopened_native_sha256':sha256(out.read_bytes()).hexdigest(),'bytes':out.stat().st_size,'unchanged_original_meshes':originals,
    'packed_images':old_images,'preserved_object_names':sorted(old_objects),'new_individually_editable_meshes':new,
    'added_triangles':sum(new.values())},ensure_ascii=False,indent=2)+'\n')
