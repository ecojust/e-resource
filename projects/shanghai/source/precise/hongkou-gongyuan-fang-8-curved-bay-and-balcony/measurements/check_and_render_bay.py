from pathlib import Path
import argparse,json,hashlib,sys
import numpy as np
from PIL import Image, ImageFont, ImageDraw
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'),str(HERE.parents[1]/'jingan-jkk-apartments-changle-street-front/measurements')]
from glb_triangles import load_triangles,material_appearance
from render_central_steel_views import draw_mesh
materials={'brick':['Brick','mortar'],'head':['cast concrete'],'window':['daylight','sash'],'back':['daylight','glazing','Retired'],'band':['cast concrete','Rose-toned'],'iron':['Painted dark metal'],'eave':['Weathered fascia']}
def read_mesh(p):
 t,mi,n,h=load_triangles(p);mat=material_appearance(p)['materials'];rgba=np.asarray([mat[k]['baseColorFactor'] for k in n]);blends=np.array([mat[k].get('alphaMode','')=='BLEND' for k in n])
 return t,mi,n,h,rgba,blends
def checks(p):
 t,mi,n,sign,_,_=read_mesh(p);a=t[:,0];e=t[:,1]-a;f=t[:,2]-a;obs=json.loads((HERE/'original-pixels.json').read_bytes());fit=json.loads((HERE/'bay-camera-fit.json').read_bytes());rows=[]
 for label,cam in fit['cameras'].items():
  m=np.asarray(cam['P']);inv=np.linalg.inv(m[:,:3]);eye=-inv@m[:,3];q=eye-a;cr=np.cross(q,e);dot=np.einsum('ij,ij->i',cr,f)
  def hit(uv):
   r=inv@[*uv,1];r/=np.linalg.norm(r);h=np.cross(r,f);det=np.einsum('ij,ij->i',e,h);ok=np.abs(det)>1e-10;dv=np.where(ok,det,1);u=np.einsum('ij,ij->i',q,h)/dv;v=cr@r/dv;dd=dot/dv
   cand=np.where(ok&(u>=0)&(v>=0)&(u+v<=1)&(dd>0))[0];return n[mi[cand[np.argmin(dd[cand])]]] if len(cand)else None
  # The thin metal strips are close to the native pixel size. Record how far
  # a real first-surface ray moves before it intersects metal, keeping the original pass flag.
  for target,pts in obs[label].items():
   for uv in pts:
    material=hit(uv);good=bool(material and any(s in material for s in materials[target]))
    row={'view':label,'expected':target,'photo_pixel':uv,'first_surface':material,'passed':good}
    if target=='iron':
     offsets=sorted((dx*dx+dy*dy,dx,dy)for dx in range(-6,7)for dy in range(-6,7)if dx*dx+dy*dy<=36)
     nearest=next(((d,dx,dy) for d,dx,dy in offsets if hit([uv[0]+dx,uv[1]+dy])=='Painted dark metal'),None)
     row['nearest_visible_iron_pixel']=([uv[0]+nearest[1],uv[1]+nearest[2]] if nearest else None)
     row['nearest_offset_px']=(round(nearest[0]**.5,3) if nearest else None)
    rows.append(row)
 return dict(asset_sha256=sign,triangles=len(t),rays=rows,counts={k:{'passed':sum(i['passed'] for i in rows if i['view']==k),'tested':sum(1 for i in rows if i['view']==k)}for k in fit['cameras']})
def board(p,out):
 t,mi,n,h,rgba,blends=read_mesh(p);fit=json.loads((HERE/'bay-camera-fit.json').read_bytes())
 bg=Image.new('RGB',(1400,870),'#f1eee7');d=ImageDraw.Draw(bg)
 def text(x,y,s,z):d.text((x,y),s,font=ImageFont.truetype('NotoSerifCJK-Regular.ttc',z,index=2),fill='#293d43')
 text(38,26,'公园坊8号 · 弧窗与退台阳台',37)
 text(38,84,'二层三扇红色窗框沿弧形砖墙排列，三层曲栏位于直线玻璃窗前。',21)
 stats={}
 for j,(name,a)in enumerate(fit['cameras'].items()):
  # The crops isolate the two upper storeys in the source frames.
  b=[258,63,575,439] if j==0 else [219,65,396,332]
  x0,y0,x1,y1=b;scale=min(600/(x1-x0),553/(y1-y0))
  screen=np.array([[scale,0,-scale*x0+18],[0,scale,-scale*y0+18],[0,0,1.]])@np.asarray(a['P'])
  im,metrics=draw_mesh((t,mi,rgba,blends),screen,{},(655,600),'all');bg.paste(im,(37+j*684,135));stats[name]=metrics
  text(40+j*684,743,'图07机位 · 门牌题作8号' if j==0 else '图08机位 · 同户斜视',22)
 text(40,818,'原照刊于2019年。模型示意可见外部构件；被遮住的栏饰间距和窗后进深依两图估算。',19)
 bg.save(out,quality=91,subsampling=0);return dict(asset_sha256=h,photo_pixels_embedded=False,plate_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),views=stats)
if __name__=='__main__':
 pa=argparse.ArgumentParser();pa.add_argument('asset',type=Path);pa.add_argument('output',type=Path);pa.add_argument('--board',type=Path);args=pa.parse_args()
 report=checks(args.asset)
 if args.board:report['board']=board(args.asset,args.board)
 args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(report['counts'])
