"""Compare retained source-photograph pixels with first surfaces of the reopened frontage GLB."""
import argparse,json,sys
from pathlib import Path
import numpy as np

here=Path(__file__).resolve().parent
sys.path.insert(0,str(here.parent/'source'))
project=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(project/'source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene
from wing_openings import GLASS,STEEL,SILL,VENT,ROD,CANVAS,DARK,CLAY
from wing_finishes import ROUGHCAST

picks={
    'left fan and cast sash':{
        GLASS:[[197,252],[217,251],[234,273],[254,265],[282,303],[238,223],[258,226]],
        STEEL:[[243,264],[208,294],[259,280]],SILL:[[237,318]],CANVAS:[[225,200]]},
    'left diamond and slots':{
        VENT:[[241,365],[247,365]],DARK:[[265,136],[251,145],[277,146],[264,154]],
        ROUGHCAST:[[228,354],[283,375],[236,144]]},
    'left connecting windows and roughcast':{
        GLASS:[[449,228],[471,258],[510,251],[450,413],[463,618]],
        SILL:[[478,273]],ROUGHCAST:[[384,198],[414,350],[363,398]]},
    'left middle hood':{CANVAS:[[195,430],[222,437],[281,447]],GLASS:[[221,473],[277,483]]},
    'right upper opening':{GLASS:[[1072,285],[1096,289],[1121,316]],
        SILL:[[1104,334]],ROUGHCAST:[[1158,349],[1092,370]]},
    'right airbrick and awning':{
        VENT:[[1104,370],[1123,535],[1144,537]],CANVAS:[[1084,416],[1139,419]],
        GLASS:[[1105,449],[1144,478]],ROUGHCAST:[[1047,379],[1153,505]]},
}
def check(mesh,camera,scale):
    scene=SerialScene(mesh);K=np.asarray(camera['intrinsic']);R=np.asarray(camera['world_to_camera'])
    centre=np.asarray(camera['camera_centre'])*scale
    I=R.T@np.linalg.inv(K);ratio=np.array(camera['working_size'])/[1450,816];rows=[]
    for label,groups in picks.items():
        for name,points in groups.items():
            for p in points:
                working=(np.asarray(p)+.5)*ratio-.5
                hit=scene.ray(centre,I@[*working,1.],150)
                actual=hit['material'] if hit else None
                rows.append(dict(set=label,photo_mark=p,expected=name,actual=actual,match=actual==name))
    return dict(asset=scene.asset,photo_working_size=[1450,816],mesh_metres_per_authored_unit=scale,
                sample_count=len(rows),matched=sum(row['match'] for row in rows),rows=rows)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh',type=Path);parser.add_argument('camera',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--scale',type=float,default=1.)
    a=parser.parse_args();r=check(a.mesh,json.loads(a.camera.read_bytes()),a.scale)
    print(r['matched'],'/',r['sample_count']);a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
