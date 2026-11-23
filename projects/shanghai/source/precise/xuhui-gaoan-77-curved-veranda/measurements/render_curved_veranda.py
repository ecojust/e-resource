from pathlib import Path
import argparse,json,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
M=Path(__file__).resolve().parent;S=M.parent
parser=argparse.ArgumentParser(description='Render the actual mesh from three registered published views using a depth buffer.');parser.add_argument('mesh',type=Path);parser.add_argument('output',type=Path);parser.add_argument('--layout',type=Path);args=parser.parse_args()
sys.path.insert(0,str(M));from check_curved_veranda import camera_in_metres,settings,SerialScene
sys.path.insert(0,str(S/'source'));from curved_veranda import PALETTE
s=json.loads((M/'curved-veranda-folded-roof.json').read_text())['stations'];g=SerialScene(args.mesh);c=[]
for mat in g.materials:
 lin=np.array(PALETTE.get(mat,{'color':[.62,.59,.52]})['color']); c.append(255*np.where(lin<.00313,12.92*lin,1.055*lin**(1/2.4)-.055))
f=lambda n:ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',n)
out=Image.new('RGB',(1430,570),'#f7f4ec');draw=ImageDraw.Draw(out);ink='#342e2b'
draw.text((28,18),'高安路77号  /  折檐、弧台与木拱',font=f(33),fill=ink)
draw.text((30,65),'同一近景模型按三张公开照片的机位绘制。细圈为铁栏实心构件，天蓝为模型外部。',font=f(19),fill=ink)
for i,(k,sub) in enumerate([('paper-25','2022年资料图25'),('sina-37','高参  /  图37'),('sina-35','高参  /  图35')]):
 p=settings(json.loads(args.layout.read_text()) if args.layout else None);P,eye=camera_in_metres(s[k],p);v=g.tri;x=v@P[:,:3].T+P[:,3];depth=x[:,:,2];uv=x[:,:,:2]/x[:,:,2:]
 lo=uv.min(axis=(0,1));hi=uv.max(axis=(0,1));span=hi-lo;fac=min(430/span[0],365/span[1]);offset=np.array([(455-span[0]*fac)/2,(395-span[1]*fac)/2]); uv=(uv-lo)*fac+offset
 pixels=np.full((395,455,3),(220,232,233),dtype='uint8');buffer=np.full((395,455),-np.inf);norm=g.cross/np.maximum(1e-12,np.linalg.norm(g.cross,axis=1,keepdims=True));light=np.array([-.45,-.58,.68]); shade=np.clip(.77+.23*(norm@light),.60,1.06)
 for j in np.argsort(-depth.mean(axis=1)):
  xy=uv[j]
  left,top=np.maximum([0,0],np.floor(xy.min(axis=0)).astype(int));right,base=np.minimum([455,395],np.ceil(xy.max(axis=0)).astype(int)+1)
  if right<=left or base<=top:continue
  a,b,c0=xy;den=(b[1]-c0[1])*(a[0]-c0[0])+(c0[0]-b[0])*(a[1]-c0[1])
  if abs(den)<1e-8:continue
  yy,xx=np.ogrid[top:base,left:right];xx=xx+.5;yy=yy+.5
  w0=((b[1]-c0[1])*(xx-c0[0])+(c0[0]-b[0])*(yy-c0[1]))/den
  w1=((c0[1]-a[1])*(xx-c0[0])+(a[0]-c0[0])*(yy-c0[1]))/den;w2=1-w0-w1
  z=w0/depth[j,0]+w1/depth[j,1]+w2/depth[j,2];buf=buffer[top:base,left:right]
  sel=(w0>=0)&(w1>=0)&(w2>=0)&(z>buf)
  if sel.any():
   buf[sel]=z[sel];pixels[top:base,left:right][sel]=np.clip(np.array(c[g.mi[j]])*shade[j],0,255)
 img=Image.fromarray(pixels)
 out.paste(img,(20+475*i,112));draw.text((22+475*i,519),sub,font=f(23),fill=ink)
out.save(args.output,quality=89,optimize=True)
