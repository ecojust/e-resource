"""Bilingual name relief, moulded side gables and the decorated courtyard cornice."""
from math import cos,pi,sin
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from photo_architecture import opening
from sign_lettering import add_facade_lettering
from pavilion_materials import CREAM,EDGE,CUT,WOOD,DARK,BLACK,MOSAIC,MOSAIC_DARK,FONT
from pavilion_windows import framed

def border(face,outline,width,back,front,label):
    inset=outline.buffer(-width,join_style=2)
    face.prism(outline.difference(inset),back,front,EDGE,label)


def central_gable(face,lod):
    base=11.80
    shoulder=14.57
    # Segment the shallow central arc separately from the two sloping tympana.
    right=[(8.72,base),(8.72,base+.10),(3.73,shoulder),(3.73,16.28),(3.57,16.34),(3.27,16.29),(3.27,16.17)]
    crest=[(3.27*cos(pi*i/24),16.17+.54*sin(pi*i/24)**2) for i in range(1,24)]
    outer=Polygon([(-8.72,base),*right,*crest,*[(-x,z) for x,z in reversed(right)][:-1]])
    window=box(-1.205,12.52,1.205,13.86)
    face.prism(outer.difference(window),-.40,0,CREAM,'central pediment with real attic opening')
    border(face,outer,.105,-.015,.11,'outer pediment coping')
    for side in [-1,1]:
        wing=Polygon([(side*8.22,12.04),(side*3.68,12.04),(side*3.68,14.12)])
        border(face,wing,.10,.009,.075,'triangular recessed field')
        face.box(side*3.55,15.30,.22,2.02,.18,.075,EDGE,'central tablet flanking pier')
    plate=Polygon([(-3.17,14.85),(3.17,14.85),(3.17,15.72)]
                  +[(3.17*cos(pi*i/20),15.72+.22*sin(pi*i/20)**2) for i in range(1,21)])
    border(face,plate,.08,.012,.11,'raised outline around French title')
    add_facade_lettering(face,'MATERNITÉ',0,15.31,5.25,.49,.058,.135,EDGE,font=FONT,label='raised French maternity title')
    for u,z,text in [(-4.30,13.10,'慈'),(-2.45,14.19,'科'),(2.45,14.19,'產'),(4.30,13.10,'廣')]:
        add_facade_lettering(face,text,u,z,.53,.55,.035,.112,EDGE,font=FONT,label='Chinese maternity relief')
    frame=window.buffer(.17,join_style=2).difference(window)
    face.prism(frame,.015,.16,EDGE,'rectangular attic window hood')
    framed(face,window,'attic four-light window',lod,4,[(13.32,.072)],None)
    for side in (-1,1):
        for z,width in ((13.90,1.49),(13.67,1.59),(13.43,1.62)):
            face.box(side*2.61,z,width,.085,.18,.078,EDGE,'courses under tablet shoulders')
        for i in range(5):
            u=side*(2.0+i*.305)
            face.prism(Polygon([(u-.09,13.66),(u+.09,13.66),(u+.062,13.49),(u,13.43),(u-.062,13.49)]),
                       .05,.18,EDGE,'pendants under tablet shoulders')
    for z,w in ((13.98,3.12),(14.09,3.30)):
        face.box(0,z,w,.086,.19,.067,EDGE,'courses above attic window')
    return outer


def shaped_gable(face,x,lod):
    # Elevated central curve, short shoulders, two concave returns, straight lower rakes.
    left=[(-3.98,11.65),(-3.98,12.43),(-2.75,13.14),(-2.21,13.47),(-1.94,13.80),
          (-1.81,14.19),(-1.79,14.50),(-1.56,14.53),(-1.52,14.67)]
    curve=[(-1.52+3.04*i/20,14.67+.52*sin(pi*i/20)**1.4) for i in range(21)]
    contour=[(x+u,z)for u,z in left[:-1]+curve+[(-u,z)for u,z in reversed(left[:-1])]]
    body=Polygon(contour)
    win=opening(x,12.21,2.59,1.68,.46,segments=12 if lod else 26)
    face.prism(body.difference(win),-.45,0,CREAM,'curved attic gable')
    border(face,body,.115,-.014,.111,'curved attic coping')
    arch=win.buffer(.13,join_style=2).difference(win)
    face.prism(arch,.015,.115,EDGE,'curved attic casing')
    framed(face,win,'four-light segmental dormer',lod,4,[(12.82,.055)],None)
    face.box(x,12.18,2.88,.105,.26,.054,CUT,'curved attic window sill')
    return body


def frieze(face,left,right,z,lod):
    face.prism(box(left,z,right,z+1.30),-.08,.068,CREAM,'mosaic frieze ground')
    for dz,h,d in ((-.05,.095,.12),(.08,.07,.12),(1.21,.07,.13)):
        face.box((left+right)/2,z+dz,right-left,h,d,.08,EDGE,'horizontal frieze mouldings')
    # The small grey tesserae form crosses and diamonds interrupted by timber corbels.
    pitch=.145
    for j in range(4):
        for i in range(int((right-left)/pitch)):
            pattern=(i%8,j)
            if pattern not in {(0,0),(4,0),(1,1),(3,1),(5,1),(7,1),(2,2),(4,2),(6,2),(2,3),(6,3)}:continue
            if lod and j==3:continue
            u=left+(i+.5)*pitch;h=z+.37+j*pitch
            face.box(u,h,.134,.134,.035,.084,MOSAIC_DARK if (i+j)%5==0 else MOSAIC,'glazed mosaic tile pattern')


def building_number(face):
    shape=box(-.58,9.60,.58,10.53)
    face.prism(shape,.075,.126,CUT,'number plaque edge')
    face.prism(shape.buffer(-.047,join_style=2),.123,.156,EDGE,'enamel building number plate')
    add_facade_lettering(face,'8',0,10.07,.43,.59,.155,.185,BLACK,font=FONT,label='pavilion number')
