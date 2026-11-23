"""Test independent image samples against the actual triangles of an exported courtyard model."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy

import numpy as np

HERE=Path(__file__).resolve().parent
HELPER=HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
# Sampled from the two original publications independently of the camera edge fit.
PICKS={
 'whb2019':[
  ('right cream screen, second from top',[435,205],'pale horizontal screen'),
  ('right cream screen, centre',[435,220],'pale horizontal screen'),
  ('right cream screen, next to floor',[435,249],'pale horizontal screen'),
  ('right screen through-slot',[440,212],'garden glass'),
  ('left screen lower cream strip',[119,225],'pale horizontal screen'),
  ('left screen upper cream strip',[119,179],'pale horizontal screen'),
  ('left screen through-slot',[119,203],'garden glass'),
  ('red-framed far opening',[349,212],'garden glass'),
  ('pale curtained bay outer face',[290,207],'garden glass'),
  ('upper ivory condenser casing',[389,193],'existing ivory unit'),
  ('canopy fascia right of the corner',[300,160],'dark olive roof fascia'),
  ('soffit above pale glazing',[295,176],'painted cream soffit')],
 'garden2017':[
  ('outer green glazing between stiles',[81,175],'garden glass'),
  ('left screen middle light member',[136,185],'pale horizontal screen'),
  ('left screen through-slot',[135,180],'garden glass'),
  ('right screen second light member',[319,178],'pale horizontal screen'),
  ('right screen lower light member',[319,194],'pale horizontal screen'),
  ('right screen through-slot',[320,182],'garden glass'),
  ('central curtain outer glazing',[242,177],'garden glass'),
  ('red framing and shadow inside corner',[178,179],'garden glass'),
  ('low garden pool surface',[260,223],'shallow garden water'),
  ('rear wall roof lip',[265,157],'painted cream soffit')]
}


def check(path):
    scene=runpy.run_path(str(HELPER))['SerialScene'](path)
    survey=json.loads((HERE/'garden-cameras.json').read_bytes())
    report={'mesh_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'views':{}}
    for name,picks in PICKS.items():
        camera=survey['stations'][name]
        k,r,eye=[np.array(camera[n])for n in ('K','R','C')]
        def read(uv):
            v=r.T@np.linalg.solve(k,[*uv,1])
            hit=scene.ray(eye,v/np.linalg.norm(v),150)
            return hit and hit['material']
        out=[]
        for label,uv,wanted in picks:
            expect='Yao | '+wanted
            actual=read(uv)
            nearest=None
            offsets=sorted(((x,y)for x in range(-4,5)for y in range(-4,5)if x*x+y*y<=16),key=lambda q:q[0]**2+q[1]**2)
            for dx,dy in offsets:
                if read([uv[0]+dx,uv[1]+dy])==expect:
                    nearest=[dx,dy];break
            out.append({'feature':label,'xy_native':uv,'expected_material':expect,'first_hit_material':actual,
                        'direct':actual==expect,'nearest_matching_offset_within_4px':nearest})
        report['views'][name]={'observations':out,'direct_count':sum(x['direct'] for x in out),
                                   'within_4px_count':sum(x['nearest_matching_offset_within_4px'] is not None for x in out)}
    return report


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('mesh',type=Path);cli.add_argument('output',type=Path)
    args=cli.parse_args();args.output.write_text(json.dumps(check(args.mesh),indent=2)+'\n')
