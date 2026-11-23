"""Wanping Road 42. Rooftop lattice, arched shoulders and projecting rafter ends.

Measurements refer to the author's 1920px rectification of the 2019 photograph
in the 22m registration. The building's global scale is applied by its Builder.
"""
import math

from shapely.affinity import affine_transform
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from street_materials import GLASS, LIME, STEEL, STONE, finish

# From left to right: lower frame limits, glazing limits and number of sashes.
GLAZED = (
    (184, 218, 269, 301, 1), (451, 491, 571, 608, 2),
    (632, 669, 712, 740, 1), (1116, 1154, 1195, 1226, 1),
    (1246, 1282, 1323, 1351, 1), (1374, 1414, 1495, 1532, 2),
    (1550, 1587, 1628, 1656, 1), (1674, 1712, 1754, 1776, 1),
)
TERMINAL = ((105, 135, 164), (1801, 1824, 1853))
# Tip column, bulkhead column, tip row and upper-face root row respectively.
# The last head is partially cropped in the 2019 frame and confirmed in 2020.
RAFTERS = (
    (16,87,35,79),(96,169,36,80),(230,305,38,80),(370,430,39,81),
    (463,523,42,82),(557,618,42,83),(694,747,43,83),(843,890,49,83),
    (1052,1105,41,85),(1181,1231,39,85),(1323,1365,43,85),
    (1412,1450,42,85),(1503,1543,43,85),(1623,1665,49,86),
    (1770,1795,54,86),(1849,1874,65,87),
)
FRONT_AT_Y0 = (21.00407628947892,-14.22979512771615,1.9841456948782932)
SECTIONS = ((61,840),(1105,1885))
LATTICE = 'Wanping 42 | ivory lattice'
CAP = 'Wanping 42 | pale eave and rafter'
PALETTE = {LATTICE:finish((222,219,201),.79), CAP:finish((193,193,177),.87)}


def plan(x):
    return x/80-12.2


def height(y):
    return 16.75-y/80


def levels(x):
    # The apparent shoulder drops gently towards the right edge of the plane.
    t=(x-100)/1750
    return 99+8*t,119+8*t,234


def section_rect(face,x0,x1,upper,lower,back,front,material,name):
    face.rect(plan(x0),plan(x1),height(lower),height(upper),back,front,material,name)


def lattice_shape(coords, pixels, width):
    ribbons=[LineString(line).buffer(width*.5,cap_style=2,join_style=2) for line in coords]
    return unary_union(ribbons).intersection(pixels)


def world_shape(shape):
    return affine_transform(shape,[1/80,0,0,-1/80,-12.2,16.75])


def slats(left,right,top,bottom):
    """Diagonal strips are clipped to the actual side-panel opening."""
    width=right-left
    lines=[]
    for n in range(-1,7):
        mid=top+n*width
        lines.extend([[(left,mid),(right,mid+width)],[(left,mid),(right,mid-width)]])
    return lattice_shape(lines,box(left,top,right,bottom),2.35)


def curved_head(x0,x1,y,sag,kind,steps):
    if kind=='glazing':
        # Upper half of an elliptical moulding over each individual sash.
        return [(x0+(x1-x0)*(1-math.cos(math.pi*t/steps))/2,
                 y-sag*math.sin(math.pi*t/steps)) for t in range(steps+1)]
    # Each flanking shoulder sweeps towards its adjacent sash. It has a
    # horizontal tangent at the outside stile and an oblique foot at the sash.
    return [(x0+(x1-x0)*t/steps,y-sag+sag*(t/steps)**1.65) for t in range(steps+1)]


