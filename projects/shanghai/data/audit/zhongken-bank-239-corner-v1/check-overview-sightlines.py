"""Test the 239 street-corner tower and gate from the ordinary directory camera."""
from argparse import ArgumentParser
from pathlib import Path
import gzip
import importlib.util
import json
import math
import subprocess

from shapely.affinity import scale,translate
from shapely.geometry import Point,shape

HERE=Path(__file__).resolve().parent
shared=HERE.parent/'pure-heart-church-v1/check-overview-sightlines.py'
spec=importlib.util.spec_from_file_location('courtyard_camera_audit',shared)
camera=importlib.util.module_from_spec(spec)
spec.loader.exec_module(camera)
PROJECT=HERE.parents[2]

def main():
    cli=ArgumentParser(description=__doc__)
    cli.add_argument('--contract',type=Path,default=HERE/'final-placement-contract.json')
    cli.add_argument('--out',type=Path,default=HERE/'overview-sightlines.json')
    cli.add_argument('--table',type=Path)
    cli.add_argument('--explore',action='store_true')
    args=cli.parse_args()
    contract=json.loads(args.contract.read_bytes())
    source=PROJECT/'source/precise'/contract['id']/'footprint-review.json'
    review=json.loads(source.read_bytes())
    binding=next(b for b in review['frozen_bindings']if b['repository_path'].endswith('feature-table.json.gz'))
    buf=args.table.read_bytes() if args.table else subprocess.check_output(['git','-C',PROJECT.parents[1],'show',review['baseline_commit']+':'+binding['repository_path']])
    assert camera.digest(buf)==binding['sha256']
    lon,lat=contract['lng'],contract['lat']
    north=math.radians(1)*camera.EARTH;east=north*math.cos(math.radians(lat))
    def meters(g):
        return scale(translate(g,xoff=-lon,yoff=-lat),xfact=east,yfact=north,origin=(0,0))
    neighbors=[];mask=meters(shape(contract['replacement_geometry']))
    for f in json.loads(gzip.decompress(buf))['features']:
        if not f.get('geometry'):continue
        poly=meters(shape(f['geometry']))
        if poly.distance(Point(0,0))>440:continue
        if f['localId'] ==contract['owner']['feature_local_id']:poly=poly.difference(mask)
        neighbors.append((f['localId'],poly,f['height']))
    h=math.radians(contract['heading']);c,s=math.cos(h),math.sin(h)
    targets=[]
    local=[('Left iron leaf boss',-1.015,.145,3.12),('Right iron leaf boss',1.015,.145,3.12),('Former sign beds',.348,-.151,9.82),
           ('Granite west jamb',2.7,-.125,5.62),('Granite east jamb',-2.7,-.125,5.62),('Transom chevrons',.9,.16,7.66),
           ('Third row central pane',.20,.31,18.82),('Tall western jamb',2.57,-.145,22.35),('Upper three-light row',.19,.31,36.82),
           ('Top central window',.20,.31,40.41),('Crown ventilation slot',.54,.26,42.9),('Stepped crown field',0,.0,44.26)]
    for name,x,y,z in local:
        targets.append((name,x*c+y*s,-x*s+y*c,z))
    rows=[]
    for name,width,height,pad in camera.VIEWS:
        viewport=dict(width=width,height=height,insets=dict(zip(['left','right','top','bottom'],pad)))
        rows.append(camera.evaluate(contract,viewport,name,neighbors,lon,lat,east,north,targets))
    if args.explore:
        options=[]
        for bearing in [-156,-153,-150,-148,-145,-142,-139,-136]:
            for pitch in [54,50,46,43,41,39,37,35]:
                contract.update(overviewBearing=bearing,overviewPitch=pitch)
                checks=[camera.evaluate(contract,dict(width=width,height=height,insets=dict(zip(['left','right','top','bottom'],pad))),name,neighbors,lon,lat,east,north,targets) for name,width,height,pad in camera.VIEWS]
                options.append({'bearing':bearing,'pitch':pitch,'clear':[v['clear_count']for v in checks]})
        print(json.dumps(options));return
    assert [r['clear_count']for r in rows]==[len(targets)]*2
    result=dict(source_sha256=camera.digest(buf),contract_sha256=camera.digest(args.contract.read_bytes()),
                shared_camera_checker_sha256=camera.digest(shared.read_bytes()),camera_module_sha256=camera.digest((PROJECT/'src/candidate-overview-camera.js').read_bytes()),
                measured_frozen_volumes=len(neighbors),views=rows,
                method_zh='核对普通目录手机与桌面两端对239号铁门、石框、三联窗带和退台塔冠的视线。')
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
