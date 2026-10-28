#!/usr/bin/env python3
"""Inspect serialized draft buffers and a few meaningful exterior rays."""
from pathlib import Path
import hashlib
import io
import json
import struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent.parent
D=json.loads((ROOT/'source/design-input.json').read_text())


def inspect(path):
    raw=path.read_bytes();magic,version,length=struct.unpack_from('<4sII',raw)
    assert magic==b'glTF' and version==2 and length==len(raw)<100_000_000
    size,kind=struct.unpack_from('<II',raw,12);assert kind==0x4e4f534a
    doc=json.loads(raw[20:20+size]);bs,bk=struct.unpack_from('<II',raw,20+size);assert bk==0x004e4942
    binary=raw[28+size:28+size+bs]
    def acc(index):
        a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
        dt={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']]
        count={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        offset=v.get('byteOffset',0)+a.get('byteOffset',0)
        stride=v.get('byteStride',np.dtype(dt).itemsize*count)
        return np.ndarray((a['count'],count),dtype=dt,buffer=binary,offset=offset,strides=(stride,np.dtype(dt).itemsize)).copy()
    arrays=[];material_ids=[];bad_normals=0;minimum_area=float('inf');uv_ranges=[]
    for mesh in doc['meshes']:
        for p in mesh['primitives']:
            assert p.get('mode',4)==4 and 'TANGENT' not in p['attributes']
            pos=acc(p['attributes']['POSITION']).astype(float);normal=acc(p['attributes']['NORMAL']).astype(float)
            assert np.isfinite(pos).all() and np.isfinite(normal).all()
            assert np.max(np.abs(np.linalg.norm(normal,axis=1)-1))<2e-6
            idx=acc(p['indices']).reshape(-1).astype(int);assert idx.min()>=0 and idx.max()<len(pos) and len(idx)%3==0
            t=pos[idx.reshape(-1,3)];n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);area=np.linalg.norm(n,axis=1)
            assert np.all(area>1e-12);minimum_area=min(minimum_area,float(area.min()/2))
            geom=n/area[:,None];supplied=normal[idx.reshape(-1,3)]
            assert np.min(np.einsum('ij,ikj->ik',geom,supplied))>.9999
            arrays.append(t);material_ids.extend([p.get('material',-1)]*len(t))
            if 'TEXCOORD_0' in p['attributes']:
                uv=acc(p['attributes']['TEXCOORD_0']);assert np.isfinite(uv).all()
                uv_ranges.append({'material':doc['materials'][p['material']]['name'],'min':uv.min(0).tolist(),'max':uv.max(0).tolist(),'unbounded_repeat':bool(np.min(uv)<0 and np.max(uv)>1)})
    tris=np.concatenate(arrays);matidx=np.asarray(material_ids)
    textures=[]
    for im in doc.get('images',[]):
        v=doc['bufferViews'][im['bufferView']];b=binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
        with Image.open(io.BytesIO(b)) as image:assert image.size==(512,512) and image.mode=='RGB'
        textures.append({'name':im.get('name'),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
    assert len(textures)==3 and all(s['wrapS']==10497 and s['wrapT']==10497 for s in doc['samplers'])
    bounds=[tris.reshape(-1,3).min(0).tolist(),tris.reshape(-1,3).max(0).tolist()]
    assert 18.80<bounds[1][1]<19.0 and abs(bounds[0][1])<1e-7
    # Transform actual GLB vertices back to the explicit architecture frame.
    enu=tris[:,:,[0,2,1]]*np.array([1,-1,1])
    f=D['frame'];xx=f['architecture_X_EN'];yy=f['architecture_Y_EN'];r=np.array([[xx[0],yy[0],0],[xx[1],yy[1],0],[0,0,1.]])
    t=enu@r
    def ray(origin,direction):
        origin=np.asarray(origin,float);direction=np.asarray(direction,float);direction/=np.linalg.norm(direction)
        a=t[:,0];e1=t[:,1]-a;e2=t[:,2]-a;pv=np.cross(np.broadcast_to(direction,e2.shape),e2)
        determinant=np.einsum('ij,ij->i',e1,pv);valid=abs(determinant)>1e-10
        inv=np.zeros_like(determinant);inv[valid]=1/determinant[valid]
        tv=origin-a;u=np.einsum('ij,ij->i',tv,pv)*inv;qv=np.cross(tv,e1)
        v=qv@direction*inv;distance=np.einsum('ij,ij->i',e2,qv)*inv
        valid&=(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7)&(distance>1e-5)
        ids=np.where(valid)[0]
        if len(ids)==0:return None
        i=ids[np.argmin(distance[ids])]
        return {'distance_m':float(distance[i]),'point_architecture_xyz':(origin+distance[i]*direction).tolist(),'material':doc['materials'][matidx[i]]['name']}
    # Offset13cm from the centre avoids the deliberately modelled central
    # plank seam, so the probe reaches a closed door board itself.
    gate=ray([.13,-24,2.0],[0,1,0]);assert gate and gate['material']=='door boards', gate
    # The closed recessed door is farther inside than the front brick skin.
    frontskin=-D['enclosure']['upper_depth_m']/2-D['enclosure']['central_gate_projection_m']-D['enclosure']['bottom_wall_outset_m']*(1-2/D['enclosure']['wall_walk_top_m'])
    assert .65<gate['point_architecture_xyz'][1]-frontskin<.75
    jamb=ray([2.50,-24,2.0],[0,1,0]);assert jamb and jamb['material'].startswith('arch stone')
    # Select the centre of one real pane in the leftmost central leaf, avoiding
    # the timber frame; a genuine aperture must expose recessed glazing.
    leaf_left=-2.98+.015;leaf_width=5.96/6-.03
    pane_x=leaf_left+.10+(leaf_width-.20)/8
    low=D['pavilion']['body_floor_m']+.22+.72;top=D['pavilion']['body_eave_m']-.32-.11
    pane_z=low+(top-low)*(6.5/12)
    pane=ray([pane_x,-24,pane_z],[0,1,0]);assert pane and pane['material']=='recessed glazing'
    return {'file':path.name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'triangles':len(tris),'materials':len(doc['materials']),'actual_bounds_glb':bounds,
            'all_serialized_positions_normals_uvs_finite':True,'normals_unit_and_face_aligned':True,'minimum_triangle_area_m2':minimum_area,'no_tangent_attribute':True,
            'images':textures,'uv_ranges':uv_ranges,'actual_rays':{'arch_centre_closed_door':gate,'masonry_jamb':jamb,'front_leaf_pane':pane},'rays_scope':'Three exterior probes only, not arbitrary route or full watertight/interior acceptance.'}


if __name__=='__main__':
    results=[inspect(ROOT/'exports'/name) for name in ['jinshanwei-gatehouse-raw.glb','jinshanwei-gatehouse-lod-source.glb']]
    out=ROOT/'review';out.mkdir(exist_ok=True)
    (out/'actual-glb-check.json').write_text(json.dumps({'schema':'jinshanwei-actual-glb-check-v1','passed':True,'assets':results,'MAIN_modified':False,'independent_root_review_pending':True},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'passed':True,'assets':[{k:r[k] for k in ['file','bytes','triangles']} for r in results]},ensure_ascii=False))
