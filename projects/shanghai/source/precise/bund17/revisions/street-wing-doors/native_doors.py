"""Append the six editable door, transom and jamb assemblies and verify the original V4.4 scene."""
import array
from hashlib import sha256
import json
import math
from pathlib import Path
import sys
import bpy

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from build_wing_doors import instances,MATERIALS


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def field(items, key, typecode, count):
    value=array.array(typecode, [0])*count
    items.foreach_get(key, value)
    return sha256(value.tobytes()).hexdigest()


def signature(obj):
    # Preserve the original mesh arrays, UV seams, face materials and placement.
    mesh=obj.data
    return {
        'vertices':len(mesh.vertices),'polygons':len(mesh.polygons),'loops':len(mesh.loops),
        'xyz':field(mesh.vertices,'co','f',len(mesh.vertices)*3),
        'faces':field(mesh.loops,'vertex_index','i',len(mesh.loops)),
        'loop_count':field(mesh.polygons,'loop_total','i',len(mesh.polygons)),
        'face_material':field(mesh.polygons,'material_index','i',len(mesh.polygons)),
        'materials':[m.name for m in mesh.materials],
        'uv':{uv.name:field(uv.data,'uv','f',len(uv.data)*2) for uv in mesh.uv_layers},
        'transform':[list(row) for row in obj.matrix_world],
        'data_name':mesh.name
    }


def images():
    return {im.name:sha256(im.packed_file.data).hexdigest()
            for im in bpy.data.images if im.packed_file}


def main():
    prior,out,receipt=map(Path,sys.argv[sys.argv.index('--')+1:])
    record=json.loads((HERE/'baseline.json').read_bytes())['assets']['native']
    assert digest(prior)==record['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(prior))
    old_objects={ob.name for ob in bpy.data.objects}
    originals={ob.name:signature(ob) for ob in bpy.data.objects if ob.type=='MESH'}
    original_images=images()
    collection=bpy.data.collections.new('Bund 17 · Ground-floor wing doors')
    bpy.context.scene.collection.children.link(collection)
    mats={}
    for name,(rgba,metal,rough)in MATERIALS.items():
        assert name not in bpy.data.materials
        m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=rgba;m.surface_render_method='DITHERED'
        shader=m.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Base Color'].default_value=rgba
        shader.inputs['Metallic'].default_value=metal
        shader.inputs['Roughness'].default_value=rough
        mats[name]=m
    new={}
    for name,parts in instances(False):
        vertices=[];faces=[];normals=[];slots=[]
        mesh=bpy.data.meshes.new(name)
        for slot,(label,(points,directions,indices))in enumerate(parts.items()):
            mesh.materials.append(mats[label])
            base=len(vertices)
            vertices.extend((x,-z,y)for x,y,z in points)
            normals.extend((x,-z,y)for x,y,z in directions)
            faces.extend(tuple(base+int(i)for i in face)for face in indices)
            slots.extend([slot]*len(indices))
        mesh.from_pydata(vertices,[],faces);mesh.update()
        mesh.polygons.foreach_set('material_index',slots)
        mesh.polygons.foreach_set('use_smooth',[True]*len(faces))
        mesh.normals_split_custom_set_from_vertices(normals)
        obj=bpy.data.objects.new(name,mesh);collection.objects.link(obj)
        new[name]=len(faces)
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
    bpy.ops.wm.open_mainfile(filepath=str(out))
    assert originals=={name:signature(bpy.data.objects[name])for name in originals}
    assert original_images==images()
    assert set(bpy.data.objects.keys())-old_objects==set(new)
    assert len({bpy.data.objects[n].data.name for n in new})==6
    assert all(len(bpy.data.objects[n].data.polygons)==count for n,count in new.items())
    info={'blender':bpy.app.version_string,'baseline_native_sha256':record['sha256'],
        'reopened_native_sha256':digest(out),'bytes':out.stat().st_size,'unchanged_original_meshes':originals,
        'packed_images':original_images,'preserved_object_names':sorted(old_objects),'new_individually_editable_meshes':new,
        'added_triangles':sum(new.values())}
    receipt.write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n')
    print('VERIFIED',info['reopened_native_sha256'])


if __name__=='__main__':main()
