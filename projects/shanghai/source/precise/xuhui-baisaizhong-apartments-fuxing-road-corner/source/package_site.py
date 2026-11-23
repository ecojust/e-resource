"""Assemble the four primary assets and the separate 1930s garage-door option."""
from pathlib import Path
import argparse,hashlib,json,shutil
from build_model import ID

def assemble(pack,native,garage,dest):
    manifest=json.loads((native/'four-role-manifest.json').read_bytes())
    if manifest['id']!=ID or set(manifest['assets'])!={'raw','full','lod','native'}:
        raise ValueError('Incomplete or unrelated four-role manifest')
    dest.mkdir(exist_ok=True,parents=True)
    for role,item in manifest['assets'].items():
        source=(native if role=='native'else pack)/item['file']
        if source.stat().st_size!=item['bytes'] or hashlib.sha256(source.read_bytes()).hexdigest()!=item['sha256']:
            raise ValueError(f'Unverified {role} file {source}')
        if source.resolve()!=(dest/source.name).resolve():shutil.copyfile(source,dest/source.name)
    payload=garage.read_bytes()
    doc=json.loads(payload[20:20+int.from_bytes(payload[12:16],'little')])
    tris=sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes']for p in m['primitives'])
    if tris<=0:raise ValueError('Garage model is empty')
    optional=ID+'-garage-1930s.glb'
    (dest/optional).write_bytes(payload)
    manifest['variants']={'garage1930s':{'file':optional,'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest(),
                           'triangles':tris,'shown_by_default':False,'source':'https://collections.lib.uwm.edu/digital/collection/agsphoto/id/16659/rec/11',
                           'period':'1930年代','source_photograph_embedded':False}}
    (dest/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for field in ['pack','native','garage','dest']:parser.add_argument(field,type=Path)
    a=parser.parse_args();m=assemble(a.pack,a.native,a.garage,a.dest)
    print(ID, {r:v['bytes']for r,v in (m['assets']|m['variants']).items()})
