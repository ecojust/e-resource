"""Use the whole unfiltered triangle scene to test original-photograph pixels."""
import argparse, hashlib,json,sys
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
from ground_arcade import DATA,DEFAULT_LAYOUT,_arc,_joints,_point,RED,GREY,BED,GREY_BED,CAP,IRON,GLASS,WOOD,HOOD,RIDGE,LIMESTONE

def inspect(asset,layout=DEFAULT_LAYOUT):
    p=np.asarray(layout['ground_camera_P'],float);scene=SerialScene(asset)
    eye=-np.linalg.solve(p[:,:3],p[:,3]);tests=[]
    def probe(name,uv,materials,y_end=.40):
        uv=np.asarray(uv,float);target=_point(*uv,y_end,layout)
        forward=target-eye;length=np.linalg.norm(forward)
        hit=scene.ray(eye,forward/length,length)
        material=hit['material']if hit else None
        tests.append(dict(detail=name,source_uv=np.round(uv,3).tolist(),until_y=y_end,expected=materials,
                          actual=material,passed=material in materials))
    for i,a in enumerate(DATA['arches'][1:]):
        for band,at in [('inner',.44),('outer',.84)]:
            angles=_joints(band)
            for j,(t,s) in enumerate(zip(angles,angles[1:])):
                if 10<np.rad2deg((t+s)/2)<169 and j%3==0:
                    probe(a['label']+' '+band+' brick',_arc(a,at,np.array([(t+s)/2]))[0],RED)
        # Two central and two side lines through the exposed depth of this arch.
        for x in [-62,-29,0,30,62]:
            for v in [878,905,947,998,1067]:
                probe(a['label']+' open arcade',[a['spring'][0]+x,v],[None],.31)
    for j,i in enumerate([1,2,3]):
        center=DATA['piers'][i]['axis']
        for x in ([-19,-15,-12] if i==3 else [-12,5,16]):
            for y,m in [(925.,[*RED,CAP]),(943.,[*RED,CAP]),(972.,[*GREY,GREY_BED]),(1014.,[*GREY,GREY_BED]),(1033.,[*RED,GREY_BED]),(1080.,[*GREY,GREY_BED]),(1110.,[LIMESTONE])]:
                sample_v=1020. if i==3 and y==972. else y
                probe(f'Pier {i+1} measured face',[center+x,sample_v],m)
    g=DATA['grille'];hub=np.array(g['hub'])
    for point in g['spoke_tip_uv']:
        probe('Exposed fan spoke',hub+(np.array(point)-hub)*.72,[IRON])
    for u in g['bars_u']:
        probe('Projecting grille vertical',[u,947.5],[IRON])
    for v in g['rails_v']:probe('Projecting grille horizontal',[433.4,v],[IRON])
    for u in [365.8,389.7,411.2,435.4,457.7,470.3]:
        for v in [940.2,967.,995.]:
            probe('Glazing reached through grille',[u,v],[GLASS,WOOD])
    probe('Fan spoke visible at the former negative control',[345,859],[IRON],-.23)
    for u,v in [(371,852),(347,854),(397,866),(403,855),(386,851)]:
        probe('Fan negative interval',[u,v],[None],-.23)
    return dict(asset=scene.asset,source=DATA['photograph'],camera_P=p.tolist(),unfiltered=True,
                tests=len(tests),passed=all(q['passed']for q in tests),rays=tests)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('mesh',type=Path);ap.add_argument('report',type=Path);ap.add_argument('--camera',type=Path)
 args=ap.parse_args();layout=DEFAULT_LAYOUT
 if args.camera:
    data=json.loads(args.camera.read_bytes());layout={'ground_camera_P':data.get('ground_camera_P',data.get('camera_P'))}
 result=inspect(args.mesh,layout)
 args.report.write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n')
 for t in result['rays']:
    if not t['passed']:print(t['detail'],t['source_uv'],t['actual'])
 print(result['tests'],result['passed']);raise SystemExit(int(not result['passed']))
