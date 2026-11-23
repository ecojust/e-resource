"""Export the architectural model to interchange formats and compare imported triangle vertices."""
import hashlib
import json
from pathlib import Path
import re
import sys
import bpy
import numpy as np
from mathutils.kdtree import KDTree

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def empty():bpy.ops.wm.read_factory_settings(use_empty=True)
def material_key(s):
    return ''.join(c for c in s if c.isalnum()).casefold()
def sample_scene():
    triangles=[];material_ids=[];materials={};names=[];with_uv=0
    for o in bpy.context.scene.objects:
        if o.type!='MESH':continue
        mesh=o.data;mesh.calc_loop_triangles()
        if not mesh.loop_triangles:continue
        names.append(o.name)
        verts=np.empty(3*len(mesh.vertices),dtype='f');mesh.vertices.foreach_get('co',verts)
        world=np.asarray(o.matrix_world,dtype='f8')
        xyz=verts.reshape(-1,3)@world[:3,:3].T+world[:3,3]
        indices=np.empty(3*len(mesh.loop_triangles),dtype='i');mesh.loop_triangles.foreach_get('vertices',indices)
        triangles.append(xyz[indices.reshape(-1,3)])
        slots=[material_key(s.name) for s in o.material_slots]
        values=[]
        for tri in mesh.loop_triangles:
            key=slots[tri.material_index] if tri.material_index<len(slots) else ''
            if key not in materials:materials[key]=len(materials)
            values.append(materials[key])
        material_ids.extend(values)
        if mesh.uv_layers:with_uv+=1
    return np.concatenate(triangles),np.asarray(material_ids),list(materials),names,with_uv
def select_meshes():
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type=='MESH':obj.select_set(True)
def portable_fbx(filepath):
    # FBX stores the author's absolute .blend and texture paths even with embedded media.
    # Keep media URI basenames and the native filename independent of the author machine.
    import io_scene_fbx.encode_bin as binary
    original=binary.FBXElem.add_string_unicode
    def relative(self,val):
        if isinstance(val,str) and Path(val).is_absolute():val=Path(val).name
        return original(self,val)
    binary.FBXElem.add_string_unicode=relative
    try:
        bpy.ops.export_scene.fbx(filepath=str(filepath),use_selection=True,object_types={'MESH'},
            apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Z',axis_up='Y',
            use_mesh_modifiers=False,use_triangles=True,path_mode='COPY',embed_textures=True,bake_anim=False)
    finally:binary.FBXElem.add_string_unicode=original
def export(blend,out,id):
    bpy.ops.wm.open_mainfile(filepath=str(blend));select_meshes()
    tri,mats,labels,names,uv=sample_scene()
    np.savez(out/'native-surfaces.npz',tri=tri,material_ids=mats,materials=np.asarray(labels))
    save(out/'native-source.json',dict(editable_sha256=digest(blend),triangles=len(tri),mesh_groups=len(names),uv_groups=uv,materials=len(labels)))
    obj=out/'obj';obj.mkdir(exist_ok=True)
    for im in bpy.data.images:
        if not im.packed_file:continue
        name=Path(im.filepath).name
        if not name.lower().endswith('.png'):continue
        path=obj/name;path.write_bytes(im.packed_file.data)
        im.filepath=str(path)
    portable_fbx(out/(id+'.fbx'))
    bpy.ops.wm.obj_export(filepath=str(obj/(id+'.obj')),export_selected_objects=True,export_materials=True,
        export_uv=True,export_normals=True,export_pbr_extensions=True,export_triangulated_mesh=True,
        forward_axis='Y',up_axis='Z',path_mode='STRIP')
    bpy.ops.wm.stl_export(filepath=str(out/(id+'.stl')),export_selected_objects=True,
        global_scale=1.0,use_scene_unit=True,forward_axis='Y',up_axis='Z',ascii_format=False)
    for p in [out/(id+'.fbx'),obj/(id+'.mtl')]:
        data=p.read_bytes()
        for prefix in (b'/workspace/',b'/dev/shm/',b'/proc/',b'/run/lock/',b'/tmp/'):
            if prefix in data:raise ValueError('Nonportable media path in '+p.name)
    lines=(obj/(id+'.mtl')).read_text().splitlines()
    for line in lines:
        if (line.startswith('map_') or line.startswith('norm ')) and line.split():
            path=obj/line.split()[-1]
            if not path.is_file():raise ValueError('Missing Wavefront material image: '+str(path))
