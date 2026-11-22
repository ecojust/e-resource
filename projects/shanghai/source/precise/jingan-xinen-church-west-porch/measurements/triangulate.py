from pathlib import Path
from PIL import Image
import json,numpy as np,math
q=Path(__file__).parent;b=json.loads((q/'survey.json').read_bytes());shots=b['shots'];points={
'cross_joint':{0:(197,46),1:(209,34),4:(177,51),5:(177,59),6:(196,39)},
'gable_top':{0:(197,57),1:(209,40),4:(177,62),5:(176,71),6:(196,48)},
'porch_north_coping':{0:(147,121),1:(137,137),4:(149,127),5:(168,129),6:(121,138)},
'porch_south_coping':{0:(291,131),1:(217,106),4:(262,134),5:(276,139),6:(216,116)},
'bay2_north_upper':{0:(220,151),1:(156,148),4:(206,156),5:(233,160),6:(153,151)},
'gable_window_peak':{0:(200,95),1:(210,82),4:(178,98),5:(178,108),6:(207,91)},
}
def getray(i,p):
 s=shots[i];a=np.asarray(s['offset_m']+[s['eye_z']]);R,U,F=map(np.array,(s['right'],s['up'],s['forward']));og=np.array(s['imsize']);sm=np.array(Image.open(q/s['filename']).size);u,v=(np.array(p)+.5)*og/sm-.5;w,h=og;d=F+(u-(w-1)/2)*R/s['focal']+((h-1)/2-v)*U/s['focal'];return a,d/np.linalg.norm(d)
def intersect(rows):
 source=[getray(i,p)for i,p in rows.items()];I=np.eye(3);ma=[I-np.outer(d,d)for a,d in source];x=np.linalg.solve(sum(ma),sum(m@a for m,(a,d)in zip(ma,source)));return x,[round(np.linalg.norm(np.cross(d,x-a)),3)for a,d in source]
result={}
for name,row in points.items():
 x,res=intersect(row);result[name]=dict(xyz=x.tolist(),errors=res,pixels=row);print(name,x.round(2),res)
target=np.array(b['target']);S=np.array([math.cos(math.radians(target[1])),1])*111195.08
P=np.array(result['porch_north_coping']['xyz']);Q=np.array(result['porch_south_coping']['xyz']);axis=Q[:2]-P[:2];L=np.linalg.norm(axis);axis/=L;normal=np.array([-axis[1],axis[0]]);mid=(P+Q)/2;gable=np.array(result['gable_top']['xyz'])
print('coping width',L,'mid',mid,'axis',axis,'gable into',np.dot(gable[:2]-mid[:2],normal),'mid wgs',target+mid[:2]/S,'gable wgs',target+gable[:2]/S)
(q/'triangulated.json').write_text(json.dumps(dict(source='survey.json',coordinate_origin=b['target'],landmarks=result,porch_front_mean_wgs=(target+mid[:2]/S).tolist(),porch_width_m=L,portico_axis=axis.tolist(),front_to_gable_setback_m=float(np.dot(gable[:2]-mid[:2],normal)),porch_coping_top_m=mid[2],gable_apex_m=gable[2]),indent=1)+'\n')
