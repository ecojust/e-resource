"""Carved entrance-window surround on the street row pictured at 351–355 South Xiangyang Road."""
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import box,LineString,Point
BRICK='Dark red running-bond brick';STONE='Grey-green rendered stone';MOULD='Pale raised border';RELIEF='Flower and leaf relief';CENTRE='Flower boss';GLASS='Dark recessed glass';SASH='Painted window sash';SHADOW='Shadowed window reveal'
PALETTE={name:dict(color=colour,roughness=roughness) for name,colour,roughness in [
 (BRICK,[1,1,1],.93),(STONE,[.578,.594,.548],.92),(MOULD,[.652,.657,.602],.9),
 (RELIEF,[.671,.677,.617],.87),(CENTRE,[.72,.715,.65],.82),(GLASS,[.176,.204,.208],.40),
 (SASH,[.383,.405,.368],.76),(SHADOW,[.33,.345,.322],.94)]}
ID='xuhui-xiangyang-351-355-floral-window-surround'
FLOWERS=[(-.83,1.37),(-.51,1.37),(-.18,1.37),(.158,1.37),(.464,1.37),(.674,1.37)]
def save_mapped_texture(tile, path):
    """Store the material pattern 2 by 2 times inside one clamp-to-edge image."""
    atlas=Image.new('P',(tile.width*2,tile.height*2))
    atlas.putpalette(tile.getpalette())
    for row in range(2):
        for col in range(2):
            atlas.paste(tile,(col*tile.width,row*tile.height))
    atlas.save(path,optimize=True)

def texture():
    p=Path(__file__).with_name('dark-red-stretchers.png')
    if not p.exists():
        y,x=np.indices((400,480));row=y//24;run=x+36*(row%2);idx=run//72;g=np.random.default_rng(787)
        a=np.array([93,64,52])+g.normal(0,8,(18,9))[row,idx,None]+g.normal(0,3.4,x.shape)[:,:,None]
        a[(y%24<=1)|(run%72<2)]=[149,135,118];save_mapped_texture(Image.fromarray(a.clip(0,255).astype('uint8')).quantize(108),p)
    PALETTE[BRICK]['texture']=str(p)
