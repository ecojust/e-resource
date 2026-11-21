"""The three photographed street levels around the gate numbered 464.

u follows Jiangxi Road south. Values below are in the plane of the elevation,
digitised from a rectified view of Fayhoo's street photograph.
"""
from pathlib import Path
from math import ceil
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union
from photo_architecture import Facade
from brick import wall_uv

GREY='grey fired brick'; RED='orange red brick'; RED2='shaded red brick'; JOINT='warm mortar'
STONE='pale weathered concrete'; PLINTH='worn grey cement'; WOOD='oxblood painted frames'
GLASS='grey green glass'; IRON='dark folding grille'; DARK='deep window shadow'; GREEN='green door plate'; LETTER='pale numerals'
PALETTE={k:{'color':rgb,'roughness':rough} for k,rgb,rough in [
    (RED,[.64,.345,.244],.91),(RED2,[.555,.293,.219],.90),(JOINT,[.566,.509,.456],.91),
    (STONE,[.726,.708,.675],.9),(PLINTH,[.498,.499,.486],.95),(WOOD,[.364,.206,.189],.71),
    (GLASS,[.254,.32,.321],.36),(IRON,[.286,.282,.245],.74),(DARK,[.185,.19,.188],.97),
    (GREEN,[.16,.302,.196],.81),(LETTER,[.83,.82,.724],.83)]}
PALETTE[GREY]={'color':[1,1,1],'roughness':.94,'texture':str(Path(__file__).with_name('grey-bond.png'))}
HALF=5.66; TOP=11.25
S=28.12/1150
def u(px): return (px-918)*S
def z(py): return (432-py)*TOP/432
def zone(x1,y1,x2,y2): return box(u(x1),z(y2),u(x2),z(y1))
MID=[(735,789),(881,940),(1017,1076)]
UP=[(690,730),(792,842),(895,941),(955,995),(1083,1124)]

def cap(x1,x2,left_z,rise,t,n):
    a=(x1+x2)/2
    return [(x1+(x2-x1)*i/n,left_z+rise*(1-((x1+(x2-x1)*i/n-a)/((x2-x1)/2))**2)+t)for i in range(n+1)]

def opening(x1,x2,bottom,spring,rise,n):
    return Polygon([(x1,bottom),(x2,bottom),*reversed(cap(x1,x2,spring,rise,0,n))])

def red_arch(face,x1,x2,spring,rise,thick,count,label):
    xs=cap(x1,x2,spring,rise,0,count);ys=cap(x1-.09,x2+.09,spring+.07,rise,thick,count)
    shape=Polygon([*xs,*reversed(ys)])
    face.prism(shape,-.026,.027,JOINT,label+' mortar')
    for i in range(count):
        p=Polygon([xs[i],xs[i+1],ys[i+1],ys[i]])
        face.prism(p.buffer(-.006,join_style=2),.027,.058,RED2 if i%6==0 else RED,label+' radial courses')

def framed(face,shape,label,double):
    x1,z1,x2,z2=shape.bounds; w=x2-x1; h=z2-z1
    face.prism(shape,-.225,-.210,GLASS,label+' glass')
    inner=shape.buffer(-.056,join_style=2)
    parts=[shape.difference(inner),box(x1+.03,z1+h*.56-.030,x2-.03,z1+h*.56+.030)]
    if double:parts.append(box((x1+x2)/2-.032,z1+.02,(x1+x2)/2+.032,z2-.03))
    face.prism(unary_union(parts),-.210,-.142,WOOD,label+' frame')
    face.box((x1+x2)/2,z1-.047,w+.18,.094,.31,-.020,STONE,label+' projecting sill')

