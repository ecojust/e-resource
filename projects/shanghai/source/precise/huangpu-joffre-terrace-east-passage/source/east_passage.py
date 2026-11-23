"""Upper east entrance at 100 South Maoming Road. X north, Y into the lane, Z up."""
from math import cos, sin, pi
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union
from photo_architecture import Facade

PALETTE = {
    'grey cement': {'color':[.60,.584,.553],'roughness':.92},
    'weathered cement': {'color':[.53,.522,.496],'roughness':.94},
    'stone trim': {'color':[.65,.638,.602],'roughness':.83},
    'joint shadows': {'color':[.37,.365,.346],'roughness':.93},
    'dark wood': {'color':[.16,.15,.14],'roughness':.64},
    'slender metal': {'color':[.14,.15,.145],'roughness':.56,'metallic':.25},
    'upper glazing': {'color':[.38,.445,.445],'roughness':.30,'metallic':.11},
    'lower glazing': {'color':[.225,.277,.273],'roughness':.36,'metallic':.12},
    'shadowed pane': {'color':[.171,.210,.208],'roughness':.37},
    'lettering': {'color':[.205,.207,.195],'roughness':.84},
    'old metal flashing': {'color':[.34,.347,.334],'roughness':.62,'metallic':.28},
    'soffit plaster': {'color':[.475,.467,.433],'roughness':.92},
}
HALF=3.56
LINTEL=3.79
CORNICE=12.88
WINDOWS=[(side*1.66,sill,1.37,head-sill,upper)for upper,sill,head in [(False,5.68,7.30),(True,8.94,10.65)]for side in [-1,1]]

def strip(points,width):
    return LineString(points).buffer(width/2,cap_style=2,join_style=2)

def chamber(b,x,sill,width,height,upper,detail):
    name=('north' if x>0 else 'south')+(' upper'if upper else ' lower')
    f=Facade(b,(-HALF,0),(HALF,0),name+' window')
    head=sill+height
    lo=x-width/2;hi=x+width/2
    # Behind a pierced outer wall, a stepped frame, separate panes and two leaves.
    frame=box(lo,sill,hi,head).difference(box(lo+.068,sill+.073,hi-.068,head-.073))
    f.prism(frame,-.233,-.154,'dark wood','rebated outer frame')
    f.box(x,sill-.035,width+.27,.10,.27,.040,'stone trim','overhanging sill')
    f.box(x,head+.060,width+.30,.12,.32,.04,'stone trim','hood')
    if detail:
        f.box(x,head+.145,width+.37,.056,.37,.058,'stone trim','hood drip')
        f.box(x,sill-.10,width+.15,.042,.21,.04,'weathered cement','sill underside')
    nx,ny=((2,2) if x>0 else (2,1)) if upper else (6,5)
    xmin,xmax=lo+.065,hi-.065;zmin,zmax=sill+.066,head-.067
    zs=[zmin,(zmax-.27),zmax]if upper and ny==2 else[zmin+(zmax-zmin)*i/ny for i in range(ny+1)]
    xs=[xmin+(xmax-xmin)*i/nx for i in range(nx+1)]
    core='dark wood'if upper else'slender metal'
    f.box(x,(sill+head)/2,.066 if upper else .048,height-.12,.085,-.16,core,'central meeting stile')
    for xx in xs[1:-1]:
        if abs(xx-x)>.04:f.box(xx,(sill+head)/2,.024,height-.12,.048,-.183,core,'vertical glazing bar')
    for zz in zs[1:-1]:
        f.box(x,zz,width-.11,.045 if upper else .027,.048,-.178,core,'transom bars')
    for i in range(nx):
        for k in range(ny):
            a,c=xs[i],xs[i+1];d,e=zs[k],zs[k+1]
            mat='upper glazing'if upper else 'shadowed pane'if detail and(i+k)%4==0 else'lower glazing'
            f.box((a+c)/2,(d+e)/2,c-a-.014,e-d-.014,.032,-.231,mat,'individual lights')
    if detail:
        for xx in [lo+.094,hi-.094]:
            f.box(xx,(head+sill)/2,.027,height-.18,.042,-.15,core,'sash beading')
        f.box(x+.057,sill+height*.51,.022,.102,.042,-.124,'slender metal','small casement catch')

def raised_stone(b,face,x):
    """Square shallow-faceted panels on the spandrels beneath the upper windows."""
    hw=.53;z=8.12;hz=.37
    y=-.025
    verts=[(x-hw,y,z-hz),(x+hw,y,z-hz),(x+hw,y,z+hz),(x-hw,y,z+hz),(x+.086,y-.10,z-.054)]
    if x<0:
        b.add(verts,[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],'grey cement','spandrel/south faceted field')
    else:
        face.box(x,z,2*hw,2*hz,.076,.031,'grey cement','north plain spandrel')
    face.prism(box(x-hw-.04,z-hz-.04,x+hw+.04,z+hz+.04).difference(box(x-hw,z-hz,x+hw,z+hz)),.005,.026,'weathered cement','spandrel border')

def corbels(face,sign,detail):
    x=sign*2.83;z=11.82
    face.box(x,z+.13,1.03,.17,.55,.12,'stone trim','corbel hood')
    face.box(x,z+.245,1.08,.071,.61,.14,'stone trim','hood coping')
    for j in (-1,0,1):
        xx=x+j*.33;sz=.17
        for k in range(4 if detail else 2):
            step=(k+.5)/(4 if detail else 2)
            face.box(xx,z-.365+.37*step,sz+.105*step,.37/(4 if detail else 2),.23+.21*step,.08+.033*step,'stone trim','tapered three corbels')
        if detail:face.box(xx,z-.39,.17,.048,.22,.078,'weathered cement','corbel foot')

