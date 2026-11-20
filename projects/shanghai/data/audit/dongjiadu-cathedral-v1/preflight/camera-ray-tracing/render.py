from pathlib import Path
from PIL import Image,ImageDraw
import runpy,struct,math,json,numpy as np,sys
v=runpy.run_path('/tmp/dong64/camera/score.py');globals().update({k:x for k,x in v.items()if not k.startswith('_')})
def normals(mesh):
 n=np.cross(mesh[:,1]-mesh[:,0],mesh[:,2]-mesh[:,0]);return n/np.linalg.norm(n,axis=1).clip(1e-9)[:,None]
def convert(linear):
 return np.where(linear<=.0031308,12.92*linear,1.055*linear**(1/2.4)-.055)
model_norm=normals(model);city_norm=normals(city);dat=asset.read_bytes();n=struct.unpack_from('<I',dat,12)[0];j=json.loads(dat[20:20+n]);colors=convert(np.asarray([m.get('pbrMetallicRoughness',{}).get('baseColorFactor',[.55,.4,.25,1])[:3]for m in j['materials']]))
def image_pose(c,W,H,factor=.56):
 pd=c.get('padding',{});left=pd.get('left',0);right=pd.get('right',0);top=pd.get('top',0);bottom=pd.get('bottom',0);cx=(W+left-right)/2;cy=(H+top-bottom)/2;f=H*.5/math.tan(math.radians(36.87)/2)
 p,b=np.deg2rad([c['pitch'],c['bearing']]);F=np.array([np.sin(p)*np.sin(b),np.sin(p)*np.cos(b),-np.cos(p)]);R=np.array([np.cos(b),-np.sin(b),0]);U=np.cross(R,F);o=eye(c,W,H)
 ww,hh=round(W*factor),round(H*factor);xx,yy=np.meshgrid(np.arange(ww)+.5,np.arange(hh)+.5);rays=F+((xx.ravel()/factor-cx)/f)[:,None]*R+((cy-yy.ravel()/factor)/f)[:,None]*U;rays/=np.linalg.norm(rays,axis=1)[:,None]
 fg=cast(ms,o,rays);back=cast_city(o,rays);fi,bi=fg['primID'],back['primID'];land=(0-o[2])/rays[:,2];land[land<=0]=1e30
 shown=(fi>=0)&(fg['tfar']<np.minimum(back['tfar'],land)+.005);facade=np.zeros(len(fi),bool);frontFacing=np.zeros(len(fi),bool)
 hp=en_model(o+rays[shown]*fg['tfar'][shown,None]);facade[shown]=(hp[:,1]<3.5)&(hp[:,2]<13.6);frontFacing[shown]=facade[shown]&(np.abs(model_norm[fi[shown],2])<.65)
 bg=(~shown)&(bi>=0)&(back['tfar']<land+.1);rgb=np.tile([.865,.852,.802],(len(fi),1));sky=(~shown)&~bg&(rays[:,2]>=0);rgb[sky]=[.76,.86,.90]
 sun=np.array([-.35,-.69,.63]);sun/=np.linalg.norm(sun)
 def shade(normal,dirs):
  norm=np.where((normal*dirs).sum(1)[:,None]>0,-normal,normal);return (.76+.24*np.clip(norm@sun,-.4,1))
 shadeModel=shade(model_norm[fi[shown]],rays[shown]);rgb[shown]=colors[mt[fi[shown]]]*shadeModel[:,None]
 shadeCity=shade(city_norm[bi[bg]],rays[bg]);rgb[bg]=np.array([.64,.665,.675])[None,:]*shadeCity[:,None]
 return Image.fromarray((255*rgb.clip(0,1)).astype('u1').reshape(hh,ww,3)),{'whole':int(shown.sum()),'front':int(facade.sum()),'frontPlanar':int(frontFacing.sum()),'renderScale':factor}
def label(img,s1,s2):
 d=ImageDraw.Draw(img);d.rectangle((0,0,img.width,26),fill='#172529');d.text((5,0),s1,fill='white');d.text((5,13),s2,fill='#d6e4e4')
def montage(ims,name,n):
 w0,h0=ims[0].size;o=Image.new('RGB',(w0*n,h0*((len(ims)+n-1)//n)),(230,220,210))
 for i,im in enumerate(ims):o.paste(im,((i%n)*w0,(i//n)*h0))
 o.save(w/name)

poses=[];stats=[]
for kk in [(1,67),(1,60),(1,56),(51,48),(61,48),(61,44)]:
 t=next(t for t in opts if t['w']==870 and t['cam']['bearing']==kk[0] and t['cam']['pitch']==kk[1]);im,state=image_pose(t['cam'],t['w'],t['h'],.56);label(im,f'bearing {kk[0]}, pitch {kk[1]}',f"visible model pixels {state['whole']}");poses.append(im);stats.append([kk,state]);
montage(poses,'candidate-perspectives.jpg',2);print(stats)
