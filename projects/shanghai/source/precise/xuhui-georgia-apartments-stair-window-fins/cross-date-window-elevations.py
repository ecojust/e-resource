"""Fit the printed fin axes to two dated panoramas with independent street-grade observations."""
from pathlib import Path
from hashlib import sha256
import json
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
q=Path(__file__).parent; panorama=q/'dated-elevations'
def read(p):return json.loads(p.read_bytes())
def digest(p):return sha256(p.read_bytes()).hexdigest()
plan=read(q/'printed-plan-axes.json')
pitch=plan['span_m']/2
def photographic_record(name):
    local=panorama/(name+'.json')
    if local.is_file() and local.with_suffix('.jpg').is_file():
        entry=read(local)
        assert digest(local.with_suffix('.jpg'))==entry['sha256']
        return entry
    import io
    import requests
    from urllib.parse import urlparse,parse_qs
    from PIL import Image
    record=read(q/'dated-view-sources.json')[name]
    x0,y0=record['xy'];width,height=record.get('dims') or record['size']
    canvas=Image.new('RGB',(width,height))
    for row in record['tiles']:
        response=requests.get(row['url'],timeout=25,headers={'Referer':'https://map.baidu.com/','User-Agent':'Mozilla/5.0'})
        response.raise_for_status()
        assert sha256(response.content).hexdigest()==row['sha256']
        parts=parse_qs(urlparse(row['url']).query)['pos'][0].split('_')
        y,x=map(int,parts)
        while (x+1)*512<=x0:x+=8
        canvas.paste(Image.open(io.BytesIO(response.content)),(x*512-x0,y*512-y0))
    rendered=io.BytesIO();canvas.save(rendered,format='JPEG',quality=record['reference_jpeg_quality'])
    assert sha256(rendered.getvalue()).hexdigest()==record['sha256']
    return record
sets=[
 dict(file='street-09000300011512071132258065Z',cx=246,rect=(3459,254),
      fin=[[(198,100),(198,330),(199,608)],[(246,99),(247,331),(246,610)],[(300,100),(301,332),(303,610)]],
      ground=[(197,886),(247,897),(301,901)],
      storeys=[[(219,372),(270,362)],[(220,301),(270,281)],[(219,269),(270,255)],[(219,213),(270,197)],
               [(218,195),(270,176)],[(219,146),(270,133)]],
      tangent=-35),
 dict(file='09000300122002210900035655O-full-height',cx=162,rect=(3740,0),
      fin=[[(66,204),(70,380),(79,700)],[(164,204),(168,383),(179,700)],[(268,204),(276,383),(288,700)]],
      ground=[(82,1203),(189,1212),(295,1215)],
      storeys=[[(111,444),(212,423)],[(111,374),(212,351)],[(110,352),(210,330)],[(108,303),(208,284)],
               [(109,288),(210,273)],[(107,260),(208,242)]],
      tangent=-17),
]
def fit(choice, return_solver=False):
    center=choice['cx'];rx,ry=choice['rect'];meta=photographic_record(choice['file'])
    depth=meta['pano']['height']
    def intersection(uv,par):
        xcam,standoff,offset,tilt,roll=par[:5]
        pts=np.asarray(uv);az=(pts[:,0]-center)*2*np.pi/4096
        el=np.pi/2-(pts[:,1]+ry)*2*np.pi/4096
        vv=np.column_stack([np.sin(az)*np.cos(el),np.cos(az)*np.cos(el),np.sin(el)])
        # Rotate the global yaw about vertical after tilting the image in camera axes.
        rotation=Rotation.from_euler('z',-offset,degrees=True)*Rotation.from_euler('xy',[tilt,roll],degrees=True)
        vr=rotation.apply(vv);ray=standoff/vr[:,1]
        return np.column_stack([xcam+ray*vr[:,0],depth+ray*vr[:,2]])
    def residual(par):
        errs=[]
        for axis,uv in zip([-pitch,0,pitch],choice['fin']):
            xs=intersection(uv,par)[:,0]
            errs.extend((xs-axis)/.045)
        errs.extend(intersection(choice['ground'],par)[:,1]/.15)
        for z,uv in zip(par[5:],choice['storeys']):
            errs.extend((intersection(uv,par)[:,1]-z)/.10)
        errs.extend([(par[2]-choice['tangent'])/4,par[3]/2,par[4]/2])
        return np.array(errs)
    initial=[6,10,choice['tangent'],0,0,10.5,12.9,13.5,15.8,16.5,18.9]
    solver=least_squares(residual,initial,max_nfev=300)
    assert solver.success
    if return_solver:return solver.x,residual
    p=solver.x
    return dict(station=meta['pano']['id'],date=meta['pano']['date'],camera_height_m=depth,reference=meta['pano']['meta'],
                photo_sha256=meta['sha256'],raw_tiles=meta['tiles'],image_origin=choice['rect'],measurements=choice,
                east_west_camera_offset=float(p[0]),normal_camera_offset=float(p[1]),view_rotation_deg=p[2:5].tolist(),
                fin_rms_m=float(np.sqrt(np.mean(np.concatenate([(intersection(uv,p)[:,0]-x)**2 for x,uv in zip([-pitch,0,pitch],choice['fin'])])))),
                pavement_residuals_m=intersection(choice['ground'],p)[:,1].tolist(),fitted_vertical_marks_m=p[5:].tolist(),
                physical_mark_readings_m=[intersection(uv,p)[:,1].tolist() for uv in choice['storeys']])
fits=[fit(case) for case in sets]
analysis=[fit(case,True) for case in sets]
a0,func0=analysis[0];a1,func1=analysis[1]
def together(p):
 return np.r_[func0(np.r_[p[:5],p[10:]]),func1(np.r_[p[5:10],p[10:]])]
adjusted=least_squares(together,np.r_[a0[:5],a1[:5],(a0[5:]+a1[5:])/2],max_nfev=300)
assert adjusted.success
marks=adjusted.x[10:]
local_openings=np.array([.28,3.28,4.29,6.96])
transform=np.linalg.lstsq(np.column_stack([np.ones(4),local_openings]),marks[2:],rcond=None)[0]
nominal=transform[0]+transform[1]*local_openings
band=np.abs(nominal-marks[2:]).max()
assert band<.20
print('joint',marks.tolist(),'geometry',transform.tolist(),'residual',band)

data=dict(id='xuhui-georgia-apartments-stair-window-fins',plan_sha256=digest(q/'printed-plan-axes.json'),
          map_frame=dict(center=plan['center'],street_normal=plan['street_normal_deg'],outer_fin_spacing_m=2*pitch),
          vertical_marks=['sill of pair below','head of pair below','selected lower sill','selected lower head','selected upper sill','selected upper head'],
          units='metres above the photographed sidewalk',results=fits,shared_elevations_m=marks.tolist(),
          model_base_above_grade_m=float(transform[0]),model_vertical_scale=float(transform[1]),
          fitted_opening_ends_m=nominal.tolist(),model_fit_residual_max_m=float(band),
          independent_date_differences_m=[abs(x-y) for x,y in zip(fits[0]['fitted_vertical_marks_m'],fits[1]['fitted_vertical_marks_m'])],
          uncertainty='The two independently fitted upper heads differ by about 1.4 m. Both source views show the same vertical sequence. The upper window translation and the wall-depth clip must still be tested against the actual old city shell.')
(q/'cross-date-window-elevations.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
for row in fits:print(row['date'],row['normal_camera_offset'],row['view_rotation_deg'],row['fin_rms_m'],row['pavement_residuals_m'],row['fitted_vertical_marks_m'])
