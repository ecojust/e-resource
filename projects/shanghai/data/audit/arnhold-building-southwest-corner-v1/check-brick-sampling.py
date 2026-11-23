"""Measure UVs at street-facing brick hits from the independent serialized geometry."""
from pathlib import Path
from io import BytesIO
from hashlib import sha256
import json,struct,runpy
from PIL import Image
import numpy as np
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
SOURCE=PROJECT/'source/precise/huangpu-arnhold-building-southwest-corner/source'
BRICK='Arnhold exposed red brick'
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
        assert record['mimeType']=='image/png' and png==(SOURCE/'arnhold-red-brick.png').read_bytes()
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
    """Compare wall-space texture coordinates against the serialized face's barycentric UV."""
    import math
    atlas=Atlas(mesh);scene=Scene(mesh);rows=[]
    # Independently calibrated straight station endpoints in local metres.
    end=(-3.7207,3.4376)
    tangent=np.array([.058303,-.998299]);normal=np.array([tangent[1],-tangent[0]])
    origin=np.array(end)-12.5*tangent
    # Derive the exact trim positions from the published cadastral line and radius.
    first=np.array([-3.643346,2.101508]);unit=np.array([.058299,-.998299])
    radius=3.65;angle=math.atan2(-unit[1],unit[0]);vx=first[0]-first[1]*unit[0]/unit[1]
    tangent_distance=radius*math.tan(angle/2);east=vx+tangent_distance
    west=np.array([vx,0])-unit*tangent_distance;start=west-unit*12.5
    for side,u,offset in [('Sichuan',7.89,0.),('Jiujiang',7.50,12.5+radius*angle-16)]:
        for h in [5.50,9.05,11.74,13.79,17.37,20.91]:
            for du in [-.047,-.012,.024,.065]:
                for dz in [-.017,.019]:
                    v=u+du;z=h+dz
                    if side=='Sichuan':t=(west-start)/np.linalg.norm(west-start);n=np.array([t[1],-t[0]]);xy=start+v*t
                    else:n=np.array([0.,-1.]);xy=np.array([east+v,0.])
                    hit=scene.ray([*(xy+n*.8),z],[*(-n),0.],1.40)
                    assert hit and hit['material']==BRICK,(side,v,z,hit)
                    uv,px,col=atlas.pixel(scene,hit);expect=[(offset+v+.66)/32.,1-(z+.25)/32.]
                    err=float(np.max(np.abs(np.subtract(uv,expect))))
                    assert err<2e-5,(side,err,uv,expect)
                    rows.append(dict(side=side,street_station=v,z=z,uv=uv,pixel=px,rgb=col,error=err))
    colors={tuple(x['rgb'])for x in rows}
    assert len(colors)>=5 and (132,102,91) in colors,colors
    return dict(count=len(rows),atlas_sha256=atlas.hash,samples=rows,distinct_rgb=len(colors),max_uv_error=max(x['error']for x in rows))
