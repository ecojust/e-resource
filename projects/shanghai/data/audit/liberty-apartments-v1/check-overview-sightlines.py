"""Test the estimated straight-on view against all nearby frozen source footprints and heights."""
from argparse import ArgumentParser
from hashlib import sha256
import gzip
import json
import math
import subprocess
from pathlib import Path

import numpy as np
import shapely as geo
from shapely.geometry import LineString, Point, shape

AUDIT=Path(__file__).resolve().parent
ID='xuhui-liberty-apartments-south-front'


def main():
    ap=ArgumentParser(description=__doc__)
    ap.add_argument('--table',type=Path,required=True)
    ap.add_argument('--contract',type=Path,default=AUDIT/'final-placement-contract.json')
    ap.add_argument('--out',type=Path,default=AUDIT/'overview-sightlines.json')
    args=ap.parse_args()
    review=json.loads((AUDIT.parents[2]/'source/precise'/ID/'footprint-review.json').read_bytes())
    contract=json.loads(args.contract.read_bytes())
    data=args.table.read_bytes()
    receipt=next(r for r in review['frozen_bindings'] if r['repository_path'].endswith('/feature-table.json.gz'))
    assert sha256(data).hexdigest()==receipt['sha256']
    center=np.array([contract['lng'],contract['lat']])
    project_scale=np.array([math.cos(math.radians(center[1])),1])*6371008.8*math.pi/180
    theta=math.radians(contract['heading'])
    axes=np.array([[math.cos(theta),-math.sin(theta)],[math.sin(theta),math.cos(theta)]])
    rows=[]
    for r in json.loads(gzip.decompress(data))['features']:
        poly=shape(r['geometry'])
        if poly.distance(Point(*center))<.0016:
            if r['localId']==3297:poly=poly.difference(shape(contract['replacement_geometry']))
            rows.append((r,geo.transform(poly,lambda xy:(xy-center)*project_scale)))
    # The retained original building is included along with all other sources.
    aim=[('recessed entry',0,1.53,1.7),('three cement fins',0,-.19,19),('center parapet projecting ribs',0,-.19,29.45),
         ('window of center',-3,.08,18.65),('west stair-step roof',-7.45,4.58,25.04),('east stair-step roof',7.19,4.27,25.04)]
    module=AUDIT.parents[2]/'src/candidate-overview-camera.js'
    program="""const fs=await import('node:fs');const {candidateOverviewCamera}=await import(process.argv[1]);
const c=JSON.parse(fs.readFileSync(0));const viewports=[
{width:900,height:650,insets:{left:304,right:68,top:154,bottom:164}},
{width:390,height:844,insets:{left:16,right:68,top:183,bottom:182}}];
process.stdout.write(JSON.stringify(viewports.map(v=>({...v,camera:candidateOverviewCamera({...c,city_integration:true},v)}))));"""
    fitted=json.loads(subprocess.check_output(['node','--input-type=module','-e',program,module.as_uri()],input=json.dumps(contract).encode()))
    views=[]
    for test in fitted:
        camera=test['camera'];viewport=test['height'];zoom=camera['zoom']
        pitch=math.radians(camera['pitch']);bearing=math.radians(camera['bearing'])
        direction=-np.array([math.sin(bearing),math.cos(bearing)])
        focal=viewport/(2*math.tan(math.radians(36.87)/2))
        distance=focal*360*project_scale[0]/(512*2**zoom)
        eye=(np.array(camera['center'])-center)*project_scale+direction*distance*math.sin(pitch)
        height=camera['elevation']+distance*math.cos(pitch)
        samples=[]
        for name,x,y,z in aim:
            start=np.array([x,y])@axes;ray=LineString([start,eye])
            obstacles=[]
            for r,poly in rows:
                overlap=ray.intersection(poly)
                if overlap.is_empty:continue
                clearance=z+(height-z)*overlap.distance(Point(start))/ray.length-r['height']
                if clearance<0:obstacles.append(dict(id=r['localId'],above_ray_m=round(-clearance,4)))
            assert not obstacles,(viewport,name,obstacles)
            samples.append(dict(feature=name,author_x_y_z_m=[x,y,z],obstacles=obstacles))
        views.append(dict(viewport=test,source_count=len(rows),eye_east_north_m=eye.tolist(),eye_height_m=height,samples=samples))
    doc=dict(id=ID,contract_sha256=sha256(args.contract.read_bytes()).hexdigest(),source_table_sha256=receipt['sha256'],
        camera_helper_sha256=sha256(module.read_bytes()).hexdigest(),
        note='The release overview helper fits the delivered geometry at two named viewport and panel sizes. Straight rays use original source heights. Labels, road structures and furnishings require inspection in the live map.',
        pitch_deg=contract['overviewPitch'],bearing_deg=contract['overviewBearing'],views=views)
    args.out.write_text(json.dumps(doc,indent=2)+'\n')


if __name__=='__main__':main()
