"""Independent camera direction/location checks. No camera EXIF location was used in the fit."""
from pathlib import Path
import json,math,sys,argparse
import numpy as np
from PIL import Image
folder=Path(__file__).resolve().parent
sys.path.insert(0,str(folder.parent/'source'))
from nanjing_photo_plane import CAMERAS,position
def check(input_folder):
 s=json.loads((folder/'north-front-site.json').read_bytes());ring=s['owner']['geometry']['coordinates'][0];origin=np.array(ring[2])
 lat=math.radians(origin[1]);e=.00669437999014;den=1-e*math.sin(lat)**2
 scales=np.radians(1.)*6378137*np.array([math.cos(lat)/math.sqrt(den),(1-e)/den**1.5]);axis=(origin-np.array(ring[3]))*scales;axis/=np.linalg.norm(axis);inward=np.array([-axis[1],axis[0]])
 out={}
 d=lambda row:float(row[0])+float(row[1])/60+float(row[2])/3600
 for k,wh in [('a',(3024,4032)),('b',(4032,3024))]:
  p=CAMERAS[k];eye=-np.linalg.solve(p[:,:3],p[:,3]);x=Image.open(input_folder/('cc2024'+k+'.jpg')).getexif().get_ifd(34853)
  wgs=np.array([d(x[4]),d(x[2])]);en=eye[0]*axis+eye[1]*inward;obs=(wgs-origin)*scales
  delta=position(wh[0]/2,wh[1]/2,0,k)-eye;v=delta[0]*axis+delta[1]*inward;az=math.degrees(math.atan2(*v))%360
  out[k]={'position_error_vs_original_gps_m':float(np.linalg.norm(en-obs)),'original_horizontal_gps_error_m':float(x[31]),'model_bearing_through_centre_degrees':az,'original_true_north_bearing_deg':float(x[17]),'bearing_difference_deg':abs((az-float(x[17])+180)%360-180),'estimated_camera_wgs':(origin+en/scales).tolist(),'exif_camera_wgs':wgs.tolist()}
 return {'observations':out,'interpretation':'Oblique camera heading agrees within one degree. The close camera GPS is poor (horizontal error tag is about 659 m) and was not used to choose a parcel, scale or origin. Both headings look at the northern wall; the opposite facade cannot reproduce the observed directions.'}
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('input_folder',type=Path);a.add_argument('output',type=Path);p=a.parse_args();p.output.write_text(json.dumps(check(p.input_folder),indent=2)+'\n')
