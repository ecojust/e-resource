from pathlib import Path
import numpy as np,json
W=Path(__file__).resolve().parent
r=json.loads((W/'villa-three-cameras.json').read_bytes())
p=r['parameters'];cam={v['source']:np.array(v['P'])for v in r['cameras']}
def inverse(uv,ax,val,P):
 idx=[k for k in range(3) if k!=ax];M=P[:,idx+[3]].copy();M[:,2]+=P[:,ax]*val;q=np.linalg.solve(M,[*uv,1]);xyz=np.empty(3);xyz[ax]=val;xyz[idx]=q[:2]/q[2];return xyz
out={}
for side,ap,toe,e in [('left',[113,62],[344,298],-1),('right',[793,261],[882,358],1)]:
 y=-p[side+'_depth'];x=p[side+'_in'];sw=p[side+'_width'];zridge=inverse(ap,1,y,cam['district2018'])[2];ze=inverse(toe,1,y,cam['district2018'])[2]
 out[side]=dict(y_face=y,x_left=min(x,x+e*sw),x_right=max(x,x+e*sw),z_eave=p['wing_eave'],z_ridge=float(zridge),z_outer_ridge=p[side+'_ridge'],z_inner_toe=float(ze),y_outer_ridge=y-p[side+'_roof_lip'])
 # The bay's light front is in front of the wall. Photograph the complete side returns separately.
 out[side].update(oriel_center=x+e*sw*.5+p['left_bay_middle' if side=='left'else 'right_bay_center'],oriel_glazing_width=p[side+'_bay_width'],oriel_y=y-p[side+'_bay_out'],oriel_glazing_top=p[side+'_bay_head'],oriel_glazing_bottom=p[side+'_bay_bottom'])
for name,vals in [('left',[[21,198],[195,202]]),('right',[[747,409],[842,407]])]:
 row=out[name];row['oriel_wall_contact']=[inverse(v,1,row['y_face'],cam['district2018']).tolist() for v in vals]
out['arcade']={'x_left':p['left_in'],'x_right':p['right_in'],'y_face':0,'z_arcade_top':p['centre_eave'],'cornice_face_y':-p['beam_overhang']}
out['rear_limit']='根据可见主屋顶与山墙截取，背面不可见的窗门未建。'
f=W/'villa-roof-interface.json';f.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False,indent=2))
