"""Check normal directory camera sightlines to the two documented street elevations."""
import argparse
import gzip
import json
import math
from pathlib import Path
import runpy
import subprocess

from shapely.affinity import scale, translate
from shapely.geometry import Point, shape

AUDIT=Path(__file__).resolve().parent
PROJECT=AUDIT.parents[2]
SHARED=runpy.run_path(str(PROJECT/'data/audit/pure-heart-church-v1/check-overview-sightlines.py'))
MODEL='xuhui-xinle-orthodox-cathedral'
LOCAL=[('north door left',-.77,12.38,2.1),('north door right',.77,12.38,2.1),
       ('north fanlight',.45,12.30,5.19),('north gable arch',.60,12.30,13.28),
       ('east paired slit',11.45,2.13,2.21),('east gable arch',11.45,.54,13.28),
       ('central dome crown',0,0,35),('northeast dome crown',6.25,7,25.46),
       ('northwest dome shoulder',-6.25,7,23.96)]


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--contract',type=Path,default=AUDIT/'final-placement-contract.json')
    cli.add_argument('--out',type=Path,default=AUDIT/'overview-sightlines.json')
    args=cli.parse_args()
    contract=json.loads(args.contract.read_bytes())
    footprint=PROJECT/'source/precise'/MODEL/'footprint-review.json'
    review=json.loads(footprint.read_bytes())
    bind=next(r for r in review['frozen_bindings']if r['repository_path'].endswith('feature-table.json.gz'))
    buf=subprocess.check_output(['git','show',review['baseline_commit']+':'+bind['repository_path']],cwd=PROJECT)
    assert SHARED['digest'](buf)==bind['sha256']
    lon,lat=contract['lng'],contract['lat']
    k_n=math.radians(1)*SHARED['EARTH']
    k_e=k_n*math.cos(math.radians(lat))
    def en(g):return scale(translate(g,xoff=-lon,yoff=-lat),xfact=k_e,yfact=k_n,origin=(0,0))
    cut=en(shape(contract['replacement_geometry']))
    neighbors=[]
    for f in json.loads(gzip.decompress(buf))['features']:
        g=shape(f['geometry'])
        if g.distance(Point(lon,lat))>.002:continue
        g=en(g)
        if g.distance(Point(0,0))>145:continue
        height=f['height']
        if f['localId']==3953:
            g=g.difference(cut)
            height=contract['source_section_caps']['roof_m']
        if not g.is_empty:neighbors.append((f['localId'],g,height))
    h=math.radians(contract['heading'])
    targets=[(label,math.cos(h)*x+math.sin(h)*y,-math.sin(h)*x+math.cos(h)*y,z)for label,x,y,z in LOCAL]
    choices=[('selected',contract['overviewBearing'],contract['overviewPitch']),('street corner lower pitch',-169,34),
             ('north pavement',159,43),('east pavement',-110,46),('roof view',-150,26)]
    result={}
    for name,bearing,pitch in choices:
        checks=[]
        for screen,w,ht,pad in SHARED['VIEWS']:
            view=dict(width=w,height=ht,insets=dict(zip(('left','right','top','bottom'),pad)))
            checks.append(SHARED['evaluate']({**contract,'overviewBearing':bearing,'overviewPitch':pitch},
                        view,screen,neighbors,lon,lat,k_e,k_n,targets))
        result[name]=checks
    report=dict(model=MODEL,contract_sha256=SHARED['digest'](args.contract.read_bytes()),feature_table_sha256=bind['sha256'],
                camera_module_sha256=SHARED['digest']((PROJECT/'src/candidate-overview-camera.js').read_bytes()),
                tested_volumes=len(neighbors),checks=result,
                interpretation='以保留的原生楼体轮廓及高度检验目录相机。门扇及窄窗的实物首交另以模型表面射线验证。')
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print({key:[row['clear_count']for row in value]for key,value in result.items()},flush=True)
    assert all(r['clear_count']>=7 and all(p['clear']for p in r['probes'][:3])for r in result['selected'])


if __name__=='__main__':main()
