"""Back-project two west-of-courtyard facade frames from the registered camera origins."""
from pathlib import Path
import json,hashlib,math
import numpy as np
from PIL import Image,ImageDraw
w=Path(__file__).parent;load=lambda n:json.loads((w/n).read_bytes());sha=lambda n:hashlib.sha256((w/n).read_bytes()).hexdigest()
osm=load('original-features.json');owner=next(f for f in osm['features'] if f['localId']==4093);west,east=owner['geometry']['coordinates'][0][3],owner['geometry']['coordinates'][0][2]
S=np.array([math.cos(math.radians(east[1])),1])*111195.08
U=(np.array(east)-west)*S;U=U/np.linalg.norm(U);N=np.array([-U[1],U[0]])
def input(i,year=2021):
 rec=load(f'upper-{i}-{year}-source.json');station=load('station-'+rec['station']+'.json');pos=(np.array(rec['wgs'])-east)*S
 return rec,pos,station['DeviceHeight']
def ray(i,x):
 r,c,z=input(i);a=math.radians(r['az']+(x/849-.5)*r['hf']);return np.array([math.sin(a),math.cos(a)])
# The transition between buff corner stone and the exposed end wall, at three visible levels.
anchors=[(682,293),(679,295),(684,290)]
junctions=[]
for px,qx in anchors:
 A,ca,_=input(0);B,cb,_=input(1);a,b=ray(0,px),ray(1,qx)
 k,ell=np.linalg.solve(np.stack([a,-b],axis=1),cb-ca);junctions.append(ca+k*a)
corner=np.median(junctions,axis=0)
def trace(i,px,py):
 r,c,eye=input(i);dir=ray(i,px);step=np.dot(corner-c,N)/np.dot(dir,N);b=c+step*dir
 el=math.radians(r['el']+(.5-py/759)*r['vf']);return [float((b-corner)@U),float(eye+step*math.tan(el))]
def project(i,x,z,year):
 r,c,eye=input(i,year);en=corner-c+x[...,None]*U;az=np.degrees(np.arctan2(en[...,0],en[...,1]));az=(az-r['az']+180)%360-180
 el=np.degrees(np.arctan2(z-eye,np.linalg.norm(en,axis=-1)));return (az/r['hf']+.5)*849,(.5-(el-r['el'])/r['vf'])*759
marks={'first_frame_left':(409,294),'first_frame_right':(602,344),'first_frame_head_mid':(510,326),'first_frame_sill_mid':(510,430),'second_frame_head_mid':(510,180),'second_frame_sill_mid':(510,268),'third_frame_head_mid':(510,82),'third_frame_sill_mid':(510,144),'wall_left_fitting':(321,327),'corner_coping':(665,110),'corner_quoin':(680,250),'terrace_edge_mid':(520,39),'western_brick_riser':(318,337)}
provisional={k:trace(0,*p)for k,p in marks.items()}
out=dict(owner=owner['localId'],osm_way='494956475@3',front_west_wgs84=west,front_east_wgs84=east,author_x_en=U.tolist(),author_y_en=N.tolist(),camera_tie_wgs84=(np.array(east)+corner/S).tolist(),tie_to_mapped_corner_en_m=(-corner).tolist(),independent_east_corner_rays=[dict(pixels=list(a),intersection_en_m=b.tolist())for a,b in zip(anchors,junctions)],raw_pixel_marks=marks,raw_landmarks_from_east_m=provisional,source_sha256={f:sha(f)for f in ['upper-0-2021-source.json','upper-1-2021-source.json','upper-2-2021-source.json','upper-0-2015-source.json','original-features.json']})
(w/'triangulated.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
def rect(i,year):
 X,Z=np.meshgrid(np.linspace(-10.4,.45,735),np.linspace(17.8,3.1,940));x,y=project(i,X,Z,year);im=np.array(Image.open(w/f'upper-{i}-{year}.jpg'));xp=np.rint(x).astype(int);yp=np.rint(y).astype(int);mask=(xp>=0)&(yp>=0)&(xp<850)&(yp<760);out=np.full((940,735,3),202,np.uint8);out[mask]=im[yp[mask],xp[mask]];return Image.fromarray(out)
for i in [0,1,2]:
 if not (w/f'upper-{i}-2021.jpg').is_file(): continue
 im=rect(i,2021);d=ImageDraw.Draw(im)
 for x in range(-10,1):
  a=(x+10.4)/10.85*734;d.line((a,0,a,940),fill='#dfbb54',width=1);d.text((a,4),str(x),fill='black',stroke_width=2,stroke_fill='gold')
 for z in range(4,18):
  b=(17.8-z)/14.7*939;d.line((0,b,735,b),fill='#c3a957',width=1);d.text((4,b+1),str(z),fill='black',stroke_width=2,stroke_fill='gold')
 im.thumbnail((470,600));im.save(w/f'rect-{i}-2021.jpg',quality=85)
print('origin',east,'correction',-corner,'landmarks',[(k,np.round(v,2))for k,v in provisional.items()])
