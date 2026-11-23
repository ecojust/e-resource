"""Compare ECUPL’s documented quadrangle and its western U-plan neighbour to two dated roof images."""
from pathlib import Path
import math, json, hashlib, gzip
from PIL import Image, ImageDraw
w=Path(__file__).parent
read=lambda p:json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
t=w/'frozen-14-13717-6694.json.gz'
features=json.loads(gzip.decompress(t.read_bytes()))['features']
owners={r['localId']:r for r in features}
r=owners[1840];ring=r['geometry']['coordinates'][0]
origin=tuple((ring[1][i]+ring[2][i])/2 for i in (0,1));dx=111319.490793*math.cos(math.radians(origin[1]));dy=110860
def delta(a,b):return((b[0]-a[0])*dx,(b[1]-a[1])*dy)
def geom(a,b):
 e,n=delta(a,b);return [math.hypot(e,n),math.degrees(math.atan2(e,n))%360]
ux,uy=delta(ring[2],ring[1]);length=math.hypot(ux,uy);ux/=length;uy/=length
def world(x,y):return [origin[0]+(ux*x-uy*y)/dx,origin[1]+(uy*x+ux*y)/dy]
def pixel(pt,m):
 n=2**m['zoom']*256;x,y=m['crop_global_pixel_origin'];return [(pt[0]+180)/360*n-x,(1-math.asinh(math.tan(math.radians(pt[1])))/math.pi)*n/2-y]
report={'feature_table_sha256':sha(t),'macro':'14-13717-6694','ground_origin':origin,'positive_x_true_bearing':geom(ring[2],ring[1])[1],'unit':'metres','frame':'Origin at the midpoint of the southern mapped wall, X east along that wall, Y towards the courtyard and river. Local true bearings use a WGS84 tangent-plane approximation.','owners':{},'dates':{}}
for k in (1840,1435,666,2173,320,2404,400):
 f=owners[k];geom0=f['geometry'];report['owners'][k]={'source':f['key'],'height':f['height'],'rings':geom0['coordinates'],'edges_m_and_bearing':[geom(a,b) for a,b in zip(geom0['coordinates'][0],geom0['coordinates'][0][1:])]}
# Same local grid from X=-35, Y=90, 0.25m per pixel. Resample imagery only for inspection.
for k in ('8432','3692'):
 m=read(w/f'release-{k}.json');im=Image.open(w/f'ortho-{k}.jpg')
 def src(i,j):return pixel(world(-35+i/4,90-j/4),m)
 a,b,c=src(0,0),src(1,0),src(0,1);aff=(b[0]-a[0],c[0]-a[0],a[0],b[1]-a[1],c[1]-a[1],a[1])
 rect=im.transform((280,404),Image.Transform.AFFINE,aff,resample=Image.Resampling.BICUBIC)
 p=ImageDraw.Draw(rect);p.line([(140-2*length,360),(140+2*length,360)],fill='#ecdc60',width=1);p.line([(140,354),(140,367)],fill='#f5dc6a',width=1)
 rect.save(w/f'local-{k}.jpg',quality=96)
 meta=m['metadata'][0]['records'][0];report['dates'][k]={'date':meta['SRC_DATE'],'imagery_pixel_m':meta['SRC_RES'],'source_absolute_accuracy_m':meta['SRC_ACC'],'local_img_transform':list(aff),'release_url':m['release']['itemURL'],'source':meta['NICE_DESC'],'manifest_sha256':sha(w/f'release-{k}.json')}
picks={
 '8432': {'south_outer_eaves': [[46,365],[229,366]],'south_ridge':[[62,335],[207,335]],'clock_roof_axis':[[137,344],[136,313]], 'south_court_between_inner_eaves':[[96,233],[178,232]],'south_court_longitudinal':[[135,193],[136,305]],'middle_cross_roof_ridge':[[69,161],[206,162]], 'north_outer_eaves':[[56,54],[219,50]]},
 '3692': {'south_outer_eaves': [[53,354],[232,349]],'south_ridge':[[66,325],[216,322]],'clock_roof_axis':[[137,342],[136,304]],'south_court_between_inner_eaves':[[100,217],[184,218]],'south_court_longitudinal':[[134,177],[134,294]],'middle_cross_roof_ridge':[[66,148],[214,146]],'north_outer_eaves':[[52,33],[223,29]]}}
for name,pp in picks.items():
 metrics={}
 for elem,pts in pp.items():
  local=[[-35+u/4,90-v/4] for u,v in pts];wgs=[world(*r) for r in local]
  metrics[elem]={'image_xy':pts,'local_xy_m':local,'wgs84':wgs,'length_m':geom(*wgs)[0]}
 report['dates'][name]['observed_controls']=metrics
report['identity']={'institution':'https://www.ecupl.edu.cn/2022/1101/c13514a193944/page.htm','municipal_page':read(w.parent/'research/district.json')['url'],'institutional_aerial':'school-02','main_hall_source_id':1840,'nearby_west_U_Siyan_40':1435,'clock_identity':'The clock projects from the central bay of the southern roof. The same oblique shows the courtyard and north cross-wing behind it and a separate U-plan classroom at left. Its source geometry is a single rectangular area with no inner ring or separate tower primitive.','limits':'Orthophoto eaves and apparent clock-roof midline are measured above ground. The two dates give source accuracy 8.47 m and show different parallax, seasonal tree cover and resampling; historic aerial control establishes the identity and side of the clock, not the ground elevation or detailed tower sides. Southern and northern cross-roofs survive in both images. The absolute roof-to-ground displacement cannot be inferred solely from either image.','model_scope':'A frontage or partial courtyard study must retain the city owner. A possible complete replacement would need intact north and side wings, verified roof/ground clearance and the actual near and distant owner mesh.'}
(w/'quadrangle.json').write_text(json.dumps(report,indent=2)+'\n')
