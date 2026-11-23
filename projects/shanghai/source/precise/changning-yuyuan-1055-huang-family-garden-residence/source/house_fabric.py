"""Dressed stone, rendered walls and red casements documented at 1055 Yuyuan Road."""
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
SOURCE=Path(__file__).parent
STUCCO='Garden house | pale ochre roughcast'
STONE='Garden house | cream dressed stone'
PLINTH='Garden house | grey rendered plinth'
SHADOW='Garden house | deep rebate'
TIMBER='Garden house | oxblood painted joinery'
GLASS='Garden house | shaded old glazing'
GLASS_LIGHT='Garden house | reflected garden light'
BRONZE='Garden house | aged iron railing'
STAIR='Garden house | stone tread'
DARKWOOD='Garden house | dark entrance door'
CONCRETE='Garden house | aged terrace coping'

def paint(rgb,roughness=.8,metallic=0):
    return {'color':[(v/255.)**2.2 for v in rgb],'roughness':roughness,'metallic':metallic}

PALETTE={STUCCO:{'texture':str(SOURCE/'garden-ochre-roughcast.png'),'color':[1,1,1],'roughness':.92},
         STONE:paint((215,206,177)),PLINTH:paint((141,142,128)),SHADOW:paint((55,53,47)),
         TIMBER:paint((116,59,54),.56),GLASS:paint((61,75,71),.24,.13),
         GLASS_LIGHT:paint((90,102,95),.22,.13),BRONZE:paint((110,78,68),.57,.35),
         'Garden house | dark green canopy sheet':paint((50,77,69),.74,.18),'Garden house | dark canopy iron':paint((70,70,61),.66,.25),STAIR:paint((160,160,145)),DARKWOOD:paint((75,53,45)),CONCRETE:paint((191,185,159))}

class Wall:
    """A wall measured from left to right when seen from outdoors."""
    def __init__(self,b,a,c):
        self.b=b;self.a=np.asarray(a,dtype=float);end=np.asarray(c,dtype=float)
        self.length=float(np.linalg.norm(end-self.a));self.tangent=(end-self.a)/self.length
        self.out=np.array([self.tangent[1],-self.tangent[0]])
    def point(self,u,z,d=0.):
        xy=self.a+u*self.tangent+d*self.out
        return float(xy[0]),float(xy[1]),float(z)
    def prism(self,poly,back,front,mat,name):
        if not poly.is_empty:self.b.prism(poly,back,front,self.point,mat,name)
    def rect(self,x0,z0,x1,z1,back,front,mat,name):
        self.prism(box(x0,z0,x1,z1),back,front,mat,name)
    def masonry(self,z0,z1,holes,name,thickness=.32):
        poly=box(0,z0,self.length,z1)
        if holes:poly=poly.difference(unary_union([box(*h)for h in holes]))
        self.prism(poly,-thickness,0,STUCCO,name)
    def sash(self,opening,cols,rows,label,lod=False,upper=.23):
        x0,z0,x1,z1=opening
        head=z1-(z1-z0)*upper
        outer=box(x0,z0,x1,z1)
        self.prism(outer.difference(outer.buffer(-.073,join_style=2)),-.15,-.055,TIMBER,label+' outer rebate')
        self.rect(x0-.083,z0-.09,x1+.083,z0-.009,-.22,.075,STONE,label+' sill')
        if not lod:self.rect(x0-.034,z1+.016,x1+.034,z1+.067,-.08,.052,STONE,label+' head')
        first,last=x0+.065,x1-.065
        for k in range(cols):
            le=first+(last-first)*k/cols;ri=first+(last-first)*(k+1)/cols
            if k:self.rect(le-.030,z0+.06,le+.030,z1-.06,-.166,-.085,TIMBER,label+' mullion '+str(k))
            self.rect(le+.031,z0+.06,ri-.031,head-.033,-.227,-.215,GLASS if k%3 else GLASS_LIGHT,label+' casement light '+str(k+1))
            self.rect(le+.031,head+.034,ri-.031,z1-.06,-.23,-.216,GLASS_LIGHT if k%3 else GLASS,label+' toplight '+str(k+1))
            center=(le+ri)/2
            self.rect(center-.018,z0+.08,center+.018,head-.032,-.195,-.143,TIMBER,label+' narrow glazing bar')
            self.rect(center-.018,head+.037,center+.018,z1-.067,-.193,-.14,TIMBER,label+' upper glazing bar')
            railwidth=.020 if not lod else .025
            for row in range(1,rows):
                zz=z0+.06+(head-.033-z0-.06)*row/rows
                self.rect(le+.018,zz-railwidth,ri-.018,zz+railwidth,-.195,-.15,TIMBER,label+' casement bar')
        self.rect(x0+.035,head-.040,x1-.035,head+.040,-.155,-.064,TIMBER,label+' transom')

def xy(layout,s,t):
    x,y,_=layout['east_photo_facing']['portico_front_right']
    return x-t,y+s

def photo_wall(b,layout,s0,t0,s1,t1):
    return Wall(b,xy(layout,s0,t0),xy(layout,s1,t1))