def canonical_face(triangle, oriented):
    points=tuple(tuple(float(v) for v in p) for p in triangle)
    if oriented:
        return min(points[i:]+points[:i] for i in range(3))
    return tuple(sorted(points))

def verify_stl_facets(path, reference, imported):
    """Compare every serialized facet, including touching closed solids' opposite faces."""
    from collections import Counter
    import struct
    data=path.read_bytes()
    count=struct.unpack_from('<I',data,80)[0]
    if len(data)!=84+50*count or count!=len(reference):
        raise ValueError('Invalid STL facet count')
    facets=np.ndarray((count,3,3),dtype='<f4',buffer=data,offset=96,strides=(50,12,4))
    original=np.asarray(reference,dtype=np.float32)
    expected=Counter(canonical_face(t,True) for t in original)
    stored=Counter(canonical_face(t,True) for t in facets)
    if stored!=expected:
        raise ValueError('The oriented STL facets differ from native east/north/up metre coordinates')
    # Blender welds coincident faces when opening one unlabelled STL mesh. Check
    # that every unique physical face survived, and that only originals occur.
    loaded=Counter(canonical_face(t,True) for t in np.asarray(imported,dtype=np.float32))
    both_sides={canonical_face(t,False) for t in facets}
    imported_sides={canonical_face(t,False) for t in imported}
    if loaded-stored or both_sides!=imported_sides:
        raise ValueError('STL import changed the geometric surface')
    return dict(serialized_facets=count,blender_import_facets=len(imported),
                coincident_facets_merged=count-len(imported),unique_geometric_faces=len(both_sides))

def material_images(socket):
    """Read the image nodes connected to a real shader socket after interchange import."""
    nodes=[link.from_node for link in socket.links]
    images=set();visited=set()
    while nodes:
        node=nodes.pop()
        if node in visited:continue
        visited.add(node)
        if node.type=='TEX_IMAGE' and node.image:
            images.add(Path(node.image.filepath).name)
        for pin in node.inputs:
            nodes.extend(link.from_node for link in pin.links)
    return sorted(images)


def required_texture_slots(raw):
    """Resolve the exact authored color and relief image names from the GLB."""
    with raw.open('rb') as stream:
        header=stream.read(20)
        if header[:4]!=b'glTF' or header[16:20]!=b'JSON':
            raise ValueError('Missing glTF JSON chunk')
        doc=json.loads(stream.read(int.from_bytes(header[12:16],'little')))
    def image(slot):
        texture=doc['textures'][slot['index']]
        return doc['images'][texture['source']]['name']
    required={}
    for mat in doc['materials']:
        color=mat.get('pbrMetallicRoughness',{}).get('baseColorTexture')
        normal=mat.get('normalTexture')
        if color is None and normal is None:
            continue
        if color is None or normal is None:
            raise ValueError(('Missing one of the authored texture slots',mat['name']))
        required[mat['name']]=(image(color),image(normal))
    return required


