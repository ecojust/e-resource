"""The inscribed 1916 gable over the upper windows of the former Jikui school at 42 Jingzhou Road."""
from pathlib import Path
from math import sin,cos,pi
import numpy as np
from PIL import Image
from shapely.geometry import Polygon,box,LineString
ID='yangpu-jikui-school-1916-gable'
PLASTER='Pale rendered wall';RED='Red masonry trim';DARK='Dark moulded eave';STONE='Dark inscription';VENT='Open louvre recess'
PALETTE={k:dict(color=c,roughness=r) for k,c,r in [(PLASTER,[1,1,1],.92),(RED,[.42,.259,.231],.90),(DARK,[.210,.210,.205],.94),(STONE,[.258,.252,.239],.82),(VENT,[.134,.151,.157],.88)]}
def texture():
    f=Path(__file__).with_name('render-grain.png')
    if not f.exists():
        y,x=np.indices((256,256));rng=np.random.default_rng(723)
        grain=rng.normal(0,3.4,x.shape)+2*np.cos(x*.09+np.sin(y*.035))
        Image.fromarray((np.array([206,204,177])+grain[:,:,None]).clip(0,255).astype('uint8')).quantize(96).save(f)
    PALETTE[PLASTER]['texture']=str(f)
def digit_paths(d):
    if d=='1':return [[(.12,.74),(.51,.96),(.43,.06)],[(.12,.05),(.76,.05)]]
    if d=='9':return [[(.16,.10),(.45,.16),(.63,.38),(.70,.70),(.64,.88),(.47,.96),(.27,.94),(.13,.81),(.11,.63),(.21,.49),(.39,.46),(.61,.57)]]
    return [[(.72,.94),(.50,.92),(.31,.79),(.17,.56),(.13,.30),(.18,.13),(.33,.04),(.51,.06),(.65,.20),(.68,.37),(.59,.51),(.43,.55),(.22,.46)]]
def add_building(b,far=False):
    texture()
    def form(poly,back,front,m,label):b.prism(poly,back,front,lambda x,z,d:(x,-d,z),m,label)
    def rect(l,r,z,t,back,front,m,label):form(box(l,z,r,t),back,front,m,label)
    shape=Polygon([(-1.48,.0),(1.48,0),(1.48,1.05),(0,2.63),(-1.48,1.05)])
    hole=box(-.086,1.48,.086,1.78)
    arch=Polygon([(-.232,-.02),(.232,-.02)]+[(.232*cos(t),.104+.232*sin(t)) for t in np.linspace(0,pi,31)])
    flanks=[box(x-.236,-.02,x+.236,.115)for x in(-.88,.88)]
    openings=hole.union(arch).union(flanks[0]).union(flanks[1])
    form(shape.difference(openings),-.217,0,PLASTER,'Rendered upper gable with a true recess for the louvre')
    for sign in (-1,1):
        edge=Polygon([(0,2.615),(sign*1.53,.981),(sign*1.53,1.082),(0,2.716)])
        form(edge,-.242,.046,DARK,'Dark projecting bargeboard along the steep gable')
        for i in range(11):
            x=sign*(.115+i*.124);z=2.615-abs(x)*1.069
            form(Polygon([(x-.027,z-.03),(x+.027,z-.03),(x+.027,z+.022),(x-.027,z+.022)]),.045,.061,RED,'Small block along the slope')
    rect(-.103,.103,1.47,1.795,-.165,-.141,VENT,'Shadow at the rear of the narrow ventilator')
    for side in (-1,1):
        x=side*.104;rect(x-.029,x+.029,1.427,1.81,-.067,.047,RED,'Brick jamb beside the louvres')
    for i in range(5):
        z=1.486+i*.062
        rect(-.088,.088,z,z+.025,-.098,-.056,DARK,'Recessed horizontal louvre blade')
    for z,width in [(1.426,.164),(1.783,.161),(1.817,.132)]:
        rect(-width,width,z,z+.028,-.036,.065,RED,'Sill or head projecting beyond the louvre jambs')
    form(Polygon([(-.155,1.842),(0,1.939),(.155,1.842)]),-.043,.061,RED,'Low pointed cap over the ventilator')
    for i,digit in enumerate('1916'):
        left=-.37+i*.192
        for stroke in digit_paths(digit):
            pts=[(left+u*.176+(v-.5)*.023,.956+v*.233)for u,v in stroke]
            band=LineString(pts).buffer(.013,cap_style=1,join_style=1,quad_segs=6 if not far else 2)
            form(band,.001,.017,STONE,'Independent drawn stroke of the relief date '+digit)
    # The plane ends in the top of the three windows, whose dark glass is visible below its brick surrounds.
    for index,part in enumerate([arch,*flanks]):
        form(part.intersection(box(-1.5,0,1.5,2.72)),-.136,-.113,VENT,'Recessed glass at the head of an upper-floor window')
        cx=(0,-.88,.88)[index]
        for dx in (-.10,.10):
            rect(cx+dx-.007,cx+dx+.007,0,.103,-.114,-.091,DARK,'Steel muntin below the brick head')
    # Uppermost masonry of the three windows under the date.
    for x in (-.88,.88):
        rect(x-.306,x+.306,.11,.218,-.02,.036,RED,'Broad horizontal lintel of one flanking window')
    for j in range(9):
        a=j*pi/9+.004;v=(j+1)*pi/9-.004
        coords=lambda r:[(r*cos(t),.104+r*sin(t))for t in np.linspace(a,v,3 if far else 6)]
        form(Polygon(coords(.232)+list(reversed(coords(.280 if j not in (2,4,6) else .326)))),-.034,.043,RED,'Alternating projecting bricks at the central window head')
    for g in b.parts:
        if g['material']==PLASTER:g['texcoords']=[[(x+1.5)/3,z/2.72]for x,y,z in g['vertices']]
