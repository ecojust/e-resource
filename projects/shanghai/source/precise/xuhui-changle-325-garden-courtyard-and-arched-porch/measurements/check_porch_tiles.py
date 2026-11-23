"""Check Fayhoo's original roof pixels against triangles read from an actual glTF file."""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parent.parent/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact')]
from glb_triangles import SerialScene
from register_porch import PorchFrame
from porch_tiles import CLAY,PALE,DARK,END,PAN,FASCIA,TRIM,BRACKET,Roof,DATA

def verify(path):
    frame=PorchFrame();camera=frame.camera;r=Roof(frame);scene=SerialScene(path);obs=[]
    def add(feature,uv,expect):
        hit=scene.ray(camera.c,camera.ray(uv),length=100)
        matched=bool(hit and hit['material'] in expect)
        distances=[]
        if not matched:
            for dx in range(-2,3):
                for dy in range(-2,3):
                    if dx*dx+dy*dy>4:continue
                    sample=scene.ray(camera.c,camera.ray((uv[0]+dx,uv[1]+dy)),length=100)
                    if sample and sample['material'] in expect:
                        distances.append(float(np.hypot(dx,dy)))
        obs.append(dict(feature=feature,original_pixel=uv,expected=expect,actual=hit,
                        matched=matched,nearby_distance_px=0. if matched else min(distances,default=None)))
    for point in [(444,604),(493,605),(599,605),(650,604),(732,604),(812,604)]:
        add('red end of hollow barrel',point,[END,CLAY,PALE,DARK])
    for point in [(538,520),(587,520),(663,520),(558,570),(635,570),(741,570),(519,595),(728,595)]:
        add('convex fired cover',point,[CLAY,PALE,DARK])
    for point in [(554,520),(603,520),(679,520),(574,570),(650,570),(757,570),(535,594),(744,594)]:
        add('pan between two cover tiles',point,[PAN])
    for point in [(451,618),(575,618),(690,618),(799,617),(843,617)]:
        add('black fascia',point,[FASCIA,TRIM])
    for point in [(470,650),(474,683),(480,704),(873,664),(879,691)]:
        add('ochre eave bracket',point,[BRACKET])
    return dict(photo_sha256=DATA['photo_sha256'],model_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                report='Actual intersections with the first serialized triangle. Single-station coordinates are conditional on the fitted stair and eaves frame.',
                courses=17,complete_disc_faces=16,observed_pan_seams=DATA['pan_lap_rows_v'],common_cover_depth=[r.front_y,r.rear_y],
                lateral_shift=r.shear,mean_axis_heights=[r.z0,r.z1],median_cover_pitch=r.pitch,observations=obs,
                direct=sum(i['matched'] for i in obs),within_2px=sum(i['nearby_distance_px'] is not None for i in obs),count=len(obs))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('glb',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    result=verify(a.glb);a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(result['direct'],result['count']);print([(q['original_pixel'],q['actual']['material']if q['actual'] else None)for q in result['observations']if not q['matched']])
