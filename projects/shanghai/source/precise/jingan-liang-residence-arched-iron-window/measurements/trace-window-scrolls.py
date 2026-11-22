"""Digitise the two wrought-iron grilles on the named 61 photograph at a fixed rectification scale."""
import hashlib,json,os
from pathlib import Path
from collections import defaultdict
import numpy as np
from PIL import Image
from scipy import ndimage as nd
from shapely.geometry import LineString

HERE=Path(__file__).resolve().parent
PHOTO=Path(os.environ.get('LIANG_WINDOW_PHOTO',HERE.parent/'61-window.jpg'))
C=json.loads((HERE/'window-camera.json').read_bytes());H=np.array(C['rectified_facade_hxz'])
R,ROWS=480,875;W=C['nominal_outer_frame_width_m'];HEIGHT=C['derived_outer_frame_height_m']
with Image.open(PHOTO) as im:
    native=im.width/510
    # Sample twice at the required scale before filtering. Numerical sample positions
    # are measured on the front plane and can be reproduced from the unmodified photo.
    metric=np.array([[W/(R*2),0,-W/2],[0,-HEIGHT/(ROWS*2),HEIGHT],[0,0,1.]])
    mat=np.diag([native,native,1.])@H@metric;mat/=mat[2,2]
    rect=im.transform((2*R,2*ROWS),Image.Transform.PERSPECTIVE,mat.ravel()[:8],Image.Resampling.BICUBIC)
    rgb=np.asarray(rect.resize((R,ROWS),Image.Resampling.LANCZOS),dtype=np.float32)
lum=rgb@np.array([.2,.50,.30],np.float32)-.30*(rgb[:,:,0]-rgb[:,:,2])
score=np.zeros_like(lum)
for sigma in [.72,1.17,1.85]:
    xx=nd.gaussian_filter(lum,sigma,order=(0,2));yy=nd.gaussian_filter(lum,sigma,order=(2,0));xy=nd.gaussian_filter(lum,sigma,order=(1,1))
    spread=np.hypot(xx-yy,2*xy);lo=(xx+yy-spread)/2;hi=(xx+yy+spread)/2
    score=np.maximum(score,np.maximum(0.,-lo-.32*abs(hi))*sigma**2)
hp=nd.gaussian_filter(lum,.54)-nd.gaussian_filter(lum,2.7)
score=np.maximum(score,.30*hp)
# A piece of vegetation crosses the lower right of the tall grille. Reinstate only
# this reciprocal motif from its intact mate, retaining the distinction in the source record.
yy,xx=np.mgrid[:ROWS,:R];axis=np.where(yy<645,239.25,240.25)
mirror=nd.map_coordinates(score,[yy,2*axis-xx],order=1,mode='nearest')
paired=np.sqrt(np.maximum(0,score*nd.maximum_filter(mirror,(5,5))))
mask=(paired>7.4)&(score>4.05)
leaf=(xx>292)&(xx<337)&(yy>441)&(yy<551)
reflected=nd.map_coordinates(mask.astype(float),[yy,2*axis-xx],order=0,mode='nearest')>.5;mask[leaf]=reflected[leaf]
panels=np.zeros_like(mask);panels[36:625,38:442]=1;panels[660:846,37:443]=1;mask&=panels
# At the bottom of each operable grille the exposed timber appears through the
# small central arch. Keep its iron outline; exclude the underlying sash meeting rail.
for cy,rx,ry,base in [(619,21.5,53,622),(842,20.0,47,844)]:
    mask[(((xx-239.5)/rx)**2+((yy-cy)/ry)**2<1)&(yy<base)]=False
