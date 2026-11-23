from pathlib import Path
import json
import numpy as np
HERE=Path(__file__).resolve().parent
def inspect(name,label,at,eye,wide):
    return dict(name=name,label=label,target=at,eye=eye,width_m=wide,width=960,height=640)
def cameras():
    book=json.loads((HERE/'roof-registration.json').read_text());p=book['parameters'];x=p['pitch'];y=p['sash_y'];z=(p['head_z']+p['sill_z'])/2
    views=[inspect('overview','朝院前坡与上层栏廊',[0,1.8,9.85],[3.0,-33,13.65],27.2)]
    for key,label,crop in [('numbered-14','题注14号楼的旧影',[31,55,281,166]),('garden-2026','2026年院景近正面',[0,62,1280,555])]:
        s=book['stations'][key];r=np.array(s['R']);k=np.array(s['K']);eye=np.array(s['eye']);w=crop[2]-crop[0];h=crop[3]-crop[1];dist=24
        cx=k[0,2]+.5-crop[0];cy=k[1,2]+.5-crop[1]
        views.append(dict(name=key,label=label,eye=eye.tolist(),target=(eye+r[2]*dist).tolist(),world_up=(-r[1]).tolist(),width=w,height=h,width_m=w*dist/k[0,0],reference=key,source_crop=crop,source_dimensions=s['size'],sensor_fit='HORIZONTAL',blender_pixel_aspect_x=1.,blender_pixel_aspect_y=1.,pixel_aspect_y=1.,shift_x=(w/2-cx)/w,shift_y=(cy-h/2)/w,principal_point_edge_px=[cx,cy],projection_world_to_photo_pixel_centres=s['P']))
    views.extend([inspect('four-sashes','四座老虎窗',[0,y,z],[.7,-18,z+1],20.4),
                  inspect('western-casements','西端四扇细格窗',[-1.5*x,y,z],[-1.5*x-1.75,-4.2,z+.36],4.25),
                  inspect('hip-flashing','东端山坡交接',[1.5*x,y,z],[2*x+2,-3.5,z+1.78],6.65),
                  inspect('centre-chimney','正脊中央烟囱',[0,p['ridge_y'],p['ridge_z']+.56],[3.45,-3,p['ridge_z']+2.60],5.1),
                  inspect('corbels','檐下托臂与柱头',[-p['pier_pitch'],.01,p['eave_z']-.94],[-x-.97,-4.60,p['eave_z']-1.57],4.25),
                  inspect('upper-parapet','上层廊栏通孔',[1.5*p['pier_pitch'],.30,p['rail_z']-.34],[1.5*x+.55,-6.45,p['rail_z']+.49],6.20)])
    return views
if __name__=='__main__':(HERE.parent/'source/cameras.json').write_text(json.dumps(cameras(),ensure_ascii=False,indent=2)+'\n')
