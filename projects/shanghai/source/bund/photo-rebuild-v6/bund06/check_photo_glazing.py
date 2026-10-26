#!/usr/bin/env python3
"""Verify published GLB image bytes, photographic selection, finite in-range UVs."""
from pathlib import Path
import json,struct,hashlib,argparse,numpy as np
HERE=Path(__file__).resolve().parent

def verify(path):
    data=path.read_bytes();magic,version,total=struct.unpack_from('<4sII',data,0);assert magic==b'glTF' and version==2 and total==len(data)
    length,typ=struct.unpack_from('<I4s',data,12);assert typ==b'JSON';doc=json.loads(data[20:20+length]);pos=20+length;n,typ=struct.unpack_from('<I4s',data,pos);assert typ==b'BIN\0';blob=data[pos+8:pos+8+n]
    ctl=json.loads((HERE/'photo-glass-controls.json').read_text());photo=(HERE/ctl['image']).read_bytes();imgs=[]
    for im in doc.get('images',[]):
        view=doc['bufferViews'][im['bufferView']];v=blob[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]
        imgs.append({'bytes':len(v),'sha256':hashlib.sha256(v).hexdigest(),'original_jpeg_bytes_exact':v==photo})
    assert len(imgs)==1 and imgs[0]['original_jpeg_bytes_exact']
    ids=[i for i,m in enumerate(doc['materials']) if m.get('name')=='PhotoFacade_Bund06Glass'];assert len(ids)==1;records=[]
    def acc(i):
        a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];assert a['componentType']==5126
        dim={'VEC2':2,'VEC3':3}[a['type']];off=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',dim*4)
        return np.ndarray((a['count'],dim),dtype='<f4',buffer=blob,offset=off,strides=(stride,4))
    for m in doc['meshes']:
        for p in m['primitives']:
            if p.get('material') not in ids:continue
            name=doc['materials'][p['material']]['name'];uv=acc(p['attributes']['TEXCOORD_0']);assert np.isfinite(uv).all() and uv.min()>=0 and uv.max()<=1
            records.append({'material':name,'triangles':doc['accessors'][p['indices']]['count']//3,'uv_min':uv.min(axis=0).astype(float).tolist(),'uv_max':uv.max(axis=0).astype(float).tolist()})
    expected=sum(p['selected'] for w in ctl['windows'] for p in w['panes'])
    geo=json.loads(path.with_suffix('.geometry.json').read_text());assert geo['sha256']==hashlib.sha256(data).hexdigest()
    parts=[p for p in geo['part_summary'] if p['material']=='PhotoFacade_Bund06Glass'];assert len(parts)==expected and all('-pane-r' in p['label'] for p in parts)
    assert sum(p['triangles'] for p in parts)==sum(p['triangles'] for p in records)
    report={'passed':True,'file':path.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'image_count':len(imgs),'images':imgs,'photo_material_count':len(ids),'photographic_panes':len(parts),'photo_primitives':len(records),'expected_control_panes':expected,'only_pane_geometry_uses_photo':True,'all_uv_finite_and_in_source_bounds':True,'file_under_100000000':len(data)<100000000,'scope':'Stored GLB original JPEG bytes and material/UV validation; source part selection verified against SHA-bound geometry sidecar and serialized material triangle count. Does not replace photo or render review.','panes':records}
    return report
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('model',type=Path);ap.add_argument('--report',type=Path);args=ap.parse_args();r=verify(args.model)
    if args.report:args.report.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps({k:v for k,v in r.items() if k!='panes'}))
