"""Two tiled eaves and a narrow, set-back clerestory on the Jinze warehouse."""
from pathlib import Path
import math,numpy as np
from PIL import Image
ID='qingpu-jinze-chen-warehouse-clerestory-and-tile-eaves'
TILE='Weathered grey fired clay';LIME='Chalked white plaster';WOOD='Red brown clerestory timber';PAN='Slate grey under tile';GLASS='Dark clerestory lights';FASCIA='Soot-stained eave backing'
PALETTE={m:dict(color=c,roughness=r)for m,c,r in ((TILE,[1,1,1],.96),(LIME,[1,1,1],.95),(WOOD,[1,1,1],.83),(PAN,[.29,.31,.30],.96),(GLASS,[.26,.31,.31],.49),(FASCIA,[.24,.21,.18],.90))}
PITCH=.175;CENTRES=[(i-8)*PITCH for i in range(17)]
def texture():
    f=Path(__file__).with_name('old-tile-lime-and-mullion.png')
    if not f.exists():
        g=np.random.default_rng(915);h,w=290,200
        def haze(a,b):return np.asarray(Image.fromarray(g.integers(0,255,(a,b),dtype='uint8')).resize((w,h),Image.Resampling.BILINEAR),float)-127
        salt=haze(21,17);slate=np.array([81,83,78])+(.24*salt+.12*haze(7,19)+g.normal(0,6.5,(h,w)))[:,:,None]
        plaster=np.array([207,205,196])+(.08*salt+.13*haze(5,9)+g.normal(0,2.4,(h,w)))[:,:,None]
        wood=np.array([90,65,48])+(.15*haze(80,12)+.09*salt+g.normal(0,3,(h,w)))[:,:,None]
        Image.fromarray(np.concatenate((slate,plaster,wood),axis=1).clip(0,255).astype('uint8')).quantize(184).save(f)
    for m in (TILE,LIME,WOOD):PALETTE[m]['texture']=str(f)
def add_building(b,far=False):
    texture()
    def plate(x,y,z,w,d,h,m,n):b.box((x,y,z),(w,d,h),m,label=n)
    def slope(y,y2,z,z2):
        a=1.49;pts=[(-a,y,z),(a,y,z),(a,y2,z2),(-a,y2,z2),(-a,y,z-.045),(a,y,z-.045),(a,y2,z2-.045),(-a,y2,z2-.045)]
        b.add(pts,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],PAN,'Continuous underside of the grey tile pans')
    def tile(cx,y0,y1,z0,z1,radius,tag):
        seg=5 if far else 14;pts=[]
        for yy,zz in ((y0,z0),(y1,z1)):
            for rr in (radius,radius-.012):
                for a in np.linspace(0,math.pi,seg+1):pts.append((cx+rr*math.cos(a),yy,zz+rr*math.sin(a)))
        n=seg+1;faces=[]
        for j in range(seg):
            faces.extend([(j,j+2*n,j+2*n+1,j+1),(n+j,n+j+1,3*n+j+1,3*n+j),(j,j+1,n+j+1,n+j),(2*n+j,3*n+j,3*n+j+1,2*n+j+1)])
        faces += [(0,n,3*n,2*n),(seg,2*n+seg,3*n+seg,n+seg)]
        b.add(pts,faces,TILE,tag)
    plate(0,-.016,.340,2.99,.331,.680,LIME,'Cropped whitewashed street wall')
    for z,d in ((.587,.380),(.653,.433)):plate(0,-.022,z,3.02,d,.041,LIME,'Continuous shallow lime cornice')
    plate(0,-.026,.693,2.99,.393,.068,FASCIA,'Shadow behind the line of front tile mouths')
    plate(0,.568,1.118,2.97,.030,.591,GLASS,'Narrow clerestory set back between the roofs')
    for x in np.linspace(-1.45,1.45,11):plate(x,.528,1.117,.043,.09,.604,WOOD,'Vertical stained timber glazing bar')
    for z,dep,ht in ((.878,.14,.081),(1.405,.153,.076),(1.485,.215,.099)):
        plate(0,.532,z,3.03,dep,ht,WOOD,'Recessed sill or lintel below upper roof')
    for stage,(start,end,low,high,rows)in enumerate(((-.291,.246,.722,.884,2),(.262,1.245,1.503,1.957,4))):
        slope(start,end,low,high)
        for x in CENTRES:
            for j in range(rows):
                f=j/rows;g=(j+1)/rows;lap=.032 if j else 0
                ya=start+(end-start)*f-lap;yb=start+(end-start)*g;za=low+(high-low)*f+.014+(j*.001)-lap*(high-low)/(end-start);zb=low+(high-low)*g+.014+j*.001
                tile(x,ya,yb,za,zb,.060 if j else .065,'Overlapping barrel cover tile on '+('street wall crown' if stage==0 else 'upper warehouse roof'))
            if not far:tile(x,start-.018,start+.016,low+.010,low+.023,.071,'Overhanging rolled tile lip')
    for p in b.parts:
        mat=p['material']
        if mat not in (TILE,LIME,WOOD):continue
        strip=(TILE,LIME,WOOD).index(mat)
        p['texcoords']=[((strip+.016+.967*(x+1.54)/3.08)/3,.988-.965*(z+.035*y)/2.1)for x,y,z in p['vertices']]
