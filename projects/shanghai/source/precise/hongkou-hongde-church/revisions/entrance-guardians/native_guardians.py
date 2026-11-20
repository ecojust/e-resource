"""Append eight editable sculptural assemblies to the signed Hongde Blender file."""
from hashlib import sha256
from pathlib import Path
import json
import runpy
import sys
import bpy

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from build_revision import BASE, PALETTE, PROJECT, payload

# Both revisions sign the original mesh topology, materials, UVs and transforms.
helpers=runpy.run_path(str(PROJECT/'source/precise/bund17/revisions/street-wing-doors/native_doors.py'))

def hashes(objects):
    return {ob.name:sha256(json.dumps(helpers['signature'](ob),sort_keys=True).encode()).hexdigest()
            for ob in objects if ob.type=='MESH'}


def main():
    old,out,record=map(Path,sys.argv[sys.argv.index('--')+1:])
    basis=BASE['assets']['native']
    assert sha256(old.read_bytes()).hexdigest()==basis['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(old))
    old_names=set(bpy.data.objects.keys());original=hashes(bpy.data.objects);images=helpers['images']()
    collection=bpy.data.collections.new('Hongde Church · North entrance stone lions')
    bpy.context.scene.collection.children.link(collection)
    mats={}
    for name,(color,rough) in PALETTE.items():
        assert name not in bpy.data.materials
        mat=bpy.data.materials.new(name);mat.use_nodes=True;mat.diffuse_color=color
        node=mat.node_tree.nodes.get('Principled BSDF');node.inputs['Base Color'].default_value=color
        node.inputs['Roughness'].default_value=rough;mats[name]=mat
    added={}
    for name,groups in payload(False).items():
        mesh=bpy.data.meshes.new(name);v=[];n=[];f=[];slots=[]
        for index,(mat,(pos,norm,faces)) in enumerate(groups.items()):
            mesh.materials.append(mats[mat]);start=len(v)
            v.extend((x,-z,y)for x,y,z in pos);n.extend((x,-z,y)for x,y,z in norm)
            f.extend(tuple(start+int(j)for j in face)for face in faces);slots.extend([index]*len(faces))
        mesh.from_pydata(v,[],f);mesh.update();mesh.polygons.foreach_set('material_index',slots)
        mesh.polygons.foreach_set('use_smooth',[True]*len(f));mesh.normals_split_custom_set_from_vertices(n)
        collection.objects.link(bpy.data.objects.new(name,mesh));added[name]=len(f)
    bpy.context.preferences.filepaths.save_version=0
    out.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
    bpy.ops.wm.open_mainfile(filepath=str(out))
    assert old_names==set(bpy.data.objects.keys())-set(added)
    assert hashes([bpy.data.objects[x]for x in original])==original and helpers['images']()==images
    assert len(added)==8 and all(len(bpy.data.objects[name].data.polygons)==n for name,n in added.items())
    record.write_text(json.dumps(dict(blender=bpy.app.version_string,prior_sha256=basis['sha256'],
        native_sha256=sha256(out.read_bytes()).hexdigest(),native_bytes=out.stat().st_size,
        original_objects=len(old_names),unchanged_original_meshes=len(original),
        original_mesh_signatures_sha256=sha256(json.dumps(original,sort_keys=True).encode()).hexdigest(),
        preserved_packed_images=images,new_editable_meshes=added),ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
