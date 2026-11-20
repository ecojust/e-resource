"""Photo-proportioned 2021 stone panels. Units match the original Bund 18 builder."""
import math

# Door-axis frame from the existing facade edge. Positions entered as across, inward, height.
A=(28.161,-7.221)
B=(25.781,22.657)
C=tuple((a+b)/2 for a,b in zip(A,B))
length=math.dist(A,B)
T=tuple((b-a)/length for a,b in zip(A,B))
N=(-T[1],T[0])
HEIGHT_SCALE=1.037
STONE='Carved_limestone_trim'

def world(u,d,z):
    return C[0]+T[0]*u+N[0]*d,C[1]+T[1]*u+N[1]*d,z*HEIGHT_SCALE

def local(e,n,h):
    x,y=e-C[0],n-C[1]
    return x*T[0]+y*T[1],x*N[0]+y*N[1],h/HEIGHT_SCALE

def is_old_rosette(u,d,z):
    return (abs(u)<.414)&(d>=-.576)&(d<=-.459)&(z>5.46)&(z<6.30)

def stonework(lod=False):
    parts=[]
    def prism(name,outline,back,front,material=STONE):
        # Planar outline follows the facade as seen from the street.
        if sum(x*q-u*y for (x,y),(u,q) in zip(outline,outline[1:]+outline[:1]))<0:
            outline=list(reversed(outline))
        points=[(x,d,z) for d in [front,back] for x,z in outline];count=len(outline)
        # Every prism here has a convex elevation outline.
        faces=[(0,i,i+1) for i in range(1,count-1)]
        faces += [(count,count+i+1,count+i) for i in range(1,count-1)]
        for i in range(count):
            j=(i+1)%count
            faces.extend([(i,count+i,count+j),(i,count+j,j)])
        parts.append((name,material,points,faces))
    def box(name,u,z,w,h,back,front,material=STONE):
        prism(name,[(u-w/2,z-h/2),(u+w/2,z-h/2),(u+w/2,z+h/2),(u-w/2,z+h/2)],back,front,material)
    def frame(name,u,z,w,h,width,back,front):
        for side in (-1,1):
            box(f'{name}.jamb{side:+}',u+side*(w-width)/2,z,width,h,back,front)
            box(f'{name}.rail{side:+}',u,z+side*(h-width)/2,w-2*width,width,back,front)
    def rim(name,u,z,rx,rz,nested,steps):
        points=[];faces=[]
        for scale,depth in nested:
            for i in range(steps):
                a=2*math.pi*i/steps
                points.append((u+scale*rx*math.cos(a),depth,z+scale*rz*math.sin(a)))
        for layer in range(len(nested)-1):
            for i in range(steps):
                j=(i+1)%steps;a=layer*steps+i;b=layer*steps+j;c=b+steps;d=a+steps
                faces.extend([(a,b,c),(a,c,d)])
        top=(len(nested)-1)*steps
        faces += [(top,top+i,top+i+1) for i in range(1,steps-1)]
        parts.append((name,STONE,points,faces))
    box('Continuous lower sill',0,5.433,3.54,.095,-.54,-.696)
    box('Raised sill lip',0,5.488,3.44,.038,-.548,-.665)
    for side in (-1,1):
        tag='North' if side==1 else 'South'
        u=.80*side
        box(tag+' recessed field',u,5.81,.84,.61,-.545,-.595)
        frame(tag+' lower field surround',u,5.748,.82,.310,.048,-.59,-.662)
        box(tag+' lower field inset',u,5.748,.694,.19,-.598,-.628)
        box(tag+' upper field inset',u,6.049,.79,.106,-.585,-.619)
        box(tag+' upper field lintel',u,6.127,.85,.035,-.559,-.658)
        # Sloping bed and lip follow the shallow cap above the plaque and side fields.
        for part,depth,shift in [('bed',-.665,0),('drip',-.728,.045)]:
            o=[(.31*side,6.184+shift),(1.56*side,6.070+shift),(1.56*side,6.148+shift),(.31*side,6.274+shift)]
            prism(tag+' sloping crown '+part,o,-.53,depth)
        box(tag+' stop',1.496*side,5.76,.13,.54,-.54,-.642)
        # Carved side consoles widen toward the sill. Overlaid stepped profiles follow the visible return.
        for part,front,delta in [('body',-.66,0),('lip',-.705,.035)]:
            # Join successive sections separately to retain the inward curvature.
            left=[(1.233+delta,5.52),(1.27+delta,5.65),(1.29+delta,5.81),(1.32+delta,6.044)]
            right=[(1.48+delta,5.52),(1.42+delta,5.65),(1.38+delta,5.81),(1.37+delta,6.044)]
            for i in range(3):
                quad=[left[i],right[i],right[i+1],left[i+1]]
                prism(f'{tag} console {part} {i+1}',[(x*side,h)for x,h in quad],-.552,front)
    prism('Central tablet', [(-.36,5.49),(.36,5.49),(.36,6.286),(0,6.322),(-.36,6.286)],-.548,-.683)
    prism('Central crown lip',[(-.392,6.183),(.392,6.183),(.392,6.301),(0,6.348),(-.392,6.301)],-.560,-.716)
    rim('Plain stone roundel and moulded rim',0,5.835,.343,.339,
        [(1.,-.680),(1.,-.705),(.958,-.734),(.91,-.745),(.884,-.728),(.861,-.727)],24 if lod else 64)
    return parts
