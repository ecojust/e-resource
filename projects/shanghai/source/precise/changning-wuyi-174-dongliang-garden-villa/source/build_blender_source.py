"""Create the editable villa, then reopen it in a fresh Blender process and compare it to the GLB."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
UV='174 architectural finish'
TEXTURES={'174 | cream roughcast':SOURCE/'wuyi-cream-roughcast.png',
          '174 | weathered interlocking clay tiles':SOURCE/'wuyi-clay-tiles.png',
          '174 | grey streaked balcony facing':SOURCE/'south-garden-grey-facing.png'}


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def document(raw):
    with raw.open('rb') as stream:
        magic,ver,length,size,kind=struct.unpack('<4sIIII',stream.read(20))
        assert (magic,ver,length,kind)==(b'glTF',2,raw.stat().st_size,0x4e4f534a)
        return json.loads(stream.read(size))


def rights(raw):
    meta=document(raw)['extras']
    keys=('photo_author','photo_source','license_url','geometry_license','texture_license')
    assert all(isinstance(meta[k],str) and meta[k].strip() for k in keys)
    return {k:meta[k] for k in keys}


def texture_extension(doc,name):
    mat=next(m for m in doc['materials'] if m['name']==name)
    tex=doc['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]
    sampler=doc['samplers'][tex['sampler']]
    if sampler.get('wrapS',10497)!=10497 or sampler.get('wrapT',10497)!=10497:
        raise ValueError('Expected repeating architectural finish')
    return 'REPEAT'


def prepare_group_file(path):
    from build_model import META, PALETTE, VillaBuilder, add_building
    b=VillaBuilder(PALETTE)
    add_building(b,False)
    groups=defaultdict(list)
    for item in b.parts:groups[item['label']].append(item)
    palette={k:v for k,v in PALETTE.items() if any(item['material']==k for item in b.parts)}
    with path.open('w') as stream:
        json.dump(dict(groups=groups,palette=palette,metadata=META),stream,ensure_ascii=False,separators=(',',':'))


def create(blend,raw,group_file):
    import bpy
    from mathutils import Vector
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version=0
    data=json.loads(group_file.read_bytes())
    scene=bpy.context.scene
    scene.unit_settings.system='METRIC'
    scene['model_id']=data['metadata']['id']
    scene['author_glb_sha256']=sha(raw)
    for field,value in rights(raw).items():scene[field]=value
    given=document(raw)
    for name,spec in data['palette'].items():
        mat=bpy.data.materials.new(name=name);mat.use_nodes=True
        node=mat.node_tree.nodes.get('Principled BSDF')
        node.inputs['Base Color'].default_value=(*spec['color'],1.)
        mat.diffuse_color=(*spec['color'],1.)
        node.inputs['Roughness'].default_value=spec.get('roughness',.75)
        node.inputs['Metallic'].default_value=spec.get('metallic',0.)
        if name in TEXTURES:
            im=bpy.data.images.load(str(TEXTURES[name]));im.pack();im.filepath='//'+TEXTURES[name].name
            imnode=mat.node_tree.nodes.new('ShaderNodeTexImage');imnode.image=im;imnode.extension=texture_extension(given,name)
            uv=mat.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map=UV
            mat.node_tree.links.new(uv.outputs['UV'],imnode.inputs['Vector'])
            mat.node_tree.links.new(imnode.outputs['Color'],node.inputs['Base Color'])
    for name,parts in data['groups'].items():
        xyz=[];faces=[];mats=[];slots=[];uvs=[]
        for part in parts:
            start=len(xyz);xyz.extend(part['vertices'])
            mat=part['material']
            if mat not in mats:mats.append(mat)
            for face in part['triangles']:
                faces.append(tuple(start+i for i in face));slots.append(mats.index(mat))
                if mat in TEXTURES:
                    uvs.extend((part['texcoords'][i][0],1.-part['texcoords'][i][1])for i in face)
                else:uvs.extend([(0.,0.)]*3)
        mesh=bpy.data.meshes.new(name)
        mesh.from_pydata(xyz,[],faces);mesh.update()
        for m in mats:mesh.materials.append(bpy.data.materials[m])
        mesh.polygons.foreach_set('material_index',slots)
        if any(m in TEXTURES for m in mats):
            layer=mesh.uv_layers.new(name=UV);layer.active_render=True
            layer.data.foreach_set('uv',[v for xy in uvs for v in xy])
        ob=bpy.data.objects.new(name,mesh)
        scene.collection.objects.link(ob)
    views=json.loads((SOURCE/'cameras.json').read_bytes())
    for i,pose in enumerate(views):
        name=pose['label'];cam=bpy.data.objects.new(name,bpy.data.cameras.new(name))
        scene.collection.objects.link(cam);cam.location=pose['eye']
        delta=Vector(pose['target'])-cam.location
        cam.rotation_euler=delta.to_track_quat('-Z','Y').to_euler()
        cam.data.sensor_fit='HORIZONTAL';cam.data.lens=cam.data.sensor_width*delta.length/pose['width_m']
        if i==0:scene.camera=cam
    scene.render.resolution_x=views[0]['width'];scene.render.resolution_y=views[0]['height']
    scene.world=bpy.data.worlds.new('Courtyard daylight');scene.world.color=(.46,.46,.44)
    lamp=bpy.data.lights.new('Sun',type='SUN');lamp.energy=3.0
    ob=bpy.data.objects.new('Courtyard sun',lamp);scene.collection.objects.link(ob)
    ob.rotation_euler=Vector((-.38,.54,-.72)).to_track_quat('-Z','Y').to_euler()
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
    bpy.ops.wm.save_as_mainfile(filepath=str(blend.resolve()),compress=True)


def verify(blend,raw,groups,output):
    import bpy
    import numpy as np
    from runpy import run_path
    from mathutils import Vector
    scene=bpy.context.scene
    assert Path(bpy.data.filepath).resolve()==blend.resolve() and scene['author_glb_sha256']==sha(raw)
    assert all(scene[k]==v for k,v in rights(raw).items())
    data=json.loads(groups.read_bytes())
    meshes={ob.name:ob for ob in scene.objects if ob.type=='MESH'}
    assert set(meshes)==set(data['groups'])
    reader=run_path(str(PROJECT/'source/precise/changning-hengchang-li-yuyuan-road-gatehouse/measurements/check_render_uv.py'))['Model'](raw)
    source={}
    for primitive in reader.doc['meshes'][0]['primitives']:
        name=reader.doc['materials'][primitive['material']]['name'];attrs=primitive['attributes']
        pos=reader.accessor(attrs['POSITION']);indices=reader.accessor(primitive['indices']).reshape(-1,3)
        uv=reader.accessor(attrs['TEXCOORD_0']) if name in TEXTURES else None
        table=defaultdict(list)
        for ids in indices:
            keys=[tuple(map(float,row))for row in pos[ids]]
            order=min(range(3),key=lambda n:tuple(keys[n:]+keys[:n]))
            key=tuple(keys[order:]+keys[:order])
            mapped=tuple((float(u),1.-float(v)) for u,v in uv[ids]) if uv is not None else ()
            table[key].append(mapped[order:]+mapped[:order])
        source[name]=table
    maximum=0.;uv_count=0;triangles=0
    for ob in meshes.values():
        mesh=ob.data
        assert np.allclose(ob.matrix_world,np.eye(4))
        for face in mesh.polygons:
            assert len(face.vertices)==3
            name=mesh.materials[face.material_index].name
            xyz=[tuple(mesh.vertices[i].co)for i in face.vertices]
            keys=[(x,z,-y)for x,y,z in xyz];order=min(range(3),key=lambda n:tuple(keys[n:]+keys[:n]))
            key=tuple(keys[order:]+keys[:order])
            matches=source[name][key]
            if not matches:raise ValueError('Unmatched native face in '+ob.name)
            expected=matches.pop()
            if name in TEXTURES:
                layer=mesh.uv_layers[UV];values=[tuple(layer.data[i].uv)for i in face.loop_indices]
                maximum=max(maximum,float(np.max(np.abs(np.asarray(values[order:]+values[:order])-expected))))
                uv_count+=3
            triangles+=1
    assert all(not rows for lookup in source.values()for rows in lookup.values()) and maximum<1e-5
    texture_report={}
    for name,file in TEXTURES.items():
        mat=bpy.data.materials[name];shader=mat.node_tree.nodes.get('Principled BSDF')
        tex=shader.inputs['Base Color'].links[0].from_node
        assert tex.inputs['Vector'].links[0].from_node.uv_map==UV and tex.extension=='REPEAT'
        digest=hashlib.sha256(bytes(tex.image.packed_file.data)).hexdigest()
        assert digest==sha(file);texture_report[name]=digest
    views=json.loads((SOURCE/'cameras.json').read_bytes())
    for view in views:
        cam=scene.objects[view['label']]
        assert cam.type=='CAMERA' and (cam.location-Vector(view['eye'])).length<1e-5
    report=dict(blend_sha256=sha(blend),source_glb_sha256=sha(raw),editable_groups=len(meshes),
                triangles=triangles,matched_textured_corners=uv_count,maximum_UV_error=maximum,
                packed_textures=texture_report,cameras=len(views),match_raw=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report),flush=True)


def main():
    if '--' in sys.argv:
        phase,*paths=sys.argv[sys.argv.index('--')+1:]
        if phase=='create':create(*map(Path,paths))
        elif phase=='verify':verify(*map(Path,paths))
        else:raise ValueError(phase)
        return
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('raw',type=Path);p.add_argument('blend',type=Path);p.add_argument('report',type=Path)
    p.add_argument('--blender',default='blender');a=p.parse_args()
    a.blend.parent.mkdir(parents=True,exist_ok=True);a.report.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=a.blend.parent) as d:
        groups=Path(d)/'editable.json'
        prepare_group_file(groups)
        flags=['--factory-startup','-t','2','--python-exit-code','1','-P',str(Path(__file__).resolve()),'--']
        subprocess.run([a.blender,'-b',*flags,'create',a.blend,a.raw,groups],check=True)
        subprocess.run([a.blender,'-b',a.blend,'-t','2','--python-exit-code','1','-P',str(Path(__file__).resolve()),'--','verify',a.blend,a.raw,groups,a.report],check=True)


if __name__=='__main__':main()