def verify_finishes():
    pack=Path(blend).parent
    info=json.loads((pack/'manifest.json').read_bytes())['assets']['raw']
    raw=pack/info['file']
    if digest(raw)!=info['sha256']:
        raise ValueError('Raw material reference differs from the signed edition')
    expected=required_texture_slots(raw)
    if len(expected)!=2:
        raise ValueError(('Expected two textured garden finishes',expected))
    mats={material_key(m.name):m for m in bpy.data.materials}
    result={}
    for name,(color_file,normal_file) in expected.items():
        mat=mats[material_key(name)]
        node=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        colour=material_images(node.inputs['Base Color']);normal=material_images(node.inputs['Normal'])
        if colour!=[color_file] or normal!=[normal_file]:
            raise ValueError(('The reopened material changed image slots',name,colour,normal))
        result[name]={'base_color':colour,'normal':normal}
    glazing = {}
    for name, expected_alpha in [('Cake house | garden glass', .60),
                                 ('Cake house | translucent glass blocks', .81)]:
        mat = mats[material_key(name)]
        node = next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        alpha = float(node.inputs['Alpha'].default_value)
        if abs(alpha - expected_alpha)>1.e-4:
            raise ValueError(('The reopened glazing lost its authored opacity',name,alpha))
        glazing[name] = alpha
    return {'bound_finishes':result, 'glass_opacities':glazing}

def compare(out,role,id):
    expected=np.load(out/'native-surfaces.npz');ref=expected['tri'];target=expected['material_ids'];oldnames=expected['materials'].tolist()
    empty()
    if role=='fbx':bpy.ops.import_scene.fbx(filepath=str(out/(id+'.fbx')),use_anim=False)
    elif role=='obj':bpy.ops.wm.obj_import(filepath=str(out/'obj'/(id+'.obj')),forward_axis='Y',up_axis='Z')
    else:bpy.ops.wm.stl_import(filepath=str(out/(id+'.stl')),forward_axis='Y',up_axis='Z',use_scene_unit=True,use_mesh_validate=False)
    tri,mats,names,objects,uv=sample_scene()
    if role=='stl':
        measurements=verify_stl_facets(out/(id+'.stl'),ref,tri)
        save(out/'stl-reopened.json',dict(role=role,oriented_triangles=len(ref),max_coordinate_error_m=0,
            matching_material_triangles=0,mesh_groups=len(objects),materials=0,uv_groups=0,imported_images={},
            units='metres',axes='east/north/up',**measurements))
        return
    assert len(tri)==len(ref),(role,len(tri),len(ref))
    centres=np.mean(tri,axis=1);index=KDTree(len(tri))
    for i,pt in enumerate(centres):index.insert(pt,i)
    index.balance()
    assigned=set();max_error=0.;material_matches=0
    tol=.00008
    for i,(t,centre)in enumerate(zip(ref,np.mean(ref,axis=1))):
        options=index.find_range(centre,tol)
        best=None
        for _,j,_d in options:
            if j in assigned:continue
            if role!='stl' and names[mats[j]]!=oldnames[target[i]]:continue
            err=min(np.abs(t-np.roll(tri[j],k,axis=0)).max() for k in range(3))
            if err<=tol and (best is None or err<best[0]):best=err,j
        if best is None:raise ValueError((role,'oriented triangle missing',i,centre.tolist(),oldnames[target[i]],len(options)))
        max_error=max(max_error,float(best[0]));assigned.add(best[1]);material_matches+=role!='stl'
    assert len(assigned)==len(ref)
    images={}
    for image in bpy.data.images:
        if image.packed_file:images[image.name]=hashlib.sha256(image.packed_file.data).hexdigest()
        elif image.filepath:
            p=Path(bpy.path.abspath(image.filepath))
            if p.is_file():images[image.name]=digest(p)
    actual_set=set(images.values());source_images={digest(p) for p in (out/'obj').glob('*.png')}
    if role!='stl' and not source_images <= actual_set:
        raise ValueError((role,'reopened images do not cover packed originals',source_images-actual_set))
    save(out/(role+'-reopened.json'),dict(role=role,oriented_triangles=len(assigned),max_coordinate_error_m=max_error,
        matching_material_triangles=material_matches,mesh_groups=len(objects),materials=len(names) if role!='stl' else 0,
        uv_groups=uv,imported_images=images,finishes=verify_finishes(),units='metres'))
stage,blend,out,id=sys.argv[sys.argv.index('--')+1:];out=Path(out)
if stage=='export':export(Path(blend),out,id)
else:compare(out,stage,id)
