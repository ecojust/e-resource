"""Export sample street windows and read actual glTF attribute arrays and texture bytes."""
import hashlib,json,struct,sys,tempfile
from pathlib import Path
import numpy as np

project = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
outdir = Path(sys.argv[2]).resolve() if len(sys.argv)>2 else project.parents[2]/'data/audit/nanyang-continental-court-street-front-v1/sashes'
outdir.mkdir(parents=True,exist_ok=True)
cache=tempfile.TemporaryDirectory(prefix="continental-sash-glb-")
out=Path(cache.name)
common=project.parent/'hongkou-general-post-office/source/common'
sys.path[:0]=[str(project/'source'),str(common)]
from continental_window_sashes import add_sash,PALETTE
from photo_architecture import Builder

data=json.loads((project/'measurements/street-window-schedule.json').read_bytes())
sample=data['bays'][7]
rows=[]
for lod in (False,True):
    builder=Builder(PALETTE)
    for fl in sample['floors']:
        bounds=fl['openings_u_m']
        for index,(a,b) in enumerate(bounds):
            add_sash(builder,lod,lambda x,y,z:(x,y,z),7,fl['floor'],index,a,b,fl['sill_z'],fl['head_z'],fl['face_depth_m']+fl['sash_recess_m'])
    path=out/('bay07-distant.glb' if lod else 'bay07-near.glb')
    builder.save(path)
    raw=path.read_bytes()
    n,kind=struct.unpack_from('<I4s',raw,12); assert kind==b'JSON'
    doc=json.loads(raw[20:20+n]); length,kind=struct.unpack_from('<I4s',raw,20+n);assert kind==b'BIN\x00'
    buf=memoryview(raw)[28+n:28+n+length]
    def portion(idx):
        v=doc['bufferViews'][idx];return buf[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
    def arr(idx):
        ac=doc['accessors'][idx];v=portion(ac['bufferView'])
        return np.frombuffer(v,dtype='<f4',count=ac['count']*2,offset=ac.get('byteOffset',0)).reshape((-1,2))
    glazed=[]
    for mesh in doc['meshes']:
        for p in mesh['primitives']:
            name=doc['materials'][p['material']]['name']
            if not name.endswith('glass'):continue
            uv=arr(p['attributes']['TEXCOORD_0'])
            assert np.isfinite(uv).all() and np.ptp(uv,axis=0).min()>.03
            z=doc['materials'][p['material']]['pbrMetallicRoughness']['baseColorTexture']['index']
            img=doc['images'][doc['textures'][z]['source']]
            texture_sha=hashlib.sha256(portion(img['bufferView'])).hexdigest()
            assert texture_sha==hashlib.sha256((project/'source/window-glazing.png').read_bytes()).hexdigest()
            glazed.append((name,len(uv)))
    assert len(glazed)==3
    rows.append(dict(file=path.name,sha256=hashlib.sha256(raw).hexdigest(),material_uvs=glazed,embedded_png_sha256=texture_sha))
(outdir/'glb-glass-uv.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows))
