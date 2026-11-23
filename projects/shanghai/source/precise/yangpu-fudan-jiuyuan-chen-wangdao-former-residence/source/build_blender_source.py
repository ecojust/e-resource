"""Make the editable Jiuyuan garden elevation project and reopen it in a clean Blender process.

Run from projects/shanghai with a full, uncompressed author GLB:
  python source/precise/yangpu-fudan-jiuyuan-chen-wangdao-former-residence/source/build_blender_source.py prepare RAW OUT
  python source/precise/yangpu-fudan-jiuyuan-chen-wangdao-former-residence/source/build_blender_source.py run RAW OUT
"""
import argparse
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import numpy as np

SOURCE=Path(__file__).absolute().parent
ID='yangpu-fudan-jiuyuan-chen-wangdao-former-residence'
UV_NAME='Jiuyuan roughcast and roof UV'
LEGAL='Photograph by Fayhoo, CC BY-SA 3.0. Geometry and procedural finishes are original project work.'
PHOTO_URL='https://commons.wikimedia.org/wiki/File:Residence_of_Chen_Wangdao.jpg'

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def write(p,data):
    temp=p.with_suffix(p.suffix+'.partial')
    temp.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n');temp.replace(p)

def read_gltf(p):
    raw=p.read_bytes()
    magic,ver,size,n,kind=struct.unpack_from('<4sIIII',raw)
    assert (magic,ver,size,kind)==(b'glTF',2,len(raw),0x4e4f534a)
    m=json.loads(raw[20:20+n]);sz,tag=struct.unpack_from('<II',raw,20+n)
    assert tag==0x004e4942
    buf=memoryview(raw)[28+n:];assert sz==len(buf) and m['extras']['id']==ID
    return m,buf

def accessor(doc,buf,ix):
    a=doc['accessors'][ix];v=doc['bufferViews'][a['bufferView']]
    dtype=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']])
    cols={'VEC3':3,'VEC2':2,'SCALAR':1}[a['type']]
    off=a.get('byteOffset',0)+v.get('byteOffset',0);stride=v.get('byteStride',dtype.itemsize*cols)
    return np.ndarray((a['count'],cols),dtype=dtype,buffer=buf,offset=off,strides=(stride,dtype.itemsize))

def signature(points,uv):
    """Hash the multiset of oriented triangle corners, including the two UV values."""
    full=np.concatenate((points,uv),axis=2).astype('<f4')
    full[full==0]=0
    first=np.lexsort(tuple(full[:,:,i]for i in (4,3,2,1,0)),axis=1)[:,0]
    perm=(first[:,None]+np.arange(3))%3
    ordered=np.ascontiguousarray(full[np.arange(len(full))[:,None],perm].reshape(-1,15)).view('V60').reshape(-1)
    return hashlib.sha256(np.sort(ordered).tobytes()).hexdigest()

def raw_textures(raw):
    doc,binary=read_gltf(raw);mats={};images={}
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            material=doc['materials'][prim['material']];pbr=material['pbrMetallicRoughness'];name=material['name']
            if 'baseColorTexture' not in pbr:continue
            tex=doc['textures'][pbr['baseColorTexture']['index']];img=doc['images'][tex['source']]
            sampler=doc.get('samplers',[{}])[tex.get('sampler',0)]
            assert sampler.get('wrapS',10497)==sampler.get('wrapT',10497)==10497
            bv=doc['bufferViews'][img['bufferView']];off=bv.get('byteOffset',0)
            digest=hashlib.sha256(binary[off:off+bv['byteLength']]).hexdigest()
            assert Path(img['name']).name==img['name'] and sha(SOURCE/img['name'])==digest
            images[name]={'image':img['name'],'bytes':bv['byteLength'],'sha256':digest}
            ids=accessor(doc,binary,prim['indices']).reshape(-1,3)
            attrs=prim['attributes'];p=accessor(doc,binary,attrs['POSITION'])[ids][:,:,[0,2,1]].copy();p[:,:,1]*=-1.
            uv=accessor(doc,binary,attrs['TEXCOORD_0'])[ids].copy();uv[:,:,1]=(1.-uv[:,:,1].astype(np.float64)).astype(np.float32)
            mats.setdefault(name,[]).append((p,uv))
    for name,samples in mats.items():
        pp,uv=zip(*samples);images[name]['oriented_uv_sha256']=signature(np.concatenate(pp),np.concatenate(uv));images[name]['textured_corners']=sum(len(a)*3 for a in pp)
    assert len(images)>=2
    return images

