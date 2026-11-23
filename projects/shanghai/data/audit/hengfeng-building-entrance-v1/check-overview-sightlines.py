"""Check the photographed street elevation on both public screen sizes with every original building retained."""
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
    for name,x,y,z in [('left title character', -1.44, -0.457, 5.48), ('right title character', 0.859444, -0.457, 5.42), ('right lower shaft', 2.38, -1.211, 2.35), ('left lower shaft', -2.38, -1.211, 2.35), ('lower order impost', 2.38, -1.3, 5.32), ('lower order volute', -2.025, -1.27, 5.1), ('curved hood at crown', 0.0, -1.32, 8.555), ('cartouche', 0.0, -1.054, 7.3), ('upper west glass', -1.47, 0.32, 11.20), ('upper opposite glass', 1.47, 0.32, 11.20), ('tall shaft', -3.05, -0.625, 9.91), ('tall round capital', 3.05, -0.76, 12.72)]:
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
                method_zh='按桌面和手机相机分别检查恒丰大楼题名、下排门柱及柱头、弧形门罩、中央心形和楼窗；使用已签入的原楼及对街保留楼体进行遮挡测试。')
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    assert [r['clear_count']for r in rows]==[len(targets)]*len(rows)

if __name__=='__main__':main()
