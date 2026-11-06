"""Read-only GLB scene transform loader and ray helper reused from prior review; no model geometry or building-specific probes. Use decoded GLBs for compressed assets; no codec is implemented here."""
from pathlib import Path
import hashlib,json,struct
import numpy as np

def load_triangles(path):
    blob = path.read_bytes()
    assert blob[:4] == b'glTF' and struct.unpack_from('<I', blob, 4)[0] == 2
    chunks, offset = {}, 12
    while offset < len(blob):
        length, kind = struct.unpack_from('<II', blob, offset)
        chunks[kind] = blob[offset + 8:offset + 8 + length]
        offset += 8 + length
    doc, binary = json.loads(chunks[0x4E4F534A]), chunks[0x004E4942]
    types = {5120: 'i1', 5121: 'u1', 5122: '<i2', 5123: '<u2', 5125: '<u4', 5126: '<f4'}
    def accessor(index):
        a = doc['accessors'][index]
        assert 'sparse' not in a
        view = doc['bufferViews'][a['bufferView']]
        count = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
        dtype = np.dtype(types[a['componentType']])
        start = view.get('byteOffset', 0) + a.get('byteOffset', 0)
        stride = view.get('byteStride', count * dtype.itemsize)
        return np.ndarray((a['count'], count), dtype=dtype, buffer=binary, offset=start,
                          strides=(stride, dtype.itemsize)).copy()
    triangles, material_ids = [], []
    def node(index, parent):
        n = doc['nodes'][index]
        if 'matrix' in n:
            local = np.array(n['matrix']).reshape(4, 4, order='F')
        else:
            x, y, z, w = n.get('rotation', [0, 0, 0, 1])
            local = np.eye(4)
            local[:3, :3] = np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                                      [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                                      [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]]) @ np.diag(n.get('scale', [1, 1, 1]))
            local[:3, 3] = n.get('translation', [0, 0, 0])
        world = parent @ local
        if 'mesh' in n:
            for p in doc['meshes'][n['mesh']]['primitives']:
                assert p.get('mode', 4) == 4 and 'KHR_draco_mesh_compression' not in p.get('extensions', {})
                position_spec=doc['accessors'][p['attributes']['POSITION']]
                assert position_spec['componentType']==5126 and not position_spec.get('normalized',False), 'Independent comparison requires actual FLOAT32 positions'
                pos = accessor(p['attributes']['POSITION']).astype(float)
                pos = (world @ np.column_stack([pos, np.ones(len(pos))]).T).T[:, :3]
                # glTF east/up/south -> author east/north/up.
                pos = pos[:, [0, 2, 1]] * [1, -1, 1]
                idx = accessor(p['indices']).reshape(-1) if 'indices' in p else np.arange(len(pos))
                t = pos[idx.reshape(-1, 3)]
                triangles.append(t)
                material_ids.extend([p.get('material', -1)] * len(t))
        for child in n.get('children', []): node(child, world)
    for root in doc['scenes'][doc.get('scene', 0)]['nodes']: node(root, np.eye(4))
    names = [m.get('name', str(i)) for i, m in enumerate(doc.get('materials', []))]
    return np.concatenate(triangles), np.array(material_ids), names, {'file': path.name, 'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest()}


def first_hit(tri, origin, direction):
    origin, direction = np.array(origin, float), np.array(direction, float)
    direction /= np.linalg.norm(direction)
    edge1, edge2 = tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
    h = np.cross(direction, edge2)
    det = np.einsum('ij,ij->i', edge1, h)
    valid = np.abs(det) > 1e-10
    inv = np.divide(1., det, out=np.zeros_like(det), where=valid)
    s = origin - tri[:, 0]
    u = inv * np.einsum('ij,ij->i', s, h)
    q = np.cross(s, edge1)
    v = inv * (q @ direction)
    distance = inv * np.einsum('ij,ij->i', edge2, q)
    valid &= (u >= -1e-8) & (v >= -1e-8) & (u + v <= 1 + 1e-8) & (distance > 1e-7)
    distance[~valid] = np.inf
    i = int(distance.argmin())
    value=float(distance[i])
    return i, value, origin + direction * value if np.isfinite(value) else np.full(3,np.nan)



class SerialScene:
    """Spatially bounded direct triangle rays, retaining actual material identity."""
    def __init__(self,path):
        self.tri,self.mi,self.materials,self.asset=load_triangles(path)
        self.lows,self.highs=self.tri.min(axis=1),self.tri.max(axis=1)
        self.cross=np.cross(self.tri[:,1]-self.tri[:,0],self.tri[:,2]-self.tri[:,0])
        self.areas=np.linalg.norm(self.cross,axis=1)*.5
    def ray(self,origin,direction,length=10,material_filter=None):
        o=np.asarray(origin,float);d=np.asarray(direction,float);d/=np.linalg.norm(d)
        end=o+d*length;lo=np.minimum(o,end)-1e-6;hi=np.maximum(o,end)+1e-6
        select=np.all(self.highs>=lo,axis=1)&np.all(self.lows<=hi,axis=1)
        if material_filter is not None:select &= np.isin(self.mi,[i for i,n in enumerate(self.materials) if material_filter(n)])
        ids=np.flatnonzero(select)
        if not len(ids):return None
        j,dist,p=first_hit(self.tri[ids],o,d)
        if not np.isfinite(dist) or dist>length:return None
        return {'distance_m':dist,'point_enu_m':p.tolist(),'material':self.materials[int(self.mi[ids[j]])],'triangle_index':int(ids[j])}
    def surface_digest(self):
        # Orientation-preserving triangle cycle canonicalization. Sorting lets
        # meshopt reorder indices while preserving the actual Float32 surfaces.
        digests={}
        for material in np.unique(self.mi):
            tris=self.tri[self.mi==material].astype('<f4');n=len(tris)
            flattened=np.stack([np.roll(tris,k,axis=1).reshape(n,9) for k in range(3)],axis=1)
            first=np.lexsort(tuple(flattened[:,:,j] for j in range(8,-1,-1)),axis=1)[:,0]
            canonical=flattened[np.arange(n),first]
            order=np.lexsort(tuple(canonical[:,j] for j in range(8,-1,-1)))
            name=self.materials[int(material)]
            digests[name]={'triangles':n,'sha256':hashlib.sha256(canonical[order].tobytes()).hexdigest()}
        return digests


def material_appearance(path):
    blob=path.read_bytes();size=struct.unpack_from('<I',blob,12)[0];doc=json.loads(blob[20:20+size])
    result={}
    used={primitive.get('material',-1) for mesh in doc.get('meshes',[]) for primitive in mesh.get('primitives',[])}
    for i,m in enumerate(doc.get('materials',[])):
        if i not in used:continue
        pbr=m.get('pbrMetallicRoughness',{})
        result[m.get('name',str(i))]={'baseColorFactor':pbr.get('baseColorFactor',[1,1,1,1]),'metallicFactor':pbr.get('metallicFactor',1),'roughnessFactor':pbr.get('roughnessFactor',1),'emissiveFactor':m.get('emissiveFactor',[0,0,0]),'alphaMode':m.get('alphaMode','OPAQUE'),'alphaCutoff':m.get('alphaCutoff',.5),'doubleSided':m.get('doubleSided',False),'extensions':m.get('extensions',{}),'textures':{k:v for k,v in {**pbr,**m}.items() if 'Texture' in k}}
    return {'materials':result,'embedded_image_count':len(doc.get('images',[])),'texture_count':len(doc.get('textures',[]))}
