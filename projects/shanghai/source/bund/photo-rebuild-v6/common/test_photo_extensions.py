"""Verify unchanged JPEG embedding and geometry-preserving selective UV export."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import numpy as np
from photo_architecture import Builder


def main(photo, output):
    source=photo.read_bytes();b=Builder()
    b.box((0,0,0),(1,.1,1),'recessed glass',label='selected-real-glass')
    b.box((2,0,0),(1,.1,1),'recessed glass',label='unselected-glass')
    original=[(p['vertices'][:],p['triangles'][:]) for p in b.parts]
    orientation={'rawSize':[5184,3456],'exifOrientation':6,'uvConvention':'stored-pixels'}
    r=b.photograph_parts(photo,lambda p:(.4+p[0]*.1,.4+p[2]*.1),
                         lambda p:p['label']=='selected-real-glass',orientation=orientation)
    assert r['parts']==1
    assert 'texcoords' not in b.parts[1]
    assert all(p['vertices']==old[0] and p['triangles']==old[1] for p,old in zip(b.parts,original))
    with tempfile.TemporaryDirectory(prefix='photo-export-check-') as directory:
        path=Path(directory)/'sample.glb';b.save(path);data=path.read_bytes()
        n,kind=struct.unpack_from('<II',data,12);assert kind==0x4E4F534A
        doc=json.loads(data[20:20+n]);binary=data[28+n:]
        assert len(doc['images'])==1
        view=doc['bufferViews'][doc['images'][0]['bufferView']]
        assert binary[view['byteOffset']:view['byteOffset']+view['byteLength']]==source
        for primitive in doc['meshes'][0]['primitives']:
            material=doc['materials'][primitive['material']]
            if material['name'].startswith('PhotoFacade_'):
                assert material['extras']['photographicSource']==orientation
                a=doc['accessors'][primitive['attributes']['TEXCOORD_0']];v=doc['bufferViews'][a['bufferView']]
                uv=np.frombuffer(binary,dtype='<f4',count=a['count']*2,offset=v['byteOffset']).reshape(-1,2)
                assert np.isfinite(uv).all() and np.all((uv>=0)&(uv<=1))
                assert np.allclose(uv.min(0),[.35,.35]) and np.allclose(uv.max(0),[.45,.45])
            else:assert 'TEXCOORD_0' not in primitive['attributes']
        assert all('uri' not in x for x in doc['buffers']+doc['images'])
    rejected=Builder();rejected.box((0,0,0),(1,1,1))
    try:rejected.photograph_parts(photo,lambda p:(2.,-.1),lambda p:True)
    except ValueError:pass
    else:raise AssertionError('Invalid source UV was accepted')
    report={'passed':True,'source_sha256':hashlib.sha256(source).hexdigest(),
            'source_bytes':len(source),'geometry_unchanged_by_mapping':True,
            'unselected_parts_unchanged':True,'embedded_original_bytes_identical':True,
            'stored_uv_and_orientation_metadata_checked':True,'out_of_image_uv_rejected':True,
            'limitations':['This checks export integrity, not photographic registration or actual browser decoding.']}
    output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--photo',type=Path,required=True)
    ap.add_argument('--output',type=Path,default=Path(__file__).with_name('photographic-geometry-audit.json'))
    args=ap.parse_args();main(args.photo,args.output)
