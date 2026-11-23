"""The pair on the stair pedestals. One close photograph resolves the fur and forequarters."""
import math

def add_lions(b,lod,stone):
    sides=10 if lod else 18
    def section_cloud(label,stations,points,transform):
        vertices=[];rings=[]
        for x,z,ry,rz in stations:
            ring=[]
            if ry==0 or rz==0:
                ring.append(len(vertices));vertices.append(transform(x,0,z))
            else:
                for k in range(points):
                    a=2*math.pi*k/points;ring.append(len(vertices));vertices.append(transform(x,ry*math.cos(a),z+rz*math.sin(a)))
            rings.append(ring)
        faces=[]
        for left,right in zip(rings,rings[1:]):
            if len(left)==1:faces.extend((left[0],right[(k+1)%points],right[k])for k in range(points))
            elif len(right)==1:faces.extend((left[k],left[(k+1)%points],right[0])for k in range(points))
            else:faces.extend((left[k],left[(k+1)%points],right[(k+1)%points],right[k]) for k in range(points))
        b.add(vertices,faces,stone,label)
    for hand in (-1,1):
        # Right pedestal shows its head at the inner end in the original wide view.
        # The left figure is obscured by a hedge in 2010. Its stance uses the close capture.
        cx=hand*3.62;cy=-1.98;floor=.55;label=('left, detailed close view' if hand<0 else 'right, wide view')+'/carved lion/'
        heading=.055 if hand<0 else math.pi-.10
        co=math.cos(heading);si=math.sin(heading)
        def world(x,y,z):return(cx+co*x-si*y,cy+si*x+co*y,floor+z)
        def solid(name,x,y,z,rx,ry,rz):
            count=5 if lod else 9;sections=[]
            for j in range(count+1):
                a=math.pi*j/count;q=math.sin(a) if 0<j<count else 0
                sections.append((x-rx*math.cos(a),z,ry*q,rz*q))
            section_cloud(label+name,sections,sides,lambda a,e,c:world(a,y+e,c))
        section_cloud(label+'recumbent silhouette',[
           (-.75,.28,0,0),(-.65,.33,.18,.18),(-.52,.38,.285,.255),(-.29,.43,.31,.27),(-.04,.45,.26,.265),
           (.16,.50,.28,.35),(.34,.53,.32,.43),(.52,.53,.27,.40),(.64,.54,.11,.29),(.68,.55,0,0)],sides,world)
        solid('rounded near haunch',-.49,-.18,.32,.305,.185,.23)
        solid('bent hind hock',-.65,-.13,.16,.151,.155,.111)
        solid('far hind paw',-.53,.20,.103,.207,.097,.066)
        solid('lower near foreleg',-.05,-.22,.157,.30,.125,.102)
        solid('forward forepaw',-.29,-.26,.10,.18,.113,.077)
        solid('far forepaw',.09,.20,.094,.185,.112,.068)
        solid('upright neck and mane',.35,0,.70,.285,.278,.39)
        solid('crown and brow',.395,-.019,.938,.212,.194,.217)
        solid('raised muzzle',.559,-.020,.945,.135,.157,.112)
        solid('nose bridge',.594,-.025,1.015,.071,.118,.066)
        for e in (-1,1):
            solid('ear '+str(e),.294,e*.132,1.085,.086,.059,.099)
            solid('eye ridge '+str(e),.501,e*.126,1.033,.078,.037,.031)
        # Locks follow the observed drooping sweep; their shallow relief is never cut through the neck.
        for n in range(4 if lod else 8):
            a=-1.36+n*(2.57/(3 if lod else 7));x=.345+.224*math.cos(a);y=.213*math.sin(a)
            strand=[world(x-.084,y-.017,.993),world(x-.061,y-.042,.904),world(x+.016,y-.047,.78),world(x+.081,y-.035,.64),world(x+.066,y-.020,.52)]
            b.tube(strand,.035 if lod else .033,stone,6 if lod else 9,label+'mane lock '+str(n+1))
        tail=[world(-.32,.215,.43),world(-.53,.241,.38),world(-.69,.155,.235),world(-.71,-.037,.129),world(-.59,-.16,.12)]
        b.tube(tail,.043,stone,6 if lod else 9,label+'tail against folded flank')
