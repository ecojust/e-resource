"""Preserve the original editable Bund 6 scene, append the six local stone shafts, and reopen to verify."""
import array
from hashlib import sha256
import json
import math
from pathlib import Path
import sys
import bpy

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from build_window_shafts import stone,transforms


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
    source,=[ob for ob in bpy.data.objects if ob.type=='MESH' and len(ob.data.polygons)>90000]
    material,=[slot.material for slot in source.material_slots if slot.material and slot.material.name=='carved pale stone']
    parts=bpy.data.collections.new('Bund 06 · Second-storey window shafts')
    bpy.context.scene.collection.children.link(parts)
    pos,norm,tri=stone(False)
    # glTF east/up/south to Blender east/north/up.
    pts=[(x,-z,y) for x,y,z in pos]
    norms=[(x,-z,y) for x,y,z in norm]
    faces=tri.tolist()
    names=[]
    for transform in transforms():
        name=transform['name']
        names.append(name)
        mesh=bpy.data.meshes.new(name)
        mesh.from_pydata(pts,[],faces);mesh.update()
        mesh.materials.append(material)
        mesh.polygons.foreach_set('use_smooth',[True]*len(mesh.polygons))
        mesh.normals_split_custom_set_from_vertices(norms)
        ob=bpy.data.objects.new(name,mesh);parts.objects.link(ob)
        x,y,z=transform['translation']
        ob.location=(x,-z,y)
        _,half,_,cosine=transform['rotation']
        ob.rotation_euler.z=2*math.atan2(half,cosine)
    # Save a new file, preserving the parent scene camera, original materials,
    # lighting, embedded source image and the original object itself.
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
    bpy.ops.wm.open_mainfile(filepath=str(out))
    assert originals=={name:signature(bpy.data.objects[name]) for name in originals}
    assert old_objects.issubset(bpy.data.objects.keys())
    assert set(bpy.data.objects.keys())-old_objects==set(names)
    assert original_images==images()
    assert len({bpy.data.objects[name].data.name for name in names})==6
    assert all(len(bpy.data.objects[name].data.polygons)==len(faces) for name in names)
    report={'blender':bpy.app.version_string,'previous_native_sha256':record['sha256'],
            'reopened_native_sha256':digest(out),'bytes':out.stat().st_size,
            'unchanged_original_meshes':originals,'preserved_original_objects':sorted(old_objects),
            'packed_images':original_images,'new_individually_editable_meshes':names,
            'added_triangles':6*len(faces),'source_meshes_unchanged':True}
    receipt.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('VERIFIED',report['reopened_native_sha256'])


if __name__=='__main__':
    main()
