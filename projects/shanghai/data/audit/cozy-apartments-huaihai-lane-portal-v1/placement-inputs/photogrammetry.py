"""Intersect documented jamb bearings from nearby days; anchor street-door dimensions to the measured frontal planes."""
import os
from pathlib import Path
from hashlib import sha256
from math import radians,degrees,atan2,cos,sin,tan
import numpy as np, subprocess,json
P=Path(__file__).parent;w=Path(os.environ['COZY_REFERENCE_FILES']);notes=json.loads((w/'stations-more.json').read_bytes())['stations']
sw=np.array([121.46504223,31.22324755]);ne=np.array([121.46575570,31.22353656]);unit=np.array([111195.08023*cos(radians(sw[1])),111195.08023]);en=lambda ll:(np.array(ll)-sw)*unit;ll=lambda xy:(sw+np.array(xy)/unit).tolist()
east=en(ne);east/=np.linalg.norm(east);inward=np.array([-east[1],east[0]])
js="""const p=require(process.env.COZY_BAIDU_PROJECTION_MODULE),fs=require('fs');console.log(JSON.stringify(JSON.parse(fs.readFileSync(0)).map(mc=>{let g=p.bmerc2ll(mc);for(let n=0;n<8;n++){let q=p.ll2bmerc(g);for(let k=0;k<2;k++)g[k]-=(q[k]-mc[k])/[111400,129600][k];}return {position:g,closure:p.ll2bmerc(g).map((v,k)=>v-mc[k])}})))"""
projected=json.loads(subprocess.run(['node','-e',js],text=True,input=json.dumps([j['mc']for j in notes]),capture_output=True,check=True).stdout)
f=lambda w:sha256(w.read_bytes()).hexdigest()
# Positions are image pixels on front stone lintel faces. Occluded corners are omitted.
config={1:('zoom-1-6-z5',{'outer_w':(363,610),'inner_w':(401,621),'inner_e':(571,635),'outer_e':(591,638),'word_last':(535,582),'top_w':(364,507),'top_e':(597,551),'sill_ref':(480,817),'west_sill':(445,525),'west_head':(450,422),'east_sill':(529,532),'east_head':(539,441)}),8:('zoom-8-329-z5',{'outer_w':(338,569),'inner_w':(390,575),'inner_e':(609,582),'outer_e':(640,584),'word_last':None,'top_w':(338,464),'top_e':(644,480),'sill_ref':(497,791),'west_sill':(463,473),'west_head':(467,368),'east_sill':(555,477),'east_head':(557,369)}),2:('zoom-2-300-z4',{'outer_w':None,'inner_w':None,'inner_e':(483,422),'outer_e':(497,422),'word_last':(465,400)}),11:('zoom-11-19-z5',{'outer_w':(249,630),'inner_w':(288,634),'inner_e':(425,640),'outer_e':(449,640),'word_last':(400,596)})}
cam={};angles={};points={}
for i,(name,clicks) in config.items():
 j=notes[i];header=json.loads((w/(name+'.json')).read_bytes());pitch=radians(header['pitch']);W,H=header['size'];F=W/(2*tan(radians(header['fov']/2)));obs=en(projected[i]['position']);assert max(abs(x) for x in projected[i]['closure'])<1e-4
 def orient(x,y):
  u=(x-W/2)/F;v=(H/2-y)/F;s=cos(pitch)-v*sin(pitch);a=(header['center']+degrees(atan2(u,s)))%360;alt=atan2(sin(pitch)+v*cos(pitch),(s*s+u*u)**.5);a1=radians(a);return a,np.array([sin(a1),cos(a1)]),alt
 cam[i]=dict(sid=j['id'],capture_date=j['date'],metadata=j['ref'],wgs84=projected[i]['position'],exact_projection_residual=projected[i]['closure'],virtual_view=header |{'sources':[v['sha256'] for v in header['sources']]},image=str(w/(name+'.jpg')),image_sha256=f(w/(name+'.jpg')),pixels=clicks)
 for k,pt in clicks.items():
  if pt:angles.setdefault(k,{})[i]=orient(*pt)
def tri(v,select):
 a=[];b=[];ids=[]
 for i,(_,vec,_) in v.items():
  if i not in select:continue
  normal=np.array([vec[1],-vec[0]]);a.append(normal);b.append(normal@en(projected[i]['position']));ids.append(i)
 xy=np.linalg.lstsq(np.array(a),b,rcond=None)[0];errs=np.array(a)@xy-b
 return dict(wgs84=ll(xy),along_source=float(xy@east),inward_source=float(xy@inward),residuals_m={i:round(float(x),3)for i,x in zip(ids,errs)},bearings={i:v[i][0]for i in ids})
for k in ['outer_w','inner_w','inner_e','outer_e','word_last']:
 points[k]=dict(same_day=tri(angles[k],{1,2,8}),cross_period=tri(angles[k],{1,2,8,11}))
def pair(t,p):return points[t][p]['along_source']
c='same_day';outerw,ow,oe,outere=[pair(k,c)for k in ('outer_w','inner_w','inner_e','outer_e')];along=(ow+oe)/2;offset=np.median([points[k][c]['inward_source']for k in ('outer_w','inner_w','inner_e','outer_e')]);ctr=ll(east*along+inward*offset)
heights={}
for i in (1,8):
 obs=en(projected[i]['position']);values={}
 for k,by in angles.items():
  if i not in by:continue
  _,vec,alt=by[i];distance=(offset-obs@inward)/(vec@inward);values[k]=distance*tan(alt)
 heights[i]={k:round(float(z-values['sill_ref']),3)for k,z in values.items()}
out=dict(order=328,origin=sw.tolist(),axis=east.tolist(),wgs84=ctr,signed_south_edge_west_to_axis_m=along,axis_inward_m=float(offset),runtime_heading_deg=(degrees(atan2(-east[1],east[0])))%360,exterior_bearing_deg=degrees(atan2(east[0],east[1]))+90,dimensions_m={'outer_width':outere-outerw,'clear_width':oe-ow,'cross_period_outer_width':pair('outer_e','cross_period')-pair('outer_w','cross_period'),'cross_period_clear_width':pair('inner_e','cross_period')-pair('inner_w','cross_period')},vertical_same_frame_difference_m=heights,points=points,stations=cam)
(P/'multi-station-portal.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(out['wgs84'],out['signed_south_edge_west_to_axis_m'],out['dimensions_m'],heights);print({k:tuple(round(r[c][s],3)for s in ('along_source','inward_source'))for k,r in points.items()})