label,n=nd.label(mask,np.ones((3,3)));sizes=np.bincount(label.ravel());mask=(label>0)&(sizes[label]>13)
mask=nd.binary_closing(mask,structure=np.array([[0,1,0],[1,1,1],[0,1,0]],bool))
def thinning(bits):
    b=np.pad(bits,1).astype(np.uint8)
    for _ in range(35):
        old=int(b.sum())
        for phase in [0,1]:
            p=[b[:-2,1:-1],b[:-2,2:],b[1:-1,2:],b[2:,2:],b[2:,1:-1],b[2:,:-2],b[1:-1,:-2],b[:-2,:-2]]
            neighbors=sum(p);turns=sum((p[k]==0)&(p[(k+1)%8]!=0) for k in range(8))
            cut=(neighbors>=2)&(neighbors<=6)&(turns==1)
            if phase==0:cut&=~((p[0]*p[2]*p[4]!=0)|(p[2]*p[4]*p[6]!=0))
            else:cut&=~((p[0]*p[2]*p[6]!=0)|(p[0]*p[4]*p[6]!=0))
            b[1:-1,1:-1][cut]=0
        if int(b.sum())==old:break
    return b[1:-1,1:-1].astype(bool)
sk=thinning(mask);pix=set(zip(*sk.nonzero()));graph={}
for y,x in pix:
    adj=[]
    for dy,dx in ((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)):
        nb=(y+dy,x+dx)
        if nb not in pix:continue
        if dy and dx and ((y+dy,x)in pix or(y,x+dx)in pix):continue
        adj.append(nb)
    graph[y,x]=sorted(adj)
knots={i for i,n in graph.items()if len(n)!=2};edges=set();chains=[]
def key(a,b):return (a,b)if a<b else(b,a)
def path(a,b):
    pts=[a];last=a;cur=b
    while True:
        edges.add(key(last,cur));pts.append(cur)
        if cur in knots or cur==a:break
        opts=[q for q in graph[cur]if q!=last and key(cur,q) not in edges]
        if not opts:break
        last,cur=cur,opts[0]
    return pts
for p in sorted(knots)+sorted(pix-knots):
    for q in graph[p]:
        if key(p,q)in edges:continue
        chains.append(path(p,q))
dist=nd.distance_transform_edt(mask);segments=[];lengths=[]
for seq in chains:
    if len(seq)<3:continue
    xy=np.array([(x,y)for y,x in seq],float)
    extent=np.linalg.norm(np.diff(xy,axis=0),axis=1).sum()
    if extent<4.6 or (extent<6.4 and min(len(graph[seq[0]]),len(graph[seq[-1]]))==1):continue
    # Smooth pixel stair steps without moving junctions or the ends of curls.
    if len(xy)>5:
        smooth=nd.gaussian_filter1d(xy,.88,axis=0,mode='nearest')
        smooth[[0,-1]]=xy[[0,-1]];xy=smooth
    pts=np.asarray(LineString(xy).simplify(.49,preserve_topology=False).coords)
    if len(pts)<2 or np.max(np.ptp(pts,axis=0))<1.5:continue
    width=float(np.clip(2*np.median([dist[p]for p in seq]),1.8,4.2))
    mid=xy.mean(0);panel='tall'if mid[1]<645 else'lower'
    group=('left' if mid[0]<110 else 'right' if mid[0]>368 else 'centre' if 202<mid[0]<278 else 'inner left' if mid[0]<239 else 'inner right')
    segments.append(dict(panel=panel,group=group,section=int((mid[1]-(36 if panel=='tall'else 660))//75)+1,
                         measured_width_px=round(width,2),xy=np.round(pts,2).tolist()))
    lengths.append(extent)
check=dict(source_sha256=hashlib.sha256(PHOTO.read_bytes()).hexdigest(),rectified_pixels=[R,ROWS],window_m=[W,HEIGHT],occupied_source_pixels=int(mask.sum()),skeleton_pixels=len(pix),source_paths=len(segments),original_chain_length_px=round(sum(lengths),2),
           recovered_by_symmetry_rectified_px=[292,441,337,551],digitisation_scope='保留可辨的铁条中心线及宽度，以正常侧补右下局部遮挡。木框、玻璃和穿过窗口的异物另作处理。',paths=segments)
(HERE/'iron-grille-traces.json').write_text(json.dumps(check,ensure_ascii=False,separators=(',',':'))+'\n');print('trace stats',len(segments),sum(len(k['xy'])for k in segments),sum(lengths))
