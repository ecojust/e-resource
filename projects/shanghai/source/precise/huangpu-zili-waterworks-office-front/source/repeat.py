"""Use a repeating sampler for this model's original tile in the shared Builder export."""
from hashlib import sha256
import json
from pathlib import Path
import struct

def repeat_only_texture(builder, filename):
    save = builder.save

    def save_tiled(path, *args, **kwargs):
        report = save(path, *args, **kwargs)
        path = Path(path)
        payload = bytearray(path.read_bytes())
        size = struct.unpack_from('<I', payload, 12)[0]
        descriptor = json.loads(payload[20:20+size])
        assert [item['name'] for item in descriptor['images']] == [filename]
        assert descriptor['textures'] == [{'source':0,'sampler':0}]
        sampler, = descriptor['samplers']
        assert (sampler['wrapS'],sampler['wrapT']) == (33071,33071)
        sampler.update(wrapS=10497,wrapT=10497)
        block = json.dumps(descriptor,ensure_ascii=False,separators=(',',':')).encode()
        assert 0 <= size-len(block) <= 3
        payload[20:20+size] = block.ljust(size,b' ')
        path.write_bytes(payload)
        report['sha256'] = sha256(payload).hexdigest()
        path.with_suffix('.geometry.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        return report

    builder.save = save_tiled
