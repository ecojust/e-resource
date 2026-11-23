"""Create a Blender scene or verify its actual reopen using the authored component list."""
import argparse
import base64
import hashlib
import json
import math
import sys
import tempfile
from pathlib import Path
import bpy
from mathutils import Matrix, Vector


def title(index, text):
    prefix = f'{index:05d} '
    # Blender stores at most 63 UTF-8 bytes. The full label stays on the object.
    return prefix + text.encode('utf-8')[:63-len(prefix)].decode('utf-8','ignore')


def orientation(view):
    forward = (Vector(view['target'])-Vector(view['eye'])).normalized()
    up = Vector(view.get('world_up', [0, 0, 1])).normalized()
    if abs(forward.dot(up)) > .99999:
        up = Vector([0,1,0])
    right = forward.cross(up).normalized()
    adjusted_up = right.cross(forward).normalized()
    return Matrix((right, adjusted_up, -forward)).transposed().to_quaternion()


def set_material(name, spec, inputs, temp):
    material = bpy.data.materials.new(name)
    material['original_name'] = name
    material.use_nodes = True
    material.diffuse_color = (*spec['color'], spec.get('alpha',1))
    bsdf = material.node_tree.nodes.get('Principled BSDF')
    for socket, value in (('Base Color',material.diffuse_color), ('Roughness',spec['roughness']),
                          ('Metallic',spec.get('metallic',0)), ('Alpha',spec.get('alpha',1))):
        bsdf.inputs[socket].default_value = value
    for channel in ('texture','normal'):
        if channel not in spec:
            continue
        file = spec[channel]
        image = next((im for im in bpy.data.images if im.get('source_image_file')==file),None)
        if image is None:
            if Path(file).name != file:raise ValueError(file)
            path = temp/file
            path.write_bytes(base64.b64decode(inputs[file]))
            image = bpy.data.images.load(str(path))
            image.name = file
            image['source_image_file'] = file
            if channel=='normal':image.colorspace_settings.name = 'Non-Color'
            image.pack()
            image.filepath = '//'+file
        tex = material.node_tree.nodes.new('ShaderNodeTexImage')
        tex.name = channel
        tex.image = image
        tex.extension = {10497:'REPEAT',33071:'EXTEND',33648:'MIRROR'}[spec[channel+'_wrap']]
        output = tex.outputs['Color']
        if channel=='normal':
            normal = material.node_tree.nodes.new('ShaderNodeNormalMap')
            normal.inputs['Strength'].default_value = spec['normal_strength']
            material.node_tree.links.new(output, normal.inputs['Color'])
            output = normal.outputs['Normal']
        material.node_tree.links.new(output, bsdf.inputs['Normal' if channel=='normal' else 'Base Color'])
    return material


def make(package, path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with tempfile.TemporaryDirectory(dir=path.parent) as temp:
        mats = {name:set_material(name,spec,package['textures'],Path(temp))
                for name,spec in package['materials'].items()}
    scene = bpy.context.scene
    for i, part in enumerate(package['parts']):
        name = title(i,part['label'])
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(part['vertices'],[],part['triangles'])
        mesh.update()
        obj = bpy.data.objects.new(name,mesh)
        obj['architectural_label'] = part['label']
        obj['index_in_source'] = i
        scene.collection.objects.link(obj)
        mesh.materials.append(mats[part['material']])
        if part.get('texcoords'):
            layer = mesh.uv_layers.new(name='Building UV')
            for loop,item in zip(mesh.loops,layer.data):
                u,v = part['texcoords'][loop.vertex_index]
                item.uv = (u,1-v)
    for i, view in enumerate(package['metadata'].get('camera_views',[])):
        name = title(i,view.get('label',view['name']))
        camera = bpy.data.cameras.new(name)
        obj = bpy.data.objects.new(name,camera)
        obj['camera_id'] = view['name']
        scene.collection.objects.link(obj)
        obj.location = view['eye']
        obj.rotation_mode = 'QUATERNION'
        obj.rotation_quaternion = orientation(view)
        camera.angle = math.radians(view['fov'])
        if scene.camera is None:scene.camera = obj
    scene['reference_sha256'] = package['reference_sha256']
    scene['model_id'] = package['metadata']['id']
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)


