"""Paired exposed-aggregate columns and the arch at 1, Lane 66 Xiangde Road."""
from math import cos, sin, pi
from random import Random


def stone(rgb):
    return {'color': [((v / 255 + .055) / 1.055) ** 2.4 for v in rgb], 'roughness': .94}


PALETTE = {
    'washed aggregate': stone((157, 149, 128)),
    'moulded stone': stone((172, 161, 139)),
    'deep groove': stone((101, 94, 82)),
    'arch soffit': stone((146, 136, 120)),
    'grey pebble': stone((138, 132, 115)), 'pale pebble': stone((174, 168, 150)),
}
SPRING = 2.52
RADIUS_X = .737
RISE = .555


def block(b, left, right, front, back, bottom, top, material, label):
    b.box(((left + right)/2, (front + back)/2, (bottom + top)/2),
          (right-left, back-front, top-bottom), material, label=label)


def prism(b, outline, front, back, material, label):
    count = len(outline)
    points = [(x, y, z) for y in (front, back) for x, z in outline]
    faces = [(0, i, i+1) for i in range(1, count-1)]
    faces += [(count, count+i+1, count+i) for i in range(1, count-1)]
    faces += [(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
    b.add(points, faces, material, label)


def column(b, x, lod, side):
    count = 20 if lod else 44
    profile = [(0,.225),(.054,.231),(.083,.222),(.105,.223),(.134,.210),
               (.165,.206),(1.41,.201),(2.164,.189),(2.181,.203),(2.209,.205)]
    pts = [(x+radius*cos(2*pi*j/count), radius*sin(2*pi*j/count), z)
           for z,radius in profile for j in range(count)]
    faces = [(k*count+j,k*count+(j+1)%count,(k+1)*count+(j+1)%count,(k+1)*count+j)
             for k in range(len(profile)-1) for j in range(count)]
    faces += [tuple(reversed(range(count))), tuple(range((len(profile)-1)*count,len(profile)*count))]
    b.add(pts, faces,'washed aggregate', side+' round shaft and foot mouldings')
    # Narrow surface grains are hand-distributed procedurally to represent washed stone.
    rng=Random(7161 if x<0 else 7193)
    clusters={'grey pebble':([],[]),'pale pebble':([],[])}
    for i in range(105 if lod else 740):
        z=rng.uniform(.18,2.14);theta=rng.uniform(pi,2*pi);spread=rng.uniform(.0015,.0042)
        radius=.206+(.201-.206)*(z-.165)/(1.41-.165) if z<=1.41 else .201+(.189-.201)*(z-1.41)/(2.164-1.41)
        # Match the polygonal circular shaft, so a chip rests on a real face.
        step=2*pi/count;mid=(int(theta/step)+.5)*step
        radius=radius*cos(step/2)/cos(theta-mid)+.0006
        verts,indices=clusters['grey pebble' if i%3 else 'pale pebble']
        base=len(verts)
        for offset,dz in ((-spread,0),(0,-spread*.7),(spread,spread*.21),(0,spread*.86)):
            angle=theta+offset/radius;verts.append((x+radius*cos(angle),radius*sin(angle),z+dz))
        indices.extend([(base,base+1,base+2),(base,base+2,base+3)])
    for mat,(verts,indices) in clusters.items():
        b.add(verts,indices,mat,side+' '+mat+' on front half of shaft')
    block(b,x-.213,x+.213,-.207,.207,2.208,2.374,'moulded stone',side+' capital core')
    for orientation in ('front','outer'):
        for sign in (-1,1):
            def face(u,v,z):
                return ((x+u,v,z) if orientation=='front' else
                        (x+(-1 if x<0 else 1)*(-v),u,z))
            u=sign*.142
            steps=16 if lod else 38
            verts=[face(u+.077*cos(2*pi*i/steps), v, 2.254+.077*sin(2*pi*i/steps))
                   for v in (-.234,-.188) for i in range(steps)]
            idx=range(steps)
            faces=[tuple(idx),tuple(range(2*steps-1,steps-1,-1))]+[
                (i,(i+1)%steps,(i+1)%steps+steps,i+steps) for i in idx]
            b.add(verts,faces,'moulded stone',f'{side} {orientation} volute {sign}')
            path=[]
            for i in range(steps+1):
                t=i/steps;theta=sign*(pi*.60+2*pi*1.35*t)
                path.append(face(u+(.064-.053*t)*cos(theta),-.237,2.254+(.064-.053*t)*sin(theta)))
            b.tube(path,.0046,'deep groove',5 if lod else 8,f'{side} {orientation} volute incision {sign}')
    for j,(width,deep,z0,z1) in enumerate([
        (.248,.246,2.334,2.369),(.262,.256,2.369,2.399),(.251,.253,2.399,2.428),
        (.274,.273,2.428,2.446),(.285,.283,2.446,2.481),(.294,.290,2.481,2.526)]):
        block(b,x-width,x+width,-deep,deep,z0,z1,'moulded stone',side+' impost course '+str(j+1))


def add_building(b, lod=False):
    for x,side in [(-1.05,'left'),(1.05,'right')]:
        column(b,x,lod,side)
    count=32 if lod else 76
    for i in range(count):
        a0=pi*i/count; a1=pi*(i+1)/count
        def arch(a,margin):
            return ((RADIUS_X+margin)*cos(a),SPRING+(RISE+margin)*sin(a))
        lower0,lower1=arch(a0,0),arch(a1,0)
        prism(b,[lower0,lower1,(lower1[0],3.355),(lower0[0],3.355)],-.198,.28,'washed aggregate','arched spandrel')
        for j,(inner,outer,front,material) in enumerate([(0,.043,-.236,'arch soffit'),(.043,.076,-.246,'moulded stone'),
                          (.077,.119,-.208,'washed aggregate'),(.119,.134,-.225,'moulded stone'),(.134,.149,-.236,'moulded stone')]):
            prism(b,[arch(a0,inner),arch(a1,inner),arch(a1,outer),arch(a0,outer)],
                  front,-.19,material,'elliptical archivolt course '+str(j+1))
    for left,right in [(-1.346,-RADIUS_X),(RADIUS_X,1.346)]:
        block(b,left,right,-.198,.28,SPRING,3.355,'washed aggregate','wall over pier')
    prism(b,[(-.08,3.065),(.08,3.065),(.107,3.291),(-.107,3.291)],-.27,-.188,'moulded stone','projecting keystone')
    for i in range(-3,4):
        x=i*.020
        b.tube([(x,-.2705,3.104),(x*1.17,-.2705,3.271)],.0035,'deep groove',
               4 if lod else 8,'keystone narrow vertical groove')
    for i,(front,z0,z1) in enumerate([(-.209,3.34,3.369),(-.244,3.369,3.394),(-.267,3.394,3.432)]):
        block(b,-1.36,1.36,front,.283,z0,z1,'moulded stone','upper stringcourse '+str(i+1))
