"""Project courtyard features through the shipped overview camera and retained frozen city volumes."""
from argparse import ArgumentParser
import gzip
import hashlib
import json
import math
from pathlib import Path
import subprocess

from shapely.affinity import scale, translate
from shapely.geometry import LineString, Point, shape

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
REPO = PROJECT.parents[1]
EARTH = 6371008.8
TESTS = [
    ('central portal', 2.90, 2.90, .90), ('inscribed balcony', 2.95, 2.95, 3.54),
    ('north stair foot', 1.40, 9.05, .60), ('east stair foot', 9.05, 1.40, .60),
    ('north broad window', 0, 8.03, 4.70), ('east broad window', 9.21, 0, 4.70),
    ('north narrow window', 0, 2.61, 4.60), ('east narrow window', 4.59, 0, 4.80)
]
VIEWS = [('desktop', 900, 650, [316, 88, 154, 241]), ('mobile', 390, 844, [16, 65, 182, 228])]
CAMERA_JS = """
import fs from 'node:fs';
import {pathToFileURL} from 'node:url';
const {candidateOverviewCamera}=await import(pathToFileURL(process.argv[1]).href);
const {place,viewport}=JSON.parse(fs.readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify(candidateOverviewCamera(place,viewport)));
"""


def digest(value):
    return hashlib.sha256(value).hexdigest()


def evaluate(place, viewport, label, neighbors, lon, lat, meter_e, meter_n, targets=TESTS):
    module = PROJECT/'src/candidate-overview-camera.js'
    args = json.dumps(dict(place={**place, 'city_integration': True},viewport=viewport))
    camera = json.loads(subprocess.check_output(['node','--input-type=module','-e',CAMERA_JS,module],
                                               input=args.encode()))
    bearing, pitch = map(math.radians, (camera['bearing'],camera['pitch']))
    width, height = viewport['width'],viewport['height']
    focal = height / (2*math.tan(math.radians(36.87)/2))
    distance = focal * (2*math.pi*EARTH*math.cos(math.radians(camera['center'][1]))) / (512*2**camera['zoom'])
    center_e,center_n = (camera['center'][0]-lon)*meter_e,(camera['center'][1]-lat)*meter_n
    eye_e = center_e-math.sin(bearing)*distance*math.sin(pitch)
    eye_n = center_n-math.cos(bearing)*distance*math.sin(pitch)
    eye_up = camera['elevation']+distance*math.cos(pitch)
    pad=camera['padding']
    probes=[]
    for name,e,n,up in targets:
        target=Point(e,n)
        ray=LineString([(e,n),(eye_e,eye_n)])
        blocked=[]
        for owner, volume, roof in neighbors:
            segment=ray.intersection(volume)
            if segment.is_empty:continue
            sample_z=up+(eye_up-up)*target.distance(segment)/ray.length
            if sample_z<roof-.05:blocked.append(dict(owner=owner,shortfall_m=round(roof-sample_z,3)))
        de,dn,du=e-center_e,n-center_n,up-camera['elevation']
        forward=de*math.sin(bearing)+dn*math.cos(bearing)
        depth=distance+forward*math.sin(pitch)-du*math.cos(pitch)
        x=(width+pad['left']-pad['right'])/2+(de*math.cos(bearing)-dn*math.sin(bearing))*focal/depth
        y=(height+pad['top']-pad['bottom'])/2-(forward*math.cos(pitch)+du*math.sin(pitch))*focal/depth
        inside=pad['left']+3<=x<=width-pad['right']-3 and pad['top']+3<=y<=height-pad['bottom']-3
        probes.append(dict(feature=name,target_enu=[e,n,up],screen_px=[round(x,2),round(y,2)],
                           within_visible_map=inside,obstructions=blocked,clear=inside and not blocked))
    return dict(view=label,viewport=viewport,camera=camera,camera_enu=[eye_e,eye_n,eye_up],probes=probes,
                clear_count=sum(p['clear']for p in probes))


def main():
    cli=ArgumentParser(description=__doc__)
    cli.add_argument('--contract',type=Path,default=HERE/'final-placement-contract.json')
    cli.add_argument('--out',type=Path,default=HERE/'overview-sightlines.json')
    args=cli.parse_args()
    contract=json.loads(args.contract.read_bytes())
    review=json.loads((PROJECT/'source/precise'/contract['id']/'footprint-review.json').read_bytes())
    bound=next(b for b in review['frozen_bindings']if b['repository_path'].endswith('feature-table.json.gz'))
    data=subprocess.check_output(['git','-C',REPO,'show',review['baseline_commit']+':'+bound['repository_path']])
    assert digest(data)==bound['sha256']
    lon,lat=contract['lng'],contract['lat']
    meter_n=math.radians(1)*EARTH
    meter_e=meter_n*math.cos(math.radians(lat))
    def meters(geom):
        return scale(translate(geom,xoff=-lon,yoff=-lat),xfact=meter_e,yfact=meter_n,origin=(0,0))
    mask=meters(shape(contract['replacement_geometry']))
    neighbors=[]
    for f in json.loads(gzip.decompress(data))['features']:
        if not f.get('geometry'):continue
        poly=meters(shape(f['geometry']))
        if poly.distance(Point(0,0))>150:continue
        if f['localId']==contract['owner']['feature_local_id']:poly=poly.difference(mask)
        neighbors.append((f['localId'],poly,f['height']))
    cases={}
    for name,bearing,pitch in [('default',contract['overviewBearing'],contract['overviewPitch']),
                               ('steeper_roof_alternative',260,12)]:
        rows=[]
        for label,w,h,pads in VIEWS:
            viewport=dict(width=w,height=h,insets=dict(zip(['left','right','top','bottom'],pads)))
            rows.append(evaluate({**contract,'overviewBearing':bearing,'overviewPitch':pitch},viewport,
                                 label,neighbors,lon,lat,meter_e,meter_n))
        cases[name]=rows
    assert all(row['clear_count']>=6 and all(p['clear']for p in row['probes'][:2])for row in cases['default'])
    assert all(row['clear_count']==8 for row in cases['steeper_roof_alternative'])
    out=dict(contract_sha256=digest(args.contract.read_bytes()),camera_module_sha256=digest((PROJECT/'src/candidate-overview-camera.js').read_bytes()),
             source_sha256=digest(data),considered_volumes=len(neighbors),cases=cases,
             interpretation_zh='推算采用原城市单栋边界和原高度，中央门洞与刻字额在两个视口都通过；保留的东侧高楼2010会遮住东翼外端。较接近俯视的备选角度能看见全部八点，但压缩竖向窗与门洞。')
    args.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
