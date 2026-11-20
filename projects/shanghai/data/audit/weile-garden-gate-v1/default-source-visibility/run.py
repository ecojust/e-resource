from pathlib import Path
import sys,subprocess,json,math,ctypes as ct,gzip,os
import numpy as np
import shapely as shp
from shapely.geometry import shape
from PIL import Image,ImageDraw
root=Path(__file__).parent;read=lambda f:json.loads(f.read_bytes());R=6371008.8;rad=np.pi/180
p=Path('/workspace/e-resource/projects/shanghai')
so=ct.CDLL(str(root/'raster.so'));pd=ct.c_void_p;so.draw.argtypes=[ct.c_int,ct.c_int,ct.c_double,ct.c_double,ct.c_double,ct.c_int,pd,pd,pd,pd,ct.c_int,pd,pd]
def rig(n):
 spec=read(root/f'{n}-decode.json');place=read(root/f'{n}-place.json');cam=root/f'{n}-camera.mjs';work=Path('/tmp/weile164/placement');audit=p/'data/audit/weile-garden-gate-v1'
 lng,lat=spec['anchor'];k=R*np.cos(lat*rad);h=place['heading']*rad;axes=np.array([[np.cos(h),-np.sin(h)],[np.sin(h),np.cos(h)]])
 def enu(q):return np.c_[(q[:,0]-lng)*rad*k,(np.arcsinh(np.tan(q[:,1]*rad))-np.arcsinh(np.tan(lat*rad)))*k]
 def local(q):
  q=np.array(q).copy();q[...,:2]=q[...,:2]@axes;return q
 props=read(work/'delivered-decode.json')
 def trimesh(role):
  arr=np.frombuffer(gzip.decompress((work/f'delivered-{role}-triangles.f64.reproducible.gz').read_bytes()),'float64').reshape(-1,3,3)
  return local(arr[:,:,[0,2,1]]*np.array([1.,-1,1])),np.fromfile(work/f'delivered-{role}-materials.u16','<u2').astype('int32')+10000
 wanted={j for g in spec['files']for j in g.get('ids',[])}
 nearby={f['localId']:shp.transform(shape(f['geometry']),enu) for f in json.loads(gzip.decompress((work/'feature-table.json.gz').read_bytes()))['features']if f['localId'] in wanted}
 owners={o['feature_local_id']for o in place.get('owners',[])}
 mask=enu(np.array(place['replacement_geometry']['coordinates'][0][:-1]))if place.get('replacement_geometry') else np.empty((0,2))
 rows={v:[]for v in ['near','far']};labs={v:[]for v in rows}
 for i,g in enumerate(spec['files']):
  a=np.frombuffer(gzip.decompress((root/f'{n}-{i}.f32.gz').read_bytes()),'<f4').reshape(-1,10);vs=np.array(a[:,:9].reshape(-1,3,3),dtype='float64');ids=a[:,9].astype('int32')
  if not len(a):continue
  if g['kind']=='near':
   ids1=np.array([i for i in g['ids']if i in nearby],dtype='int32')
   if not ids1.size:continue
   tree=shp.STRtree([nearby[j]for j in ids1]);ids=ids1[tree.nearest(shp.points(vs[:,:,:2].mean(1)))]
  rows[g['kind']].append(vs);labs[g['kind']].append(ids)
 caps=place.get('source_section_caps')
 if caps:
  for line in caps['geometry']['coordinates']:
   (a,b)=enu(np.array(line));v=np.array([[*a,caps['base_m']],[*b,caps['base_m']],[*b,caps['roof_m']],[*a,caps['roof_m']]])
   for l in rows:rows[l].append(v[[0,1,2,0,2,3]].reshape(2,3,3));labs[l].append(np.full(2,9999,dtype='int32'))
 context={l:(np.concatenate(rows[l]),np.concatenate(labs[l]))for l in rows}

 ob=read(audit/'visible-surfaces.json')['variants']
 matching=next(row['rays'] for row in ob if row['variant']=='web')
 parts={'left pier masonry','right pier masonry','green 120 plaque','mid arch ceramic ring','west roughcast shoulder','central scallop fluting','left pendant grape','right pendant grape','left side wall panel','upper curved wall below coping'}
 points=[]
 for s in matching:
  if s['feature'] in parts and s['first_depth_m'] is not None:
   x,z=s['coordinates_m'];points.append((s['feature'],local([x,s['first_depth_m'],z]).tolist()))
 assert len(points)==len(parts)
 vp=[('desktop',870,660,[316,88,154,241]),('phone',390,844,[16,65,182,228]),('wide',1280,800,[350,88,154,233])]
 cur=place['overviewBearing']
 configs=[('default',cur,place['overviewPitch']),('from west',cur+18,49),('from east',cur-18,49),('raised',cur,31),('close from west',cur+14,35),('close from east',cur-14,35)]
 def jobcfg(label,b,pi,nm,w,hh,pads):
  return {'label':label,'viewport':nm,'place':{**place,'city_integration':True,'overviewBearing':b,'overviewPitch':pi},'v':{'width':w,'height':hh,'insets':dict(zip(['left','right','top','bottom'],pads))}}
 requests=[jobcfg(*cfg,*v)for cfg in configs for v in vp]
 run="""import fs from 'node:fs';import{pathToFileURL}from'node:url';const {candidateOverviewCamera}=await import(pathToFileURL(process.argv[1]));console.log(JSON.stringify(JSON.parse(fs.readFileSync(0)).map(x=>candidateOverviewCamera(x.place,x.v))));"""
 cameras=json.loads(subprocess.check_output(['node','--input-type=module','-e',run,cam],input=json.dumps(requests).encode()))
 res=[]
 for req,c in zip(requests,cameras):
  w=req['v']['width'];hh=req['v']['height'];pa=c['padding'];f=hh/(2*np.tan(36.87*rad/2));dist=f*2*np.pi*R*np.cos(c['center'][1]*rad)/(512*2**c['zoom']);b=c['bearing']*rad;pitch=c['pitch']*rad
  r=np.array([np.cos(b),-np.sin(b),0]);up=np.array([np.sin(b)*np.cos(pitch),np.cos(b)*np.cos(pitch),np.sin(pitch)]);fw=np.array([np.sin(b)*np.sin(pitch),np.cos(b)*np.sin(pitch),-np.cos(pitch)])
  eye=np.r_[enu(np.array([c['center']]))[0],c['elevation']]-fw*dist;mat=np.array([r,up,fw]).T;cx=(w+pa['left']-pa['right'])/2;cy=(hh+pa['top']-pa['bottom'])/2
  def draw(vs,labels,cd=None,source=False):
   transformed=np.ascontiguousarray(np.concatenate(((vs-eye)@mat,vs[:,:,:2]),2));clips=np.isin(labels,list(owners)).astype('int32') if source else np.zeros(len(vs),'int32');labels=np.ascontiguousarray(labels,'int32');m=np.ascontiguousarray(mask);
   if cd is None:color=np.zeros((hh,w),'int32');depth=np.zeros((hh,w),'float32')
   else:color,depth=cd
   so.draw(w,hh,cx,cy,f,len(vs),transformed.ctypes.data,labels.ctypes.data,clips.ctypes.data,m.ctypes.data,len(mask),depth.ctypes.data,color.ctypes.data)
   return color,depth
  row=dict(pose=req['label'],viewport=req['viewport'],size=[w,hh],camera=c,eye_enu=eye.tolist(),tested={})
  for context_role,asset_role in [('near','web'),('far','lod')]:
   asset,materials=trimesh(asset_role);isol,dist0=draw(asset,materials);ctx,ctxdepth=draw(*context[context_role],source=True);combined=isol.copy();zcomb=dist0.copy();closer=ctxdepth>dist0+1e-8;combined[closer]=ctx[closer];zcomb[closer]=ctxdepth[closer]
   target=isol>=10000;visible=combined>=10000;usable=np.zeros_like(target);usable[pa['top']:hh-pa['bottom'],pa['left']:w-pa['right']]=True
   py,px=np.nonzero(visible&usable);block,counts=np.unique(ctx[target&closer&usable],return_counts=True);probes=[]
   for name,xyz in points:
    u,v,z=(np.array(xyz)-eye)@mat;xx=cx+u*f/z;yy=cy-v*f/z;ix,iy=int(xx),int(yy)
    if 0<=ix<w and 0<=iy<hh:owner=int(ctx[iy,ix]);front=0 if ctxdepth[iy,ix]==0 else float(1/ctxdepth[iy,ix]);blocked=bool(front and front<z-.08)
    else:owner=-1;front=0;blocked=True
    probes.append(dict(feature=name,xy_px=[round(xx,1),round(yy,1)],in_view=bool(pa['left']<=xx<w-pa['right']and pa['top']<=yy<hh-pa['bottom']),blocked_by=owner if blocked else None))
   denom=np.sum(target&usable);metrics=dict(isolated_pixels_in_ui=int(denom),selected_visible_pixels=int(len(px)),visible_percent=round(100*len(px)/denom,2)if denom else 0,visible_bounds=[int(px.min()),int(py.min()),int(px.max()),int(py.max())]if len(px)else None,occluding_owners={int(i):int(k)for i,k in zip(block,counts)},clear_witnesses=sum(q['in_view']and q['blocked_by']is None for q in probes),witnesses=probes)
   row['tested'][context_role]=metrics
   if context_role=='near' and req['viewport']!='wide':
    palette=[[211,186,144],[106,87,72],[139,107,86],[224,205,166],[78,67,57],[64,71,72],[161,153,141],[95,104,112],[157,137,103],[103,116,107],[75,69,68],[183,171,148],[219,209,191],[77,76,80]]
    img=np.zeros((hh,w,3),dtype='uint8');img[:]=[235,241,243];contextpix=(combined>0)&(combined<10000);val=combined[contextpix];img[contextpix]=np.stack([142+val%24,153+val%19,162+val%16],axis=1)
    for i,co in enumerate(palette):img[combined==10000+i]=co
    img[target&closer]=[162,79,93];im=Image.fromarray(img);d=ImageDraw.Draw(im);d.rectangle((pa['left'],pa['top'],w-pa['right'],hh-pa['bottom']),outline='#334954');d.text((10,10),f"{n} {req['label']} {req['viewport']}  {metrics['visible_percent']}% geometry visible",fill='#122432')
    im.save(root/f"{n}-{req['label']}-{req['viewport']}.png",optimize=False)
  res.append(row)
  if req['label']=='default':print(n,req['label'],req['viewport'],[(k,v['visible_percent'],v['clear_witnesses'],v['occluding_owners'])for k,v in row['tested'].items()],flush=True)
 out=dict(order=n,registered_camera_module_sha256=spec['camera_sha256'],catalog_sha256=spec['catalog_sha256'],near_triangles=len(context['near'][0]),far_triangles=len(context['far'][0]),near_groups=len(spec['files'])-1,selected_materials=props[1]['material_names'],poses=res)
 (root/f'{n}-pixels.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
for n in [int(v)for v in sys.argv[1:]]:rig(n)
