"""Draw an original orthographic plate of the modeled crown sash and recessed panels."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image,ImageDraw,ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import load_triangles

PAPER = (244,242,234)
COLORS = {
    'Tanggu windows | weathered frame':(87,84,73),
    'Tanggu windows | painted glazing bars':(78,85,83),
    'Tanggu windows | pale glass':(167,182,183),
    'Tanggu windows | shaded glass':(89,98,94),
    'Tanggu shades | faded canvas':(105,101,92),
    'Tanggu shades | pale stitched hem':(174,165,143),
    'Tanggu shades | bound side seam':(109,105,93),
    'Tanggu panels | warm brick return':(146,91,62),
    'Tanggu panels | inset brickwork':(171,116,80),
}


def paint(tri, mids, labels, size, axis):
    direction=np.asarray(axis, float)
    direction/=np.linalg.norm(direction)
    side=np.cross(direction,[0,0,1]);side/=np.linalg.norm(side)
    up=np.cross(side,direction)
    screen=tri@np.stack([side,-up,direction],axis=1)
    low,high=screen[:,:,:2].min(axis=(0,1)),screen[:,:,:2].max(axis=(0,1))
    width,height=size
    zoom=min((width-12)/(high[0]-low[0]),(height-12)/(high[1]-low[1]))
    screen[:,:,:2]=(screen[:,:,:2]-(high+low)/2)*zoom+[width/2,height/2]
    p=np.full((height,width,3),PAPER,dtype=np.uint8);depth=np.full((height,width),np.inf)
    light=np.array([-.42,-.65,.63]);light/=np.linalg.norm(light)
    for t, world, material in zip(screen,tri,mids):
        normal=np.cross(world[1]-world[0],world[2]-world[0])
        if normal@direction>=0: continue
        color=COLORS[labels[material]]
        n=normal/np.linalg.norm(normal)
        col=np.clip(np.asarray(color)*(.70+.30*max(0.,n@light)),0,255)
        verts=t[:,:2];i,j=np.maximum(0,np.floor(verts.min(axis=0)).astype(int))
        k,l=np.minimum([width,height],np.ceil(verts.max(axis=0)).astype(int)+1)
        if i>=k or j>=l:continue
        yy,xx=np.ogrid[j:l,i:k]
        x0,y0=t[0,:2];x1,y1=t[1,:2];x2,y2=t[2,:2]
        den=(x1-x0)*(y2-y0)-(x2-x0)*(y1-y0)
        if abs(den)<1e-9:continue
        a=((xx+.5-x0)*(y2-y0)-(x2-x0)*(yy+.5-y0))/den
        b=((x1-x0)*(yy+.5-y0)-(xx+.5-x0)*(y1-y0))/den
        z=t[0,2]+a*(t[1,2]-t[0,2])+b*(t[2,2]-t[0,2])
        good=(a>=0)&(b>=0)&(a+b<=1)&(z<depth[j:l,i:k])
        depth[j:l,i:k][good]=z[good]
        p[j:l,i:k][good]=col
    return Image.fromarray(p)


def font(size, bold=False):
    style='Bold' if bold else 'Regular'
    return ImageFont.truetype(f'/usr/share/fonts/opentype/noto/NotoSansCJK-{style}.ttc',size,index=2)


def plate(model,layout,dest):
    tri,mid,labels,asset=load_triangles(model)
    chosen=np.isin(mid,[i for i,name in enumerate(labels) if name in COLORS])
    tri,mid=tri[chosen],mid[chosen]
    if len(set(mid))!=len(COLORS):
        raise ValueError('An expected curtain, frame, glass or brick material is absent')
    sheet=Image.new('RGB',(1410,930),PAPER)
    d=ImageDraw.Draw(sheet)
    def text(x,y,msg,s=19,bold=False,fill='#393d35'):
        d.text((x,y),msg,font=font(s,bold),fill=fill)
    def render(t,m,size,axis):
        return paint(t,m,labels,(2*size[0],2*size[1]),axis).resize(size,Image.Resampling.LANCZOS)
    text(52,28,'纪年匾下的四窗与浅凹砖板',42,True)
    text(54,91,'2015年历史建筑报道与建筑史旧影所见形制。图示采用匾宽统一的展示比例。',22)
    sheet.paste(render(tri,mid,(1300,382),(0,1,0)),(55,136))
    d.line((56,534,1354,534),fill='#bfbdac',width=2)
    xcentre=tri[:,:,0].mean(axis=1)
    select=[xcentre<(layout['openings'][0]['x1']+layout['openings'][1]['x0'])*.5,
            (xcentre>layout['openings'][2]['x0']-.012)&(xcentre<layout['openings'][2]['x1']+.012),
            np.isin(mid,[labels.index(k) for k in COLORS if k.startswith('Tanggu panels')])&(xcentre>layout['openings'][3]['x0']-.01)]
    for i,(sel,title,caption) in enumerate(zip(select,['曲篷侧面','右侧明窗','浅凹砖板'],
        ['独立端布、弧形篷面与浅色波边。','四列六行，第二道横梃更粗。','四边有窄口，板心退入墙面。'])):
        x=57+450*i
        # Isolate only the sash under study in the first two enlarged details.
        if i<2:
            sel &= ~np.isin(mid,[labels.index(k) for k in COLORS if k.startswith('Tanggu panels')])
        sheet.paste(render(tri[sel],mid[sel],(408,235),(.56,1,-.22) if i!=1 else (0,1,0)),(x,552))
        text(x,794,title,23,True)
        text(x,839,caption,18)
    text(56,890,'原创建模图　窗篷遮住左二窗上端，其框头采用展示推定。窗框退深、篷布出挑和砖板进退为展示取值。',16,fill='#616659')
    sheet.save(dest,quality=91,optimize=True,subsampling=0)
    digest=hashlib.sha256(dest.read_bytes()).hexdigest()
    record={'image':dest.name,'sha256':digest,'model_sha256':asset['sha256'],
        'source':'Orthographic and oblique projections of the exported editable mesh, with triangle depth ordering.',
        'scale':'The display scale is relative to the width of the date cartouche.',
        'rights':'Original diagram generated from project geometry. MIT.'}
    dest.with_suffix('.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print(digest)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('model',type=Path)
    parser.add_argument('layout',type=Path)
    parser.add_argument('image',type=Path)
    args=parser.parse_args()
    plate(args.model,json.loads(args.layout.read_bytes()),args.image)