def semantic(label):
    if label.startswith('Bay'):return '弧窗与上缘'
    return {'Middle':'中央立面','Hall':'底层钢窗','Door':'花园门','Upper':'二层钢窗','Balcony':'悬挑阳台','West':'退台西翼','Setback':'上层退台','Vent':'通风口','Tower':'屋冠与烟囱','Ground':'花园台阶'}[label.split(' | ')[0]]

def prepare(raw,out):
    from build_model import build
    b=build(False);doc,_=read_gltf(raw)
    regenerated=out/'regenerated.glb';b.save(regenerated,doc['extras'])
    assert sha(regenerated)==sha(raw),'Rebuilt grouped source differs from the selected complete GLB'
    names=Counter(x['label'] for x in b.parts);seen=Counter();parts=[]
    for part in b.parts:
        key=part['label'];seen[key]+=1;end=f' {seen[key]:03d}' if names[key]>1 else ''
        name=key+end
        if len(name.encode())>63:
            cut=key.encode()[:48].decode('utf-8','ignore')
            name=cut+' '+hashlib.sha256(key.encode()).hexdigest()[:6]+end
        verts=np.asarray(part['vertices'],dtype='<f4');tris=np.asarray(part['triangles'],dtype=int)
        # Weld the split chart vertices within this one original component.
        # Distinct corner UVs are retained independently for every face loop.
        xyz,inv=np.unique(verts,axis=0,return_inverse=True)
        el={'name':name,'label':key,'collection':semantic(key),'material':part['material'],'v':xyz.tolist(),'t':inv[tris].tolist()}
        if 'texcoords' in part:
            uv=np.asarray(part['texcoords'],dtype='<f4')[tris];uv[:,:,1]=(1.-uv[:,:,1].astype(np.float64)).astype(np.float32)
            el['corner_uv']=uv.reshape(-1,2).tolist()
        parts.append(el)
    assert len(set(a['name']for a in parts))==len(parts)
    cams=json.loads((SOURCE/'cameras.json').read_text());assert len(cams)==7
    palette={m['name']:m['pbrMetallicRoughness'] for m in doc['materials']}
    data={'id':ID,'source':doc['extras'],'copyright':doc['asset'].get('copyright'), 'raw_sha256':sha(raw),'parts':parts,'materials':palette,
          'textures':raw_textures(raw),'cameras':cams,'layout_sha256':sha(SOURCE/'building-layout.json')}
    write(out/'editable-parts.json',data)
    report={'id':ID,'raw_sha256':sha(raw),'rebuilt_raw_sha256':sha(regenerated),'source_parts':len(parts),'faces':sum(len(a['t']) for a in parts),
            'materials':len(palette),'collections':dict(Counter(a['collection'] for a in parts)),'cameras':len(cams),'texture_signatures':data['textures'],
            'signed_parts':sha(out/'editable-parts.json'),'layout_sha256':data['layout_sha256'],'camera_sha256':sha(SOURCE/'cameras.json')}
    write(out/'editable-inputs.json',report);print(json.dumps(report,ensure_ascii=False))

