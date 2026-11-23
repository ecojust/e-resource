"""Fixed upper-storey observations on the two February 2020 street frames."""
from pathlib import Path
import argparse,json,sys
import numpy as np
here=Path(__file__).resolve().parent
sys.path.insert(0,str(here.parents[1]/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
sys.path.insert(0,str(here.parent/'source'))
from glb_triangles import SerialScene
from materials import PLASTER,GLASS,FRAME,CEMENT,DARK,ROOF
survey=json.loads((here/'roof-room-two-stations.json').read_bytes())
street=json.loads((here/'street-facade-dimensions.json').read_bytes())
along=np.asarray(street['along_unit_vector']);arr=np.eye(3)
arr[:2,0]=along;arr[:2,1]=[-along[1],along[0]]
rows=[
 [('south side plaster',397,213,[PLASTER]),('south wall before corner',408,208,[PLASTER]),('left pane',441,225,[GLASS,FRAME]),('right pane',455,234,[GLASS,FRAME]),('middle pier',449,227,[PLASTER]),('north panel',468,242,[PLASTER]),('front coping edge',431,205,[DARK,ROOF,CEMENT]),('north of upper building',490,216,[])],
 [('left glass',279,159,[GLASS,FRAME]),('right glass',306,165,[GLASS,FRAME]),('between paired sashes',295,167,[PLASTER]),('higher south plaster',260,161,[PLASTER]),('north plaster',331,168,[PLASTER]),('front cornice',318,148,[DARK,ROOF,CEMENT]),('above flat coping',325,137,[])]]
def run(mesh):
    scene=SerialScene(mesh);result=[]
    for cam,targets in zip(survey['projections'],rows):
        P=np.asarray(cam['P']);inv=np.linalg.inv(P[:,:3]);eye=arr@(-inv@P[:,3])
        for name,x,y,accepted in targets:
            hit=scene.ray(eye,arr@inv@[x,y,1],120.)
            result.append(dict(station=cam['station'],subject=name,pixel=[x,y],expected=accepted,first=hit,match=bool(hit and hit['material']in accepted) if accepted else hit is None))
    return dict(asset=scene.asset,passed_samples=sum(r['match']for r in result),total=len(result),rows=result)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mesh',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();j=run(a.mesh);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n');print(j['passed_samples'],j['total'],[(r['subject'],r['first']['material']if r['first']else None)for r in j['rows'] if not r['match']])
