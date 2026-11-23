"""Trace the photographed frame, roughcast, coping and cast-iron leader on both upper winter gardens."""
import argparse
import hashlib
import json
import runpy
import sys
from math import hypot
from pathlib import Path

from register_garden import Camera

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from central_front import PLASTER,COPING,PIPE,FRAME
GLASS='Winter gardens | cool reflected glazing'
HINGE='Winter gardens | slightly brighter casement metal'

# Working image coordinates. Source 04 is reduced to 1080x711 and 06 is the 934x700 original.
CHECKS={
    4:[
        ('near reflective left light',586,242,GLASS,4),('near second reflective light',668,230,GLASS,4),
        ('near third reflective light',768,237,GLASS,4),('near fourth shaded glass',849,239,GLASS,4),
        ('roughcast first mullion pier',633,233,PLASTER,5),('roughcast middle pier',731,226,PLASTER,4),
        ('roughcast far pier',824,235,PLASTER,4),('first bay apron',583,312,PLASTER,5),
        ('front bay apron',750,318,PLASTER,5),('far apron',870,322,PLASTER,5),
        ('upper curved plaster parapet',703,97,PLASTER,5),('crown of parapet',800,90,PLASTER,5),
        ('projecting eave concrete',684,135,COPING,5),('projecting lower slab',754,353,COPING,5),
        ('near leader at left jamb',560,231,PIPE,7),('distant right light',136,306,GLASS,5),
        ('distant middle light',64,305,GLASS,6),('distant pier at last window',96,306,PLASTER,7),
        ('distant roof parapet',72,233,PLASTER,5)],
    6:[
        ('near first glass',174,208,GLASS,4),('second closed right light',327,208,GLASS,4),
        ('outward hinged left glass',279,216,GLASS,5),('free edge of open leaf',290,205,HINGE,7),
        ('near third glass',400,214,GLASS,4),('jamb between first two windows',246,216,PLASTER,4),
        ('broad third jamb',365,211,PLASTER,4),('outer pier on curve',445,231,PLASTER,5),
        ('broad lower west apron',208,333,PLASTER,4),('broad east apron',368,341,PLASTER,4),
        ('roof parapet west',168,66,PLASTER,4),('roof parapet centre',292,61,PLASTER,4),
        ('near eave soffit',283,117,COPING,6),('distant westernmost return glass',746,349,GLASS,8),
        ('distant middle glass',800,354,GLASS,8),('distant apron',815,407,PLASTER,7)]}

def inspect(path):
    api=runpy.run_path(str(HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))
    scene=api['SerialScene'](path)
    measured=[]
    for view,checks in CHECKS.items():
        camera=Camera(view)
        for detail,x,y,material,radius in checks:
            first=None
            closest=None
            for length,dx,dy in sorted((hypot(i,j), i,j) for i in range(-radius,radius+1)
                                        for j in range(-radius,radius+1) if hypot(i,j)<=radius):
                hit=scene.ray(camera.c,camera.ray((x+dx,y+dy)),80)
                if length==0:
                    first=hit
                if hit and hit['material']==material:
                    closest={'offset_px':[dx,dy],'distance_px':length,'hit':hit}
                    break
            measured.append(dict(photo=view,detail=detail,source_pixel=[x,y],expected=material,
                                 tolerance_px=radius,first=first,nearest=closest))
    return dict(asset_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),samples=measured,
                exact=sum(bool(q['first']) and q['first']['material']==q['expected'] for q in measured),
                within=sum(q['nearest'] is not None for q in measured),total=len(measured))

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('mesh',type=Path);cli.add_argument('result',type=Path)
    args=cli.parse_args();result=inspect(args.mesh)
    args.result.parent.mkdir(parents=True,exist_ok=True);args.result.write_text(json.dumps(result,indent=2)+'\n')
    print(result['exact'],result['within'],result['total'])
