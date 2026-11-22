"""Undulating iron gate at the street entrance to Hua Cun, Lane 76 Wuyuan Road."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from shapely.geometry import box,Point,LineString,shape,Polygon
from shapely.affinity import translate,scale
ID='xuhui-hua-cun-lane76-waved-iron-gate'
WALL='Yellow-beige granular render';PIER='Smoother buff street pier';IRON='Black painted iron';HIGHLIGHT='Forged iron collars';GREEN='Dark-green lane tablet';WHITE='Ivory enamel lettering'
PALETTE={m:dict(color=c,roughness=r)for m,c,r in [(WALL,[1,1,1],.94),(PIER,[.753,.72,.589],.92),(IRON,[.105,.111,.106],.69),(HIGHLIGHT,[.176,.177,.163],.66),(GREEN,[.105,.230,.174],.74),(WHITE,[.804,.814,.682],.70)]}
def texture():
    p=Path(__file__).with_name('warm-render.png')
    if not p.exists():
        g=np.random.default_rng(803);s=np.array([182,170,138])+g.normal(0,6,(430,322,1));Image.fromarray(s.clip(0,255).astype('uint8')).quantize(93).save(p)
    PALETTE[WALL]['texture']=str(p)
def wave(x):return 1.59+.032*np.cos(2*np.pi*(x+.80)/1.21)
def letters():
    data=json.loads(Path(__file__).with_name('lane-characters.json').read_bytes())
    for chars,origin,level,advance,high in [('76弄1-16号',.68,2.024,.054,.068),('五原路',.68,1.962,.054,.043)]:
        for i,ch in enumerate(chars):
            poly=shape(data[ch]);x,z,r,t=poly.bounds
            hh=high*(.19 if ch=='-' else 1)
            poly=scale(poly,xfact=advance*.81/(r-x),yfact=hh/(t-z),origin=(0,0));x,z,r,t=poly.bounds
            yield ch,translate(poly,origin+(i-(len(chars)-1)/2)*advance-(x+r)/2,level-(z+t)/2)
def crest_ornament(x):
    z=wave(x)-.111
    shape=Point(x,z).buffer(.042,resolution=13).difference(Point(x,z).buffer(.033,resolution=13))
    kite=Polygon([(x-.014,z),(x,z+.026),(x+.014,z),(x,z-.026)])
    return shape.union(kite)
def add_building(b,far=False):
    texture()
    def face(poly,lo,hi,mat,label):b.prism(poly,lo,hi,lambda x,z,d:(x,-d,z),mat,label)
    def block(l,r,z,t,lo,hi,mat,label):face(box(l,z,r,t),lo,hi,mat,label)
    def wire(points,thickness,depth,mat,label):
        face(LineString(points).buffer(thickness,resolution=3 if far else 7,join_style=1),depth,depth+.018,mat,label)
    block(-1.02,.198,0,2.265,-.200,-.193,WALL,'Incised buff render on wall seen through ironwork')
    block(.198,1.024,0,2.265,-.202,.031,PIER,'Rendered pier carrying the green lane tablet')
    block(.425,.935,1.910,2.090,.031,.047,GREEN,'Green enamel lane and street sign')
    for ch,p in letters():
        face(p.simplify(.0004 if far else .00012,preserve_topology=True),.047,.051,WHITE,'Visible lettering '+ch)
    a,r=-.935,.145
    for x in [a,r]:
        block(x-.018,x+.018,0,wave(x)+.016,-.045,.016,IRON,'Gate side stile')
    ts=np.linspace(a,r,25 if far else 56)
    for drop in [0,.218]:
        wire([(x,wave(x)-drop) for x in ts],.015,.010,IRON,'Sinuous flat iron transom')
    for x in [-.69,-.43,-.17]:
        p=crest_ornament(x)
        face(p.simplify(.0016 if far else .0002,preserve_topology=True),.003,.023,HIGHLIGHT,'Ring and lozenge between curved transoms')
        block(x-.005,x+.005,wave(x)-.20,wave(x)-.151,.003,.021,IRON,'Stem below crest ring')
        block(x-.005,x+.005,wave(x)-.074,wave(x)-.014,.003,.021,IRON,'Stem above crest ring')
    for x in np.linspace(-.805,-.146,8):
        block(x-.010,x+.010,0,wave(x)-.218,-.004,.019,IRON,'Slender straight upright')
    for z in [.40,.903]:block(a,r,z,z+.021,-.006,.020,IRON,'Rectangular cross rail')
    block(-.071,-.052,0,wave(-.06)-.218,-.002,.019,IRON,'Border to scrollwork at right of gate')
    for level in [.278,.565,.853,1.142]:
        angles=np.linspace(-1.7,5.85,21 if far else 46);rad=np.linspace(.071,.012,len(angles))
        wave_points=[(.043+v*np.cos(u),level+1.24*v*np.sin(u)) for u,v in zip(angles,rad)]
        begin=wave_points[0];wire([(-.052,level-.083),(.0,level-.08),begin]+wave_points[1:],.010,.008,IRON,'S-curled iron amid right border')
        ornament=Point(.05,level+.069).buffer(.019,resolution=4 if far else 10)
        face(ornament,.010,.026,HIGHLIGHT,'Forged bud on side scroll')
    for p in b.parts:
        if p['material']==WALL:p['texcoords']=[[(x+1.02)/1.218,z/2.265] for x,y,z in p['vertices']]
