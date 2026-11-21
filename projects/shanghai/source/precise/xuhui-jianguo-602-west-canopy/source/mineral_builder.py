"""Keep both original, metric finish images on a repeating sampler."""
import json
import re
import struct
from pathlib import Path
from photo_architecture import Builder

class MineralBuilder(Builder):
    def save(self, path, metadata=None):
        super().save(path,metadata)
        with Path(path).open('r+b') as stream:
            stream.seek(12)
            size,kind=struct.unpack('<II',stream.read(8))
            assert kind==0x4e4f534a
            original=stream.read(size)
            document=json.loads(original)
            expected={'ochre-dragged-render.png','dressed-grey-granite.png'}
            assert len(document['images'])==2 and {v['name'] for v in document['images']}==expected
            assert len(document['samplers'])==1 and all(t['sampler']==0 for t in document['textures'])
            updated,n=re.subn(rb'("wrap[ST]"\s*:\s*)33071',rb'\g<1>10497',original)
            assert n==2 and len(updated)==size
            stream.seek(20)
            stream.write(updated)
