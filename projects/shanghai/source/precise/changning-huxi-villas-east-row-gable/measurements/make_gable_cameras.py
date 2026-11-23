"""Resolve the courtyard station and the independently geolocated, restricted winter view for each row hypothesis."""
from pathlib import Path
import json,math,numpy as np
HERE=Path(__file__).absolute().parent
def camera_sets():
    refs=json.loads((HERE/'photographs.json').read_bytes());reg=json.loads((HERE/'courtyard-camera.json').read_bytes())
    models=json.loads((HERE/'row-hypotheses.json').read_bytes());ox,oy=json.loads((HERE/'aerial-release-39767.json').read_bytes())['crop_global_pixel_origin']
    cam=dict(K=reg['K'],R=reg['R'],C=reg['camera_xyz'],width=4912,height=3264,crop=[1190,0,4740,3264])
    stations={'courtyard-2014':cam}
    p=refs['outside_2015'];raw=p['station'];scale=256*2**19
    az,pitch=np.radians([p['az'],p['pitch']]);right=np.array([np.cos(az),-np.sin(az),0]);flat=np.array([np.sin(az),np.cos(az),0]);up=np.array([0,0,1])
    rot=np.array([right,flat*np.sin(pitch)-up*np.cos(pitch),flat*np.cos(pitch)+up*np.sin(pitch)]);w,h=p['width'],p['height'];f=w/2/np.tan(np.radians(p['hfov']/2));k=[[f,0,w/2],[0,f,h/2],[0,0,1]]
    for i,tag in enumerate(['lane-first-position','lane-second-position']):
        a,b=models['roof_sample_pixels'][i];lon=(ox+a+.5)/scale*360-180;lat=np.degrees(np.arctan(np.sinh(np.pi*(1-2*(oy+b+.5)/scale))))
        loc=np.array(raw['position'])-[lon,lat];c=[loc[0]*111319.49*np.cos(np.radians(lat)),loc[1]*110890,raw['height']]
        stations[tag]=dict(K=k,R=rot.tolist(),C=c,width=w,height=h,crop=[247,175,470,400],outside_date=raw['date'],row_hypothesis=i+1,actual_street_station=raw['id'])
    return stations
def make():
    def view(k,label,c,t,span):return dict(name=k,label=label,eye=c,target=t,width_m=span,width=1080,height=648)
    result=[view('overview','临弄山墙与院墙折角',[-19,-23,6.9],[2,3,5.5],24.1),view('south-sash','南面跨层钢窗',[5,-11,6.3],[2.12,0,6.45],8.5),view('narrow-lights','山墙双狭窗及机架',[-11,3.1,6.4],[.02,3.9,6.65],7.9),view('roof-coping','山尖通气口与檐盖',[-11,-3,14.45],[2.05,3.4,10.35],13.2),view('pipe-return','折管和砖墙灰顶',[-5.1,-7.7,2.8],[.25,.4,2.15],7.45),view('short-return','后方短返翼',[ -9,11,8.3],[.25,6.43,7.0],7.8)]
    for (key,cam),label in zip(camera_sets().items(),['2014年弄内原照','2015年南口·首排位置假设','同一南口·次排位置假设']):
        x,y,a,b=cam['crop'];w,h=a-x,b-y;k=np.array(cam['K'],float);k[0,2]-=x;k[1,2]-=y;r=np.array(cam['R']);c=np.array(cam['C']);d=float((np.array([1.2,2.,6.2])-c)@r[2]);aspect=k[0,0]/k[1,1];cx=k[0,2]+.5;cy=k[1,2]+.5
        result.append(dict(name=key,label=label,eye=c.tolist(),target=(c+r[2]*d).tolist(),world_up=(-r[1]).tolist(),width_m=d*w/k[0,0],width=w,height=h,reference=key,source_crop=cam['crop'],source_dimensions=[cam['width'],cam['height']],sensor_fit='HORIZONTAL',pixel_aspect_y=aspect,blender_pixel_aspect_x=max(1.,1./aspect),blender_pixel_aspect_y=max(1.,aspect),shift_x=(w/2-cx)/w,shift_y=(cy-h/2)*aspect/w,principal_point_edge_px=[cx,cy],projection_world_to_photo_pixel_centres=(k@np.c_[r,-r@c]).tolist()))
    return result
if __name__=='__main__':
    (HERE.parent/'source/cameras.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
    (HERE/'gable-photo-stations.json').write_text(json.dumps(dict(stations=camera_sets()),ensure_ascii=False,indent=2)+'\n')
