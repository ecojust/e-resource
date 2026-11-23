"""Trace independent photo-03 marks through the delivered triangles at native resolution."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import numpy as np
from register_court import Camera
HERE=Path(__file__).absolute().parent
HELPER='data/audit/postal-office-v1/independent-glb-review-helpers.py'
PROJECT=next(p for p in HERE.parents if (p/HELPER).is_file())
ITEMS=[
 ('left foliage',[242,593],['dark green foliage','upper foliage']),
 ('right foliage',[549,590],['dark green foliage','upper foliage']),
 ('left flared planter',[239,620],['patinated planter']),
 ('right flared planter',[552,620],['patinated planter']),
 ('left planter foot',[235,657],['patinated planter']),
 ('right planter foot',[553,657],['patinated planter']),
 ('warm pendant',[399,493],['warm entrance glass']),
 ('amber shape in panel',[400,511],['amber on framed panel']),
 ('ceiling fitting below bowed balcony',[395,349],['bronze door leading']),
 ('circular landing inlay, west perimeter',[354,668],['entry mosaic']),
 ('circular landing inlay, east perimeter',[433,667],['entry mosaic']),
 ('dark band inside top step',[390,696],['entry mosaic','pale inlay chips']),
 ('entrance opening below pendant',[394,575],['shaded recess'])]
def trace(path):
    scene=runpy.run_path(str(PROJECT/HELPER))['SerialScene'](path)
    cam=Camera('03');rows=[]
    offsets=sorted((round(np.hypot(x,y),5),x,y) for x in range(-3,4) for y in range(-3,4) if np.hypot(x,y)<=3)
    for label,uv,expected in ITEMS:
        success=None
        for radius,dx,dy in offsets:
            h=scene.ray(cam.c,cam.ray([uv[0]+dx,uv[1]+dy]),25.)
            if radius==0:first=h
            if h and h['material'].removeprefix('Fudefang | ') in expected:
                success={'offset':[dx,dy],'distance_px':radius,'hit':h};break
        rows.append(dict(label=label,photo_pixel=uv,expected_materials=expected,first_hit=first,matching_hit=success))
    return dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),view='03',size=cam.size,
                direct=sum(bool(r['matching_hit'] and not r['matching_hit']['distance_px']) for r in rows),
                within_three_pixels=sum(bool(r['matching_hit']) for r in rows),total=len(rows),rays=rows)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('glb',type=Path);parser.add_argument('out',type=Path)
    a=parser.parse_args();data=trace(a.glb);a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(data,indent=2)+'\n');print(data['file'],data['direct'],data['within_three_pixels'],data['total'])
