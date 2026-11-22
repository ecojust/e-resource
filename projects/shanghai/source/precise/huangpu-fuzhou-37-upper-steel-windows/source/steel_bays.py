"""Two different rows of steel windows at 37 Fuzhou Road in Fayhoo's 2015 photograph."""
from math import cos,sin,pi
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import box,Polygon
from shapely.ops import unary_union
ID='huangpu-fuzhou-37-upper-steel-windows'
WALL='Slightly ochre render';SILL='Weathered sill';FRAME='Blackened steel';CLAY='Oxidised steel reveal';PIPE='Dark rainwater pipe';CLIP='Iron pipe socket';PANE='Grey green glass';SKY='Clouded reflection';DARK='Unlit interior';CAP='Dark parapet coping'
PALETTE={m:{'color':c,'roughness':r}for m,c,r in [(WALL,[1.,1.,1.],.98),(SILL,[.678,.646,.543],.96),(FRAME,[.113,.121,.106],.70),(CLAY,[.258,.248,.177],.89),(PIPE,[.138,.127,.108],.79),(CLIP,[.268,.241,.196],.88),(PANE,[.240,.284,.261],.36),(SKY,[.318,.362,.329],.37),(DARK,[.101,.139,.129],.83),(CAP,[.349,.332,.263],.90)]}
def texture():
    p=Path(__file__).with_name('plaster.png')
    if not p.exists():
        r=np.random.default_rng(531);size=(604,480)
        grain=np.asarray(Image.fromarray(r.integers(0,255,(35,71),dtype='u1')).resize(size,Image.Resampling.BICUBIC),float)
        run=np.maximum(0,np.sin(np.linspace(0,pi*17,size[0]))-.72)[None,:]*np.linspace(0,8,size[1])[:,None]
        field=np.array([188,185,164])+((grain-128)*.044+r.normal(0,2.1,size[::-1])-run)[:,:,None]
        Image.fromarray(np.clip(field,0,255).astype('u1')).quantize(152).save(p)
    PALETTE[WALL]['texture']=str(p)
F=lambda x,z,d:(x,-d,z)
def slab(b,g,d,back,m,name):b.prism(g,back,d,F,m,name)
def rect(b,l,r,z0,z1,d,back,m,name):slab(b,box(l,z0,r,z1),d,back,m,name)
CS=(-1.30,1.30)
def grid(b,c,half,lo,hi,cols,rows,far,open_leaf=False):
    # The sash is slightly set into the masonry. All panes are individually bounded.
    frame=box(c-half-.029,lo-.027,c+half+.029,hi+.027)
    void=box(c-half+.025,lo+.026,c+half-.025,hi-.027)
    slab(b,frame.difference(void),-.076,-.190,CLAY,'Perimeter of the recessed steel window')
    rect(b,c-half,c+half,lo,hi,-.197,-.217,DARK,'Unlit recess behind the steel sash')
    xs=np.linspace(c-half+.027,c+half-.027,cols+1);zs=np.linspace(lo+.026,hi-.026,rows+1)
    for i in range(cols):
        for j in range(rows):
            if open_leaf and i in (cols-2,cols-1) and j in range(1,rows-1):continue
            rect(b,xs[i]+.012,xs[i+1]-.013,zs[j]+.011,zs[j+1]-.012,-.136,-.162,PANE if (i+2*j)%5 else SKY,'Steel casement individual glass')
    for i,x in enumerate(xs):
        halfbar=.019 if i%2==0 else .010
        rect(b,x-halfbar,x+halfbar,lo,hi,-.089,-.146,FRAME,'Steel sash upright with thicker meeting stile')
    for j,z in enumerate(zs):
        rect(b,c-half,c+half,z-.011,z+.011,-.086,-.143,FRAME,'Horizontal steel glazing bar')
    if not far:
        for x in xs[::2]:
            rect(b,x-.004,x+.004,lo+.011,hi-.011,-.084,-.089,CLAY,'Narrow weathered edge on the sash')
    if open_leaf:
        a=.65;l=xs[-1]-xs[-3];pivot=xs[-1];b0=zs[1];b1=zs[-2]
        def turn(u,z,d):return(pivot-u*cos(a)-d*sin(a),-u*sin(a)+d*cos(a)+.078,z)
        panel=box(0,b0,l,b1);hollow=box(.022,b0+.025,l-.022,b1-.025)
        b.prism(panel.difference(hollow),-.024,.013,turn,FRAME,'Open steel casement on the end hinge')
        b.prism(hollow,-.015,-.010,turn,SKY,'Glass in the projecting open leaf')
        for bar in (box(l/2-.011,b0,l/2+.011,b1),box(0,(b0+b1)/2-.010,l,(b0+b1)/2+.010)):
            b.prism(bar,-.013,.010,turn,FRAME,'Crossbars in the open leaf')
    rect(b,c-half-.057,c+half+.057,lo-.106,lo-.018,.112,-.118,SILL,'Exposed grey sill under the windows')
def cylinder(b,x,y,r,lo,hi,n,m,name):
    xy=[(x+r*cos(2*pi*i/n),y+r*sin(2*pi*i/n))for i in range(n)]
    b.prism(Polygon(xy),lo,hi,lambda u,v,h:(u,v,h),m,name)
def add_building(b,far=False):
    texture()
    top=[(c+d,.360)for c in CS for d in(-.505,.505)]
    holes=[box(c-.957,.30,c+.957,2.165) for c in CS]+[box(x-w,3.21,x+w,4.639)for x,w in top]
    slab(b,box(-2.62,0,2.62,5.21).difference(unary_union(holes)),0,-.255,WALL,'Two storeys of the light rendered upper elevation')
    for c in CS:grid(b,c,.955,.301,2.163,6,5,far,open_leaf=c<0)
    for x,w in top:grid(b,x,w,3.213,4.637,2,4,far)
    for x in (-2.56,-.018,2.56):
        rect(b,x-.018,x+.018,.03,4.92,.022,-.025,SILL,'Shallow vertical relief in the stucco')
    for lo,hi,d,m in [(2.90,2.944,.048,SILL),(2.945,2.977,.029,WALL),(4.914,5.07,.137,WALL),(5.06,5.205,.186,CAP),(5.198,5.25,.201,SILL)]:
        rect(b,-2.65,2.65,lo,hi,d,-.257,m,'Storey stringcourse or roof parapet cap')
    for lo,hi in [(0.,1.62),(1.59,3.59),(3.55,5.17)]:
        cylinder(b,.147,-.106,.036,lo,hi,10 if far else 18,PIPE,'Round rainwater downpipe')
    for z in (1.62,3.59,4.82):
        cylinder(b,.147,-.106,.048,z-.052,z+.024,10 if far else 18,CLIP,'Socket and clamp below the pipe connection')
        rect(b,.096,.199,z-.015,z+.015,.077,-.005,CLIP,'Rainwater pipe bracket back to the wall')
    for part in b.parts:
        if part['material']==WALL:part['texcoords']=[[(x+2.71)/5.42,z/5.30]for x,y,z in part['vertices']]
