"""Render the two reconstructed street elevations; all graphics come from the model."""
from pathlib import Path
import argparse,json,struct,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont

root=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(root/'source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import load_triangles

def render(path):
    tri,material,names,asset=load_triangles(path)
    with path.open('rb')as f:
        f.seek(12);length,kind=struct.unpack('<II',f.read(8));doc=json.loads(f.read(length))
    colors=np.array([m.get('pbrMetallicRoughness',{}).get('baseColorFactor',[.4,.4,.4,1])[:3] for m in doc['materials']])
    colors=np.clip(np.where(colors<=.0031308,colors*12.92,1.055*colors**(1/2.4)-.055),0,1)
    # A slight eastern and upper offset exposes the glazing rebates and fascia returns.
    eye=np.array([37.,-90.,19.]);target=np.array([17.75,.0,5.7]);forward=target-eye;forward/=np.linalg.norm(forward)
    right=np.cross(forward,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,forward)
    cam=(tri-eye)@np.array([right,-up,forward]).T
    xy=cam[:,:,:2]/cam[:,:,2,None]*2360+[478,188]
    normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    norm=np.maximum(np.linalg.norm(normal,axis=1),1e-12)
    lighting=.77+.23*np.maximum(0,(normal@np.array([-.32,-.70,.64]))/norm)
    rgb=(np.clip(colors[material]*lighting[:,None],0,1)*255).astype('uint8')
    width,height=960,340
    depth=np.zeros((height,width),dtype=np.float32)
    pixels=np.empty((height,width,3),dtype=np.uint8);pixels[:]=(239,235,225)
    for i,points in enumerate(xy):
        x0,y0=np.maximum(np.floor(points.min(axis=0)),[0,0]).astype(int)
        x1,y1=np.minimum(np.ceil(points.max(axis=0)),[width-1,height-1]).astype(int)
        if x0>x1 or y0>y1:
            continue
        (ax,ay),(bx,by),(cx,cy)=points
        den=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
        if abs(den)<1.e-6:
            continue
        ix=np.arange(x0,x1+1)[None,:]+.5
        iy=np.arange(y0,y1+1)[:,None]+.5
        a=((by-cy)*(ix-cx)+(cx-bx)*(iy-cy))/den
        b=((cy-ay)*(ix-cx)+(ax-cx)*(iy-cy))/den
        c=1.-a-b
        inverse=a/cam[i,0,2]+b/cam[i,1,2]+c/cam[i,2,2]
        saved=depth[y0:y1+1,x0:x1+1]
        visible=(a>=0)&(b>=0)&(c>=0)&(inverse>saved)
        saved[visible]=inverse[visible]
        pixels[y0:y1+1,x0:x1+1][visible]=rgb[i]
    return Image.fromarray(pixels)

def font(size):
    return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',size)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('historic',type=Path);parser.add_argument('current',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args()
    page=Image.new('RGB',(1000,855),(251,250,246));d=ImageDraw.Draw(page)
    d.text((20,12),'Hengchang Li | South street facade',font=font(25),fill='#252723')
    for i,(path,title) in enumerate([(args.historic,'10 February 2018  |  Round-headed tower window and individual shop signs'),(args.current,'2021–22  |  Raised centre facade, silver fascias and separate roller shutters')]):
        y=55+i*383;d.text((22,y),title,font=font(18),fill='#42423d');page.paste(render(path),(20,y+31))
    d.text((22,825),'Same camera in both views. Exteriors follow Antigng (2018) and the January 2021 street survey.',font=font(14),fill='#4b4a44')
    page.save(args.output,'JPEG',quality=89,optimize=True)
if __name__=='__main__':main()
