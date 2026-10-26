"""Static geometry / real photographic-source checks; no renderer or network."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from build_model import Residence222,project


def audit_parts(model):
    errors=[];min_volume=1e9;max_uv_error=0.;parts=0
    for part in model.b.parts:
        xyz=np.asarray(part['vertices'],dtype=np.float32).astype(float)
        ids=np.asarray(part['triangles'],int)
        assert ids.min()>=0 and ids.max()<len(xyz)
        # Welding at actual exported FLOAT32 positions reveals collapsed edges.
        remap={};mapped=[]
        for v in xyz:
            key=tuple(v)
            if key not in remap:remap[key]=len(remap)
            mapped.append(remap[key])
        triangles=np.asarray(mapped)[ids];edges=Counter()
        for a,b,c in triangles:
            for x,y in [(a,b),(b,c),(c,a)]:edges[tuple(sorted((int(x),int(y))))]+=1
        bad=sum(n!=2 for n in edges.values())
        q=xyz[ids];norm=np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)
        volume=float(np.einsum('ij,ij->i',q[:,0]-xyz.mean(0),np.cross(q[:,1]-xyz.mean(0),q[:,2]-xyz.mean(0))).sum()/6)
        duplicates=len(triangles)-len({tuple(sorted(map(int,t))) for t in triangles})
        if bad or norm.min()<=1e-12 or volume<=0 or duplicates:
            errors.append({'label':part['label'],'bad_edge_count':bad,'min_twice_area':float(norm.min()),'signed_volume':volume,'duplicate_faces':duplicates})
        min_volume=min(min_volume,volume);parts+=1
    return {'parts':parts,'closed_positive_volume_parts':parts-len(errors),'minimum_signed_volume_m3':min_volume,'errors':errors}


def load_glb(path):
    data=path.read_bytes();magic,version,length=struct.unpack_from('<4sII',data)
    assert magic==b'glTF' and version==2 and length==len(data)<100000000
    jl,jt=struct.unpack_from('<II',data,12);assert jt==0x4e4f534a
    doc=json.loads(data[20:20+jl]);bl,bt=struct.unpack_from('<II',data,20+jl);assert bt==0x004e4942
    binary=data[28+jl:];assert len(binary)==bl
    assert all('uri' not in b for b in doc['buffers']) and all('uri' not in x for x in doc.get('images',[]))
    return data,doc,binary


def access(doc,binary,index):
    a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
    size={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    dtype={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']]
    assert 'byteStride' not in v
    return np.frombuffer(binary,dtype=dtype,count=a['count']*size,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape((-1,size))


def assert_serialized_photo_uvs(positions,uv,name,model):
    expected={}
    for part in model.b.parts:
        if part['material']!=name:continue
        xyz=np.asarray(part['vertices'])[:,[0,2,1]]*[1,1,-1]
        for pos,coord in zip(np.asarray(xyz,dtype=np.float32),part['texcoords']):
            expected.setdefault(tuple(pos),[]).append(np.asarray(coord,dtype=np.float32))
    for pos,coord in zip(positions,uv):
        assert tuple(pos) in expected
        assert min(np.max(np.abs(coord-want)) for want in expected[tuple(pos)])<2e-6,'Serialized UV differs from declared original-photo sample'


def assert_original_image(doc,binary,original):
    assert len(doc.get('images',[]))==1
    vi=doc['bufferViews'][doc['images'][0]['bufferView']]
    embedded=binary[vi['byteOffset']:vi['byteOffset']+vi['byteLength']]
    assert embedded==original,'Embedded source photograph bytes differ'
    return embedded


def assert_right_door_untextured(model,doc):
    door=[p for p in model.b.parts if '/right-closed-glass-door-pane-' in p['label']]
    assert len(door)==2,'Right door must have exactly two complete glass leaves'
    assert all(p['material']=='right door estimated glass' and 'texcoords' not in p for p in door),'Right-door photograph island or material split reintroduced'
    assert not any('/right-door-leaf-' in p['label'] for p in model.b.parts)
    mats=[(i,m) for i,m in enumerate(doc['materials']) if m['name']=='right door estimated glass']
    assert len(mats)==1
    index,mat=mats[0];assert 'baseColorTexture' not in mat['pbrMetallicRoughness']
    assert np.allclose(mat['pbrMetallicRoughness']['baseColorFactor'][:3],model.c['glazing']['right_door_material']['color'])
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            if prim['material']==index:assert 'TEXCOORD_0' not in prim['attributes']
    return door


def main():
    path=HERE/'output/qingpu-beidajie-222.glb'
    model=Residence222();model.construct();part_report=audit_parts(model)
    glazing=[]
    for win in model.windows:
        if win.get('glass_depth_range') is None:continue
        low,high=win['glass_depth_range'];back,front=win['frame_depth_range']
        assert back-1e-8<=low<high<=front+1e-8,(win['label'],low,high,back,front)
        assert abs((front-high)-.02)<1e-8
        origin=np.asarray(win['facade_origin']);normal=np.asarray(win['facade_normal'])
        frame=next(p for p in model.b.parts if p['label'].endswith('/'+win['label']+'-frame'))
        actual=(np.asarray(frame['vertices'])-origin)@normal
        assert np.allclose([actual.min(),actual.max()],[back,front],atol=1e-7)
        for pane in win['panes']:
            part=next(p for p in model.b.parts if p['label']==pane['label'])
            actual=(np.asarray(part['vertices'])-origin)@normal
            assert np.allclose([actual.min(),actual.max()],[low,high],atol=1e-7)
        glazing.append({'label':win['label'],'glass_range':win['glass_depth_range'],
                        'frame_range':win['frame_depth_range'],'setback_m':front-high})
    data,doc,binary=load_glb(path);triangles=0;min_area=1e9;min_normal=1.;max_normal=1.;photo_primitives=0
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            p=access(doc,binary,primitive['attributes']['POSITION']).astype(float)
            n=access(doc,binary,primitive['attributes']['NORMAL']).astype(float)
            i=access(doc,binary,primitive['indices']).ravel().reshape((-1,3))
            assert np.isfinite(p).all() and np.isfinite(n).all() and i.max()<len(p)
            q=p[i];area=np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)
            assert area.min()>1e-12
            lengths=np.linalg.norm(n,axis=1);assert lengths.min()>.9999 and lengths.max()<1.0001
            min_area=min(min_area,float(area.min()));min_normal=min(min_normal,float(lengths.min()));max_normal=max(max_normal,float(lengths.max()));triangles+=len(i)
            if 'TEXCOORD_0' in primitive['attributes']:
                uv=access(doc,binary,primitive['attributes']['TEXCOORD_0']);assert np.isfinite(uv).all() and uv.min()>=0 and uv.max()<=1
                name=doc['materials'][primitive['material']]['name'];assert name.startswith('PhotoFacade_Qingpu222')
                assert_serialized_photo_uvs(p,uv,name,model)
                photo_primitives+=1
    embedded=assert_original_image(doc,binary,model.photo.read_bytes())
    # All selected parts use exact per-sample homographies. The sign was then
    # rotated physically; reverse that operation before checking its UVs.
    max_error=0.
    for mapping in model.photo_maps:
        part=next(p for p in model.b.parts if p['label']==mapping['label']);h=np.asarray(mapping['homography']);expected=[]
        for point in part['vertices']:
            q=model.local(point)
            if 'post_uv_rotation' in mapping:
                rot=mapping['post_uv_rotation'];_,d,z=rot['center_u_d_z'];a=np.radians(-rot['degrees']);dd=q[1]-d;zz=q[2]-z
                q[2]=z+zz*np.cos(a)-dd*np.sin(a)
            expected.append((project(h,[q[0],q[2]])+.5)/[4000,3000])
        err=float(np.abs(np.asarray(expected)-part['texcoords']).max());max_error=max(max_error,err);assert err<1e-8
    assert np.array_equal(model.original,np.asarray(model.g['polygon_local_east_north']))
    plinth=next(p for p in model.b.parts if p['label']=='exact-source-footprint-plinth')
    actual_xy={tuple(np.asarray(v[:2],dtype=np.float32)) for v in plinth['vertices'] if v[2]==0}
    assert actual_xy=={tuple(np.asarray(v,dtype=np.float32)) for v in model.original}
    assert doc['extras']['height_is_measured'] is False
    assert doc['extras']['license']['model']=='CC-BY-SA-4.0'
    assert len(model.photo_maps)==1 and photo_primitives==1
    assert model.photo_maps[0]['label'].endswith('/central-cursive-board-photo-face')
    # Source geometry and serialized material must both have two coherent leaves.
    coherent_door=assert_right_door_untextured(model,doc)
    leftboard=next(p for p in model.b.parts if p['label'].endswith('/left-gallery-sign-board'))
    leftdepth=np.array([model.local(p)[1] for p in leftboard['vertices']])
    assert leftdepth.min()>.024 and np.isclose(leftdepth.max(),.155)
    signparts=[p for p in model.b.parts if 'right-to-left-gallery-sign' in p['label']]
    assert signparts
    assert min(model.local(v)[1] for p in signparts for v in p['vertices'])>.164
    assert max(model.local(v)[2] for p in signparts for v in p['vertices'])<model.h['frieze_bottom']
    upper=[w for w in model.windows if w['label'].startswith('upper-window')]
    assert len(upper)==3 and upper[0]['opaque_top_panels']==4
    assert all(w['small_light_count']>30 and w['front_glass_area_fraction']<.66 for w in upper)
    assert part_report['errors']==[],part_report['errors'][:10]
    report={'result':'PASS','file':path.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
      'triangles':triangles,'materials':len(doc['materials']),'parts':part_report,
      'self_contained':True,'minimum_twice_triangle_area_m2':min_area,'normal_length_range':[min_normal,max_normal],
      'embedded_original_jpeg_byte_exact':True,'embedded_jpeg_sha256':hashlib.sha256(embedded).hexdigest(),
      'photo_part_count':len(model.photo_maps),'photo_material_count':photo_primitives,'maximum_original_uv_error':max_error,
      'serialized_uvs_match_original_sample_maps':True,'glazing_embedded_in_frames':glazing,
      'right_door_photo_maps':0,'right_door_coherent_untextured_leaves':len(coherent_door),
      'left_sign_clear_of_front_wall':True,
      'upper_actual_small_light_counts':[w['small_light_count'] for w in upper],
      'original_source_ring_equal':True,'actual_plinth_footprint_vertices_equal':True,'source_provider':'zenodo/east_asian_buildings2024-11-01;notOSMbuilding',
      'model_license':'CC-BY-SA-4.0','height_is_measured':False,'render_or_browser_used':False}
    (HERE/'output/validation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='parts'},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