def verify(package):
    scene = bpy.context.scene
    assert scene['reference_sha256']==package['reference_sha256']
    objects = {o['index_in_source']:o for o in scene.objects if o.type=='MESH'}
    assert len(objects)==len(package['parts'])
    triangles=uv_corners=0
    for i, part in enumerate(package['parts']):
        obj=objects[i]; mesh=obj.data
        assert obj['architectural_label']==part['label'] and mesh.materials[0]['original_name']==part['material']
        assert len(mesh.vertices)==len(part['vertices']) and len(mesh.polygons)==len(part['triangles'])
        assert all((obj.matrix_world@v.co-Vector(p)).length<2e-5 for v,p in zip(mesh.vertices,part['vertices']))
        assert all(list(p.vertices)==face for p,face in zip(mesh.polygons,part['triangles']))
        triangles+=len(mesh.polygons)
        if part.get('texcoords'):
            for loop,item in zip(mesh.loops,mesh.uv_layers.active.data):
                u,v=part['texcoords'][loop.vertex_index]
                assert abs(item.uv.x-u)<2e-5 and abs(item.uv.y-(1-v))<2e-5
                uv_corners+=1
    mats={m['original_name']:m for m in bpy.data.materials if 'original_name' in m}
    assert set(mats)==set(package['materials'])
    for name,spec in package['materials'].items():
        nodes=mats[name].node_tree.nodes
        bsdf=nodes.get('Principled BSDF')
        for channel,slot in [('texture','Base Color'),('normal','Normal')]:
            if channel not in spec:continue
            node=bsdf.inputs[slot].links[0].from_node
            if channel=='normal':
                assert node.type=='NORMAL_MAP' and abs(node.inputs['Strength'].default_value-spec['normal_strength'])<1e-5
                node=node.inputs['Color'].links[0].from_node
                assert node.image.colorspace_settings.name=='Non-Color'
            assert node.image['source_image_file']==spec[channel]
            assert node.extension=={10497:'REPEAT',33071:'EXTEND',33648:'MIRROR'}[spec[channel+'_wrap']]
    images={im['source_image_file']:hashlib.sha256(bytes(im.packed_file.data)).hexdigest() for im in bpy.data.images if im.packed_file}
    assert images=={k:hashlib.sha256(base64.b64decode(v)).hexdigest() for k,v in package['textures'].items()}
    cameras={o['camera_id']:o for o in scene.objects if o.type=='CAMERA'}
    views=package['metadata'].get('camera_views',[])
    assert set(cameras)=={v['name'] for v in views}
    for v in views:
        obj=cameras[v['name']]
        assert (obj.location-Vector(v['eye'])).length<1e-5 and abs(obj.data.angle-math.radians(v['fov']))<1e-5
        assert abs(obj.matrix_world.to_quaternion().dot(orientation(v)))>.99999
    return dict(reference_sha256=package['reference_sha256'],parts=len(objects),triangles=triangles,
                uv_corners=uv_corners,cameras=len(cameras),images=images,materials=len(mats))

p=argparse.ArgumentParser()
p.add_argument('phase',choices=['make','verify'])
for k in ('components','blend','report'):p.add_argument(k,type=Path)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
package=json.loads(a.components.read_bytes())
a.blend.parent.mkdir(parents=True,exist_ok=True)
if a.phase=='make':make(package,a.blend)
elif Path(bpy.data.filepath).resolve()!=a.blend.resolve():raise ValueError('Open the specified .blend on the Blender command line')
result=verify(package)
result['file']=a.blend.name;result['bytes']=a.blend.stat().st_size
result['sha256']=hashlib.sha256(a.blend.read_bytes()).hexdigest()
a.report.parent.mkdir(parents=True,exist_ok=True)
a.report.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
