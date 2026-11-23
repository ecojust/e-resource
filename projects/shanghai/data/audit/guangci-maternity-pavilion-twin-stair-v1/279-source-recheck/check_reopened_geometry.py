"""Repeat the signed courtyard and open-space queries on the three delivered mesh roles."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile


def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def verify(project, assets, audited, out):
    helper=project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
    Scene=runpy.run_path(str(helper))['SerialScene']
    package=json.loads((assets/'manifest.json').read_text())
    rays=json.loads((audited/'preflight/geometry-rays.json').read_text())
    decoder=project/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
    codec=project/'vendor/meshopt_decoder.module.js'
    roles={}
    with tempfile.TemporaryDirectory(dir=out.parent) as tmp:
        for role in ('raw','full','lod'):
            rec=package['assets'][role];source=assets/rec['file'];mesh=source
            assert digest(source)==rec['sha256'],role
            if role!='raw':
                mesh=Path(tmp)/(role+'.glb')
                subprocess.run(['node',decoder,source,mesh,codec],check=True,stdout=subprocess.DEVNULL)
            scene=Scene(mesh);cases=[]
            for case in rays[role]['cases']:
                hit=scene.ray(case['origin'],case['direction'],case['length'])
                allowed=case['allowed']
                good=(hit is None) if allowed is None else bool(hit and hit['material'] in allowed)
                limits=case.get('range_m')
                if limits:
                    good=bool(good and hit and limits[0]<=hit['distance_m']<=limits[1])
                cases.append({'feature':case['name'],'hit':hit,'passes':good})
            roles[role]=dict(delivered_sha256=digest(source),decoded_sha256=digest(mesh),
                triangles=len(scene.tri),rays=len(cases),passed=sum(row['passes'] for row in cases),
                open_spaces=sum(c['allowed'] is None for c in rays[role]['cases']),
                original_reference_mesh_sha256=rays[role]['asset']['sha256'],
                material_and_distance=cases)
            del scene
    doc=dict(id=package.get('id'),original_queries_sha256=digest(audited/'preflight/geometry-rays.json'),
             helper_sha256=digest(helper),decoder_sha256=digest(decoder),codec_sha256=digest(codec),roles=roles)
    out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
    print([(k,v['triangles'],v['passed'],v['rays']) for k,v in roles.items()])
    assert all(v['rays']==232 and v['passed']==232 and v['open_spaces']==43 for v in roles.values())


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for name in ('project','assets','audit','output'):cli.add_argument(name,type=Path)
    opt=cli.parse_args();verify(opt.project,opt.assets,opt.audit,opt.output)
