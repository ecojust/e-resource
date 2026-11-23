"""Trace the independently read 600 × 401 garden photograph through the output mesh."""
import argparse,hashlib,json,sys
import numpy as np
from pathlib import Path
from render_court import HERE,PRECISE,projection
sys.path.insert(0,str(PRECISE/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene
from upper_sash import GREEN_GLASS,LIGHT_GLASS
from residence_materials import GLASS,GREEN,IVORY_RENDER,PEBBLEDASH,PLINTH,SHADE,SILL

# These are readings of the photograph, including small or partly screened elements.
MARKS={
 'aggregate, garden':(PEBBLEDASH,[(103,192),(143,164),(176,211),(236,181),(251,291),(252,339)]),
 'aggregate, street':(PEBBLEDASH,[(342,153),(351,191),(366,247),(377,289),(439,189),(491,124)]),
 'ivory corner':(IVORY_RENDER,[(302,151),(305,233),(311,298),(323,318)]),
 'ivory entrance piers':(IVORY_RENDER,[(104,273),(137,328),(65,296),(103,217)]),
 'plinth below aggregate':(PLINTH,[(250,368),(356,373)]),
 'glazing under air conditioning':(GLASS,[(208,300),(226,345)]),
 'street lower paired glazing':(GLASS,[(408,280),(445,319)]),
 'green shutter leaves':(GREEN,[(480,155),(507,185),(534,176)]),
 'garden upper pale casement glass':(LIGHT_GLASS,[(170,82),(183,99),(166,120)]),
 'return upper green glazing':(GREEN_GLASS,[(378,56),(392,83),(486,85)]),
 'recess behind arch':(SHADE,[(117,285),(119,273)]),
}
def check(mesh):
    scene=SerialScene(mesh);p=projection();inv=np.linalg.inv(p[:,:3]);eye=-inv@p[:,3]
    rows=[]
    for feature,(wanted,pixels) in MARKS.items():
        for x,y in pixels:
            hit=scene.ray(eye,inv@[x,y,1],80);actual=hit['material'] if hit else None
            rows.append(dict(feature=feature,pixel=[x,y],expected=wanted,observed=actual,matched=actual==wanted))
    return dict(source='Garden plate 190, 600×401. Measurements from image, photo excluded from delivery.',
                asset=mesh.name,sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),
                matched=sum(q['matched']for q in rows),count=len(rows),observations=rows)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();report=check(args.mesh)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(report['matched'],report['count'])
