"""Install or verify the Xiangyang Road residence materials, original UVs and surveyed cameras in Blender."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
PROJECT=next(p for p in [*SOURCE.parents,Path(os.getenv('E_RESOURCE_SHANGHAI','.'))] if (p/'tools/verify_editable_model.py').is_file())
sys.path.insert(0,str(SOURCE))
from materials import PLASTER, BASE
shared=PROJECT/'source/precise/xuhui-baisaizhong-apartments-fuxing-road-corner/source/build_blender_source.py'
spec=importlib.util.spec_from_file_location('shanghai_textured_native',shared)
helpers=importlib.util.module_from_spec(spec)
import_paths = sys.path.copy()
try:
    spec.loader.exec_module(helpers)
finally:
    sys.path[:] = import_paths
# The shared readers key UV corners by oriented Float32 vertex tuples and check the packed PNG bytes.
helpers.SOURCE=SOURCE
helpers.MODEL_ID='xuhui-xiangyang-364-arched-residence'
helpers.TEXTURES={PLASTER:SOURCE/'street-plaster.png', BASE:SOURCE/'granite-chips.png'}
helpers.UV='Xiangyang 364 original face UV'
NODE='Xiangyang 364 packed exterior finish'

def read_file(path):return json.loads(path.read_bytes())
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def attribution(raw):
    doc=helpers.raw_document(raw)['extras']
    assert doc['id']==helpers.MODEL_ID and doc['photos_embedded'] is False
    assert doc['geometry_license']==doc['texture_license']=='MIT'
    fields = ('id', 'name', 'address', 'heritage_group', 'period', 'geometry_license',
              'texture_license', 'photos_embedded', 'source', 'photo_source', 'scope')
    required = ('name', 'address', 'period')
    assert all(doc.get(key) for key in required)
    return {key: doc[key] for key in fields if key in doc and isinstance(doc[key], (bool, str))}

def prepare(_scene):
    import bpy
    scene=bpy.context.scene; raw=Path(os.environ['XIANGYANG_364_RAW'])
    for material,path in helpers.source_materials(raw).items():
        mat=bpy.data.materials[material];nodes=mat.node_tree.nodes;links=mat.node_tree.links
        shader=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
        uv=nodes.new('ShaderNodeUVMap');uv.uv_map=helpers.UV
        node=nodes.new('ShaderNodeTexImage');node.name=NODE
        node.image=bpy.data.images.load(str(path),check_existing=True);node.image.pack();node.image.filepath='//'+path.name
        node.extension=helpers.texture_extension(helpers.raw_document(raw),material)
        links.new(uv.outputs['UV'],node.inputs['Vector']);links.new(node.outputs['Color'],shader.inputs['Base Color'])
        helpers.native_uv(scene,helpers.texture_faces(raw,material),True,material)
    for k,v in attribution(raw).items():scene[k]=v
    scene['source_glb_sha256']=digest(raw)
    aliases = read_file(Path(os.environ['XIANGYANG_364_GROUPS']))['original_names']
    for name, original in aliases.items():
        scene.objects[name]['authored_group_name'] = original
    names=[o.name for o in scene.objects if o.type=='MESH']
    scene['editable_group_sha256']=helpers.editable_groups(names)['names_sha256']
    cameras=helpers.cameras(scene,True)
    scene.render.resolution_x=cameras[0]['width'];scene.render.resolution_y=cameras[0]['height'];scene.render.resolution_percentage=100
    bpy.context.view_layer.update()

def verify(blend,raw,output):
    import bpy
    scene=bpy.context.scene;doc=read_file(output)
    assert Path(bpy.data.filepath).samefile(blend) and doc['match_raw'] and scene['source_glb_sha256']==digest(raw)
    materials={}
    for material,path in helpers.source_materials(raw).items():
        mat=bpy.data.materials[material];nodes=mat.node_tree.nodes;node=nodes[NODE];shader=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
        assert node.extension=='REPEAT' and shader.inputs['Base Color'].links[0].from_node==node
        assert node.inputs['Vector'].links[0].from_node.uv_map==helpers.UV
        assert hashlib.sha256(bytes(node.image.packed_file.data)).hexdigest()==digest(path)
        faces=helpers.texture_faces(raw,material)
        materials[material]=dict(packed_png_sha256=digest(path),textured_corners=len(faces)*3,extension=node.extension,
                                 max_uv_error=helpers.native_uv(scene,faces,False,material))
    names=[o.name for o in scene.objects if o.type=='MESH'];groups=helpers.editable_groups(names)
    assert groups['names_sha256']==scene['editable_group_sha256'] and groups['count']==doc['mesh_count']
    aliases = read_file(Path(os.environ['XIANGYANG_364_GROUPS']))['original_names']
    assert all(scene.objects[name]['authored_group_name'] == original for name, original in aliases.items())
    data=attribution(raw);assert all(scene[k]==v for k,v in data.items())
    doc['xiangyang_364']={'metadata':data,'raw_sha256':digest(raw),'editable_groups':groups,'textured_materials':materials,
                    'cameras':helpers.cameras(scene,False)}
    output.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    phase=os.environ['XIANGYANG_364_STAGE']
    if phase=='make':
        import bpy
        bpy.app.handlers.save_pre.append(bpy.app.handlers.persistent(prepare))
    elif phase=='reopen':verify(*map(Path,sys.argv[sys.argv.index('--')+1:]))
    else:raise ValueError(phase)
