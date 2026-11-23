"""Write untextured study solids using per-component flat normals and bounded memory."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import struct
import numpy as np
from finishes import HERE,STEMS,REPEATS

def save_study(builder, path, metadata):
    path=Path(path)
    by_material=defaultdict(list)
    for part in builder.parts:by_material[part['material']].append(part)
    binary=bytearray();views=[];access=[];primitives=[];materials=[];minimum=[];maximum=[];images=[];textures=[]
    def push(collection,kind,component,target,dimensions):
        while len(binary)%4:binary.append(0)
        start=len(binary);count=0;lo=None;hi=None
        for arr in collection:
            binary.extend(arr.tobytes());count+=len(arr)
            if dimensions==3:
                low=arr.min(axis=0);high=arr.max(axis=0)
                lo=low if lo is None else np.minimum(lo,low);hi=high if hi is None else np.maximum(hi,high)
        views.append(dict(buffer=0,byteOffset=start,byteLength=len(binary)-start,target=target))
        obj=dict(bufferView=len(views)-1,componentType=component,count=count,type=kind)
        if dimensions==3:obj.update(min=lo.tolist(),max=hi.tolist())
        access.append(obj);return len(access)-1
    totals=0
    for mat,parts in by_material.items():
        vertices=[]; normals=[];indices=[];uvs=[];offset=0; is_textured=mat in STEMS
        for part in parts:
            points=np.asarray(part['vertices'],dtype='<f4')[:,[0,2,1]].copy()
            points[:,2]*=-1
            tri=np.asarray(part['triangles'],dtype=np.int32)
            xyz=points[tri].astype(float);n=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0])
            magnitude=np.linalg.norm(n,axis=1)
            if (magnitude<1e-12).any():raise ValueError('Collapsed face in '+part['label'])
            n=np.asarray(n/magnitude[:,None],dtype='<f4');wn=np.broadcast_to(n[:,None],xyz.shape).reshape(-1,3)
            # The positional index and the actual flat normal define a render vertex.
            key=np.empty((tri.size,6 if is_textured else 4),dtype='<u4');key[:,0]=tri.ravel();key[:,1:4]=wn.copy().view('<u4')
            if is_textured:
                flat=points[tri.ravel()];X,Y,Z=flat[:,0],-flat[:,2],flat[:,1]
                horizontal=np.abs(wn[:,1])>.70
                front=np.abs(wn[:,2])>np.abs(wn[:,0])
                u=np.where(horizontal & (mat!='red glazed pantile'),X,np.where(front,X,Y))
                vv=np.where(horizontal,np.where(front | (mat!='red glazed pantile'),Y,X),Z)
                uv=np.asarray(np.column_stack([u/REPEATS[mat][0],vv/REPEATS[mat][1]]),dtype='<f4')
                key[:,4:6]=uv.view('<u4')
            _,first,local=np.unique(key,axis=0,return_index=True,return_inverse=True)
            if is_textured:uvs.append(uv[first])
            vertices.append(points[tri.ravel()[first]]);normals.append(wn[first])
            indices.append(np.asarray(local+offset,dtype='<u4'));offset+=len(first);totals+=len(tri)
        pos=push(vertices,'VEC3',5126,34962,3);normal=push(normals,'VEC3',5126,34962,3);ind=push(indices,'SCALAR',5125,34963,1)
        minimum.append(access[pos]['min']);maximum.append(access[pos]['max'])
        attributes=dict(POSITION=pos,NORMAL=normal)
        spec=builder.palette[mat];alpha=spec.get('alpha',1.0);pbr=dict(baseColorFactor=([1.,1.,1.] if is_textured else spec['color'])+[alpha],roughnessFactor=spec['roughness'],metallicFactor=0)
        material=dict(name=mat,pbrMetallicRoughness=pbr)
        if is_textured:
            attributes['TEXCOORD_0']=push(uvs,'VEC2',5126,34962,2)
            for suffix in ('','-normal'):
                name=STEMS[mat]+suffix+'.png';data=(HERE/name).read_bytes()
                while len(binary)%4:binary.append(0)
                views.append(dict(buffer=0,byteOffset=len(binary),byteLength=len(data)));binary.extend(data)
                images.append(dict(name=name,mimeType='image/png',bufferView=len(views)-1));textures.append(dict(source=len(images)-1,sampler=0))
                if suffix:material['normalTexture']=dict(index=len(textures)-1)
                else:pbr['baseColorTexture']=dict(index=len(textures)-1)
        if alpha<1.:material.update(alphaMode='BLEND',doubleSided=False)
        primitives.append(dict(attributes=attributes,indices=ind,material=len(materials)));materials.append(material)
    doc=dict(asset=dict(version='2.0',generator='Editable Xinhua Road photographic survey'),scene=0,scenes=[dict(nodes=[0])],nodes=[dict(mesh=0,name=metadata['name'])],meshes=[dict(primitives=primitives)],materials=materials,buffers=[dict(byteLength=len(binary))],bufferViews=views,accessors=access,extras=metadata)
    if images:doc.update(images=images,textures=textures,samplers=[dict(wrapS=10497,wrapT=10497,magFilter=9729,minFilter=9987)])
    while len(binary)%4:binary.append(0)
    doc['buffers'][0]['byteLength']=len(binary)
    head=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();head+=b' '*(-len(head)%4)
    with path.open('wb')as out:
        out.write(struct.pack('<4sIIII',b'glTF',2,28+len(head)+len(binary),len(head),0x4E4F534A));out.write(head);out.write(struct.pack('<II',len(binary),0x004E4942));out.write(binary)
    with path.open('rb')as src:sha=hashlib.file_digest(src,'sha256').hexdigest()
    summary=[dict(label=p['label'],material=p['material'],vertices=len(p['vertices']),triangles=len(p['triangles']))for p in builder.parts]
    report=dict(file=path.name,bytes=path.stat().st_size,sha256=sha,triangles=totals,materials=len(materials),parts=len(summary),bounds_glb=dict(min=np.min(minimum,axis=0).tolist(),max=np.max(maximum,axis=0).tolist()),part_summary=summary)
    path.with_suffix('.geometry.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');return report
