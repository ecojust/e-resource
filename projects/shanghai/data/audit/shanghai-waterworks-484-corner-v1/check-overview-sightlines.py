"""Check the photographed street corner on both public screen sizes with every original building retained."""
from argparse import ArgumentParser
from pathlib import Path
import gzip
import importlib.util
import json
import math
import os
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
    args=cli.parse_args()
    contract=json.loads(args.contract.read_bytes())
    source=PROJECT/'source/precise'/contract['id']/'footprint-review.json'
    review=json.loads(source.read_bytes())
    binding=next(b for b in review['frozen_bindings']if b['repository_path'].endswith('feature-table.json.gz'))
    captured=os.environ.get('QA_FROZEN_FEATURE_TABLE')
    buf=Path(captured).read_bytes() if captured else subprocess.check_output(['git','-C',PROJECT.parents[1],'show',review['baseline_commit']+':'+binding['repository_path']])
    assert camera.digest(buf)==binding['sha256']
    lon,lat=contract['lng'],contract['lat']
    north=math.radians(1)*camera.EARTH;east=north*math.cos(math.radians(lat))
    def meters(g):
        return scale(translate(g,xoff=-lon,yoff=-lat),xfact=east,yfact=north,origin=(0,0))
    neighbors=[];assert contract['replacement_geometry'] is None
    for f in json.loads(gzip.decompress(buf))['features']:
        if not f.get('geometry'):continue
        poly=meters(shape(f['geometry']))
        if poly.distance(Point(0,0))>180:continue
        neighbors.append((f['localId'],poly,f['height']))
    h=math.radians(contract['heading']);c,s=math.cos(h),math.sin(h)
    targets=[]
    for name,x,y,z in [('left corner ruled pier', -2.2, -0.42, 6.22), ('panel raised right frame', 1.37, -0.55, 2.3), ('blank inset field', 0.38, -0.458, 2.79), ('hollow centre of garland', 0, -0.42, 5.92), ('stone crown flower', 0, -0.687, 6.94), ('right horn binding', 1.1, -0.63, 6.02), ('lower stone knot', 0, -0.63, 4.89), ('rectangular window glass', 0.26, -0.145, 8.79), ('projecting upper flashing', -1.28, -0.77, 11.25), ('red hipped roof', 0.47, -0.26, 11.87)]:
        targets.append((name,x*c+y*s,-x*s+y*c,z+contract['altitude']))
    rows=[]
    for name,width,height,pad in camera.VIEWS:
        viewport=dict(width=width,height=height,insets=dict(zip(['left','right','top','bottom'],pad)))
        rows.append(camera.evaluate(contract,viewport,name,neighbors,lon,lat,east,north,targets))
    if args.explore:
        options=[]
        for bearing in [336,344,352,0,8,16,20,24,32,40,48,56,64,72,80]:
            for pitch in [67,62,58,52,47,43,38,33]:
                contract.update(overviewBearing=bearing,overviewPitch=pitch)
                checks=[camera.evaluate(contract,dict(width=width,height=height,insets=dict(zip(['left','right','top','bottom'],pad))),name,neighbors,lon,lat,east,north,targets) for name,width,height,pad in camera.VIEWS]
                options.append({'bearing':bearing,'pitch':pitch,'clear':[v['clear_count']for v in checks]})
        print(json.dumps(options));return
    result=dict(source_sha256=camera.digest(buf),contract_sha256=camera.digest(args.contract.read_bytes()),
                shared_camera_checker_sha256=camera.digest(shared.read_bytes()),camera_module_sha256=camera.digest((PROJECT/'src/candidate-overview-camera.js').read_bytes()),
                measured_frozen_volumes=len(neighbors),views=rows,
                method_zh='按桌面和手机相机逐项检查斜角花环、窗洞、素面板、深色檐边和红瓦坡面。原楼与邻楼均按签入体量参与视线判断。')
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    assert [r['clear_count']for r in rows]==[10,10]

if __name__=='__main__':main()
