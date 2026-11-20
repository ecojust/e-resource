"""Open the issued editable Bund 18 scene, replace its one rosette and verify after saving."""
from pathlib import Path
from collections import Counter
from hashlib import sha256
import argparse,array,struct,json,sys
import bpy,bmesh
from mathutils import Vector
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from stonework import STONE,local,world,stonework,is_old_rosette

def digest(p):return sha256(p.read_bytes()).hexdigest()

def triangles(ob,skip=False):
    m=ob.data;m.calc_loop_triangles();uv=m.uv_layers.active;result=Counter()
    for tri in m.loop_triangles:
        verts=[m.vertices[i].co for i in tri.vertices]
        selected=all(is_old_rosette(*local(*v)) for v in verts)
        if skip and selected:continue
        points=[]
        for v,i in zip(verts,tri.loops):
            coords=tuple(v)+(tuple(uv.data[i].uv)if uv is not None else ())
            points.append(struct.pack('<'+'f'*len(coords),*coords))
        key=min(b''.join(points[i:]+points[:i])for i in range(3))
        result[(tri.material_index,key)]+=1
    return result

def unchanged(ob):
    h=sha256();m=ob.data
    for items,key,count,typ in [(m.vertices,'co',3*len(m.vertices),'f'),(m.loops,'vertex_index',len(m.loops),'i'),(m.polygons,'material_index',len(m.polygons),'i')]:
        a=array.array(typ,[0])*count;items.foreach_get(key,a);h.update(a.tobytes())
    for uv in m.uv_layers:
        a=array.array('f',[0])*(2*len(uv.data));uv.data.foreach_get('uv',a);h.update(a.tobytes())
    for row in ob.matrix_world:h.update(struct.pack('<4f',*row))
    for mat in m.materials:h.update(mat.name.encode())
    return h.hexdigest()

def images():return {im.name:sha256(im.packed_file.data).hexdigest() for im in bpy.data.images if im.packed_file}

def render(filename):
    scene=bpy.context.scene;cam=bpy.data.cameras.new('Door detail working camera');ob=bpy.data.objects.new(cam.name,cam);scene.collection.objects.link(ob)
    ob.location=world(.78,-8.1,6.74);target=Vector(world(0,-.48,5.77))
    ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler();cam.type='ORTHO';cam.ortho_scale=4.75;scene.camera=ob
    scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=False;scene.render.resolution_percentage=100;scene.render.resolution_x=640;scene.render.resolution_y=360
    scene.render.image_settings.file_format='PNG';scene.render.filepath=str(filename);bpy.ops.render.render(write_still=True);bpy.data.objects.remove(ob,do_unlink=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prior',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);ap.add_argument('--preview',type=Path);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
    a.out.parent.mkdir(exist_ok=True,parents=True);a.report.parent.mkdir(exist_ok=True,parents=True)
    original=json.loads((HERE/'baseline.json').read_bytes())['assets']['native'];assert digest(a.prior)==original['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(a.prior));bpy.context.preferences.filepaths.save_version=0
    if a.preview:
        a.preview.mkdir(exist_ok=True,parents=True);render(a.preview/'door-before.png')
        bpy.ops.wm.open_mainfile(filepath=str(a.prior))
    ob=bpy.data.objects['Bund18_trim'];old=triangles(ob);kept=triangles(ob,True);removed=sum(old.values())-sum(kept.values());assert removed==1320,removed
    untouched={o.name:unchanged(o)for o in bpy.data.objects if o.type=='MESH'and o!=ob};photos=images();assert photos
    bm=bmesh.new();bm.from_mesh(ob.data);kill=[v for v in bm.verts if is_old_rosette(*local(*v.co))];bmesh.ops.delete(bm,geom=kill,context='VERTS');bm.to_mesh(ob.data);bm.free();ob.data.update()
    assert triangles(ob)==kept
    col=bpy.data.collections.new('East entrance cartouche');ob.users_collection[0].children.link(col);names=[]
    for name,mat,pts,faces in stonework():
        mesh=bpy.data.meshes.new(name);mesh.from_pydata([world(*p)for p in pts],[],faces);mesh.materials.append(bpy.data.materials[mat]);mesh.update()
        obj=bpy.data.objects.new(name,mesh);col.objects.link(obj);names.append(obj.name)
    bpy.ops.wm.save_as_mainfile(filepath=str(a.out),compress=True);bpy.ops.wm.open_mainfile(filepath=str(a.out));assert images()==photos
    assert triangles(bpy.data.objects['Bund18_trim'])==kept
    assert all(unchanged(bpy.data.objects[name])==sig for name,sig in untouched.items());assert all(bpy.data.objects.get(name)for name in names)
    result={'native_sha256':digest(a.out),'baseline_native_sha256':digest(a.prior),'blender':bpy.app.version_string,'removed_triangles':removed,'retained_edited_mesh_triangles':sum(kept.values()),'other_unchanged_meshes':untouched,'packed_images':photos,'parts':names,'reopened':True}
    if a.preview:render(a.preview/'door-after.png')
    a.report.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
if __name__=='__main__':main()
