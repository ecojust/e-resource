"""Project landmarks measured on each delivered GLB, keeping independent photographic hold-outs."""
from pathlib import Path
import json,sys,math
from check_assets import read_glb
f=Path(__file__).resolve().parent
reg=json.loads((f/'two-photograph-registration.json').read_bytes())
def bounds(points):return [[min(x[i]for x in points),max(x[i]for x in points)]for i in range(3)]
def three_role(path):
 g,points,faces=read_glb(path)
 def box(prefix):
  return bounds([p for obj,m,*vs in faces if obj.startswith(prefix)for p in vs])
 def getbox(prefix,side='mid'):
  x,y,z=box(prefix)
  return [(x[0]+x[1])/2,y[0],(z[0]+z[1])/2]
 plaque=box('04.number-four');post=box('01.East');ventnames=['12.dark-interior-'+str(i)for i in (1,2,3)]
 sash=box('11.four-light-steel-window-stiles');a,b,c=box('14.window-side-condenser-fan-opening');x,y,z=plaque
 sites={'gate_seam':[0,.021,2.087],'right_jamb':[1.143,.021,2.087],'right_pier_cap_inner':[post[0][0],-.085,2.374],'right_pier_cap_outer':[post[0][1],-.085,2.374],'door_number':getbox('04.number-four'),'door_number_top_left':[x[0],y[0],z[1]],'door_number_lower_right':[x[1],y[0],z[0]],'east_panel_lower_left':[1.787,.019,1.515],'steel_sash_upper_left':[sash[0][0]+.0125,sash[1][0],sash[2][1]],'steel_sash_upper_right':[sash[0][1]-.0125,sash[1][0],sash[2][1]],'air_conditioner_round_fan':[(a[0]+a[1])/2,b[0],(c[0]+c[1])/2]}
 for n,v in zip(('gable_upper_vent','gable_lower_left_vent','gable_lower_right_vent'),ventnames):
  xyz=getbox(v);xyz[1]=box('12.three-gable-vents')[1][0];sites[n]=xyz
 rows=[]
 for one in reg['anchors']:
  xyz=sites[one['feature']]
  for view,obs in [('press-2023',one['source_2023']),('shangguan-2021',one['source_2021'])]:
   a=reg['stations'][view]['projection_3x4'];q=[sum(m*v for m,v in zip(rr,[*xyz,1.]))for rr in a];p=[q[i]/q[2]for i in (0,1)]
   rows.append(dict(landmark=one['feature'],photo=view,used_for_registration=one['used'],original_pixel=obs,model_pixel=[round(x,2)for x in p],error_px=round(math.dist(obs,p),2),model_xyz=[round(v,4)for v in xyz]))
 def rms(rows):return round(math.sqrt(sum(a['error_px']**2 for a in rows)/len(rows)),2)
 return {'rms_all_px':rms(rows),'held_out_2021_rms_px':rms([a for a in rows if a['photo']=='shangguan-2021' and not a['used_for_registration']]),'rows':rows}
if __name__=='__main__':
 folder,out=map(Path,sys.argv[1:]);data={s:three_role(folder/(s+'.glb'))for s in ('raw','full','lod')};out.write_text(json.dumps(data,indent=2)+'\n');print([(k,v['rms_all_px'],v['held_out_2021_rms_px'])for k,v in data.items()])
