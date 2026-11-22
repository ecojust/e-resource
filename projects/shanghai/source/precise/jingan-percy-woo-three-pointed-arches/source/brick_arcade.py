"""Measured pointed brick windows and pair of spiral shafts on the red face of the Percy Woo residence."""
from math import acos,cos,sin,pi
from shapely.geometry import Polygon,box as rectangle
from shapely.ops import unary_union

def color(rgb,roughness=.82,metallic=0):
    def linear(v):return v/3294.6 if v<=10 else ((v/255+.055)/1.055)**2.4
    return dict(color=[linear(v)for v in rgb],roughness=roughness,metallic=metallic)
PALETTE={
    'pale joint':color((165,139,120)),'recessed lime':color((208,202,171)),
    'cut stone':color((208,197,162)),'soffit shadow':color((168,157,130)),
    'spiral stone':color((206,194,161)),'capital return':color((187,174,142)),
    'carved highlight':color((220,208,174)),'deep grey sash':color((73,85,80)),
    'patinated green':color((74,100,94)),'glazing shadow':color((79,105,120),.31,.08),
    'blue glazing':color((104,139,151),.27,.12),'lower stucco':color((206,195,166))
}
for i,rgb in enumerate([(149,80,58),(156,83,62),(137,72,55),(169,91,67),(158,86,62)]):
    PALETTE[f'face brick {i+1}']=color(rgb)
CENTERS=(-1.22,0,1.22)
AXES=(-.61,.61)
HALF=.505
SPRING=2.08
RISE=.76
MAPPER=lambda x,z,depth:(x,-depth,z)

def box(b,x0,x1,y0,y1,z0,z1,material,label):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),material,label=label)

def curve(c,side,t,thickness=0):
    shift=(HALF**2-RISE**2)/(2*HALF); r=HALF-shift
    angle=t*acos(-shift/r)
    x=c+side*(shift+(r+thickness)*cos(angle))
    return x,SPRING+(r+thickness)*sin(angle)
def opening(c,segments,extra=0):
    right=[curve(c,1,k/segments,extra) for k in range(segments+1)]
    left=[curve(c,-1,k/segments,extra) for k in reversed(range(segments+1))]
    return Polygon([(c+HALF+extra,SPRING-.025),*right,*left,(c-HALF-extra,SPRING-.025)]).buffer(0)
def arch(b,c,j,lod):
    n=9 if lod else 12
    for side in (-1,1):
        for i in range(n):
            a,d=(i+.045)/n,(i+.955)/n
            steps=[a,(a+d)/2,d]
            if i==n-1:
                # The two facing last joints meet on the central arris.
                outer=[curve(c,side,t,.105) for t in steps]
                outer[-1]=(c,SPRING+RISE+.105)
            else:outer=[curve(c,side,t,.105) for t in steps]
            outline=Polygon([*(curve(c,side,t)for t in steps),*reversed(outer)]).buffer(0)
            b.prism(outline,-.018,.019,MAPPER,f'face brick {(j+2*i+(side==1))%5+1}',f'arch {j+1} radial brick {side} {i+1}')
    interior=opening(c,12 if lod else 26)
    b.prism(interior,-.25,-.113,MAPPER,'recessed lime',f'blind pointed head over window {j+1}')

def twist(b,x,index,lod):
    bottom,top=.03,1.948
    around,rows=(18,54) if lod else (38,120)
    vertices=[];faces=[];pitch=.243
    for j in range(rows+1):
        z=bottom+(top-bottom)*j/rows
        for k in range(around):
            angle=2*pi*k/around
            bevel=cos(2*angle-2*pi*(z-bottom)/pitch)
            r=.093+.018*(.5+.5*bevel)**1.5
            vertices.append((x+r*cos(angle),-.012+r*sin(angle),z))
    for j in range(rows):
        for k in range(around):
            a=j*around+k;b1=j*around+(k+1)%around
            faces.append((a,b1,b1+around,a+around))
    faces.extend([tuple(range(around-1,-1,-1)),tuple(range(rows*around,(rows+1)*around))])
    b.add(vertices,faces,'spiral stone',f'twisted shaft {index+1}')
    b.lathe((x,-.012),[(1.92,.092),(1.936,.108),(1.949,.12),(1.963,.117),(1.974,.104),(1.998,.115),(2.032,.144)],
            'capital return',16 if lod else 32,f'neck and bell on shaft {index+1}')
    for k,(hw,front,back,z0,z1,mat) in enumerate([(.128,-.151,.116,2.008,2.029,'capital return'),(.146,-.165,.129,2.028,2.057,'cut stone'),(.162,-.174,.145,2.057,2.077,'carved highlight')]):
        box(b,x-hw,x+hw,front,back,z0,z1,mat,f'cut cap {index+1} course {k+1}')
    for side in (-1,1):
        pts=[]
        for j in range(12 if lod else 29):
            t=j/(11 if lod else 28);ang=pi*.13+pi*2.02*t;r=.028*(1-.82*t)
            pts.append((x+side*(.100+r*cos(ang)),-.151,2.018+r*sin(ang)))
        b.tube(pts,.007,'carved highlight',5 if lod else 8,f'capital volute {index+1} {side}')
        b.tube([(x+side*.016,-.125,1.968),(x+side*.033,-.136,1.986),(x+side*.055,-.149,2.007)],.006,'carved highlight',5 if lod else 8,f'capital leaf {index+1} {side}')

