"""Install or verify the Maresca house materials, original UVs and surveyed cameras in Blender."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
PROJECT=next(p for p in [*SOURCE.parents,Path(os.getenv('E_RESOURCE_SHANGHAI','.'))] if (p/'tools/verify_editable_model.py').is_file())
sys.path.insert(0,str(SOURCE))
from materials import BRICK, CREAM, TILE
shared=PROJECT/'source/precise/xuhui-baisaizhong-apartments-fuxing-road-corner/source/build_blender_source.py'
spec=importlib.util.spec_from_file_location('shanghai_textured_native',shared)
helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)
# The shared readers key UV corners by oriented Float32 vertex tuples and check the packed PNG bytes.
helpers.SOURCE=SOURCE
helpers.MODEL_ID='xuhui-wuyuan-289-garden-houses'
helpers.TEXTURES={BRICK:SOURCE/'red-facing-brick.png',CREAM:SOURCE/'lime-plaster.png',TILE:SOURCE/'clay-roof.png'}
helpers.UV='Maresca original face UV'
NODE='Maresca packed exterior finish'

def read_file(path):return json.loads(path.read_bytes())
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def attribution(raw):
    doc=helpers.raw_document(raw)['extras']
    assert doc['id']==helpers.MODEL_ID and doc['photos_embedded'] is False
    assert doc['geometry_license']==doc['texture_license']=='MIT'
    return {k:doc[k] for k in ('id','name','address','heritage_group','period','geometry_license','texture_license','photos_embedded','source','photo_source')}

def prepare(_scene):
    import bpy
    scene=bpy.context.scene; raw=Path(os.environ['MARESCA_RAW'])
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
    data=attribution(raw);assert all(scene[k]==v for k,v in data.items())
    doc['maresca']={'metadata':data,'raw_sha256':digest(raw),'editable_groups':groups,'textured_materials':materials,
                    'cameras':helpers.cameras(scene,False)}
    output.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    phase=os.environ['MARESCA_STAGE']
    if phase=='make':
        import bpy
        bpy.app.handlers.save_pre.append(bpy.app.handlers.persistent(prepare))
    elif phase=='reopen':verify(*map(Path,sys.argv[sys.argv.index('--')+1:]))
    else:raise ValueError(phase)