def blender_make(out):
    import bpy
    from mathutils import Vector
    data=json.loads((out/'editable-parts.json').read_text())
    bpy.ops.wm.read_factory_settings(use_empty=True);prefs=bpy.context.preferences.filepaths;prefs.save_version=0
    scene=bpy.context.scene;scene.unit_settings.system='METRIC'
    scene['model_id']=ID;scene['raw_sha256']=data['raw_sha256'];scene['building_layout_sha256']=data['layout_sha256']
    scene['source']=PHOTO_URL;scene['attribution']=LEGAL;scene['glb_copyright']=data['copyright'];scene['scope']=data['source']['scope']
    mats={}
    for name,spec in data['materials'].items():
        mat=bpy.data.materials.new(name);mat.use_nodes=True;color=spec['baseColorFactor'];mat.diffuse_color=color
        nodes=mat.node_tree.nodes;links=mat.node_tree.links;shader=nodes.get('Principled BSDF')
        shader.inputs['Base Color'].default_value=color;shader.inputs['Roughness'].default_value=spec['roughnessFactor'];shader.inputs['Metallic'].default_value=spec['metallicFactor']
        if name in data['textures']:
            ti=data['textures'][name];uv=nodes.new('ShaderNodeUVMap');uv.uv_map=UV_NAME
            tex=nodes.new('ShaderNodeTexImage');tex.name='Packed architectural finish'
            tex.image=bpy.data.images.load(str(SOURCE/ti['image']),check_existing=True);tex.image.pack();tex.image.filepath='//'+ti['image'];tex.extension='REPEAT'
            links.new(uv.outputs['UV'],tex.inputs['Vector']);links.new(tex.outputs['Color'],shader.inputs['Base Color'])
        mats[name]=mat
    collections={}
    for a in data['parts']:
        name=a['collection']
        if name not in collections:
            coll=bpy.data.collections.new(name);scene.collection.children.link(coll);collections[name]=coll
        mesh=bpy.data.meshes.new(a['name']);mesh.from_pydata(a['v'],[],a['t']);mesh.update()
        mesh.materials.append(mats[a['material']])
        if 'corner_uv' in a:
            layer=mesh.uv_layers.new(name=UV_NAME);layer.data.foreach_set('uv',np.array(a['corner_uv'],dtype=np.float32).reshape(-1));layer.active_render=True
        ob=bpy.data.objects.new(a['name'],mesh);ob['architectural_label']=a['label'];collections[name].objects.link(ob)
    stage=bpy.data.collections.new('展览相机与照明');scene.collection.children.link(stage)
    for i,v in enumerate(data['cameras']):
        cd=bpy.data.cameras.new(v['label']);cam=bpy.data.objects.new(v['label'],cd);stage.objects.link(cam)
        cam.location=v['eye'];delta=Vector(v['target'])-cam.location;cam.rotation_euler=delta.to_track_quat('-Z','Y').to_euler()
        cd.type='PERSP';cd.sensor_fit='HORIZONTAL';cd.lens=cd.sensor_width*delta.length/v['width_m'];cd.clip_start=.025;cd.clip_end=400.
        cam['registered_view']=v['name'];cam['target_xyz']=[float(coordinate) for coordinate in v['target']]
        if i==0:scene.camera=cam
    light=bpy.data.lights.new('柔光','SUN');light.energy=3.2;light.angle=.13
    sun=bpy.data.objects.new('柔光',light);stage.objects.link(sun);sun.location=(-22,-32,48);sun.rotation_euler=(-sun.location).to_track_quat('-Z','Y').to_euler()
    world=bpy.data.worlds.new('展览背景');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.22,.26,.27,1.)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=.72;scene.world=world
    scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=False;scene.cycles.use_adaptive_sampling=True
    scene.render.resolution_x,scene.render.resolution_y=data['cameras'][0]['width'],data['cameras'][0]['height'];scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.filepath='//native-preview.png'
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
    bpy.context.view_layer.update();blend=out/(ID+'.blend')
    bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True);bpy.ops.wm.open_mainfile(filepath=str(blend))
    bpy.context.scene.render.filepath=str(out/'native-preview.png');bpy.ops.render.render(write_still=True)

