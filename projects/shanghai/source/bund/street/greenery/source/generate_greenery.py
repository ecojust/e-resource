"""Offline ground-plane placement from frozen OSM bed corners and 2010 photo controls.
All tree locations/heights are reconstruction estimates. No live requests.
"""
from pathlib import Path
import argparse, hashlib, json, math, random
import numpy as np
from shapely.geometry import Polygon, Point
P=Path(__file__).resolve().parent
R=6378137; ORIGIN=(121.4862,31.2385); SCALE=math.cos(math.radians(ORIGIN[1])); Y0=math.asinh(math.tan(math.radians(ORIGIN[1])))
def metric(lon,lat): return [R*math.radians(lon-ORIGIN[0])*SCALE, -R*(math.asinh(math.tan(math.radians(lat)))-Y0)*SCALE]
def geographic(x,z): return [ORIGIN[0]+math.degrees(x/(R*SCALE)),math.degrees(math.atan(math.sinh(Y0-z/(R*SCALE))))]
def homography(src,dst):
 A=[];B=[]
 for (x,y),(u,v) in zip(src,dst):
  A.extend([[x,y,1,0,0,0,-x*u,-y*u],[0,0,0,x,y,1,-x*v,-y*v]]);B.extend([u,v])
 return np.r_[np.linalg.solve(np.array(A),np.array(B)),1.].reshape(3,3)
def project(H,p):
 q=H@np.r_[p,1.];return (q[:2]/q[2]).tolist()
def run(output):
 output.mkdir(parents=True,exist_ok=True)
 evidence=json.loads((P/'planting-evidence.json').read_text());controls=json.loads((P/'photo-controls.json').read_text())
 photo=P/controls['photo'];assert hashlib.sha256(photo.read_bytes()).hexdigest()==controls['photo_sha256']
 data={'version':'bund-greenery-v4.5-photo-2010','anchor':list(ORIGIN),'units':'metres, X east Y up Z south','capture_date':'2010-09-18','reconstruction_is_current_survey':False,'photo_controls':'photo-controls.json','trees':[],'beds':[],'grass':[],'validation':{'passed':False},'disclaimer_zh':'2010年公开照片推定的外滩17/18号对面绿化。树位、株高及枝叶为照片比例估计，部分树根被遮挡；不表示2026年精测现状。'}
 audits=[];rng=random.Random(17018045)
 for bed in controls['beds']:
  coordinates=evidence['beds'][bed['source_key']]['coordinates_wgs84']; local=[metric(*a) for a in coordinates];poly=Polygon(local);inner=poly.buffer(-.18,join_style=2)
  H=homography(bed['corners_px'],local);roots=[]
  for index,tree in enumerate(bed['trees']):
   x,z=project(H,tree['root_px']);assert inner.contains(Point(x,z)),(tree['id'],x,z)
   uncertainty=[]
   for _ in range(600):
    corners=np.array(bed['corners_px'])+np.array([[rng.uniform(-3,3),rng.uniform(-3,3)] for _ in range(4)])
    root=np.array(tree['root_px'])+np.array([rng.uniform(-v,v) for v in tree['root_uncertainty_px']])
    try: uncertainty.append(project(homography(corners,local),root))
    except np.linalg.LinAlgError:pass
   delta=np.array(uncertainty)-[x,z];radii=np.linalg.norm(delta,axis=1)
   record={**tree,'bed':bed['id'],'x':x,'z':z,'lng':geographic(x,z)[0],'lat':geographic(x,z)[1],'ground_altitude_m':.09,'seed':170180+len(data['trees'])*963,'support_radius_m':.85,'support_top_m':2.25,'root_to_inner_edge_m':inner.boundary.distance(Point(x,z)),'manual_control_sensitivity_95_m':float(np.percentile(radii,95)),'sensitivity_note':'Monte Carlo perturbation of manually estimated pixel marks; model sensitivity, not confidence interval of real-world position.'}
   data['trees'].append(record);roots.append(record)
  grass=[];minx,minz,maxx,maxz=inner.bounds
  for _ in range(round(inner.area*30)):
   for trial in range(100):
    x=rng.uniform(minx,maxx);z=rng.uniform(minz,maxz)
    if inner.buffer(-.09).contains(Point(x,z)) and all(math.hypot(x-t['x'],z-t['z'])>.24 for t in roots):break
   else: continue
   grass.append([round(x,4),round(z,4),round(rng.random()*math.tau,4),round(rng.uniform(.65,1.25),4),bed['id']])
  data['grass'].extend(grass)
  data['beds'].append({'id':bed['id'],'coordinates_wgs84':coordinates,'local_outer':local,'local_inside':list(map(list,inner.exterior.coords))[:-1],'grass_instances':len(grass),'grass_base_m':.09,'grass_blade_height_estimate_m':[.025,.075]})
  audits.append({'id':bed['id'],'homography_image_to_ground':H.tolist(),'four_control_fit_max_m':max(np.linalg.norm(np.array(project(H,p))-q) for p,q in zip(bed['corners_px'],local)),'independent_reprojection_check':False,'corners_exact_from_frozen_osm':True,'all_root_centres_inside_grass':True,'area_m2':poly.area,'support_base_all_inside_grass':all(inner.contains(Point(t['x'],t['z']).buffer(t['support_radius_m']+.045)) for t in roots)})
 assert all(a['support_base_all_inside_grass'] for a in audits),audits
 data['validation']={'passed':True,'scope':'Base trunk, all support feet and grass mesh envelopes remain in the two frozen grass interiors; canopies may overhang as real trees do. Existing street geometry untouched.','trees':len(data['trees']),'added_shrubs':0,'added_unlocated_trees':0,'beds':audits,'source_sha256':{f:hashlib.sha256((P/f).read_bytes()).hexdigest() for f in ['photo-controls.json','planting-evidence.json']}}
 (output/'greenery-v4.5.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 # Overlay uses an unmodified external reference image; markings are separate SVG shapes.
 svg=['<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="2450 2280 1250 470"><image x="0" y="0" width="4752" height="3168" xlink:href="../references/aerial-2010-original.jpg"/>']
 for bed in controls['beds']:
  svg.append('<polygon points="'+' '.join(f'{x},{y}' for x,y in bed['corners_px'])+'" fill="none" stroke="#00eaff" stroke-width="2"/>')
  for t in bed['trees']:
   x,y=t['root_px'];color='#ffe24b' if t['root_uncertainty_px'][0]>3 else '#50ff86'
   svg.append(f'<circle cx="{x}" cy="{y}" r="4" stroke="black" fill="{color}"/><path d="M{x},{y} L{x},{y+70}" stroke="{color}"/><text x="{x-25}" y="{y+85}" font-size="14" stroke="black" stroke-width=".4" fill="{color}">{t["id"]}</text>')
 svg.append('</svg>');(output/'photo-controls-overlay.svg').write_text(''.join(svg))
 print(json.dumps({'passed':True,'trees':len(data['trees']),'grass_clumps':len(data['grass']),'sensitivity_95_m':{t['id']:round(t['manual_control_sensitivity_95_m'],2) for t in data['trees']}}))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=P.parent/'data');args=parser.parse_args();run(args.output)