def add_building(b,lod=False):
    holes=unary_union([opening(c,18 if lod else 42)for c in CENTERS])
    shoulders=rectangle(-1.95,SPRING,1.95,3.12).difference(holes)
    b.prism(shoulders,-.32,.0,MAPPER,'pale joint','wall pierced by three lancets')
    outer=unary_union([opening(c,18 if lod else 42,.109)for c in CENTERS])
    wall=shoulders.difference(outer);height=.065;length=.221
    for j in range(16):
        z=SPRING+j*height;shift=.5*length*(j%2)
        for i in range(20):
            left=-2.09+i*length-shift
            patch=rectangle(left+.004,z+.003,left+length-.004,min(3.12,z+height-.003)).intersection(wall)
            if patch.area>.0001:
                b.prism(patch,-.001,.005,MAPPER,f'face brick {(i*3+j*2)%5+1}',f'brickwork course {j+1} unit {i+1}')
    for j,c in enumerate(CENTERS):
        arch(b,c,j,lod)
        box(b,c-HALF,c+HALF,.039,.30,1.982,2.077,'cut stone',f'flat window head under pointed brick {j+1}')
        box(b,c-HALF-.007,c+HALF+.007,.061,.29,.031,.38,'lower stucco',f'stucco apron {j+1}')
        box(b,c-HALF-.015,c+HALF+.015,.028,.30,.35,.398,'cut stone',f'window sill {j+1}')
        width=.83;a=c-width/2;d=c+width/2
        for k,(x0,x1) in enumerate([(c-HALF,a),(d,c+HALF)]):
            box(b,x0,x1,.08,.27,.39,1.983,'recessed lime',f'inner jamb {j+1}-{k+1}')
        for name,x0,x1 in [('left',a,a+.035),('right',d-.035,d),('middle',c-.019,c+.019)]:
            box(b,x0,x1,.152,.23,.403,1.37 if name=='middle' else 1.982,'patinated green',f'painted sash {j+1} {name}')
        for k,(z0,z1) in enumerate([(.401,.437),(1.370,1.417),(1.632,1.675),(1.947,1.981)]):
            box(b,a,d,.144,.25,z0,z1,'deep grey sash',f'sash rail {j+1} level {k+1}')
        for k,(x0,x1) in enumerate([(a+.035,c-.019),(c+.019,d-.035)]):
            mat='blue glazing' if (j+k)%3 else 'glazing shadow'
            box(b,x0,x1,.207,.22,.437,1.37,mat,f'lower window glass {j+1}-{k+1}')
        for h,(z0,z1) in enumerate([(1.417,1.632),(1.675,1.947)]):
            mat='blue glazing' if (j+h)%3 else 'glazing shadow'
            box(b,a+.035,d-.035,.207,.22,z0,z1,mat,f'continuous upper transom glass {j+1}-{h+1}')
    for j,x in enumerate(AXES):twist(b,x,j,lod)
    for side in (-1,1):
        xs=sorted([side*1.95,side*(CENTERS[-1]+HALF)])
        box(b,*xs,0,.3,.03,SPRING,'pale joint',f'side pier {side}')
        for j in range(31):
            z=.031+j*.066
            b.prism(rectangle(xs[0]+.004,z+.002,xs[1]-.004,z+.064),0,.005,MAPPER,
                    f'face brick {(j+2*side)%5+1}',f'side pier {side} course {j+1}')
