"""Verify at least one raised surface for every glyph and the punched counters in 言 and 思."""
from pathlib import Path
import json,sys,argparse
from shapely.geometry import Polygon
S=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(S/'source'))
sys.path.insert(0,str(S.parent/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene
from garden_letters import letter_shapes
from materials import DARK,RENDER

def run(mesh):
    scene=SerialScene(mesh);probes=[]
    for label,c,shape in letter_shapes():
        polys=list(getattr(shape,'geoms',[shape]))
        for i,p in enumerate(polys):
            if p.area < .00004:
                continue
            checks=[('stroke',p.representative_point(),DARK)]
            for ring in p.interiors:
                checks.append(('counter',Polygon(ring).representative_point(),RENDER))
            for kind,point,accepted in checks:
                hit=scene.ray((point.x,-.25,point.y),(0,1,0),.45)
                passed=bool(hit and hit['material']==accepted)
                probes.append(dict(letter=c,label=label,component=i+1,kind=kind,expected=accepted,
                                   xz=[point.x,point.y],hit=hit,passed=passed))
    return dict(asset=scene.asset,passed=sum(p['passed'] for p in probes),total=len(probes),rows=probes)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args(); j=run(args.mesh)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
    print(f"{j['passed']}/{j['total']}")
