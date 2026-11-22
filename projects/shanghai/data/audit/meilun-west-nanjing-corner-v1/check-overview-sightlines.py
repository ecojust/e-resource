"""Test the two Meilun street fronts and stone pediments against neighboring roofs."""
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
    corners=json.loads((source.parent/'corner-study.json').read_bytes())['corner']
    n,w=corners['nanjing_end'],corners['west_end']
    edges=[([n[0]+12.8,n[1]],n,2,.74,'Nanjing'),(n,w,1,.86,'diagonal'),
           (w,corners['west_study_end'],1,.67,'Jiangxi')]
    local=[]
    for a,b,count,depth,street in edges:
        length=math.dist(a,b);tx,ty=(b[0]-a[0])/length,(b[1]-a[1])/length
        nx,ny=ty,-tx
        for i in range(count):
            u=(i+.5)/count
            x,y=a[0]+(b[0]-a[0])*u,a[1]+(b[1]-a[1])*u
            for name,d,z in [('shopfront',-depth-.26,2.44),('upper windows',-.12,10.14)]:
                local.append((f'{street} {i+1} {name}',x+nx*d,y+ny*d,z))
            if street=='diagonal':
                for name,z in [('lower stone pediment',8.51),('upper stone pediment',13.92)]:
                    local.append((name,x+nx*.27,y+ny*.27,z))
            elif street=='Jiangxi':
                local.append(('street parapet rail',x+nx*.09,y+ny*.09,13.72))
    for name,x,y,z in local:
        targets.append((name,x*c+y*s,-x*s+y*c,z))
    rows=[]
    for name,width,height,pad in camera.VIEWS:
        viewport=dict(width=width,height=height,insets=dict(zip(['left','right','top','bottom'],pad)))
        rows.append(camera.evaluate(contract,viewport,name,neighbors,lon,lat,east,north,targets))
    if args.explore:
        options=[]
        for bearing in [108,117,126,135,144,153,162,171,180]:
            for pitch in [44,38,33,27,21]:
                contract.update(overviewBearing=bearing,overviewPitch=pitch)
                checks=[camera.evaluate(contract,dict(width=width,height=height,insets=dict(zip(['left','right','top','bottom'],pad))),name,neighbors,lon,lat,east,north,targets) for name,width,height,pad in camera.VIEWS]
                options.append({'bearing':bearing,'pitch':pitch,'clear':[v['clear_count']for v in checks]})
        print(json.dumps(options));return
    assert [r['clear_count']for r in rows]==[len(targets)]*2
    result=dict(source_sha256=camera.digest(buf),contract_sha256=camera.digest(args.contract.read_bytes()),
                shared_camera_checker_sha256=camera.digest(shared.read_bytes()),camera_module_sha256=camera.digest((PROJECT/'src/candidate-overview-camera.js').read_bytes()),
                measured_frozen_volumes=len(neighbors),views=rows,
                method_zh='以手机和桌面普通地图目录的相机复算三面店铺、两层石窗和山花到相邻街区体量的视线。')
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