def blender_verify(raw,out,project):
    from mathutils import Vector
    from bpy_extras.object_utils import world_to_camera_view
    import bpy
    import runpy
    blend=out/(ID+'.blend');proof=out/'reopened.json'
    sys.argv=[sys.argv[0],'--',str(blend),str(raw),str(proof)]
    runpy.run_path(str(project/'tools/verify_editable_model.py'),run_name='__main__')
    scene=bpy.context.scene;report=json.loads(proof.read_text());data=json.loads((out/'editable-parts.json').read_text())
    assert scene['raw_sha256']==sha(raw)==data['raw_sha256'] and scene['building_layout_sha256']==data['layout_sha256']
    groups={o.name:o for o in scene.objects if o.type=='MESH'}
    assert len(groups)==len(data['parts'])==report['mesh_count']
    samples={name:[]for name in data['textures']};counts=Counter()
    for part in data['parts']:
        ob=groups[part['name']];m=ob.data
        assert ob['architectural_label']==part['label'] and ob.users_collection[0].name==part['collection']
        assert len(m.polygons)==len(part['t']) and len(m.vertices)==len(part['v'])
        counts[part['collection']]+=1;material=part['material']
        if material not in samples:continue
        indices=np.empty(len(m.loops),dtype=np.int32);m.loops.foreach_get('vertex_index',indices)
        verts=np.empty(len(m.vertices)*3,dtype=np.float32);m.vertices.foreach_get('co',verts)
        layer=m.uv_layers[UV_NAME];assert layer.active_render;uv=np.empty(len(m.loops)*2,dtype=np.float32);layer.data.foreach_get('uv',uv)
        samples[material].append((verts.reshape(-1,3)[indices].reshape(-1,3,3),uv.reshape(-1,3,2)))
    for name,spec in data['textures'].items():
        mat=bpy.data.materials[name];nodes=mat.node_tree.nodes;tex=nodes['Packed architectural finish'];shader=nodes.get('Principled BSDF')
        assert tex.extension=='REPEAT' and shader.inputs['Base Color'].links[0].from_node==tex
        assert tex.inputs['Vector'].links[0].from_node.uv_map==UV_NAME and hashlib.sha256(bytes(tex.image.packed_file.data)).hexdigest()==spec['sha256']
        pp,uv=zip(*samples[name]);isig=signature(np.concatenate(pp),np.concatenate(uv))
        assert isig==spec['oriented_uv_sha256'] and sum(len(a)*3 for a in pp)==spec['textured_corners']
    for name,expected in data['materials'].items():
        sm=bpy.data.materials[name].node_tree.nodes.get('Principled BSDF')
        assert np.allclose(sm.inputs['Base Color'].default_value[:],expected['baseColorFactor'],atol=1.e-6)
        assert abs(sm.inputs['Metallic'].default_value-expected['metallicFactor'])<1.e-6 and abs(sm.inputs['Roughness'].default_value-expected['roughnessFactor'])<1.e-6
    for view in data['cameras']:
        cam=bpy.data.objects[view['label']];assert cam['registered_view']==view['name'] and (cam.location-Vector(view['eye'])).length<1.e-4
        distance=(Vector(view['target'])-cam.location).length
        assert abs(distance*cam.data.sensor_width/cam.data.lens-view['width_m'])<1.e-4
        uv=world_to_camera_view(scene,cam,Vector(view['target']));assert abs(uv.x-.5)<.001 and abs(uv.y-.5)<.001 and uv.z>0
    assert scene.camera['registered_view']=='overview'
    report.update(raw_sha256=sha(raw),blend_sha256=sha(blend),model_id=ID,cameras=data['cameras'],source_mesh_collections=dict(counts),layout_sha256=data['layout_sha256'],material_values_match=True,
                named_mesh_count=len(groups),packed_texture_checks=data['textures'],checked_uv_corners=sum(a['textured_corners']for a in data['textures'].values()))
    write(proof,report)

def run(raw,out,project):
    source=json.loads((out/'editable-inputs.json').read_bytes())
    assert source['raw_sha256']==sha(raw) and source['signed_parts']==sha(out/'editable-parts.json')
    exe=os.environ.get('JIUYUAN_BLENDER')or shutil.which('blender');assert exe
    events=[]
    for stage in ('make','verify'):
        cmd=[exe,'-b','--threads','1','--python-exit-code','1','--python',str(Path(__file__).absolute()),'--',stage,str(raw),str(out),'--project',str(project)]
        started=datetime.now(timezone.utc).isoformat()
        log=out/(stage+'.log')
        with log.open('w') as stream:
            p=subprocess.Popen(cmd,stdout=stream,stderr=subprocess.STDOUT,env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'});code=p.wait()
        events.append(dict(phase=stage,start=started,finish=datetime.now(timezone.utc).isoformat(),pid=p.pid,exit=code,log_sha256=sha(log)))
        write(out/'blender-exits.json',events)
        if code:raise RuntimeError(f'Blender {stage} exited {code}, see {log}')
    print((out/'reopened.json').read_text())

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',choices=('prepare','run','make','verify'));p.add_argument('raw',type=Path);p.add_argument('out',type=Path);p.add_argument('--project',type=Path,default=Path.cwd())
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:];a=p.parse_args(argv)
    raw=a.raw.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True);project=a.project.resolve()
    os.chdir(project)
    if a.stage=='prepare':prepare(raw,out)
    elif a.stage=='run':run(raw,out,project)
    elif a.stage=='make':blender_make(out)
    else:blender_verify(raw,out,project)
