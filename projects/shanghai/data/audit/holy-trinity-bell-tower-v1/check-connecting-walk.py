"""Check the physical joint of the two independent Holy Trinity models after GLB decoding."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json
import runpy
import subprocess
from tempfile import TemporaryDirectory
import numpy as np
from shapely.geometry import shape, Point

AUDIT=Path(__file__).resolve().parent
PROJECT=AUDIT.parents[2]
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
SerialScene=runpy.run_path(str(READER))['SerialScene']
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'


def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def run(out):
    names=['cathedral','bell-tower']
    contracts={}
    manifests={}
    for name in names:
        path=PROJECT/'assets/models/candidates'/('huangpu-holy-trinity-'+name)/'manifest.json'
        manifests[name]=(path,json.loads(path.read_bytes()))
        file=PROJECT/'data/audit'/('holy-trinity-'+name+'-v1')/'final-placement-contract.json'
        contracts[name]=json.loads(file.read_bytes())
    assert all(x['scale']==1 and x['altitude']==0 for x in contracts.values())
    first,last=(contracts[n] for n in names)
    assert abs(first['heading']-last['heading'])<1e-8
    earth=6371008.8
    east=(np.radians(last['lng']-first['lng'])*earth*np.cos(np.radians(first['lat'])))
    north=(np.arcsinh(np.tan(np.radians(last['lat'])))-np.arcsinh(np.tan(np.radians(first['lat']))))*earth*np.cos(np.radians(first['lat']))
    h=np.radians(first['heading'])
    dx=east*np.cos(h)-north*np.sin(h)
    dy=east*np.sin(h)+north*np.cos(h)
    assert np.hypot(dx-24,dy-9.6)<.001
    def geographic(x,y):
        k=earth*np.cos(np.radians(first['lat']))
        nx=x*np.cos(h)+y*np.sin(h)
        ny=-x*np.sin(h)+y*np.cos(h)
        return Point(first['lng']+np.degrees(nx/k),np.degrees(np.arctan(np.sinh(np.arcsinh(np.tan(np.radians(first['lat'])))+ny/k))))
    obstructions=[shape(x['collision_geometry']) for x in contracts.values()]
    y=8.65
    stations=[10.85,11.70,12.10,12.30,13.10,14.35,16.70,18.75,20.50]
    results={}
    with TemporaryDirectory() as directory:
        for role in ['raw','full','lod']:
            scenes={}
            for name in names:
                path,m=manifests[name]
                receipt=m['assets'][role];file=path.parent/receipt['file']
                assert digest(file)==receipt['sha256'] and file.stat().st_size==receipt['bytes']
                if role!='raw':
                    raw=Path(directory)/(name+'-'+role+'.glb')
                    subprocess.run(['node',UNPACK,file,raw,DECODER],check=True,stdout=subprocess.DEVNULL)
                    file=raw
                scenes[name]=SerialScene(file)
            samples=[]
            for x in stations:
                sample={'church_x_m':x}
                hits=[scenes[n].ray([x-offset_x,y-offset_y,1.66],[0,0,-1],2.5)
                      for n,offset_x,offset_y in [(names[0],0,0),(names[1],dx,dy)]]
                hits=[k for k in hits if k]
                assert len(hits)==1 and hits[0]['material']=='porch pavement',(x,hits)
                elevation=1.66-hits[0]['distance_m']
                assert abs(elevation-(.105 if x<12.18 else .082))<.002
                assert not any(p.covers(geographic(x,y)) for p in obstructions)
                samples.append(dict(**sample,paving_z_m=elevation,collision=False))
            start=10.78
            assert scenes[names[0]].ray([start,y,1.7],[1,0,0],12) is None
            door=scenes[names[1]].ray([start-dx,y-dy,1.7],[1,0,0],12)
            assert door and door['material']=='oak door' and abs(door['distance_m']-10.45)<.004
            results[role]=dict(samples=samples,from_church_walk_to_tower_door=door)
    report=dict(id='holy-trinity-connecting-walk',model_manifest_sha256={n:digest(path)for n,(path,_)in manifests.items()},
        projected_offset_from_church_m=[dx,dy],tested_walk_y_m=y,point_count_per_model_role=len(stations),
        scope='把两套已交付的独立GLB按实际经纬原点重合。主堂北廊至塔门中线两侧都有柱列，九个铺地点均可通行，廊际铺地落差约2.3厘米。',role_checks=results,
        checker_sha256=digest(Path(__file__)),reader_sha256=digest(READER),decoder_sha256=digest(DECODER),passed=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    ap=ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,default=AUDIT/'connecting-walk.json')
    run(ap.parse_args().out)
