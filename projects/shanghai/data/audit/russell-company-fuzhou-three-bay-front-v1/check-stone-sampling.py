"""Measure UVs at street-facing ashlar surfaces from the independent serialized geometry."""
from pathlib import Path
from io import BytesIO
from hashlib import sha256
import json,struct,runpy
from PIL import Image
import numpy as np
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
SOURCE=PROJECT/'source/precise/huangpu-russell-company-fuzhou-three-bay-front/source'
STONE='Weathered dark granite ashlar'
Scene=runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
class Atlas:
    def __init__(self,path):
        data = path.read_bytes()
        length = struct.unpack_from('<I',data,12)[0]
        self.doc = json.loads(data[20:20+length])
        self.binary = data[28+length:]
        doc = self.doc
        assert len(doc['nodes'])==1 and doc['nodes'][0]['mesh']==0 and len(doc['meshes'])==1
        idx = next(i for i,m in enumerate(doc['materials']) if m['name']==STONE)
        texture = doc['textures'][doc['materials'][idx]['pbrMetallicRoughness']['baseColorTexture']['index']]
        sampler = doc['samplers'][texture['sampler']]
        assert sampler['wrapS']==sampler['wrapT']==33071
        record = doc['images'][texture['source']]
        view = doc['bufferViews'][record['bufferView']]
        offset = view.get('byteOffset',0)
        png = self.binary[offset:offset+view['byteLength']]
        assert record['mimeType']=='image/png' and png==(SOURCE/'russell-weathered-stone.png').read_bytes()
        self.hash = sha256(png).hexdigest()
        self.image = np.asarray(Image.open(BytesIO(png)).convert('RGB'))
        assert self.image.shape==(1024,768,3)
        skip = 0
        self.ranges = []
        for prim in doc['meshes'][0]['primitives']:
            access = doc['accessors'][prim['indices']]
            n = access['count']//3
            if prim['material']==idx:
                ids=self.array(prim['indices'],1).reshape(-1,3)
                uv=self.array(prim['attributes']['TEXCOORD_0'],2)[ids]
                assert np.isfinite(uv).all() and uv.min()>=-.00002 and uv.max()<=1.00002
                self.ranges.append((skip,skip+n,uv))
            skip+=n
        assert self.ranges

    def array(self,index,width):
        a=self.doc['accessors'][index]
        view=self.doc['bufferViews'][a['bufferView']]
        dtype=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']])
        offset=view.get('byteOffset',0)+a.get('byteOffset',0)
        stride=view.get('byteStride',width*dtype.itemsize)
        return np.ndarray((a['count'],width),dtype,self.binary,offset,(stride,dtype.itemsize))

    def pixel(self,scene,hit):
        index=hit['triangle_index']
        start,end,coords=next(row for row in self.ranges if row[0]<=index<row[1])
        v=scene.tri[index]
        ab=np.column_stack((v[1]-v[0],v[2]-v[0]))
        x,y=np.linalg.lstsq(ab,np.array(hit['point_enu_m'])-v[0],rcond=None)[0]
        uv=np.array([1-x-y,x,y])@coords[index-start]
        px,py=np.clip(np.floor(uv*[768,1024]).astype(int),[0,0],[767,1023])
        return uv.tolist(),[int(px),int(py)],self.image[py,px].tolist()



def sample(mesh):
    atlas=Atlas(mesh);scene=Scene(mesh);rows=[]
    sites={0.78: [8.31, 10.29], 2.91: [2.99, 3.43, 4.07, 4.98, 5.55, 6.9, 7.19, 8.31, 9.74, 10.29], 3.04: [2.99, 3.43, 4.07, 4.98, 5.55, 6.9, 7.19, 8.31, 9.74, 10.29], 5.77: [2.99, 3.43, 4.07, 4.98, 5.55, 6.9, 7.19, 8.31, 9.74, 10.29], 6.11: [2.37, 2.99, 3.43, 4.07, 4.98, 5.55, 6.9, 7.19, 8.31, 9.74, 10.29], 8.53: [2.37, 2.99, 3.43, 4.07, 4.98, 5.55, 6.9, 7.19, 8.31, 9.74, 10.29]}
    for x,heights in sites.items():
        for z in heights:
            hit=scene.ray([x,-1.8,z],[0,1,0],2.3)
            assert hit and hit['material']==STONE,(x,z,hit)
            uv,px,col=atlas.pixel(scene,hit);expect=[(x+.4)/10,1-(z+.30)/13.]
            error=float(np.max(np.abs(np.subtract(uv,expect))))
            assert error<2.e-5,(x,z,uv,expect)
            rows.append(dict(x=x,z=z,material=hit['material'],uv=uv,pixel=px,rgb=col,error=error))
    assert len(rows)==54 and len({tuple(r['rgb'])for r in rows})>=13
    return dict(count=len(rows),atlas_sha256=atlas.hash,samples=rows,distinct_rgb=len({tuple(r['rgb'])for r in rows}),max_uv_error=max(r['error']for r in rows))
