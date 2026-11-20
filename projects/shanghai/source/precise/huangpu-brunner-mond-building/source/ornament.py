"""Original surviving 2020 shell, scroll and acanthus shapes at 133 Middle Sichuan Road."""
import math
import numpy as np
from shapely.geometry import Polygon

STONE='dressed limestone'
LIGHT='pale cement ornament'
SAND='weathered buff stucco'


def spiral(face,u,z,radius,side,depth,wire,lod,label):
    angles=np.linspace(-.25*math.pi,2.50*math.pi,16 if lod else 38)
    path=[]
    for i,a in enumerate(angles):
        r=radius*(1-.86*i/(len(angles)-1))
        path.append(face.point(u+side*r*math.cos(a),z+r*math.sin(a),depth))
    face.builder.tube(path,wire,LIGHT,5 if lod else 8,face.label+'/'+label)


def leaf(face,u,z,w,h,d,side,lod,label='acanthus'):
    # Broad lobes, a pointed tip and a protruding central rib form a closed folded leaf.
    raw=[(0,0),(-.25,.08),(-.46,.29),(-.34,.34),(-.52,.52),(-.30,.51),
         (-.39,.70),(-.21,.65),(-.20,.83),(0,1.),(.19,.80),(.19,.67),
         (.38,.71),(.30,.51),(.51,.53),(.34,.34),(.46,.30),(.25,.09)]
    if lod:raw=[(0,0),(-.4,.28),(-.26,.36),(-.38,.61),(-.19,.7),(0,1.),(.2,.68),(.38,.61),(.27,.38),(.4,.28)]
    points=Polygon([(u+side*(x*w+.12*h*y*y),z+y*h)for x,y in raw])
    face.prism(points,d,d+.056,LIGHT,label+' lobes')
    face.builder.tube([face.point(u,z+.02,d+.07),face.point(u+side*.028*h,z+h*.47,d+.12),
                       face.point(u+side*.115*h,z+h*.89,d+.084)],.025 if lod else .031,
                      LIGHT,5 if lod else 7,face.label+'/'+label+' ribs')


def capital(face,u,z,w,lod):
    # In the 2013 and 2020 photos the two central capitals and the two outer
    # pilaster heads carry foliage. The present lower supports have no atlantes.
    face.box(u,z+.13,w*.91,.24,.29,.18,STONE,'capital foot')
    face.box(u,z+.51,w*1.05,.64,.34,.235,SAND,'capital core')
    for i,x in enumerate(np.linspace(-.36,.36,5 if not lod else 3)):
        leaf(face,u+x*w,z+.05,w*.32,.64,.40,-1 if i%2==0 else 1,lod,'folded capital foliage')
    for dx in (-1,1):
        leaf(face,u+dx*w*.30,z+.30,w*.40,.56,.43,dx,lod,'outer acanthus')
        spiral(face,u+dx*w*.41,z+.69,w*.113,dx,.55,.035,lod,'volute curls')
    face.box(u,z+.90,w*1.18,.15,.52,.19,LIGHT,'capital upper abacus')


def shell_pediment(face,u,z,lod):
    # Three ridged triangular mouldings sit below a separate fan-shaped shell.
    # The 2020 head-on image shows a shell flanked by symmetrical spirals.
    tri=Polygon([(u-2.58,z),(u,z+.94),(u+2.58,z)])
    face.prism(tri,-.02,.42,SAND,'triangular tympanum')
    for offset,projection,depth in ((0,.47,.085),(.13,.54,.072),(.27,.61,.064)):
        points=[face.point(u-2.63,z+offset,projection),face.point(u,z+.96+offset,projection),
                face.point(u+2.63,z+offset,projection)]
        face.builder.tube(points,depth,LIGHT,6 if lod else 8,face.label+'/pediment sloping mouldings')
    face.box(u,z-.04,5.21,.20,.43,.23,STONE,'pediment horizontal sill')
    root=z+1.03
    points=[(u-.65,root-.16)]
    for a in np.linspace(math.pi,0,25 if lod else 57):
        r=1.+.07*math.cos(a*12)
        points.append((u+1.01*r*math.cos(a),root+.09+1.01*r*math.sin(a)))
    points.append((u+.65,root-.16))
    face.prism(Polygon(points),.073,.283,LIGHT,'central scallop shell')
    for ang in np.linspace(.16,math.pi-.16,8 if lod else 14):
        top=(u+.94*math.cos(ang),root+.14+.94*math.sin(ang))
        face.builder.tube([face.point(u+.09*math.cos(ang),root-.10,.297),
                           face.point(u+.48*math.cos(ang),root+.12+.44*math.sin(ang),.36),
                           face.point(*top,.294)],.039,LIGHT,5 if lod else 8,face.label+'/shell flutes')
    for side in (-1,1):
        scroll=Polygon([(u+side*.48,root-.16),(u+side*.72,root+.53),(u+side*1.13,root+.58),
                        (u+side*1.48,root+.31),(u+side*1.91,root+.20),(u+side*2.19,root-.23),
                        (u+side*2.35,root-.64),(u+side*.75,root-.10)])
        face.prism(scroll,.060,.244,STONE,'scrolled shell supports')
        spiral(face,u+side*1.14,root+.19,.36,side,.286,.050,lod,'large shell scroll')
        spiral(face,u+side*1.76,root-.18,.21,-side,.281,.042,lod,'small shell scroll')
        leaf(face,u+side*1.85,root-.50,.69,.71,.27,side,lod,'pediment leaf')