def add_bay(face,number,bay,lod):
    left,gl,gr,right,count=bay
    top,rail,base=levels((left+right)/2)
    name=f'roof light {number:02d}'
    section_rect(face,left,right,top,base,-.15,-.13,LIME,name+' recess lining')
    hole=box(gl,rail+2,gr,base)
    inner=hole.buffer(-2.2,join_style=2)
    face.solid(world_shape(hole.difference(inner)),-.071,-.046,STEEL,name+' sash perimeter')
    face.solid(world_shape(inner),-.087,-.071,GLASS,name+' glazing')
    if count==2:
        x=(gl+gr)/2
        section_rect(face,x-1.3,x+1.3,rail+2,base,-.071,-.044,STEEL,name+' meeting stile')
    elif number in (1,3):
        section_rect(face,gl,gr,rail+40,rail+42,-.071,-.044,STEEL,name+' lower rail')
    shapes=[slats(left,gl,rail,base),slats(gr,right,rail,base),box(left,rail-1,right,rail+1)]
    lines=[curved_head(left,gl,rail,rail-top,'side',6 if lod else 14),curved_head(right,gr,rail,rail-top,'side',6 if lod else 14)]
    for n in range(count):
        lines.append(curved_head(gl+(gr-gl)*n/count,gl+(gr-gl)*(n+1)/count,rail,rail-top,'glazing',8 if lod else 18))
    for x in [left,gl,gr,right]:
        shapes.append(box(x-1,top,x+1,base))
    shapes.append(lattice_shape(lines,box(left,top-1,right,rail+1),2.25))
    face.solid(world_shape(unary_union(shapes)),-.019,.007,LATTICE,name+' diagonal and archwork')


def add_terminal(face,num,part,lod):
    a,m,c=part
    top,rail,bottom=levels(m)
    name=f'roof end screen {num}'
    section_rect(face,a,c,top,bottom,-.15,-.13,LIME,name+' recessed plaster')
    bars=[slats(a,m,rail,bottom),slats(m,c,rail,bottom),box(a,rail-1,c,rail+1),
          box(m-1,top,m+1,bottom)]
    for x in (a,c):
        bars.append(box(x-1,top,x+1,bottom))
        bars.append(lattice_shape([curved_head(x,m,rail,rail-top,'side',6 if lod else 14)],box(a,top-1,c,rail+1),2.25))
    face.solid(world_shape(unary_union(bars)),-.019,.007,LATTICE,name+' diagonal and shoulder')


def rafter_points(mark):
    tip,root,tip_row,root_row=mark
    cx,cy,cz=FRONT_AT_Y0
    u=plan(root)
    t=(u-cx)/(plan(tip)-cx)
    return u,cy*(1-t),cz+t*(height(tip_row)-cz),height(root_row)


def add_rafter(face,index,row):
    u,d,z,z0=rafter_points(row)
    # Use the measured tip's image ray and the facade-normal axis. Positive d
    # enters the house. The unobservable bearing length is set to 0.28m.
    profile=Polygon([(d,z-.074),(d,z),(.0,z0),(.28,z0),(.28,z0-.074),(.0,z0-.074)])
    side=face.face(u,0,0,1)
    side.solid(profile,-.066,.066,CAP,f'projecting rafter {index:02d}')


def add_roof_lattice(face,lod=False):
    for n,bay in enumerate(GLAZED,1):
        add_bay(face,n,bay,lod)
    for n,part in enumerate(TERMINAL,1):
        add_terminal(face,n,part,lod)
    segments=sorted((a,d) for a,b,c,d,n in GLAZED)
    segments+= [(a,c) for a,m,c in TERMINAL]+[(312,424),(758,838)]
    for n,(a,b) in enumerate(SECTIONS,1):
        local=sorted((i,j) for i,j in segments if a<=i and j<=b)
        start=a
        for i,j in local+[(b,b)]:
            if i>start:
                top,rail,base=levels((start+i)/2)
                section_rect(face,start,i,top-1,241,-.25,-.005,LIME,f'attic pier {n}.{int(start)}')
            start=j
        top1=levels(a)[0];top2=levels(b)[0]
        shape=Polygon([(a,top1),(b,top2),(b,top2-12),(a,top1-12)])
        face.solid(world_shape(shape),-.29,.034,CAP,f'eave fascia {n}')
        section_rect(face,a,b,234,241,-.22,.017,STONE,f'attic sill {n}')
    section_rect(face,312,424,102,234,-.16,-.14,LIME,'later enclosed opening | face')
    section_rect(face,345,420,122,234,-.134,-.111,GLASS,'later enclosed opening | glazed panel')
    for u in (345,383,418):
        section_rect(face,u,u+2.7,121,234,-.11,-.067,LIME,'later enclosed opening | sash')
    # At the left of the central yellow head the actual image only resolves
    # a short metal guard. The space behind this portion is left open.
    for u in (764,783,802,821,834):
        section_rect(face,u,u+1.3,120,232,-.13,-.092,STEEL,'open end railing | uprights')
    for y in (119,224):
        section_rect(face,763,837,y,y+1.8,-.13,-.091,STEEL,'open end railing | rail')
    for i,m in enumerate(RAFTERS,1):
        add_rafter(face,i,m)
