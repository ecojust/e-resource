"""Estimate the square, tapered frame and ring elevations from two independent public views."""
from pathlib import Path
from scipy.optimize import least_squares
import numpy as np,json,hashlib,math
import argparse
ROOT=Path(__file__).resolve().parent
refs={row['commons_page_id']:row for row in json.loads((ROOT/'photographic-witnesses.json').read_bytes())}
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('output',type=Path)
output=parser.parse_args().output
# Coordinates in 720-pixel-wide copies, x right / y down. First edges are the exterior
# corners of the same concrete band, not its nearer supporting column center.
photo1={'id':'49573755','size':[720,1084],'mean_lens':950,'marks':{
 'eave':[(0,273,110),(1,432,111)],'cab':[(0,272,233),(1,431,236)],
 'gallery':[(0,248,382),(1,454,384)],'middle':[(0,213,598),(1,475,601)],
 'arch':[(0,174,819),(1,515,823)],'crest':[(0,295,57),(1,406,58)]}}
photo2={'id':'86478504','size':[720,961],'mean_lens':710,'marks':{
 'eave':[(0,312,187),(1,371,193),(2,418,187)],'cab':[(0,302,261),(1,373,267),(2,428,259)],
 'gallery':[(0,292,343),(1,373,360),(2,444,338)],'middle':[(0,277,448),(1,375,484),(2,461,440)],
 'arch':[(0,260,543),(1,375,601),(2,479,530)],'crest':[(0,324,153),(1,371,160),(2,405,151)],
 'foot':[(1,376,731)]}}
levels=['foot','arch','middle','gallery','cab','eave','crest']
angles=np.array([[-1,-1],[1,-1],[1,1],[-1,1]])
H=35.2
# Corners of individual balustrade piers are inset from the overhanging eaves.
def setup(x):
 bottom,top,arch,middle,gallery,cab,eave,crest_half=x[:8]
 hts=[0,arch,middle,gallery,cab,eave,H]
 layout={k:[z,(bottom+(top-bottom)*z/eave) if k!='crest' else crest_half] for k,z in zip(levels,hts)}
 layout['eave'][1]+=x[-1]
 return layout
def project(x,half,z,corner,width,height):
 az,radius,eye_height,aim_x,aim_z,focal,roll=x
 eye=np.array([np.sin(az)*radius,-np.cos(az)*radius,eye_height])
 tangent=np.array([np.cos(az),np.sin(az),0])
 aim=tangent*aim_x+np.array([0,0,aim_z])-eye;aim/=np.linalg.norm(aim)
 right=np.cross(aim,[0.,0,1]);right/=np.linalg.norm(right);up=np.cross(right,aim)
 u=right*np.cos(roll)+up*np.sin(roll);v=-right*np.sin(roll)+up*np.cos(roll)
 pt=np.r_[angles[corner]*half,z]-eye;return np.array([width/2+focal*(pt@u)/(pt@aim),height/2-focal*(pt@v)/(pt@aim)])
photos=[photo1,photo2];starting=[6.2,2.45,9.1,16.8,23.8,28.5,32.7,1.88,
  .03,42,18,0,17,950,0,.78,44,32,0,14,710,0,.38]
lo=[3,1,6,13,19,25.5,31,.8,-.33,22,2,-5,9,450,-.10,.42,22,12,-5,6,350,-.12,.05]
hi=[8,3.8,13,20.5,26,31.4,34.6,3.0,.33,90,36,5,25,2300,.10,1.10,110,62,5,26,1800,.12,.85]
def error(params,detail=False):
 layout=setup(params);errors=[];all_marks=[]
 for i,p in enumerate(photos):
  camera=params[8+7*i:15+7*i]
  for label,marks in p['marks'].items():
   z,side=layout[label]
   for corner,x,y in marks:
    xy=project(camera,side,z,corner,*p['size']);res=xy-[x,y];errors.extend(res)
    all_marks.append({'photo':p['id'],'level':label,'corner':corner,'point':[x,y],'projected':xy.round(3).tolist(),'error_px':round(np.linalg.norm(res),3)})
 return all_marks if detail else errors
sol=least_squares(error,starting,bounds=(lo,hi),loss='soft_l1',f_scale=3,max_nfev=900)
marks=error(sol.x,True);errors=[v['error_px']for v in marks]
report={'method':'Two public views with shared taper and six free band heights. Nominal overall height 35.2 m as reported by The Paper in 2016 (article 1452498). The base point is partially obscured. Distances are approximate. Coordinates are scaled to width 720, from original Commons-supplied previews.',
 'source_photographs':[{'id':p['id'],'size_for_observations':p['size'],'preview_sha256':refs[p['id']]['inspected']['sha256']}for p in photos],
 'square_width_at_bands_and_elevation_m':{k:{'height':round(z,4),'width':round(h*2,4)}for k,(z,h)in setup(sol.x).items()},'upper_overhang_m':round(float(sol.x[-1]),3),'rms_px':round(np.mean(np.square(errors))**.5,3),'median_px':round(float(np.median(errors)),3),'max_px':max(errors),'parameters':sol.x.tolist(),'marks':marks}
output.write_text(json.dumps(report,indent=2)+'\n');print(report['square_width_at_bands_and_elevation_m'],report['rms_px'],report['median_px'],report['max_px']);print(sorted(marks,key=lambda v:-v['error_px'])[:4])
