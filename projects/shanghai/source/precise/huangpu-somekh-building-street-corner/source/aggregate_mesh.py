"""Select repeating metric UVs for this facade's original aggregate material."""
from pathlib import Path
import json,struct
from photo_architecture import Builder

class AggregateBuilder(Builder):
    def save(self,path,metadata=None):
        super().save(path,metadata)
        # The shared exporter uses a single clamped sampler for photographic
        # atlases. This model has one original, repeating aggregate texture.
        path=Path(path)
        with path.open('r+b')as stream:
            stream.seek(12)
            size,chunk=struct.unpack('<II',stream.read(8))
            if chunk!=0x4e4f534a:raise ValueError('Missing glTF JSON chunk')
            original=stream.read(size)
            doc=json.loads(original)
            if len(doc['images'])!=1 or len(doc['samplers'])!=1:
                raise ValueError('Expected one original aggregate texture')
            sampler=doc['samplers'][0]
            if sampler['wrapS']!=33071 or sampler['wrapT']!=33071:
                raise ValueError('Unexpected source texture sampler')
            # Both constants have five digits. Replacing just the JSON keys keeps all
            # embedded image bytes and all geometry offsets exactly as exported.
            import re
            revised,n=re.subn(rb'("wrap[ST]"\s*:\s*)33071',rb'\g<1>10497',original)
            if n!=2 or len(revised)!=size:raise ValueError('Could not update the aggregate sampler')
            stream.seek(20);stream.write(revised)
