#!/usr/bin/env python3
"""Read actual GLB: image bytes, calibrated glass UVs, axes and triangle normals."""
from pathlib import Path
import argparse,hashlib,json,struct
import numpy as np
HERE=Path(__file__).resolve().parent


def check(output):
    data=(output/'bund09-raw.glb').read_bytes();assert len(data)<100_000_000
    magic,version,total=struct.unpack_from('<4sII',data);assert (magic,version,total)==(b'glTF',2,len(data))
    jl,jt=struct.unpack_from('<II',data,12);assert jt==0x4e4f534a
    doc=json.loads(data[20:20+jl]);bl,bt=struct.unpack_from('<II',data,20+jl);assert bt==0x004e4942
    binary=data[28+jl:28+jl+bl]
    def acc(i):
        a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];n={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']]
        return np.frombuffer(binary,{5126:'<f4',5125:'<u4'}[a['componentType']],a['count']*n,v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,n)
    evidence=json.loads((output/'photo-uv-evidence.json').read_text());source=(HERE/evidence['image']).read_bytes()
    assert hashlib.sha256(source).hexdigest()==evidence['image_sha256']
    assert len(doc['images'])==1 and 'uri' not in doc['images'][0]
    view=doc['bufferViews'][doc['images'][0]['bufferView']]
    assert binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]==source
    mapped=[];minimum_alignment=1.;triangles=0;serialized_bounds=[]
    for prim in doc['meshes'][0]['primitives']:
        positions=acc(prim['attributes']['POSITION']).astype(float);normal=acc(prim['attributes']['NORMAL']).astype(float)
        indices=acc(prim['indices']).reshape(-1,3);assert np.isfinite(positions).all() and np.isfinite(normal).all()
        assert indices.min()>=0 and indices.max()<len(positions)
        a,b,c=positions[indices[:,0]],positions[indices[:,1]],positions[indices[:,2]]
        cross=np.cross(b-a,c-a);length=np.linalg.norm(cross,axis=1);assert np.all(length>1e-12)
        actual=cross/length[:,None];alignment=np.einsum('ij,ij->i',actual,normal[indices[:,0]])
        minimum_alignment=min(minimum_alignment,float(alignment.min()));assert np.all(alignment>1-1e-5)
        triangles+=len(indices);serialized_bounds.extend([positions.min(0),positions.max(0)])
        mat=doc['materials'][prim['material']]
        if mat.get('pbrMetallicRoughness',{}).get('baseColorTexture'):
            assert mat['name']=='PhotoFacade_Bund09_RegisteredGlass';mapped.append(prim)
            assert mat['extras']['photographicSource']=={'rawSize':[5184,3456],'exifOrientation':1,'uvConvention':'stored-pixels'}
        else:assert 'TEXCOORD_0' not in prim['attributes']
    assert len(mapped)==1 and evidence['glazing_parts']==20
    uv=acc(mapped[0]['attributes']['TEXCOORD_0']).astype(float);assert np.isfinite(uv).all() and np.all((uv>=0)&(uv<=1))
    actual=np.unique(uv,axis=0);expected=np.array([q for p in evidence['per_pane'] for q in p['stored_uv_corners']])
    assert actual.shape==expected.shape==(80,2)
    distance=np.linalg.norm(actual[:,None,:]-expected[None,:,:],axis=2)
    error=float(max(distance.min(0).max(),distance.min(1).max()));assert error<8e-8
    inverse_error=0.
    for pane in evidence['per_pane']:
        for xy,uv0 in zip(pane['source_stored_quad_px'],pane['stored_uv_corners']):
            inverse_error=max(inverse_error,float(np.linalg.norm(np.array(uv0)*[5184,3456]-xy)))
    assert inverse_error<1e-7 and len(acc(mapped[0]['indices']))//3==20*12
    assert 'Suicasmo' in doc['asset']['copyright'] and 'CC0-1.0' in doc['asset']['copyright']
    audit=json.loads((output/'bund09-all-parts-check.json').read_text());assert audit['passed']
    mesh_audit=json.loads((output/'bund09-raw.geometry.json').read_text())
    assert mesh_audit['sha256']==hashlib.sha256(data).hexdigest() and mesh_audit['triangles']==triangles
    inset=json.loads((output/'glass-frame-depth-check.json').read_text());assert inset['passed']
    assert len(inset['panes'])==672
    for pane in inset['panes']:
        gb,gf=pane['actual_float32_glass_depth_m'];fb,ff=pane['frame_depth_m']
        assert gb>=fb-.000003 and gf<=ff+.000003 and abs((ff-gf)-.02)<.000003
    bounds=np.array(serialized_bounds)
    report={'schema':'bund09-serialized-geometry-photo-check-v1','passed':True,'raw_bytes':len(data),'raw_sha256':hashlib.sha256(data).hexdigest(),'triangles':triangles,'embedded_images':1,'source_jpeg_byte_identical':True,'source_image_sha256':evidence['image_sha256'],'photo_windows':2,'photo_panes':20,'photographic_triangles':240,'registered_unique_uv_corners':80,'max_serialized_uv_error':error,'max_inverse_source_pixel_error':inverse_error,'minimum_face_normal_alignment':minimum_alignment,'bounds_glb':{'min':bounds.min(0).tolist(),'max':bounds.max(0).tolist()},'source_control_review':['references/glazing-controls-review-floor2.png','references/glazing-controls-review-floor3.png'],'source_scope':'20 individually viewed unobscured rectangular body panes only; arched fanlights and other glazing remain procedural. No street objects projected.','geometry_scope':'Serialized nonzero triangles and normals, per-generated-part topology audit, exact original embedded JPEG and registered UV evidence. No whole-building Boolean union, native/renderer or visual acceptance claim.'}
    report['candidate_revision']='roof-continuity-v3'
    report['geometry_report_raw_sha_linked']=True
    report['inset_glazing_pane_count']=len(inset['panes'])
    report['inset_vertex_depth_check']='glass-frame-depth-check.json'
    (output/'photo-uv-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=HERE/'output');args=ap.parse_args();check(args.output)
