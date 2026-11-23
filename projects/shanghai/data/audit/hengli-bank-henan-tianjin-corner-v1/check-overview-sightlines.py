"""Test the Hengli Bank entrance, both streets, and the upper setback from the ordinary directory camera."""
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
    local=[('Corner kindergarten entrance',1.54,1.56,3.27),('Projecting stone portal',1.54,1.45,5.02),('Brown chamfer second sash',1.46,1.94,9.7),
           ('Henan continuous fin',2.80,4.5,11.8),('Henan central brass doorway',1.90,16.55,3.6),('Henan high sash',1.11,26.48,23.0),
           ('Tianjin paired street windows',-5.75,-.12,3.0),('Tianjin fin and window',-8.5,0.,13.4),('Tianjin brick end',-14.25,-.02,11.25),
           ('Setback southeast corner',-2.16,6.53,27.24),('Upper corners north light',-2.16,10.70,26.10),('High setback parapet',-6.02,6.54,29.17)]
    for name,x,y,z in local:
        targets.append((name,x*c+y*s,-x*s+y*c,z))
    rows=[]
    for name,width,height,pad in camera.VIEWS:
        viewport=dict(width=width,height=height,insets=dict(zip(['left','right','top','bottom'],pad)))
        rows.append(camera.evaluate(contract,viewport,name,neighbors,lon,lat,east,north,targets))
    if args.explore:
        options=[]
        for bearing in [-64,-58,-52,-48,-44,-39,-35,-31,-25]:
            for pitch in [54,50,46,43,41,39,37,35]:
                contract.update(overviewBearing=bearing,overviewPitch=pitch)
                checks=[camera.evaluate(contract,dict(width=width,height=height,insets=dict(zip(['left','right','top','bottom'],pad))),name,neighbors,lon,lat,east,north,targets) for name,width,height,pad in camera.VIEWS]
                options.append({'bearing':bearing,'pitch':pitch,'clear':[v['clear_count']for v in checks]})
        print(json.dumps(options));return
    assert [r['clear_count']for r in rows]==[len(targets)]*2
    result=dict(source_sha256=camera.digest(buf),contract_sha256=camera.digest(args.contract.read_bytes()),
                shared_camera_checker_sha256=camera.digest(shared.read_bytes()),camera_module_sha256=camera.digest((PROJECT/'src/candidate-overview-camera.js').read_bytes()),
                measured_frozen_volumes=len(neighbors),views=rows,
                method_zh='核对手机与桌面从东南路口看两街窗带、幼儿园门牌、黄铜侧门和退台高窗的视线。')
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
