"""Test the first material present at independent facade features and red roof sections in the exported mesh."""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
sys.path.insert(0,str(HERE.parents[1]/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene
from materials import ASHLAR,EAVE,GLASS,PALE,RIDGE,ROOF,TRIM
from photo_plane import INV,EYE

def check(path):
    scene=SerialScene(path)
    def material(x,y):
        direction=INV@[x,y,1]
        if direction[1]<0:direction=-direction
        h=scene.ray(EYE,direction,48)
        return h['material'] if h else None
    samples=[
        ('left broad upper sash',[315,190],[GLASS]),('second leaf in broad sash',[335,214],[GLASS]),
        ('upper narrow left sash',[384,179],[GLASS]),('lower pane of narrow sash',[386,191],[GLASS]),
        ('narrow sash stepped apron',[390,211],[PALE,TRIM]),('plaster immediately below apron',[390,216],[ASHLAR]),
        ('lower narrow window',[383,268],[GLASS]),('partially visible lower broad window',[320,295],[GLASS]),
        ('upper window of higher wing',[473,149],[GLASS]),('lower window of higher wing',[481,243],[GLASS]),
        ('ruled plaster on high wing',[588,153],[ASHLAR]),('higher right wall field',[586,160],[ASHLAR]),
        ('upper edge of right floor belt',[616,209],[PALE,TRIM]),('pendant frieze on right',[610,210],[PALE,TRIM]),
        ('lower right belt',[609,213],[PALE,TRIM]),('right eave soffit',[571,116],[EAVE])]
    readings=[]
    for label,pixel,expected in samples:
        mat=material(*pixel)
        readings.append({'feature':label,'pixel':pixel,'expected':expected,'first_material':mat,'passed':mat in expected})
    roof=json.loads((HERE/'visible-roof-pitch-fit.json').read_bytes())
    for name,row in roof.items():
        for x,top,bottom in zip(row['columns'],row['top'],row['bottom']):
            mid=(top+bottom)/2
            first=material(x,mid)
            readings.append({'feature':name+' roof tile','pixel':[x,mid],'photograph_red_interval':[top,bottom],
                             'first_material':first,'passed': first in [ROOF,RIDGE]})
    return {'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'passed':sum(r['passed'] for r in readings),'total':len(readings),'samples':readings}
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mesh',type=Path);parser.add_argument('output',type=Path);a=parser.parse_args()
    r=check(a.mesh);a.output.write_text(json.dumps(r,indent=2)+'\n');print(r['passed'],r['total'],[(p['feature'],p['pixel'],p['first_material'])for p in r['samples']if not p['passed']])
