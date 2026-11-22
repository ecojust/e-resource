"""Set repeat sampling for the original courses on the Guiren Li street front."""
import hashlib,json,struct,re
from pathlib import Path
from photo_architecture import Builder
from material_names import TEXTURES
class RepeatingBuilder(Builder):
    def save(self,path,metadata=None):
        report=super().save(path,metadata)
        path=Path(path)
        with path.open('r+b') as f:
            f.seek(12);size,kind=struct.unpack('<II',f.read(8));assert kind==0x4e4f534a
            raw=f.read(size);doc=json.loads(raw);assert len(doc['samplers'])==1
            assert {im['name']for im in doc['images']}=={file.name for file in TEXTURES.values()}
            for mat in doc['materials']:
                pbr=mat['pbrMetallicRoughness']
                if mat['name'] in TEXTURES:
                    tex=doc['textures'][pbr['baseColorTexture']['index']];im=doc['images'][tex['source']]
                    assert tex['sampler']==0 and im['name']==TEXTURES[mat['name']].name
            revised,n=re.subn(rb'("wrap[ST]"\s*:\s*)33071',rb'\g<1>10497',raw)
            assert len(revised)==size and n==2
            f.seek(20);f.write(revised)
        report['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        path.with_suffix('.geometry.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        return report
