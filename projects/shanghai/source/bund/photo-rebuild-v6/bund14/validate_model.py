"""Read-only audit of Bund14 raw GLB, its original photo bytes and pane UVs."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent


def validate(folder):
    model=folder/'bund14.glb';raw=model.read_bytes()
    assert struct.unpack_from('<4sII',raw)==(b'glTF',2,len(raw))
    assert len(raw)<100_000_000
    jl,jt=struct.unpack_from('<II',raw,12);assert jt==0x4e4f534a
    doc=json.loads(raw[20:20+jl]);bl,bt=struct.unpack_from('<II',raw,20+jl)
    assert bt==0x004e4942 and 28+jl+bl==len(raw)
    binary=memoryview(raw)[28+jl:]
    assert len(doc['buffers'])==1 and 'uri' not in doc['buffers'][0]
    assert doc['buffers'][0]['byteLength']==bl
    assert len(doc['images'])==1 and len(doc['textures'])==1
    image=doc['images'][0];assert image['mimeType']=='image/jpeg' and 'uri' not in image
    view=doc['bufferViews'][image['bufferView']]
    image_bytes=bytes(binary[view['byteOffset']:view['byteOffset']+view['byteLength']])
    source=(HERE/'research/commons-164811484.jpg').read_bytes()
    assert image_bytes==source
    im=Image.open(io.BytesIO(image_bytes));assert im.size==(5184,3456) and im.getexif().get(274)==6
    report=json.loads((folder/'bund14.geometry.json').read_text())
    photographic=report['photographic_glazing'];cal=json.loads((HERE/'calibration.json').read_text())
    expected_sha=hashlib.sha256(raw).hexdigest()
    assert report['sha256']==expected_sha and doc['extras']['heights_m']==cal['heights_m']
    for rel,entry in doc['extras']['generator_sources'].items():
        assert hashlib.sha256((HERE/rel).read_bytes()).hexdigest()==entry['sha256'],rel
    assert report['solid_topology_audit']['passed'] and photographic['geometry_unchanged_by_texture_mapping']
    assert report['verification']['observed_front_window_count']==48
    samples=json.loads((HERE/'glazing-samples.json').read_text())
    assert samples['selected_panes']==photographic['selected_panes']==137
    photo_materials=[i for i,m in enumerate(doc['materials']) if m['name'].startswith('PhotoFacade_')]
    assert len(photo_materials)==1
    pm=doc['materials'][photo_materials[0]]
    assert pm['name']=='PhotoFacade_Bund14Glass'
    assert pm['extras']['photographicSource']['rawSize']==[5184,3456]
    assert pm['extras']['photographicSource']['exifOrientation']==6
    assert pm['extras']['photographicSource']['uvConvention']=='stored-pixels'
    def accessor(index):
        a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
        assert 'sparse' not in a and 'byteStride' not in v
        dt={5126:'<f4',5125:'<u4'}[a['componentType']]
        size={'VEC2':2,'VEC3':3,'SCALAR':1}[a['type']]
        off=v.get('byteOffset',0)+a.get('byteOffset',0)
        value=np.frombuffer(binary,dtype=dt,count=a['count']*size,offset=off).reshape(a['count'],size)
        assert np.isfinite(value).all()
        return value
    geom=json.loads((HERE/'geometry-input.json').read_text())
    origin=np.r_[geom['front_edge']['center_local_east_north_m'],0.]
    tangent=np.r_[geom['front_edge']['tangent_east_north'],0.]
    normal=np.r_[geom['front_edge']['outward_normal_east_north'],0.]
    nglb=normal[[0,2,1]]*np.array([1,1,-1])
    controls=photographic['per_pane_controls'];triangles=0;texture_vertices=0;front_uv_zero=0;max_uv_error=0
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            pos=accessor(primitive['attributes']['POSITION']);nr=accessor(primitive['attributes']['NORMAL']);idx=accessor(primitive['indices']).ravel()
            assert len(idx)%3==0 and idx.max()<len(pos) and len(pos)==len(nr)
            assert np.allclose(np.linalg.norm(nr,axis=1),1,atol=1e-6)
            tri=pos[idx].reshape(-1,3,3).astype(float)
            assert (np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)>1e-12).all()
            triangles+=len(idx)//3
            if primitive['material'] not in photo_materials:
                assert 'TEXCOORD_0' not in primitive['attributes'];continue
            uv=accessor(primitive['attributes']['TEXCOORD_0']);assert len(uv)==len(pos) and uv.min()>=0 and uv.max()<=1
            enu=pos[:,[0,2,1]].astype(float)*np.array([1,-1,1]);uz=np.c_[(enu-origin)@tangent,enu[:,2]]
            depth=(enu-origin)@normal
            assert np.all(np.isclose(depth,-.31,atol=1e-5)|np.isclose(depth,-.33,atol=1e-5))
            matched=np.zeros(len(pos),int)
            for item in controls:
                q=np.array(item['model_quad_u_z_m']);lo=q.min(0)-2e-5;hi=q.max(0)+2e-5
                mask=np.all((uz>=lo)&(uz<=hi),axis=1)
                if not mask.any():continue
                pix=np.c_[uz[mask],np.ones(mask.sum())]@np.asarray(item['model_to_source_oriented_homography']).T
                oriented=pix[:,:2]/pix[:,2:]
                expected=np.c_[(oriented[:,1]+.5)/5184,(3455-oriented[:,0]+.5)/3456]
                error=float(np.max(np.abs(expected-uv[mask])));max_uv_error=max(max_uv_error,error)
                assert error<2e-6
                matched[mask]+=1
            assert np.all(matched==1)
            tuv=uv[idx].reshape(-1,3,2).astype(float);a=tuv[:,1]-tuv[:,0];b=tuv[:,2]-tuv[:,0];area=np.abs(a[:,0]*b[:,1]-a[:,1]*b[:,0])
            front=(nr[idx[::3]]@nglb)>.99
            front_uv_zero+=int(np.count_nonzero(area[front]<1e-14));texture_vertices+=len(pos)
    assert triangles==report['triangles'] and front_uv_zero==0
    result={'passed':True,'model':model.name,'bytes':len(raw),'sha256':expected_sha,'triangles':triangles,
      'header_length_valid':True,'external_resources':0,'image_count':1,'image_bytes_unchanged':True,
      'image_sha256':hashlib.sha256(image_bytes).hexdigest(),'image_raw_size':list(im.size),'image_exif_orientation':6,
      'photographic_material_count':1,'photographic_windows':28,'photographic_panes':137,
      'textured_vertices_checked_against_individual_pane_homographies':texture_vertices,
      'maximum_uv_error_against_controls':max_uv_error,'out_of_bounds_uvs':0,'front_glass_degenerate_uv_triangles':0,
      'frame_or_wall_textured':False,'source_hashes_match':True,'geometry_closed_solid_audit':report['solid_topology_audit'],
      'lettering':report['lettering'],'height_is_measured':False,'heights_m':cal['heights_m'],
      'remaining_runtime_check':'Root real GLTFLoader/browser EXIF correction and Blender render/native validation; static UV checks do not substitute for decoder verification.'}
    (folder/'bund14.validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['passed','bytes','sha256','triangles','photographic_windows','photographic_panes','maximum_uv_error_against_controls']}))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=HERE/'output');args=p.parse_args();validate(args.output)
