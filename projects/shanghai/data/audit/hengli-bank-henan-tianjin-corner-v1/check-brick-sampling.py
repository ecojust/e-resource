"""Measure UVs at street-facing brick hits from the independent serialized geometry."""
from pathlib import Path
from io import BytesIO
from hashlib import sha256
import json,struct,runpy
from PIL import Image
import numpy as np
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
SOURCE=PROJECT/'source/precise/huangpu-hengli-bank-henan-tianjin-corner/source'
BRICK='Hengli dark fired brick'
Scene=runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
class Atlas:
    def __init__(self,path):
        data = path.read_bytes()
        length = struct.unpack_from('<I',data,12)[0]
        self.doc = json.loads(data[20:20+length])
        self.binary = data[28+length:]
        doc = self.doc
        assert len(doc['nodes'])==1 and doc['nodes'][0]['mesh']==0 and len(doc['meshes'])==1
        idx = next(i for i,m in enumerate(doc['materials']) if m['name']==BRICK)
        texture = doc['textures'][doc['materials'][idx]['pbrMetallicRoughness']['baseColorTexture']['index']]
        sampler = doc['samplers'][texture['sampler']]
        assert sampler['wrapS']==sampler['wrapT']==33071
        record = doc['images'][texture['source']]
        view = doc['bufferViews'][record['bufferView']]
        offset = view.get('byteOffset',0)
        png = self.binary[offset:offset+view['byteLength']]
        assert record['mimeType']=='image/png' and png==(SOURCE/'brown-brick-bond.png').read_bytes()
        self.hash = sha256(png).hexdigest()
        self.image = np.asarray(Image.open(BytesIO(png)).convert('RGB'))
        assert self.image.shape==(2048,1536,3)
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
        px,py=np.clip(np.floor(uv*[1536,2048]).astype(int),[0,0],[1535,2047])
        return uv.tolist(),[int(px),int(py)],self.image[py,px].tolist()


def sample(mesh):
    atlas=Atlas(mesh);scene=Scene(mesh);rows=[]
    starts=[(-15.8184,0.),(0.,0.),(2.8775,3.2731)]
    ends=[(0.,0.),(2.8775,3.2731),(.8376,32.4104)]
    # Positions run from each original street edge's south/west end. Each cross
    # samples mortar and multiple fired-brick faces in the original fitted bond.
    for tag,a,b,u in zip(['Tianjin','Chamfer','Henan'],starts,ends,[.36,3.25,25.23]):
        a=np.asarray(a);t=np.subtract(b,a);t/=np.linalg.norm(t);n=np.array([t[1],-t[0]])
        for h in [9.05,10.89,14.77,17.61]:
            for shift in [-.026,0.,.026]:
                for lift in [-.017,.017]:
                    s=u+shift;z=h+lift;xy=a+t*s+n*.65
                    ray=scene.ray([*xy,z],[*list(-n),0.],1.40)
                    assert ray and ray['material']==BRICK,(tag,s,z,ray)
                    uv,px,color=atlas.pixel(scene,ray)
                    target=[(s+.70)/32,1-(z+.25)/32]
                    err=float(np.max(np.abs(np.subtract(uv,target))))
                    assert err<1.7e-5,(tag,s,z,uv,target)
                    rows.append(dict(wall=tag,u=s,z=z,uv=uv,expected=target,error=err,pixel=px,rgb=color))
    colors=set(tuple(x['rgb'])for x in rows)
    assert (126,119,104)in colors and len(colors)>=5
    return dict(count=len(rows),atlas_sha256=atlas.hash,samples=rows,unique_rgb=len(colors),max_error=max(v['error']for v in rows))
