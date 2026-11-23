"""Stream a GLB and retain triangles overlapping either registered image window.

A triangle that crosses the camera plane is retained conservatively. This
bounds memory while preserving every foreground object along the sampled rays.
"""
import json
import mmap
import struct
import numpy as np


def read_windowed(path,cameras,windows,serial_scene):
    kept,ids,face_ids=[],[],[]
    with path.open('rb') as stream,mmap.mmap(stream.fileno(),0,access=mmap.ACCESS_READ) as data:
        assert data[:4]==b'glTF'
        json_size=struct.unpack_from('<I',data,12)[0]
        model=json.loads(data[20:20+json_size])
        binary=28+json_size
        materials=[m.get('name',str(i)) for i,m in enumerate(model['materials'])]
        def accessor(idx):
            entry=model['accessors'][idx]
            assert 'sparse' not in entry
            view=model['bufferViews'][entry['bufferView']]
            assert 'EXT_meshopt_compression' not in view.get('extensions',{})
            dtype=np.dtype({5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[entry['componentType']])
            width={'VEC3':3,'SCALAR':1}[entry['type']]
            stride=view.get('byteStride',width*dtype.itemsize)
            return np.ndarray((entry['count'],width),dtype,buffer=data,
                offset=binary+view.get('byteOffset',0)+entry.get('byteOffset',0),
                strides=(stride,dtype.itemsize))
        def visit(index,parent):
            nonlocal serial
            node=model['nodes'][index]
            if 'matrix' in node:
                local=np.array(node['matrix']).reshape(4,4,order='F')
            else:
                x,y,z,w=node.get('rotation',[0,0,0,1])
                rotation=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                    [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                    [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
                local=np.eye(4)
                local[:3,:3]=rotation@np.diag(node.get('scale',[1,1,1]))
                local[:3,3]=node.get('translation',[0,0,0])
            transform=parent@local
            if 'mesh' in node:
                for primitive in model['meshes'][node['mesh']]['primitives']:
                    assert primitive.get('mode',4)==4
                    pos=accessor(primitive['attributes']['POSITION'])
                    assert pos.dtype==np.dtype('<f4')
                    idx=accessor(primitive['indices']).reshape(-1,3) if 'indices' in primitive else np.arange(len(pos)).reshape(-1,3)
                    for start in range(0,len(idx),2048):
                        tri=pos[idx[start:start+2048]].astype(float)@transform[:3,:3].T+transform[:3,3]
                        tri=tri[:,:,[0,2,1]]*[1,-1,1]
                        keep=np.zeros(len(tri),dtype=bool)
                        for year,cam in cameras.items():
                            lo,hi=windows[year]
                            ust=(tri-cam.origin)@cam.basis
                            clip=(ust-cam.c_uzd)@cam.r.T@cam.k.T
                            z=clip[:,:,2]
                            # Off-axis rectangle tests are homogeneous and remain
                            # conservative even when one vertex is behind the eye.
                            keep |= (z.max(axis=1)>0)&((clip[:,:,0]-lo[0]*z).max(axis=1)>=0)&((hi[0]*z-clip[:,:,0]).max(axis=1)>=0)&((clip[:,:,1]-lo[1]*z).max(axis=1)>=0)&((hi[1]*z-clip[:,:,1]).max(axis=1)>=0)
                        if keep.any():
                            kept.append(tri[keep])
                            ids.append(np.full(keep.sum(),primitive.get('material',-1),dtype=int))
                            face_ids.append(serial+start+np.flatnonzero(keep))
                    serial+=len(idx)
            for child in node.get('children',[]):visit(child,transform)
        serial=0
        for node in model['scenes'][model.get('scene',0)]['nodes']:visit(node,np.eye(4))
    result=serial_scene.__new__(serial_scene)
    result.tri=np.concatenate(kept)
    result.mi=np.concatenate(ids)
    result.materials=materials
    result.lows,result.highs=result.tri.min(axis=1),result.tri.max(axis=1)
    return result,np.concatenate(face_ids),serial
