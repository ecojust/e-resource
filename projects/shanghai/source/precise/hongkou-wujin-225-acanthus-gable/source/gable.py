"""Wujin Road Lane 225 carved gable photographed in 2009 and 2016.

The local origin is the centre of the acanthus plaque. +X faces right
when looking at the wall, +Y runs into the building, and +Z is up.
"""
from math import floor, sin, cos
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from brick_builder import WujinBuilder as GableBuilder
from courtyard_materials import PLASTER, RED, WHITE, SOFFIT, WOOD, STONE, GUTTER, finish, PALETTE as FACING
from acanthus_relief import PALETTE as RELIEF, add_acanthus_relief
FRAME='Carved gable | faded red painted timber'
GLASS='Carved gable | dusty blue glass'
AWNING='Carved gable | green canvas'
HEM='Carved gable | dark green folded hem'
ROOF='Carved gable | weathered clay roof covering'
MORTAR='Carved gable | pale mortar underneath tiles'
APPLIANCE='Carved gable | pale enamel casing'
VENT='Carved gable | grey appliance grille'
DARK='Carved gable | dark glazed timber'
PALETTE={**FACING,**RELIEF,FRAME:finish([119,63,53]),GLASS:finish([124,149,152],.45,.18),
    AWNING:finish([55,81,65]),HEM:finish([42,65,48]),ROOF:finish([118,86,77]),MORTAR:finish([146,135,122]),
    APPLIANCE:finish([180,176,160],.77,.15),VENT:finish([94,96,87],.73,.18),DARK:finish([61,64,60])}
INFILL='Carved gable | chalky mortar in blocked opening'
PIGMENTS=['Carved gable | weathered infill '+str(i+1) for i in range(7)]
PALETTE[INFILL]=finish([146,124,118])
for label,rgb in zip(PIGMENTS,[(137,101,93),(149,115,106),(155,122,115),(161,129,121),(151,125,122),(159,137,132),(164,141,137)]):
    PALETTE[label]=finish(rgb,.94)
def weathered_infill(b,lod=False):
    # The wall between the sashes is paler than the red pier above and below.
    # Model the 2016 worn face over its original horizontal running bond.
    a,c=-1.015,.903
    bottom,top=.717,3.980
    cube(b,a,c,-.076,-.042,bottom,top,INFILL,'Carved gable | chalky central infill joints')
    course=.063
    unit=.243
    row=0
    while bottom+row*course<top-.012:
        lo=bottom+row*course
        hi=min(top,lo+course)
        x=a-(row%2)*unit*.5
        col=0
        while x<c-.014:
            xl=max(a,x)+.0035
            xr=min(c,x+unit)-.0035
            if xr-xl>.011:
                z=(hi+lo)*.5
                # The uppermost and lowest courses retain more of their red skin.
                fade=min(1.,(z-bottom)/.64,(top-z)/.40)
                grain=sin(19.3*row+5.1*col+1.4)*.72+cos(.27*row-col*.54)*.48
                tint=min(6,max(0,round(.85+3.3*fade+grain)))
                inset=.0 if lod else .0016*(.5+.5*sin(10.*row+7.87*col))
                cube(b,xl,xr,-.080-inset,-.0745,lo+.0026,hi-.0026,PIGMENTS[tint],'Carved gable | infill brick course '+str(row+1))
            col+=1
            x+=unit
        row+=1
    cube(b,a-.023,c+.019,-.100,-.046,top-.018,top+.046,RED,'Carved gable | top course of central infill')
    cube(b,a-.026,c+.024,-.112,-.046,bottom-.055,bottom+.018,RED,'Carved gable | drip beneath infill')
LEFT,RIGHT=-3.01,3.07
BASE=-2.44
PEAK=(-.114,7.89)
WEST=(-3.453,3.503)
EAST=(3.709,3.619)
# The front fascia's sky edge was traced on the 2016 oblique photograph.
# The overhang was estimated against a second, separately registered photograph.
FRONT=-.80
BACK=.78
def section(b,shape,front,back,material,label):
    if not shape.is_empty:
        b.prism(shape,-back,-front,lambda u,v,d:(u,-d,v),material,label)
