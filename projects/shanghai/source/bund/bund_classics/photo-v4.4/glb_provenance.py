"""Canonical provenance retained after optimizers rewrite the glTF asset block."""
from pathlib import Path
import json,struct,os
COPYRIGHT=('Photograph/reference: Suicasmo, CC0-1.0; '
 'https://commons.wikimedia.org/wiki/File:North_China_Daily_News_Building_20250501.jpg ; '
 'https://creativecommons.org/publicdomain/zero/1.0/ . '
 'Original geometric model/source: MIT. OSM footprint © OpenStreetMap contributors, ODbL-1.0.')
def retain_provenance(path):
 path=Path(path);data=path.read_bytes();length,kind=struct.unpack_from('<II',data,12)
 assert kind==0x4e4f534a and data[:4]==b'glTF'
 document=json.loads(data[20:20+length]);document['asset']['copyright']=COPYRIGHT
 payload=json.dumps(document,separators=(',',':'),ensure_ascii=False).encode('utf-8');payload+=b' '*((-len(payload))%4)
 tail=data[20+length:];result=struct.pack('<4sII',b'glTF',2,20+len(payload)+len(tail))+struct.pack('<II',len(payload),0x4e4f534a)+payload+tail
 temporary=path.with_suffix(path.suffix+'.provenance.tmp');temporary.write_bytes(result);os.replace(temporary,path)
 return document['asset']
