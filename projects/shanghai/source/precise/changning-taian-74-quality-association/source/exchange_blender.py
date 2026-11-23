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
def facet_keys(triangles, oriented):
    """Represent each triangle by one float32 record, canonically ordered."""
    result = np.empty(len(triangles), dtype='V36')
    for start in range(0, len(triangles), 8192):
        points = np.array(triangles[start:start+8192], dtype='<f4', copy=True)
        if not np.isfinite(points).all():
            raise ValueError('Nonfinite STL coordinate')
        points[points == 0] = 0.0  # Signed zero has identical geometric meaning.
        order = np.lexsort((points[:,:,2], points[:,:,1], points[:,:,0]), axis=1)
        rows = np.arange(len(points))[:, None]
        ordered = points[rows, order]
        if oriented:
            cyclic = (order[:, :1] + np.arange(3)) % 3
            rotated = points[rows, cyclic]
            # With two equal minima either winding is the same degenerate cycle.
            tied = np.all(ordered[:,0] == ordered[:,1], axis=1)
            rotated[tied] = ordered[tied]
            ordered = rotated
        result[start:start+len(points)] = np.ascontiguousarray(ordered).reshape(-1,9).view('V36').reshape(-1)
    return result


def verify_stl_facets(path, reference, imported):
    """Compare native, stored and reimported facets without Python vertex tuples."""
    import struct
    with path.open('rb') as stream:
        header = stream.read(84)
    count = struct.unpack_from('<I', header, 80)[0]
    if path.stat().st_size != 84 + 50*count or count != len(reference):
        raise ValueError('Invalid STL facet count')
    data = np.memmap(path, mode='r', dtype=np.uint8)
    facets = np.ndarray((count,3,3), dtype='<f4', buffer=data, offset=96, strides=(50,12,4))
    expected = np.sort(facet_keys(reference, True))
    stored = np.sort(facet_keys(facets, True))
    if not np.array_equal(expected, stored):
        raise ValueError('The oriented STL facets differ from native frontage/inward/upward metre coordinates')
    del expected
    loaded = np.sort(facet_keys(imported, True))
    if not np.array_equal(loaded, stored):
        keys, counts = np.unique(stored, return_counts=True)
        imported_keys, imported_counts = np.unique(loaded, return_counts=True)
        positions = np.searchsorted(keys, imported_keys)
        if (np.any(positions == len(keys)) or not np.array_equal(keys[positions], imported_keys)
                or np.any(imported_counts > counts[positions])):
            raise ValueError('STL import added or reversed triangles')
    del stored, loaded
    originals = np.unique(facet_keys(facets, False))
    if not np.array_equal(originals, np.unique(facet_keys(imported, False))):
        raise ValueError('STL import changed the geometric surface')
    return dict(serialized_facets=count, blender_import_facets=len(imported),
                coincident_facets_merged=count-len(imported), unique_geometric_faces=len(originals))

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
    photographed_finishes = {'scored pale render', 'warm red entrance tile', 'off-white cast moulding', 'blue-black canopy metal'}
    if set(expected) != photographed_finishes:
        raise ValueError(('Expected the four photographed portico finishes', sorted(expected)))
    mats={material_key(m.name):m for m in bpy.data.materials}
    result={}
    for name,(color_file,normal_file) in expected.items():
        mat=mats[material_key(name)]
        node=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        colour=material_images(node.inputs['Base Color']);normal=material_images(node.inputs['Normal'])
        if colour!=[color_file] or normal!=[normal_file]:
            raise ValueError(('The reopened material changed image slots',name,colour,normal))
        result[name]={'base_color':colour,'normal':normal}
    return {'bound_finishes':result}

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
            units='metres',axes='right along street / into the building / up',**measurements))
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