def grille(face,x1,x2,low,head,distant):
    name='464 folding gate'; h=head-low; count=8; width=(x2-x1)/count
    face.prism(box(x1,low,x2,head),-.352,-.34,DARK,name+' backing')
    for i in range(count+1):
        x=x1+i*width
        face.box(x,(head+low)/2,.024,h,.045,-.218,IRON,name+' stiles')
    for level in range(4):
        za=low+level*h/4; zb=low+(level+1)*h/4
        for k in range(count):
            xa=x1+k*width;xb=xa+width
            line=LineString([(xa,za),(xb,zb)]if (level+k)%2 else[(xb,za),(xa,zb)])
            face.prism(line.buffer(.014 if distant else .018,cap_style=2),-.209,-.171,IRON,name+' diamond braces')

def add_building(b,distant):
    from repeat import repeat_only_texture
    repeat_only_texture(b,'grey-bond.png')
    face=Facade(b,(-HALF,0),(HALF,0),'464 street wall')
    arc_steps=16 if distant else 40
    gate=(u(855),u(954),.08,z(354),.267)
    slit=(u(739),u(787),z(357),z(329),.14)
    blind=(u(1080),u(1138),z(352),z(349),.21)
    windows=[zone(a,181,b,252)for a,b in MID]+[zone(a,39,b,113)for a,b in UP]
    arcs=[opening(*d,arc_steps)for d in (gate,slit,blind)]
    wall=box(-HALF,0,HALF,TOP).difference(unary_union(windows+arcs))
    face.prism(wall,-.89,0,GREY,'perforated grey masonry')
    face.prism(box(-HALF,.04,HALF,z(402)).difference(arcs[0]),.001,.025,PLINTH,'cement plinth')
    face.box(0,.075,HALF*2,.15,.20,.027,PLINTH,'footing')
    for index,(a,spec) in enumerate(zip(arcs,(gate,slit,blind))):
        x1,x2,bot,spring,rise=spec;word=['door','small opening','blocked arch'][index]
        red_arch(face,x1,x2,spring,rise,.24,13 if distant else 25,word)
        if index==2:
            face.prism(a,-.09,-.013,GREY,word+' brick infill')
        else:
            face.prism(a,-.46,-.43,DARK,word+' back')
    grille(face,gate[0]+.045,gate[1]-.045,gate[2],gate[3]-.02,distant)
    for i,win in enumerate(windows):framed(face,win,'middle '+str(i+1)if i<3 else'upper '+str(i-2),True)
    for pos,wide in ((z(206),.074),(z(63),.073)):
        belt=box(-HALF,pos,HALF,pos+wide).difference(unary_union(windows))
        face.prism(belt,.002,.016,RED,'flush red brick belt')
    for level in (z(292),z(145),z(8)):
        face.box(0,level-.135,HALF*2,.16,.23,.025,RED2,'corbel course bed')
        step=.252;num=int(2*HALF/step)
        for j in range(num):
            x=-HALF+(j+.5)*2*HALF/num
            face.box(x,level-.174,.129,.186,.257,.047,RED,'corbel course teeth')
        face.box(0,level+.025,HALF*2,.182,.355,.067,STONE if level<10 else RED2,'projecting cornice')
    # A physical glazed-enamel address plaque over the arched tiled opening.
    mx=(gate[0]+gate[1])/2; cz=gate[3]+gate[4]+.18
    face.box(mx,cz,.285,.211,.038,.081,GREEN,'enamel door plate')
    glyphs={'4':[((0,1),(0,.48)),((0,.48),(1,.48)),((.81,1),(.81,0))],
            '6':[((.9,.95),(.18,1)),((.18,1),(0,.55)),((0,.55),(.03,.12)),((.03,.12),(.78,0)),((.78,0),(.94,.45)),((.94,.45),(0,.48))]}
    for i,num in enumerate('464'):
        cx=mx+(i-1)*.075
        obj=[LineString([(cx+(a-.5)*.054,cz+(b-.5)*.119)for a,b in seg]).buffer(.006,cap_style=2)
             for seg in glyphs[num]]
        face.prism(unary_union(obj),.100,.105,LETTER,'door plate numerals')
    for part in b.parts:
        if part['material']==GREY:part['texcoords']=[wall_uv(*v)for v in part['vertices']]
