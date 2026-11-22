"""Check the restored street arcade, the curved corner and the roof openings against intact city solids."""
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
    cli.add_argument('--explore',action='store_true')
    cli.add_argument('--control',action='store_true',help='Record a comparison camera even when a retained neighbor obscures part of the facade.')
    args=cli.parse_args()
    contract=json.loads(args.contract.read_bytes())
    source=PROJECT/'source/precise'/contract['id']/'footprint-review.json'
    review=json.loads(source.read_bytes())
    binding=next(b for b in review['frozen_bindings']if b['repository_path'].endswith('feature-table.json.gz'))
    buf=subprocess.check_output(['git','-C',PROJECT.parents[1],'show',review['baseline_commit']+':'+binding['repository_path']])
    assert camera.digest(buf)==binding['sha256']
    lon,lat=contract['lng'],contract['lat']
    north=math.radians(1)*camera.EARTH;east=north*math.cos(math.radians(lat))
    def meters(g):
        return scale(translate(g,xoff=-lon,yoff=-lat),xfact=east,yfact=north,origin=(0,0))
    neighbors=[];mask=meters(shape(contract['replacement_geometry']))
    for f in json.loads(gzip.decompress(buf))['features']:
        if not f.get('geometry'):continue
        poly=meters(shape(f['geometry']))
        if poly.distance(Point(0,0))>180:continue
        if f['localId']==contract['owner']['feature_local_id']:poly=poly.difference(mask)
        neighbors.append((f['localId'],poly,f['height']))
    h=math.radians(contract['heading']);c,s=math.cos(h),math.sin(h)
    targets=[]
    for name,x,y,z in [('west arcade',-18.,.14,2.22),('east covered arcade',16.1,.12,2.22),
                       ('corner return',23.65,.89,3.1),('west gable',-19.09,-.03,17.38),
                       ('middle gable',0.,-.03,17.49),('east gable',19.09,-.03,17.38),
                       ('paired dormers',-6.6,.84,16.65),('arched balcony rail',8.36,-.11,9.12)]:
        targets.append((name,x*c+y*s,-x*s+y*c,z))
    rows=[]
    for name,width,height,pad in camera.VIEWS:
        viewport=dict(width=width,height=height,insets=dict(zip(['left','right','top','bottom'],pad)))
        rows.append(camera.evaluate(contract,viewport,name,neighbors,lon,lat,east,north,targets))
    if args.explore:
        options=[]
        for bearing in [-80,-65,-48,-32,-22,-16,-8,0,12,28,42,58,74]:
            for pitch in [53,47,43,39,34,29,24,19]:
                contract.update(overviewBearing=bearing,overviewPitch=pitch)
                checks=[camera.evaluate(contract,dict(width=width,height=height,insets=dict(zip(['left','right','top','bottom'],pad))),name,neighbors,lon,lat,east,north,targets) for name,width,height,pad in camera.VIEWS]
                options.append({'bearing':bearing,'pitch':pitch,'clear':[v['clear_count']for v in checks]})
        print(json.dumps(options));return
    adequate=all(row['clear_count']==len(targets) for row in rows)
    if not args.control:assert adequate
    result_kind='comparison' if args.control else 'selected_default'
    result=dict(passed=adequate,role=result_kind,source_sha256=camera.digest(buf),contract_sha256=camera.digest(args.contract.read_bytes()),
                shared_camera_checker_sha256=camera.digest(shared.read_bytes()),camera_module_sha256=camera.digest((PROJECT/'src/candidate-overview-camera.js').read_bytes()),
                measured_frozen_volumes=len(neighbors),views=rows,
                method_zh='按2965沿九江路制作范围扣去其临街部分，保留其余楼体及附近独立建筑原高度，检查首层外廊、路口弧角、三山花及阁窗与栏杆。')
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