def curve(controls,n):
    a,b,c,d=np.asarray(controls,float);t=np.linspace(0,1,n)[:,None]
    return (1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d
def add_building(b,far=False):
    texture()
    def surface(poly,lo,hi,material,name):b.prism(poly,lo,hi,lambda x,z,d:(x,-d,z),material,name)
    def rect(l,r,z,t,lo,hi,material,name):surface(box(l,z,r,t),lo,hi,material,name)
    def ribbon(points,width,lo,hi,material,name):
        surface(LineString(points).buffer(width,resolution=3 if far else 7,join_style=1),lo,hi,material,name)
    def dome(x,z,rx,rz,rot,depth,material,name):
        n=8 if far else 16;k=3 if far else 6
        v=[];f=[]
        for i in range(k):
            phi=.5*np.pi*i/k
            for j in range(n):
                theta=2*np.pi*j/n;u=rx*np.cos(theta)*np.cos(phi);v0=rz*np.sin(theta)*np.cos(phi)
                v.append((x+u*np.cos(rot)-v0*np.sin(rot),-(.043+depth*np.sin(phi)),z+v0*np.cos(rot)+u*np.sin(rot)))
        v.append((x,-(.043+depth),z))
        for i in range(k-1):
            for j in range(n):
                q=i*n+j;r=i*n+(j+1)%n;f.append((q,r,r+n,q+n))
        for j in range(n):f.append(((k-1)*n+j,(k-1)*n+(j+1)%n,len(v)-1))
        b.add(v,f,material,name)
    hole=box(-.665,-.01,.274,1.126);second=box(.806,-.01,.955,1.132);cut=hole.union(second)
    surface(box(-1.126,0,.957,1.72).difference(cut),-.206,-.012,BRICK,'Original dark brickwork at the top of the surround')
    block=box(-1.00,0,.955,1.527).difference(cut)
    surface(block,-.093,.040,STONE,'Continuous render surround and wide mullion')
    rect(-1.0,.955,1.502,1.538,.040,.067,MOULD,'Uppermost projecting strip')
    rect(-1.0,.955,1.469,1.484,.040,.054,MOULD,'Second shallow upper band')
    for x0,x1 in [(-.682,.291),(.789,.954)]:
        rect(x0,x1,1.145,1.178,.04,.066,MOULD,'Projecting line over window head')
        rect(x0,x0+.021,0,1.169,.040,.064,MOULD,'Raised upright of window moulding')
        if x1<.95:rect(x1-.021,x1,0,1.169,.040,.064,MOULD,'Raised opposite window moulding')
    for x0,x1 in [(-.665,.274),(.806,.956)]:
        rect(x0,x0+.042,0,1.128,-.154,.032,SHADOW,'Set-back rendered reveal')
        if x0<0:rect(x1-.04,x1,0,1.128,-.154,.032,SHADOW,'Right reveal')
        rect(x0,x1,1.082,1.128,-.154,.034,SHADOW,'Window soffit')
        rect(x0,x1,0,1.085,-.19,-.158,GLASS,'Shaded glass')
        rect(x0+.042,x0+.069,0,1.085,-.157,-.137,SASH,'Visible vertical painted frame')
        rect(x0,x1,.51,.553,-.158,-.136,SASH,'Transom in the street window')
    for x,z in FLOWERS:
        for k in range(7):
            angle=2*np.pi*k/7+.17
            dome(x+.036*np.cos(angle),z+.036*np.sin(angle),.027,.018,angle,.025,RELIEF,'Relief petal of the seven-lobed head ornament')
        dome(x,z,.022,.022,0,.036,CENTRE,'Round flower centre')
    xc=.567
    ribbon(curve([(xc,1.29),(xc+.026,1.11),(xc-.026,.74),(xc,.39)],30 if not far else 15),.009,.040,.063,RELIEF,'Hanging stem beneath the paired top rosettes')
    for s in [-1,1]:
        def leaf(coords):
            return [(xc+s*u,v) for u,v in coords]
        top=curve(leaf([(0,1.24),(.047,1.22),(.100,1.23),(.106,1.319)]),17)
        ribbon(top,.012,.043,.072,RELIEF,'Upturned stem below a rosette')
        for away,level,height in [(0.064,1.22,.105),(.087,1.145,.127),(.116,1.08,.106),(.078,.890,.096),(.105,.657,.095),(.057,.518,.087)]:
            a=curve(leaf([(0,level),(.03,level-.017),(.062,level-height), (away,level-height*.68)]),12 if far else 24)
            widths=.006+.025*np.sin(np.linspace(0,np.pi,len(a)))**.82
            v=[];f=[]
            for i,((x,z),wd) in enumerate(zip(a,widths)):
                tangent=a[min(i+1,len(a)-1)]-a[max(i-1,0)];tangent=tangent/np.linalg.norm(tangent);o=np.array([-tangent[1],tangent[0]])*wd
                for off,dep in [(-o,.049),(np.zeros(2),.071+.012*np.sin(i*np.pi/(len(a)-1))),(o,.049)]:v.append((x+off[0],-dep,z+off[1]))
            for i in range(len(a)-1):
                for j in [0,1]:
                    q=3*i+j;f.append((q,q+3,q+4,q+1))
            b.add(v,f,RELIEF,'Raised central ridge of a drooping acanthus leaf')
        th=np.linspace(-1.53,3.86,17 if far else 35);rad=np.linspace(.058,.010,len(th))
        ribbon([(xc+s*(.095+r*np.cos(t)),1.015+r*np.sin(t)) for t,r in zip(th,rad)],.011,.046,.071,RELIEF,'Small rolled tip of leaf pair')
    for part in b.parts:
        if part['material']==BRICK:part['texcoords']=[[(x+1.13)/(2*1.44),z/(2*1.20)] for x,y,z in part['vertices']]