# Stroke skeletons are original diagrams of three legible characters, in cap-height units.
RADICAL=[[(.12,.90),(.22,.82)],[(.085,.65),(.19,.585)],[(.11,.23),(.205,.34),(.27,.49)]]
GLYPHS={
'淮':RADICAL+[[(.49,.94),(.42,.78),(.32,.65)],[(.405,.76),(.405,.14)],[(.64,.94),(.71,.85)],[(.435,.79),(.91,.79)],[(.64,.78),(.64,.19)],[(.43,.61),(.86,.61)],[(.43,.42),(.86,.42)],[(.43,.21),(.92,.21)]],
'海':RADICAL+[[(.49,.95),(.42,.80),(.31,.67)],[(.435,.83),(.9,.83)],[(.45,.66),(.405,.30),(.825,.30)],[(.45,.66),(.83,.66),(.773,.16),(.676,.18)],[(.30,.49),(.94,.49)],[(.57,.60),(.64,.54)],[(.555,.415),(.625,.345)]],
'坊':[[(.18,.86),(.18,.35)],[(.062,.67),(.32,.67)],[(.048,.30),(.35,.405)],[(.55,.94),(.64,.85)],[(.345,.75),(.94,.75)],[(.598,.735),(.56,.53),(.49,.35),(.35,.16)],[(.575,.59),(.853,.59),(.80,.24),(.735,.15),(.64,.20)]]}

def inscription(face,detail):
    cx=0;z=5.00;W=1.61;H=.49
    face.box(cx,z,W+.22,H+.14,.074,.027,'stone trim','title stone surround')
    face.box(cx,z,W+.09,H+.040,.044,.065,'weathered cement','inset title stone')
    strokes=[]
    for i,g in enumerate('淮海坊'):
        for branch in GLYPHS[g]:
            pts=[((i-1)*.477+(.88*xx-.44)*.46,z+(zz-.5)*.476)for xx,zz in branch]
            strokes.append(strip(pts,.025 if detail else .033))
    face.prism(unary_union(strokes),.086,.098,'lettering','three raised lane characters')
    for side in [-1,1]:
        x=side*1.47
        theta=[pi*i/(24 if detail else 10)for i in range((24 if detail else 10)+1)]
        shape=strip([(x+.262*cos(t),z-.043+.216*sin(t))for t in theta],.052)
        face.prism(shape,.0,.031,'weathered cement','semicircular field beside name')

def add_building(b,lod=False):
    face=Facade(b,(-HALF,0),(HALF,0),'east passage')
    holes=[box(x-width/2,sill,x+width/2,sill+height)for x,sill,width,height,_ in WINDOWS]
    shoulder=CORNICE-.42
    extent=box(-HALF,LINTEL,HALF,shoulder).union(box(-2.60,shoulder,2.60,CORNICE))
    pierced=extent.difference(unary_union(holes))
    face.prism(pierced,-.40,-.012,'joint shadows','pierced wall bed')
    if lod:face.prism(pierced,-.023,.0,'grey cement','plastered face')
    else:
        courses=[LINTEL,4.19,4.50,4.76,5.30,5.63,6.04,6.49,6.90,7.30,7.68,8.10,8.50,8.93,9.36,9.78,10.20,10.64,11.10,11.55,11.96,12.42,CORNICE]
        for row,(low,high)in enumerate(zip(courses,courses[1:])):
            cuts=[-HALF]+[x for x in [-3.55+i*1.37+(.67 if row%2 else 0)for i in range(6)]if -HALF+.06<x<HALF-.06]+[HALF]
            for a,c in zip(cuts,cuts[1:]):
                piece=box(a+.006,low+.005,c-.006,high-.005).intersection(pierced)
                if piece.area:face.prism(piece,-.021,.0,'grey cement'if (row+round(a*2))%11 else'weathered cement','faced block courses')
    for x,sill,w,h,u in WINDOWS:chamber(b,x,sill,w,h,u,not lod)
    for side in [-1,1]:
        x=side*(HALF-.17)
        face.box(x,(LINTEL+shoulder)/2,.30,shoulder-LINTEL,.32,.044,'stone trim','edge pilaster')
        face.box(x,shoulder-.07,.38,.14,.37,.06,'stone trim','raised end block')
        face.box(x,shoulder+.022,.42,.045,.44,.072,'old metal flashing','end coping')
        face.box(side*3.08,shoulder-.035,.99,.076,.37,.045,'stone trim','lower stepped parapet cap')
        corbels(face,side,not lod)
        raised_stone(b,face,side*1.66)
    face.box(0,LINTEL+.20,2*HALF,.40,.72,-.14,'soffit plaster','flat passage lintel')
    face.box(0,4.23,2*HALF+.04,.13,.52,-.036,'stone trim','long lintel drip')
    face.box(0,CORNICE-.04,5.26,.105,.41,.01,'stone trim','parapet coping')
    if not lod:face.box(0,CORNICE+.026,5.25,.055,.46,.01,'old metal flashing','thin weathering cap')
    # The grey underside is visible above the through-lane. The measured section ends behind the frontage.
    face.box(0,LINTEL+.068,2*HALF-.37,.135,1.30,-.82,'soffit plaster','open passage ceiling')
    inscription(face,not lod)