def cube(b,xl,xr,yl,yr,zl,zr,mat,name):
    b.box(((xl+xr)/2,(yl+yr)/2,(zl+zr)/2),(xr-xl,yr-yl,zr-zl),mat,label=name)
def roof_z(x):
    a,c=(WEST,PEAK) if x<=PEAK[0] else (PEAK,EAST)
    return a[1]+(c[1]-a[1])*(x-a[0])/(c[0]-a[0])
def roof_strip(b,a,c,low,high,y0,y1,material,label):
    poly=Polygon([(a,roof_z(a)+low),(c,roof_z(c)+low),(c,roof_z(c)+high),(a,roof_z(a)+high)])
    section(b,poly,y0,y1,material,label)
def folded_awning(b,left,right,base,tag):
    # The outer edge is lower than the wall fixing. The fascia underneath is visible from the lane.
    poly=Polygon([(-.89,base-.215),(.015,base),(.015,base+.038),(-.89,base-.173)])
    b.prism(poly,left,right,lambda y,z,x:(x,y,z),AWNING,tag+' | sloping green canopy')
    cube(b,left-.012,right+.012,-.909,-.862,base-.285,base-.178,HEM,tag+' | green valance')
    for x in [left+.09,(left+right)/2,right-.09]:
        b.tube([(x,-.024,base-.49),(x,-.84,base-.211)],.015,GUTTER,8,tag+' | iron canopy struts')
        b.tube([(x,-.835,base-.21),(x,-.028,base-.005)],.012,GUTTER,8,tag+' | rails below cover')
def frame(b,left,right,sill,head,tag,lower=False,small=False):
    mat=DARK if small else FRAME
    width=.061 if not small else .032
    rim=box(left,sill,right,head).difference(box(left+width,sill+width,right-width,head-width))
    section(b,rim,.035,.122,mat,tag+' | outer frame')
    centre=(left+right)/2
    cube(b,left+width,right-width,.157,.178,sill+width,head-width,GLASS if not lower else DARK,tag+' | inset glazing')
    cube(b,centre-.019,centre+.019,.073,.150,sill+.039,head-.039,mat,tag+' | central sash')
    if small:return
    trans=head-.52 if not lower else head-.31
    for z,half in [(trans,.034),*[(sill+(trans-sill)*r,.013) for r in ([.5] if lower else [.34,.68])]]:
        cube(b,left+.038,right-.038,.069,.153,z-half,z+half,mat,tag+' | transom and glazing bars')
    for xl,xr in [(left+.062,centre-.017),(centre+.017,right-.062)]:
        for z0,z1 in [(sill+.052,trans-.021),(trans+.023,head-.049)]:
            if z1<=z0+.04:continue
            sash=box(xl,z0,xr,z1).difference(box(xl+.026,z0+.025,xr-.026,z1-.025))
            section(b,sash,.067,.144,mat,tag+' | rebated sash rails')
