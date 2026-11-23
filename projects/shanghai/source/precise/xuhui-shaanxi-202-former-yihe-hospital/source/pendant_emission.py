"""Preserve the two lit inner globes in standard glTF materials."""
import hashlib
import json
from pathlib import Path
import struct

GLOBE='Yihe | illuminated vestibule globe'
EMISSION=[.95,.65,.20]

def bind(path,report):
    path=Path(path);raw=path.read_bytes();size,kind=struct.unpack_from('<II',raw,12)
    doc=json.loads(raw[20:20+size]);target=next(m for m in doc['materials'] if m['name']==GLOBE)
    target['emissiveFactor']=EMISSION
    chunk=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode('utf8')
    chunk+=b' '*((-len(chunk))%4);tail=raw[20+size:]
    data=struct.pack('<4sIIII',b'glTF',2,20+len(chunk)+len(tail),len(chunk),kind)+chunk+tail
    path.write_bytes(data)
    report.update(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
    path.with_suffix('.geometry.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report
