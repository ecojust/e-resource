"""The central south doorway of the former Jiangsu Inn, from the photographed lane side."""
from math import cos, sin, pi
from shapely.affinity import scale, translate
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade

PLASTER='weathered pale lime plaster'
STONE='grey carved stone'
IVORY='light raised stucco'
WOOD='red brown sash'
GLASS='grey blue glazing'
IRON='dark green iron leaves'
BLK='dark transom grille'
PLAQUE='green enamel address'
NUM='ivory number strokes'
SHADOW='unlit entry beyond sightline'
CORNICE='weathered limestone edge'
PALETTE={mat:{'color':color,'roughness':rough} for mat,color,rough in [
    (PLASTER,[.76,.743,.691],.93),(STONE,[.555,.544,.510],.85),
    (IVORY,[.844,.817,.760],.86),(WOOD,[.380,.195,.174],.71),
    (GLASS,[.262,.319,.327],.37),(IRON,[.182,.269,.222],.69),
    (BLK,[.166,.156,.141],.65),(PLAQUE,[.119,.338,.220],.59),
    (NUM,[.869,.865,.800],.71),(SHADOW,[.100,.102,.091],.99),
    (CORNICE,[.616,.594,.553],.83)]}
HALF=2.12
ENTRY=.83
def ellipse(x,z,rx,rz,n):return translate(scale(Point(0,0).buffer(1,quad_segs=n),xfact=rx,yfact=rz),xoff=x,yoff=z)
def line(points,r):return LineString(points).buffer(r,cap_style=2,join_style=2)
def strip(f,x,z,w,h,back,front,mat,name):
    f.prism(box(x-w/2,z,x+w/2,z+h),back,front,mat,name)
def draw_number(f,lod):
    x=1.015;z=2.51
    strip(f,x,z-.105,.275,.210,.010,.039,PLAQUE,'green address plate')
    zero=ellipse(x+.052,z+.010,.036,.061,5 if lod else 10)
    hole=ellipse(x+.052,z+.010,.021,.045,5 if lod else 10)
    five=line([(x-.018,z+.065),(x-.078,z+.065),(x-.082,z+.010),
               (x-.047,z+.018),(x-.020,z+.007),(x-.014,z-.018),
               (x-.025,z-.045),(x-.055,z-.053),(x-.082,z-.039)],.009)
    f.prism(unary_union([zero.difference(hole),five]),.039,.045,NUM,'raised address 50')
def shutter(b,x,sign,lod):
    # Two green leaves stand ajar against the jambs in the 2015 and later photographs.
    hinge=(x,-.025);end=(x-sign*.142,-.63)
    f=Facade(b,hinge,end,'green cut steel leaf')
    w=f.length;lo=.04;hi=2.18
    outer=box(-w/2,lo,w/2,hi);inside=outer.buffer(-.042,join_style=2)
    slots=[box(-w/2+w*i/(6 if lod else 10)-.010,lo,-w/2+w*i/(6 if lod else 10)+.010,hi)
           for i in range(1,6 if lod else 10)]
    rails=[box(-w/2,z,w/2,z+.030) for z in [.14,1.12,1.97]]
    f.prism(outer.difference(inside.difference(unary_union(slots+rails))),-.012,.020,IRON,'open green barred leaf')
def wood_window(f,x,sill,width,height,lod,attic=False):
    outer=box(x-width/2,sill,x+width/2,sill+height);inner=outer.buffer(-.070,join_style=2)
    panels=2 if attic else 4;step=width/panels
    bars=[box(x-width/2+step*i-.020,sill,x-width/2+step*i+.020,sill+height)for i in range(1,panels)]
    if attic:
        bars.append(box(x-width/2,sill+height*.60,x+width/2,sill+height*.60+.033))
    else:
        for z in [.21,.46]:bars.append(box(x-width/2,sill+z,x+width/2,sill+z+.026))
        for k in range(panels):
            mid=x-width/2+(k+.5)*step
            rhomb=line([(mid-step*.48,sill+height*.56),(mid,sill+height*.89),(mid+step*.48,sill+height*.56)],.017 if lod else .012)
            bars.append(rhomb)
            if not lod:bars.append(line([(mid-step*.46,sill+height*.86),(mid,sill+height*.54),(mid+step*.46,sill+height*.86)],.010))
    f.prism(outer,-.204,-.187,GLASS,'inset attic glass' if attic else 'four glazed casements')
    f.prism(outer.difference(inner.difference(unary_union(bars))),-.178,-.089,WOOD,'attic sash' if attic else 'pointed wood casements')
    f.prism(outer.buffer(.057,join_style=2).difference(outer),.003,.069,CORNICE,'window opening reveal')
    strip(f,x,sill-.085,width+.24,.085,-.025,.159,CORNICE,'projecting window sill')
    strip(f,x,sill+height+.006,width+.25,.090,-.022,.206,STONE,'window lintel and drip')
    return outer
def scroll(f,cx,cz,rx,rz,lod,side,name):
    pts=[]
    n=14 if lod else 34
    for i in range(n+1):
        t=i/n;ang=.16*pi+1.82*pi*t;decay=1-.77*t
        pts.append((cx+side*rx*decay*cos(ang),cz+rz*decay*sin(ang)))
    f.prism(line(pts,.020 if lod else .014),.043,.091,IVORY,name)
