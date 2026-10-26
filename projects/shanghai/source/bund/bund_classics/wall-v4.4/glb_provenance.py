"""Retain original authorship, OSM and photograph-reference provenance in GLB."""
from pathlib import Path
import json
import os
import struct

HERE = Path(__file__).resolve().parent


def copyright_for(ident):
    manifest = json.loads((HERE/'baseline-manifest.json').read_text())
    record = manifest['models'][ident]['original_navigation_record']
    reference = record['reference']
    return (f"Original geometric model/source: {manifest['original_author']}, MIT License. "
            f"OSM footprint © OpenStreetMap contributors, ODbL-1.0; {record['source_url']}. "
            f"Reference photograph (not embedded): {reference['author']}, "
            f"{reference['license']}; {reference['source']}; {reference['license_url']}. "
            "Structural wall topology corrected from the frozen native model; "
            "geographic position and source architectural interpretation retained.")


def retain_provenance(path, ident):
    path = Path(path)
    data = path.read_bytes()
    assert struct.unpack_from('<4sII',data) == (b'glTF',2,len(data))
    length,kind = struct.unpack_from('<II',data,12)
    assert kind == 0x4e4f534a
    document = json.loads(data[20:20+length])
    document['asset']['copyright'] = copyright_for(ident)
    payload = json.dumps(document,separators=(',',':'),ensure_ascii=False).encode()
    payload += b' '*((-len(payload))%4)
    tail = data[20+length:]
    result = (struct.pack('<4sII',b'glTF',2,20+len(payload)+len(tail))
              + struct.pack('<II',len(payload),0x4e4f534a) + payload + tail)
    assert len(result) < 100_000_000
    temporary = path.with_suffix(path.suffix+'.provenance.tmp')
    temporary.write_bytes(result)
    os.replace(temporary,path)
    return document['asset']
