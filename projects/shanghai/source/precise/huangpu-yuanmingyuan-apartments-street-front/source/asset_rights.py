"""Preserve the geometry and photographic attribution in the three GLBs and regular four-download export manifest."""
import json
import struct
from pathlib import Path

def document(path):
    data=Path(path).read_bytes()
    size=struct.unpack_from('<I',data,12)[0]
    return json.loads(data[20:20+size])

def retain_metadata(path,source):
    data=path.read_bytes()
    size=struct.unpack_from('<I',data,12)[0]
    result=json.loads(data[20:20+size])
    original=document(source)
    result['extras']=original['extras']
    # A model may incorporate licensed media. Preserve an explicitly supplied
    # copyright notice when gltfpack creates a new asset header.
    if 'copyright' in original['extras']:
        result['asset']['copyright']=original['asset']['copyright']
    header=json.dumps(result,ensure_ascii=False,separators=(',',':')).encode()
    header+=b' '*((-len(header))%4)
    bin_chunks=data[20+size:]
    path.write_bytes(struct.pack('<4sIIII',b'glTF',2,20+len(header)+len(bin_chunks),len(header),0x4e4f534a)+header+bin_chunks)

def licensed_writer(write_json, model):
    """Apply this model's license at the packager's final manifest write."""
    def write(path, record):
        if path.name=='manifest.json' and record.get('model_id')==model['id']:
            record={**record, 'geometry_license':model['geometry_license'], 'photos_embedded':model['photos_embedded']}
        write_json(path,record)
    return write