def ground_columns(b,f,lod):
    for hand in [-1,1]:
        x=hand*1.46;side='west' if hand<0 else 'east'
        b.lathe([x,-.12],[(.09,.195),(.22,.197),(.245,.173),(.29,.163),
            (2.49,.154),(2.55,.160),(2.57,.184),(2.63,.186),(2.67,.176)],
            STONE,14 if lod else 26,side+' round entrance column')
        strip(f,x,0,.46,.145,-.10,.330,CORNICE,side+' base plinth')
        strip(f,x,2.63,.50,.185,-.08,.327,STONE,side+' capital block')
        for h in [-1,1]:
            center=x+h*.166
            ring=ellipse(center,2.69,.099,.095,5 if lod else 10)
            f.prism(ring,.323,.368,IVORY,side+' entrance volute disc')
            inn=ellipse(center,2.69,.070,.065,5 if lod else 10)
            f.prism(inn.difference(inn.buffer(-.020)),.369,.385,STONE,side+' volute rim')
        strip(f,x,2.81,.56,.104,-.08,.34,CORNICE,side+' capital abacus')
def pediment(f,lod):
    # Central blind attic shoulders frame a narrow opening under the pitched stone crest.
    outline=Polygon([(-1.99,7.02),(-1.99,7.91),(-1.81,7.91),(-1.81,8.59),
        (-1.55,8.59),(-1.55,8.91),(-1.21,8.91),(0,9.56),(1.21,8.91),
        (1.55,8.91),(1.55,8.59),(1.81,8.59),(1.81,7.91),(1.99,7.91),(1.99,7.02)])
    att=wood_window(f,0,7.61,.91,1.25,lod,True)
    f.prism(outline.difference(att),-.33,.002,PLASTER,'stepped attic plane')
    for s in [-1,1]:
        for xx,head,wide in [(1.36,8.91,.245),(1.73,8.59,.180)]:
            x=s*xx
            strip(f,x,7.05,wide,head-7.05,-.05,.115,IVORY,'paired attic pilasters')
            strip(f,x,head-.066,wide+.105,.082,-.02,.183,CORNICE,'stepped pier caps')
    roofline=[(-1.26,8.91),(0,9.60),(1.26,8.91)]
    f.prism(line(roofline,.049),-.08,.123,CORNICE,'gabled stone cap')
    f.prism(line([(x,z-.074)for x,z in roofline],.023),.004,.094,IVORY,'lower gable mould')
def install(b,lod):
    f=Facade(b,(-HALF,0),(HALF,0),'south portal')
    entry=box(-ENTRY,0,ENTRY,2.83)
    main=wood_window(f,0,4.69,1.76,1.39,lod)
    face=box(-HALF,0,HALF,7.04).difference(unary_union([entry,main]))
    f.prism(face,-.35,0,PLASTER,'pier and solid street wall')
    # Only visible passage entrance and shaded reveal are shown. The six courts stay outside this fragment.
    strip(f,0,0,ENTRY*2,.028,-.94,.065,STONE,'doorway threshold')
    strip(f,0,.03,ENTRY*2,2.31,-1.01,-.99,SHADOW,'shaded passage extent')
    for side in [-1,1]:
        strip(f,side*(ENTRY+.03),.03,.075,2.62,-.98,-.31,STONE,'inner entrance reveal')
        shutter(b,side*(ENTRY-.036),side,lod)
    strip(f,0,2.25,ENTRY*2,.56,-.39,-.378,SHADOW,'transom shadow')
    for z in [2.27,2.43,2.59,2.77]:
        strip(f,0,z,ENTRY*2,.032,-.18,-.113,BLK,'horizontal entrance grille')
    strip(f,0,2.82,2.28,.076,-.055,.242,IRON,'green painted door hood')
    draw_number(f,lod);ground_columns(b,f,lod)
    for z,w,h,front in [(2.93,3.75,.11,.218),(3.11,3.76,.10,.240),
        (4.41,3.88,.10,.118),(4.56,3.96,.085,.190),(6.87,4.05,.105,.215),(7.00,4.24,.105,.278)]:
        strip(f,0,z,w,h,-.09,front,CORNICE,'horizontal band '+str(z))
    panel=box(-1.20,3.24,1.20,4.35)
    f.prism(panel.difference(panel.buffer(-.065,join_style=2)),.014,.094,IVORY,'raised rectangular spandrel')
    for h in (-1,1):
        x=h*1.56
        strip(f,x,4.59,.36,2.22,-.035,.108,PLASTER,'upper square pier')
        strip(f,x,6.35,.48,.115,-.015,.159,STONE,'upper pier shoulder')
        strip(f,x,6.66,.51,.18,-.022,.194,IVORY,'upper pier capital')
        flutes=[box(x+i*.047-.009,6.47,x+i*.047+.009,6.65) for i in range(-3,4)]
        f.prism(unary_union(flutes),.110,.137,CORNICE,'square capital flutes')
    crest=ellipse(0,6.41,.177,.210,6 if lod else 13)
    f.prism(crest,.021,.089,STONE,'elliptical cartouche field')
    f.prism(crest.difference(crest.buffer(-.034)),.090,.132,IVORY,'cartouche relief rim')
    for h in (-1,1):
        for dx,sz in [(.32,1.),(.58,.82),(.79,.54)]:
            scroll(f,h*dx,6.45+(dx-.32)*.11,.155*sz,.12*sz,lod,h,'mirrored plant scroll')
        leaf=Polygon([(h*.76,6.46),(h*.95,6.55),(h*.83,6.39),(h*.69,6.40)])
        f.prism(leaf,.041,.087,IVORY,'leaf beside cartouche')
    pediment(f,lod)
