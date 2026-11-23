"""Construct the measured 2013–15 Meiquan Villas brick entrance, gates and street fence."""
import argparse,json,math,sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
HERE=Path(__file__).resolve().parent
MEASUREMENTS=HERE.parent/'measurements'
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder
sys.path.insert(0,str(HERE))
from name_plaques import add_plaques
ID='changning-meiquan-villas-inscribed-entrance'
BRICK='Meiquan | pale gate brick';STONE='Meiquan | cut plaque stone';IRON='Meiquan | painted black iron'
OLD='Meiquan | grey heritage tablet';WORDS='Meiquan | dark letter recess';LAMP='Meiquan | opal globe';CORD='Meiquan | bronze lamp seat'
PALETTE={BRICK:{'color':[.49,.445,.364],'roughness':.85},STONE:{'color':[.43,.352,.266],'roughness':.88},
         OLD:{'color':[.28,.275,.247],'roughness':.85},IRON:{'color':[.035,.031,.025],'roughness':.66,'metallic':.48},
         WORDS:{'color':[.041,.031,.018],'roughness':.95},LAMP:{'color':[.78,.75,.575],'roughness':.36},CORD:{'color':[.21,.165,.082],'metallic':.43}}
META={'id':ID,'name':'新华路593弄梅泉别墅东北入口刻名门柱与铁门','address':'上海市长宁区新华路593弄东北口','heritage_id':'sh-historic-b3-116','official_id':'3M018','geometry_license':'MIT','texture_license':'MIT','photos_embedded':False,'source':'http://sh.people.com.cn/n2/2021/1004/c134768-34943565.html','photo_source':'https://m.thepaper.cn/baijiahao_8356585','viewer_page':'meiquan-villas-inscribed-entrance.html','camera_views':json.loads((HERE/'cameras.json').read_bytes()),'scope':'The named public street gate, walk-through gate, early open paired leaves, globe finials and adjoining fence panel as documented in 2013–15. A geographically registered 2020 comparison records a different cap and closed-gate state. No attribution of a villa interior or all twenty houses.'}

def block(b,label,mat,x1,x2,y1,y2,z1,z2):
    b.box([(x1+x2)/2,(y1+y2)/2,(z1+z2)/2],[x2-x1,y2-y1,z2-z1],mat,label=label)

def pier(b,x,width,height,globe,tag,lod):
    block(b,tag+' / brick shaft',BRICK,x-width/2,x+width/2,0,width,0,height-.17)
    for i,(extra,z0,z1)in enumerate([(.038,-.17,-.132),(.068,-.132,-.073),(.085,-.073,-.023),(.054,-.023,0)]):
        block(b,tag+f' / projecting cap course {i+1}',BRICK,x-width/2-extra,x+width/2+extra,-extra,width+extra,height+z0,height+z1)
    if globe:
        radius=.151
        b.lathe((x,width*.50),[(height,.081),(height+.029,.089),(height+.053,.067),(height+.151,.044),(height+.208,.072),(height+.222,.066)],CORD,12 if lod else 22,tag+' / globe socket')
        cz=height+.371
        angles=np.linspace(-math.pi*.465,math.pi*.465,9 if lod else 17)
        b.lathe((x,width*.50),[(cz+radius*math.sin(t),radius*math.cos(t))for t in angles],LAMP,14 if lod else 28,tag+' / opal ball')

def field(b,tag,origin,tangent,width,top,lod,leaf=True,sweep=True):
    u=np.array(tangent,float);u/=np.linalg.norm(u);v=np.array([-u[1],u[0]])
    def xyz(t,z,out=0):
        p=np.asarray(origin)+t*u+out*v;return [*p,z]
    def rail(t0,t1,z0,z1,d,label):
        b.box(xyz((t0+t1)/2,(z0+z1)/2),[t1-t0,d,z1-z0],IRON,basis=([*u,0],[*v,0],[0,0,1]),label=tag+' / '+label)
    def profile(t):
        frac=t/width;return top+(.21*math.sin(math.pi*frac)+.121*frac if sweep else 0)
    low=.098 if leaf else .53
    for i,t in enumerate([.026,width-.026]):
        rail(t-.022,t+.022,low,profile(t)+.075,.061,'edge stile '+str(i+1))
    for i,z in enumerate([low+.025,low+.415,low+.505]):
        rail(.048,width-.048,z-.012,z+.012,.032,'lower rail '+str(i+1))
    pts=np.linspace(.048,width-.048,9 if lod else 20)
    for layer in ([0,.153]if leaf else [0]):
        b.tube([xyz(t,profile(t)-layer)for t in pts],.018 if leaf else .023,IRON,7 if lod else 12,tag+f' / swept upper rail {layer}')
    bars=max(4,round(width/.132))
    for i in range(1,bars):
        t=.046+(width-.092)*i/bars
        rail(t-.010,t+.010,low+.04,profile(t)+.041,.023,'solid picket '+str(i))
        if not lod and leaf:
            pt=xyz(t,profile(t)+.042);px,py=pt[:2];z=pt[2]
            b.lathe((px,py),[(z,.012),(z+.019,.022),(z+.064,.0025)],IRON,6,tag+' / lance '+str(i))
    if leaf:
        for i in range(4):
            t=width*(i+.55)/4.10;z=profile(t)-.079
            points=[xyz(t+.039*math.cos(a),z+.049*math.sin(a),-.025)for a in np.linspace(.21,math.tau-.29,11 if lod else 18)]
            b.tube(points,.0078,IRON,6 if lod else 8,tag+' / upper scroll '+str(i+1))

def add_building(b,lod=False):
    p=json.loads((MEASUREMENTS/'gate-cameras.json').read_bytes())['parameters']
    d,w=p['axes_distance'],p['pier_width']
    for x,height,name in [(-d,p['plain_cap'],'plain gate pier'),(0,p['inscribed_cap'],'named gate pier')]:
        pier(b,x,w,height,True,name,lod)
    walk=-6.73
    pier(b,walk,.41,2.74,False,'walk-through outer jamb',lod)
    block(b,'plain gate pier / heritage panel',OLD,-d-.247,-d+.247,-.032,0,1.77,2.25)
    add_plaques(b,STONE,WORDS,lod)
    kw=d-w;segment=kw/2-.031
    for n,x,angle in [('left',-d+w/2+.015,88.),('right',-w/2-.015,94.)]:
        th=math.radians(angle);direction=[math.cos(th)*(1 if n=='left' else -1),math.sin(th)]
        field(b,'main iron leaf '+n,[x,.36],direction,segment,2.02,lod)
    field(b,'pedestrian gate',[walk+.218,.34],[1,0],(-d-w/2)-(walk+.218)-.020,2.02,lod)
    xend=4.62
    pier(b,xend,.53,2.63,False,'fence outer pier',lod)
    block(b,'street fence / brick curb',BRICK,w/2,xend-.265,.10,.48,0,.49)
    block(b,'street fence / curb cap',STONE,w/2,xend-.265,.07,.50,.49,.54)
    field(b,'street fence',[w/2+.014,.29],[1,0],xend-.265-w/2-.026,2.32,lod,False,False)

def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('path',type=Path,nargs='?');cli.add_argument('--output',type=Path);cli.add_argument('--lod',action='store_true');a=cli.parse_args();out=a.output or a.path
    if not out:cli.error('an output GLB path is required')
    b=Builder(PALETTE);add_building(b,a.lod);b.save(out,META)
if __name__=='__main__':main()
