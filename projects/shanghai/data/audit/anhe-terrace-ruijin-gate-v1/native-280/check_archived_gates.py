"""Check the five frozen gate files and replay the signed exterior queries on three decoded meshes."""
import argparse
import hashlib
import json
import lzma
import os
from pathlib import Path
import runpy

def digest(b):
    return hashlib.sha256(b).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('project', type=Path)
    parser.add_argument('checked', type=Path)
    parser.add_argument('output', type=Path)
    arg = parser.parse_args()
    os.environ['SHANGHAI_PROJECT_ROOT'] = str(arg.project.resolve())
    survey = arg.project / 'source/precise/huangpu-anhe-terrace-ruijin-gate/source/check_surfaces.py'
    tool = runpy.run_path(str(survey)); catalog = arg.checked / 'packed-paths.json'
    marks = json.loads(catalog.read_bytes())
    manifest = arg.checked / 'manifest.json'
    source = json.loads(manifest.read_bytes())
    observed = {}; probes = {}
    for name, expected in marks.items():
        packed = (arg.checked/(name+'.xz')).read_bytes()
        assert digest(packed) == expected['xz_sha256'] and len(packed) == expected['xz']
        raw = lzma.decompress(packed)
        assert digest(raw)==expected['sha256'] and len(raw)==expected['bytes']
        observed[name]={'sha256':digest(raw),'bytes':len(raw),'xz_sha256':digest(packed)}
        role = {'raw.glb':'raw','decoded-full.glb':'full','decoded-lod.glb':'lod'}.get(name)
        if role is None:continue
        fd=os.memfd_create('anhe-checked',os.MFD_CLOEXEC)
        try:
            with os.fdopen(fd,'wb',closefd=False) as f:f.write(raw)
            geom=tool['Reader'](Path('/proc/self/fd')/str(fd)); test=tool['check'](geom)
            assert test['passed'] and all(r['passed'] for r in test['samples'])
            probes[role]={'file':name,'sample_count':len(test['samples']),'passed':test['passed'],'samples':test['samples']}
        finally:os.close(fd)
    for k,a in source['assets'].items():assert observed[a['file']]['sha256']==a['sha256']
    report={'id':source['id'],'manifest_sha256':digest(manifest.read_bytes()),'packed_path_catalog_sha256':digest(catalog.read_bytes()),'query_program_sha256':digest(survey.read_bytes()),'checked_files':observed,'roles':probes}
    arg.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print({k:r['sample_count'] for k,r in probes.items()},digest(arg.output.read_bytes()))
if __name__=='__main__':main()
