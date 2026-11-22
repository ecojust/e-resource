"""Broken arched doorhead, central stone urn and transom of No. 376 Wukang Road."""
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import box,Polygon,Point
from shapely.affinity import translate
ID='xuhui-wukang-376-broken-pediment-and-urn'
BRICK='Warm running-bond red brick';STONE='Grey weathered stone';EDGE='Lighter stone moulding'
TIMBER='Black-green transom frame';GLASS='Smoke-grey transom glass';SHADE='Dark sheltered tympanum'
PALETTE={q:dict(color=c,roughness=r) for q,c,r in [(BRICK,[1,1,1],.96),(STONE,[.537,.516,.474],.88),(EDGE,[.623,.601,.553],.86),(TIMBER,[.141,.161,.149],.64),(GLASS,[.287,.307,.296],.39),(SHADE,[.403,.391,.355],.94)]}
URN=[(1.06,.132),(1.11,.132),(1.126,.103),(1.172,.102),(1.186,.071),(1.219,.065),(1.241,.08),(1.256,.086),(1.276,.067),(1.299,.082),(1.31,.097),(1.326,.089),(1.341,.111),(1.38,.124),(1.532,.164),(1.568,.170),(1.578,.185),(1.597,.187),(1.613,.158),(1.638,.147),(1.671,.088),(1.69,.067),(1.707,.065),(1.726,.03),(1.74,.002)]
def texture():
    p=Path(__file__).with_name('small-red-brick.png')
    if not p.exists():
        y,x=np.indices((512,512));course=y//19;offset=(course%2)*24;col=(x+offset)//48;random=np.random.default_rng(751)
        colours=random.normal(0,6,(30,13));noise=random.normal(0,3.7,x.shape)
        result=np.array([131,80,60])+colours[course,col][:,:,None]+noise[:,:,None]
        mortar=(y%19<1)|((x+offset)%48<1);result[mortar]=np.array([156,135,112])+noise[mortar,None]
        Image.fromarray(result.clip(0,255).astype('uint8')).quantize(122).save(p)
    PALETTE[BRICK]['texture']=str(p)
def arc(x):
    return 1.064+.63*(1-(x/.998)**2)
def add_building(b,far=False):
    texture()
    def shape(poly,back,front,material,name):
        b.prism(poly,back,front,lambda x,z,d:(x,-d,z),material,name)
    def block(l,r,lo,hi,back,front,material,name):shape(box(l,lo,r,hi),back,front,material,name)
    opening=box(-.666,-.02,.666,.617)
    shape(box(-1.17,0,1.17,1.91).difference(opening),-.19,0,BRICK,'Brick wall visible through the break in the arch')
    pane=box(-.627,.034,.627,.579)
    shape(opening.difference(pane),-.09,.024,TIMBER,'Broad timber transom frame')
    shape(pane,-.124,-.092,GLASS,'Four glazed lights behind the doorhead')
    for x in(-.311,0,.311):block(x-.021,x+.021,.026,.586,-.105,-.014,TIMBER,'Transom mullion')
    for s in [-1,1]:
        xmin,xmax=sorted((s*.663,s*.906))
        block(xmin,xmax,0,.778,-.055,.158,STONE,'Stone jamb carrying the architrave')
        xs=np.linspace(.248,.998,17 if not far else 10)
        def band(lo,hi):
            return Polygon([(s*x,arc(x)+lo)for x in xs]+[(s*x,arc(x)+hi)for x in xs[::-1]])
        outline=Polygon([(s*x,arc(x)-.079)for x in xs]+[(s*.998,1.015),(s*.207,1.015),(s*.24,1.123),(s*.326,1.19),(s*.373,1.27),(s*.386,1.35),(s*.357,1.431),(s*.248,1.505)])
        shape(outline.buffer(0),.003,.064,SHADE,'Recessed half tympanum beside the central break')
        for lower,upper,depth,mat in [(-.082,.017,.138,STONE),(-.019,.016,.192,EDGE),(.031,.064,.188,EDGE),(.014,.038,.153,STONE)]:
            shape(band(lower,upper),.04,depth,mat,'Successive cornice on broken arcuated pediment')
        center=s*.824
        block(center-.081,center+.081,.315,.748,.135,.177,STONE,'Straight lower stem of console')
        profile=Polygon([(-.074,.75),(.070,.75),(.082,.788),(.080,.861),(.062,.889),(-.058,.889),(-.08,.85)])
        shape(translate(profile,xoff=center),.107,.235,EDGE,'Top scroll of doorhead console')
        disc=Point(center,.335).buffer(.072,resolution=9 if far else 16)
        shape(disc,.13,.199,EDGE,'Rounded end of hanging bracket')
        for dx in(-.047,-.018,.018,.047):
            block(center+dx-.005,center+dx+.005,.364,.752,.168,.187,EDGE,'Narrow groove ridge on bracket')
    for low,high,depth,side,mat in [(.596,.650,.134,.995,STONE),(.648,.699,.158,1.021,EDGE),(.698,.930,.112,.99,STONE),(.928,.972,.16,1.020,EDGE),(.966,1.016,.195,1.05,STONE),(1.012,1.057,.212,1.066,EDGE)]:
        block(-side,side,low,high,-.015,depth,mat,'Horizontal stone course supporting the broken segment')
    block(-.146,.146,1.054,1.114,.01,.218,EDGE,'Square plinth for the central stone urn')
    b.lathe((0,-.126),URN,STONE,16 if far else 36,'Lidded urn with turned foot, tapered belly and finial')
    for part in b.parts:
        if part['material']==BRICK:part['texcoords']=[[(x+1.17)/2.34,z/1.91]for x,y,z in part['vertices']]