def add_gable(b,lod=False):
    upper=[(-2.47,-1.24,.53,3.12,'West window'),(1.04,2.48,.58,3.13,'East window')]
    lower=[(-2.16,-1.15,BASE-.21,-1.51,'West lower window'),(1.38,2.33,BASE-.21,-1.52,'East lower window')]
    attic=(1.00,1.51,4.93,5.58,'Small attic opening')
    cuts=unary_union([box(x,z,r,h)for x,r,z,h,n in upper+lower+[attic]])
    profile=Polygon([(LEFT,BASE),(RIGHT,BASE),(RIGHT,roof_z(RIGHT)-.20),(PEAK[0],PEAK[1]-.20),(LEFT,roof_z(LEFT)-.20)])
    lower_wall=box(LEFT,BASE,RIGHT,-.94)
    section(b,lower_wall.difference(cuts),0,.38,WHITE,'Carved gable | limewash below the string course')
    section(b,profile.difference(lower_wall).difference(cuts),0,.38,PLASTER,'Carved gable | blue-grey brick wall')
    # Exposed historical red brick is prominent through the centre of the gable.
    core=profile.intersection(box(-1.04,-.68,.91,PEAK[1]+.1))
    section(b,core,-.049,.006,RED,'Carved gable | red central brick pier')
    weathered_infill(b,lod)
    for z,h,y,tag in [(-.98,.094,-.170,'lower drip'),(-.879,.143,-.116,'lower fascia'),(-.73,.128,-.073,'lower step'),
                       (.487,.059,-.075,'upper sill line'),(.55,.076,-.094,'window sills'),
                       (4.26,.094,-.071,'upper string course'),(4.39,.114,-.117,'projecting upper band')]:
        stripe=box(LEFT-.045,z,RIGHT+.045,z+h).difference(cuts)
        section(b,stripe,y,.014,RED,'Carved gable | '+tag)
    section(b,box(LEFT,-.69,RIGHT,.52).difference(cuts),-.019,.003,RED,'Carved gable | frieze around the sculpture')
    section(b,box(-1.10,-.62,.997,.60),-.081,-.042,RED,'Carved gable | backing behind carved panel')
    add_acanthus_relief(b,lod,dict(x0=-.91,x1=.91,z0=-.55,z1=.55,face_y=-.084))
    for a,c,tag in [(WEST[0],PEAK[0],'West rake'),(PEAK[0],EAST[0],'East rake')]:
        roof_strip(b,a,c,-.165,-.045,FRONT+.027,BACK,SOFFIT,tag+' | pale boarded soffit')
        roof_strip(b,a,c,-.160,-.012,FRONT-.022,FRONT+.055,FRAME,tag+' | painted outer fascia')
        roof_strip(b,a,c,-.011,.023,FRONT-.028,BACK,MORTAR,tag+' | bedding beneath tiles')
        roof_strip(b,a,c,.023,.071,FRONT-.039,BACK,ROOF,tag+' | exposed roof section')
        count=max(10,round((c-a)/(.19 if lod else .10)))
        for i in range(count):
            x=a+(i+.5)*(c-a)/count
            roof_strip(b,x-.007,x+.007,-.178,-.160,FRONT+.045,.073,WOOD,tag+' | narrow soffit board joints')
        for i in range(max(2,round((c-a)/.32))):
            x=a+(i+.5)*.32
            if x>=c-.05:break
            roof_strip(b,x-.011,x+.011,.068,.083,FRONT+.01,BACK,ROOF,tag+' | clay tile joints')
    for x,r,z,h,tag in upper:
        frame(b,x,r,z,h,tag)
        folded_awning(b,x-.23,r+.23,h+.30,tag+' shade')
    for x,r,z,h,tag in lower:
        # The exhibit stops within the downstairs openings, at its documented crop.
        frame(b,x,r,z,h,tag,lower=True)
    frame(b,*attic,small=True)
    # Three air-conditioning casings are visible under the sash sills and above
    # the upper stringcourse in the 2016 reference. The grilles are simplified.
    for x,z,width,tag in [(-2.51,.16,.73,'West sill unit'),(1.39,.40,.72,'East sill unit'),(.08,5.89,.73,'Upper unit')]:
        cube(b,x-width/2,x+width/2,-.388,-.068,z-.245,z+.245,APPLIANCE,tag+' | enamel casing')
        cube(b,x-width*.39,x+width*.24,-.405,-.384,z-.177,z+.177,VENT,tag+' | grille recess')
        for i in range(3 if lod else 9):
            shift=(i+.5)/(3 if lod else 9)
            xx=x-width*.39+width*.63*shift
            cube(b,xx-.009,xx+.009,-.418,-.402,z-.178,z+.178,APPLIANCE,tag+' | front grille slats')
        for xx in (x-width*.35,x+width*.35):
            b.tube([(xx,-.04,z-.45),(xx,-.34,z-.253),(xx,-.026,z-.253)],.018,GUTTER,7,tag+' | wall bracket')
    for x0,x1,label in [(LEFT,LEFT+.13,'West'),(RIGHT-.13,RIGHT,'East')]:
        cube(b,x0,x1,.38,BACK,BASE,-.94,WHITE,label+' | lower masonry return')
        cap=Polygon([(x0,-.94),(x1,-.94),(x1,roof_z(x1)-.21),(x0,roof_z(x0)-.21)])
        section(b,cap,.38,BACK,PLASTER,label+' | upper masonry return')
