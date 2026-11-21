"""Street elevation above the 213 Yangshupu Road gate, photographed on 16 February 2018."""
from math import cos,pi,sin
from shapely.geometry import LineString,Polygon,box
from shapely.ops import unary_union
from photo_architecture import Facade

COLOURS={'grey pointing':(134,131,124),'grey brick':(139,138,133),'smoke grey brick':(126,125,121),
        'warm grey brick':(143,137,130),'red joint bed':(141,97,87),'vermilion brick':(165,103,86),
        'deep red brick':(149,86,73),'ochre brick':(175,110,91),'pale frame':(203,198,179),
        'fanlight bars':(123,122,101),'fanlight glass':(96,110,103),'sash glass':(73,81,77),
        'sill concrete':(153,147,136)}
def linear(c):
    s=c/255
    return s/12.92 if s<=.04045 else ((s+.055)/1.055)**2.4
PALETTE={n:{'color':[linear(i) for i in c],'roughness':.36 if 'glass' in n else .9} for n,c in COLOURS.items()}
CENTRES=(-.81,.81)
RX=.604
RZ=.535
SPRING=1.51
SILL=.285
def point(x,extra,angle):
    return (x+(RX+extra)*cos(angle), SPRING+(RZ+extra)*sin(angle))
def arc(x,extra,n):
    return [point(x,extra,pi*i/n) for i in range(n+1)]
def arch_hole(x,n):
    return Polygon([(x-RX,SILL),(x+RX,SILL)]+arc(x,0,n))
def add_building(builder,lod=False):
    facade=Facade(builder,(-1,0),(1,0),'213 street windows')
    steps=20 if lod else 44
    openings=unary_union([arch_hole(x,steps).buffer(.017,join_style=2) for x in CENTRES])
    outline=box(-1.61,.02,1.61,2.39)
    facade.prism(outline.difference(openings),-.27,-.014,'grey pointing','brick backing and reveals')
    outside=unary_union([Polygon([(x-RX,SILL),(x+RX,SILL),(x+RX,SPRING)]+arc(x,.175,steps)+[(x-RX,SPRING)]) for x in CENTRES])
    face=outline.difference(outside)
    height=.065 if not lod else .13
    for row in range(int(2.39/height)+1):
        z=.02+row*height
        for k in range(-9,10):
            width=.215 if not lod else .42
            x=k*width+(row%2)*width/2
            tile=box(x+.003,z+.003,x+width-.003,z+height-.003).intersection(face)
            if tile.area>.00007:
                mat=('grey brick','smoke grey brick','warm grey brick')[(row*7+k*5+(k*row)//3)%3]
                facade.prism(tile,-.017,0,mat,f'grey stretchers course {row+1}')
    reds=['vermilion brick','deep red brick','ochre brick']
    for i,x in enumerate(CENTRES):
        name=('west' if i==0 else 'east')+' fanlight'
        intrados=Polygon(arc(x,.18,steps)+list(reversed(arc(x,.019,steps))))
        facade.prism(intrados,-.20,.011,'red joint bed',name+' continuous joint bed')
        for ring,(lo,hi,n) in enumerate([(.001,.142,29),(.146,.177,32)]):
            for k in range(n):
                a=pi*k/n+.004; b=pi*(k+1)/n-.004
                wedge=Polygon([point(x,lo,a),point(x,hi,a),point(x,hi,b),point(x,lo,b)])
                depth=.038 if ring==0 else .048
                if ring==0 and abs((a+b)/2-pi/2)<.09:depth+=.028
                facade.prism(wedge,-.170,depth,reds[(k*7+ring+i)%3],name+' radial bricks '+str(ring+1))
        for side in (-1,1):
            for lev,(lo,hi,w,d) in enumerate([(SPRING-.086,SPRING-.046,.22,.058),(SPRING-.046,SPRING-.010,.265,.075),(SPRING-.010,SPRING+.034,.287,.089)]):
                s=x+side*(RX+.074);facade.prism(box(s-w/2,lo,s+w/2,hi),-.123,d,reds[(lev+i)%3],name+' impost '+str(side))
        # Each fan is a semicircular glazed assembly behind the brick reveals.
        fan=Polygon(arc(x,-.022,steps))
        facade.prism(fan,-.156,-.143,'fanlight glass',name+' fan panes')
        rim=Polygon(arc(x,0,steps)+list(reversed(arc(x,-.031,steps))))
        facade.prism(rim,-.148,-.114,'fanlight bars',name+' curved perimeter')
        for j,a in enumerate((pi/4,pi/2,3*pi/4)):
            bar=LineString([(x,SPRING+.014),point(x,-.025,a)]).buffer(.009 if not lod else .013,cap_style=2)
            facade.prism(bar,-.147,-.109,'fanlight bars',name+' spoke '+str(j+1))
        glazed=box(x-RX+.028,SILL+.035,x+RX-.028,SPRING-.023)
        facade.prism(glazed,-.166,-.153,'sash glass',name+' lower glazing')
        surround=box(x-RX,SILL,x+RX,SPRING).difference(box(x-RX+.036,SILL+.041,x+RX-.036,SPRING-.056))
        facade.prism(surround,-.148,-.078,'pale frame',name+' rectangular sash perimeter')
        facade.prism(box(x-.022,SILL+.041,x+.022,SPRING-.045),-.151,-.084,'pale frame',name+' meeting stile')
        facade.prism(box(x-RX-.055,SILL-.048,x+RX+.055,SILL+.004),-.188,.056,'sill concrete',name+' projecting sill')
    for z,h,width,d,mat in [(2.34,.047,3.245,.035,'vermilion brick'),(2.389,.057,3.285,.073,'deep red brick'),(.116,.038,3.22,.021,'deep red brick')]:
        facade.prism(box(-width/2,z,width/2,z+h),-.27,d,mat,'horizontal brick course')
