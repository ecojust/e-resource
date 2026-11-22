"""Test the two Hengye street elevations and the rounded corner against surrounding roofs."""
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
    import sys
    sys.path.insert(0,str(source.parent/'source'))
    from brickwork import CENTER,RADIUS,TURN,EAST_AXIS,EAST_TANGENT,SOUTH_LENGTH,EAST_LENGTH
    local=[]
    for name,begin,t,span in [('Sijing',(CENTER[0]-SOUTH_LENGTH,0.),(1.,0.),SOUTH_LENGTH),('Jiangxi',EAST_TANGENT,EAST_AXIS,EAST_LENGTH)]:
        normal=(t[1],-t[0])
        for axis,z,label in [(.5*span/3,.0,'lower'),(1.5*span/3,6.1,'middle sash'),(2.5*span/3,9.42,'upper sash')]:
            z=z or (1.62 if name=='Sijing' else 1.64)
            if name=='Jiangxi' and label=='lower':axis=1.56
            local.append((name+' '+label,begin[0]+t[0]*axis-normal[0]*.18,begin[1]+t[1]*axis-normal[1]*.18,z))
        local.append((name+' street eave',begin[0]+t[0]*span*.68+normal[0]*.2,begin[1]+t[1]*span*.68+normal[1]*.2,11.4))
    for z,label in [(1.65,'blind round corner'),(4.42,'round brick belt'),(8.13,'round upper belt'),(11.4,'continuous eave')]:
        q=TURN*.5
        local.append((label,CENTER[0]+RADIUS*math.sin(q),CENTER[1]-RADIUS*math.cos(q),z))
    for name,x,y,z in local:
        targets.append((name,x*c+y*s,-x*s+y*c,z))
    rows=[]
    for name,width,height,pad in camera.VIEWS:
        viewport=dict(width=width,height=height,insets=dict(zip(['left','right','top','bottom'],pad)))
        rows.append(camera.evaluate(contract,viewport,name,neighbors,lon,lat,east,north,targets))
    if args.explore:
        options=[]
        for bearing in [-96,-84,-72,-60,-58,-48,-36,-24,-12,0]:
            for pitch in [44,38,33,27,21]:
                contract.update(overviewBearing=bearing,overviewPitch=pitch)
                checks=[camera.evaluate(contract,dict(width=width,height=height,insets=dict(zip(['left','right','top','bottom'],pad))),name,neighbors,lon,lat,east,north,targets) for name,width,height,pad in camera.VIEWS]
                options.append({'bearing':bearing,'pitch':pitch,'clear':[v['clear_count']for v in checks]})
        print(json.dumps(options));return
    assert [r['clear_count']for r in rows]==[len(targets)]*2
    result=dict(source_sha256=camera.digest(buf),contract_sha256=camera.digest(args.contract.read_bytes()),
                shared_camera_checker_sha256=camera.digest(shared.read_bytes()),camera_module_sha256=camera.digest((PROJECT/'src/candidate-overview-camera.js').read_bytes()),
                measured_frozen_volumes=len(neighbors),views=rows,
                method_zh='以手机和桌面地图普通目录机位复算两街窗组、圆角砖面、腰线和檐口到周围原房体量的视线。')
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
