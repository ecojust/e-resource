"""Test the 320 portal, the rounded corner and the south arch from the ordinary directory camera."""
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
    local=[('320 paired entrance',-4.12,10.33,1.62),('320 gold inscription',-4.16,10.33,3.43),
           ('West sash rail',-4.18,10.4,13.42),('West-window hood',-4.37,14.2,18.79),
           ('Rounded blue fascia',-3.10,1.28,4.07),('First curved bay',-3.23,1.87,10.2),
           ('Second curved bay',-1.61,.39,15.80),('Curved upper entablature',-2.62,.60,22.98),
           ('South sash',5.88,0.,9.97),('South segmental sash head',13.15,0.,18.72),
           ('Stone arch',16.47,-.21,3.43),('Roof guard and cornice',8.57,-.24,26.49)]
    for name,x,y,z in local:
        targets.append((name,x*c+y*s,-x*s+y*c,z))
    rows=[]
    for name,width,height,pad in camera.VIEWS:
        viewport=dict(width=width,height=height,insets=dict(zip(['left','right','top','bottom'],pad)))
        rows.append(camera.evaluate(contract,viewport,name,neighbors,lon,lat,east,north,targets))
    if args.explore:
        options=[]
        for bearing in [15,20,25,30,35,40,45,50,55,60,65,70]:
            for pitch in [54,50,46,43,41,39,37,35]:
                contract.update(overviewBearing=bearing,overviewPitch=pitch)
                checks=[camera.evaluate(contract,dict(width=width,height=height,insets=dict(zip(['left','right','top','bottom'],pad))),name,neighbors,lon,lat,east,north,targets) for name,width,height,pad in camera.VIEWS]
                options.append({'bearing':bearing,'pitch':pitch,'clear':[v['clear_count']for v in checks]})
        print(json.dumps(options));return
    assert [r['clear_count']for r in rows]==[len(targets)]*2
    result=dict(source_sha256=camera.digest(buf),contract_sha256=camera.digest(args.contract.read_bytes()),
                shared_camera_checker_sha256=camera.digest(shared.read_bytes()),camera_module_sha256=camera.digest((PROJECT/'src/candidate-overview-camera.js').read_bytes()),
                measured_frozen_volumes=len(neighbors),views=rows,
                method_zh='核对手机与桌面从西南路口看四川中路320号门窗、弧角蓝檐、出挑檐带及九江路石拱门的视线。')
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
