"""Joinery in the rectangular openings of both photographed faces at No. 2."""
from shapely.geometry import box
from shapely.ops import unary_union
from house_finishes import STEEL,SILL

ALUMINIUM='280-2 | silver grey replacement frame'
DARK_GLASS='280-2 | dim garden reflection'
LIGHT_GLASS='280-2 | pale sky reflection'
GRILLE='280-2 | weather-darkened grille'
CERAMIC='280-2 | reddish brown sill tiles'
JOINT='280-2 | grey sill bedding'
PALETTE={
    ALUMINIUM:{'color':[.42,.46,.46],'metallic':.56,'roughness':.49},
    DARK_GLASS:{'color':[.13,.175,.165],'metallic':.22,'roughness':.36},
    LIGHT_GLASS:{'color':[.225,.276,.29],'metallic':.24,'roughness':.36},
    GRILLE:{'color':[.104,.104,.095],'metallic':.44,'roughness':.72},
    CERAMIC:{'color':[.365,.192,.120],'roughness':.79},
    JOINT:{'color':[.36,.338,.288],'roughness':.95}}

def add_grille(face,aperture,label,lod):
    x0,z0,x1,z1=aperture.bounds
    span=x1-x0
    rim=aperture.buffer(.022,join_style=2).difference(aperture.buffer(-.018,join_style=2))
    face.prism(rim,.087,.117,GRILLE,label+' exterior grille rim')
    strips=[]
    count=max(3,round(span/.145))
    for i in range(1,count):
        x=x0+span*i/count
        strips.append(box(x-.008,z0,x+.008,z1))
    for fraction in [.20,.53,.85]:
        z=z0+fraction*(z1-z0)
        strips.append(box(x0,z-.009,x1,z+.009))
    face.prism(unary_union(strips),.094,.105,GRILLE,label+' grille rods')
    if not lod:
        for x in (x0+.045,x1-.045):
            for z in (z0+.045,z1-.045):
                face.box(x,z,.035,.032,.105,.050,GRILLE,label+' return holdfast')

def add_projecting_sill(face,aperture,label,lod):
    x0,z0,x1,_=aperture.bounds
    x0-=.085;x1+=.085
    # In the direct winter view two independent reddish sill bands have a
    # continuous upper lip and narrow vertical joints across the front.
    face.prism(box(x0,z0-.29,x1,z0-.024),.015,.277,JOINT,label+' bedding')
    face.prism(box(x0-.019,z0-.037,x1+.019,z0+.016),.001,.305,SILL,label+' projecting top edge')
    count=max(5,round((x1-x0)/(.23 if lod else .12)))
    for i in range(count):
        left=x0+(x1-x0)*i/count
        right=x0+(x1-x0)*(i+1)/count
        face.prism(box(left+.002,z0-.268,right-.002,z0-.039),.268,.289,CERAMIC,label+' front tile '+str(i+1))

def add_window(face,aperture,face_name,code,lod=False):
    x0,z0,x1,z1=aperture.bounds
    width=x1-x0;height=z1-z0
    bank=code[0];storey=int(code[1]);label=face_name+' '+code
    square=bank=='B' if face_name=='south' else bank in ('D','F','S')
    retrofit=storey==2
    material=ALUMINIUM if retrofit else STEEL
    columns=2 if square else (3 if bank in ('A','F') else 5)
    if face_name=='south' and bank=='E':columns=3
    if retrofit and not square:columns=3 if bank in ('A','E') else 4
    outer=.045 if square else (.057 if retrofit else .049)
    inner=box(x0+outer,z0+outer,x1-outer,z1-outer)
    frame=aperture.difference(inner)
    bars=[]
    thickness=.048 if retrofit else .028
    for n in range(1,columns):
        x=x0+width*n/columns
        bars.append(box(x-thickness/2,z0+outer,x+thickness/2,z1-outer))
    if square:
        transoms=[] if height<1.15 or retrofit else [.30]
    elif retrofit:
        transoms=[]
    else:
        transoms=[.23,.71]
    for fraction in transoms:
        z=z0+height*fraction
        bars.append(box(x0+outer,z-.016,x1-outer,z+.016))
    sections=unary_union([frame,*bars])
    face.prism(sections,-.094,-.040,material,label+' surround and glazing bars')
    glazing=aperture.difference(sections)
    for k,pane in enumerate(getattr(glazing,'geoms',[glazing])):
        face.prism(pane,-.113,-.096,LIGHT_GLASS if (k+storey)%4==1 else DARK_GLASS,label+' pane '+str(k+1))
    if not square:
        face.prism(box(x0-.026,z0-.033,x1+.026,z0+.002),-.045,.033,SILL,label+' narrow sill arris')
    if storey==1 and bank=='A' and face_name=='south':
        add_grille(face,aperture,label,lod)
    if storey==1 and bank in ('C','E') and face_name=='south':
        add_projecting_sill(face,aperture,label,lod)
