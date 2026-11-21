"""One upper bay of the former Anglo-Chinese School on Wujin Road."""
from math import cos, sin, pi, sqrt, hypot
COLOURS = {
    'dark grey brick': (98,99,94), 'grey stretcher': (119,118,110), 'pointing': (142,138,126),
    'radial red brick': (159,92,78), 'dark fired brick': (141,77,65), 'grey voussoir': (129,119,107),
    'rust red joinery': (111,55,51), 'red painted bars': (127,60,54), 'scroll highlight': (137,66,59),
    'grey pane': (145,159,157), 'pale pane': (160,174,171), 'limestone edge': (181,177,158),
}
def linear(c):
    t=c/255
    return t/12.92 if t<=.04045 else ((t+.055)/1.055)**2.4
PALETTE={k:{'color':[linear(c) for c in rgb],'roughness':.35 if 'pane' in k else .89} for k,rgb in COLOURS.items()}
SPRING=1.47
RX=1.56
RZ=1.23
def box(b,k,material,x0,x1,front,back,z0,z1):
    b.box(((x0+x1)/2,(front+back)/2,(z0+z1)/2),(x1-x0,back-front,z1-z0),material,label=k)
def slab(b,k,material,points,front,back):
    # Convex section ordered counterclockwise in the x/z elevation.
    if sum(x*v-u*z for (x,z),(u,v) in zip(points,points[1:]+points[:1]))<0:points=list(reversed(points))
    n=len(points);verts=[(x,y,z)for y in (front,back)for x,z in points]
    triangles=[]
    for j in range(1,n-1):triangles.extend([(0,j,j+1),(n,n+j+1,n+j)])
    for j in range(n):
        q=(j+1)%n;triangles.extend([(j,n+j,n+q),(j,n+q,q)])
    b.add(verts,triangles,material,k)
def anglepoint(angle,inc):
    return ((RX+inc)*cos(angle),SPRING+(RZ+inc)*sin(angle))
def ring(b,name,start,end,front,back,number,palette,gap=.0):
    for i in range(number):
        a=pi*i/number+gap;c=pi*(i+1)/number-gap
        slab(b,f'{name} {i+1}',palette(i),[anglepoint(a,start),anglepoint(a,end),anglepoint(c,end),anglepoint(c,start)],front,back)
def top(x,gap=0):
    return SPRING+(RZ-gap)*sqrt(max(0.,1-(x/(RX-gap))**2))
def brickwork(b,lod):
    # Running-bond grey masonry meets the outside radial course; bay cropped at the crown.
    bound=2.05;maxz=3.14;step=.12 if lod else .072
    for i in range(int(maxz/step)+1):
        z0=max(.155,i*step+.003);z1=min(maxz,(i+1)*step-.003)
        if z1<=z0:continue
        for side in (-1,1):
            def edge(z):
                if z<.885:return 1.58
                if z<SPRING:return 1.90
                return (RX+.34)*sqrt(max(0.,1-((z-SPRING)/(RZ+.34))**2)) if z<SPRING+RZ+.34 else 0.
            xl0=edge(z0);xl1=edge(z1)
            positions=[-0.12 if i%2 else 0.]
            while positions[-1]<bound:positions.append(min(bound,positions[-1]+(.47 if lod else .239)))
            for j,(a,c) in enumerate(zip(positions,positions[1:])):
                a0=max(xl0,a+.003,0);a1=max(xl1,a+.003,0);rc=c-.003
                if rc<=max(a0,a1)+.004:continue
                col='grey stretcher' if (i+2*j)%6==0 else 'dark grey brick'
                slab(b,f'Grey masonry {side} {i} {j}',col,[(side*a0,z0),(side*rc,z0),(side*rc,z1),(side*a1,z1)],-.02,.19)
            if min(xl0,xl1)<bound:
                slab(b,f'Mortar background {side} {i}','pointing',[(side*xl0,z0-.003),(side*bound,z0-.003),(side*bound,z1+.003),(side*xl1,z1+.003)],.004,.2)
    ring(b,'Backing at radial brick and horizontal wall junction',.315,.425,.050,.18,64 if not lod else 36,lambda i:'dark grey brick')
    ring(b,'Arch backing',0,.347,-.03,.20,48 if not lod else 24,lambda i:'pointing')
    ring(b,'Recessed red reveal',-.05,.031,-.048,.11,48 if not lod else 30,lambda i:'dark fired brick')
    ring(b,'Inner concentric red soldiers',.033,.121,-.078,-.027,56 if not lod else 30,lambda i:'dark fired brick' if i%6==0 else 'radial red brick',.0017)
    ring(b,'Stepped inner moulding',.124,.166,-.105,-.025,48 if not lod else 26,lambda i:'dark fired brick')
    n=64 if not lod else 32
    ring(b,'Bichrome brick arch',.172,.326,-.064,-.027,n,lambda i:('grey voussoir' if (i*8//n)%2==0 else 'radial red brick'),.0017 if not lod else .0012)
    ring(b,'Narrow outer brick edging',.328,.355,-.089,-.024,52 if not lod else 28,lambda i:'dark fired brick')
    for side in (-1,1):
        x0,x1=sorted((1.54*side,1.902*side))
        box(b,f'Side masonry behind red jamb {side}','dark grey brick',x0,x1,.005,.18,.805,SPRING)
        for j in range(7):
            x0,x1=sorted((1.55*side,1.75*side));z=.85+j*.095
            box(b,f'Red jamb bricks {side} {j}','dark fired brick' if j%3==0 else 'radial red brick',x0,x1,-.049,.18,z,z+.092)
        x0,x1=sorted((1.68*side,2.05*side))
        for j,(z,depth) in enumerate([(1.433,.11),(1.485,.155),(1.537,.196)]):
            box(b,f'Projecting springer {side} {j}','dark fired brick',x0,x1,-depth,.10,z,z+.051)
    for i,(a,z,hi,mat) in enumerate([(.10,0,.08,'dark fired brick'),(.16,.08,.16,'radial red brick'),(.20,.16,.196,'limestone edge')]):
        box(b,f'Base string course {i}',mat,-2.05,2.05,-a,.16,z,hi)
def joinery(b,lod):
    ring(b,'Painted arch frame',-.136,-.054,.029,.126,40 if not lod else 24,lambda i:'rust red joinery')
    for i,(left,right) in enumerate([(-1.455,-.791),(-.747,-.033),(.033,.747),(.791,1.455)]):
        n=11 if not lod else 6
        for j in range(n):
            a=left+(right-left)*j/n;c=left+(right-left)*(j+1)/n
            slab(b,f'Glazing {i+1} strip {j+1}','pale pane' if i%3==0 else 'grey pane',[(a,.875),(c,.875),(c,top(c,.11)),(a,top(a,.11))],.151,.177)
    box(b,'Glazing above central meeting stile','grey pane',-.035,.035,.152,.177,1.948,top(.035,.11))
    for i,x in enumerate((-1.485,-.771,.771,1.485)):
        w=.055 if i in (0,3) else .066
        z=top(x,.085)
        box(b,f'Tall red mullion {i+1}','rust red joinery',x-w,x+w,.011,.147,.846,z)
    box(b,'Central double leaf meeting stile','rust red joinery',-.041,.041,.018,.145,.866,1.96)
    for sign in (-1,1):
        l,r=sorted((sign*.837,sign*1.466))
        for j,z in enumerate((1.276,1.682)):
            # At spring level the outer bars terminate against the arch.
            edge=(RX-.115)*sqrt(max(0,1-((z-SPRING)/(RZ-.115))**2)) if z>SPRING else 1.466
            a,c=sorted((sign*.836,sign*edge))
            box(b,f'Side light transom {sign} {j}','rust red joinery',a,c,.059,.151,z-.018,z+.018)
        for j,x in enumerate((.189,.339,.49,.639)):
            cx=x*sign
            box(b,f'Painted guard bar {sign} {j+1}','red painted bars',cx-.014,cx+.014,-.010,.041,.865,1.965)
        a,c=sorted((sign*.056,sign*.711))
        box(b,f'Guard mid rail {sign}','red painted bars',a,c,-.026,.040,1.385,1.417)
    box(b,'Top of paired casements','rust red joinery',-.74,.74,.001,.14,1.952,2.012)
    box(b,'Raised sill across opening','rust red joinery',-1.62,1.62,-.084,.13,.80,.873)
def ribbon(b,label,path,width,front,material='red painted bars'):
    # An extruded ribbon has an open space on either side of the scroll.
    edges=[]
    for i,(x,z) in enumerate(path):
        a=path[max(i-1,0)];c=path[min(i+1,len(path)-1)];dx,dz=c[0]-a[0],c[1]-a[1];l=hypot(dx,dz)
        edges.append(((x-dz*width/l,z+dx*width/l),(x+dz*width/l,z-dx*width/l)))
    for i,((a,bb),(c,d)) in enumerate(zip(edges,edges[1:])):
        slab(b,f'{label} segment {i+1}',material,[a,bb,d,c],front,front+.022)
def skirt(b,lod):
    for k,(lo,hi) in enumerate([(.196,.232),(.692,.719),(.768,.804)]):
        box(b,f'Skirt rail {k}','rust red joinery',-1.59,1.59,-.082,.016,lo,hi)
    for i,x in enumerate((-1.57,-.362,-.267,.267,.362,1.57)):
        box(b,f'Skirt division uprights {i+1}','rust red joinery',x-.016,x+.016,-.080,.015,.205,.80)
    for k,cx in enumerate((-1.225,-.655,0,.655,1.225)):
        width=.51 if k==2 else .52
        for sign in (-1,1):
            # Paired sweeps meet at the centre and curl back out, with smaller reverse lobes underneath.
            for j,(h,wx,wz,theta) in enumerate(((.51,.113,.100,1.17),(.346,.077,.061,-1.05))):
                n=(16 if not lod else 9) if j==0 else (13 if not lod else 8)
                path=[]
                for i in range(n+1):
                    t=i/n;rr=1-.80*t;ang=theta+t*1.16*2*pi
                    path.append((cx+sign*(width*.235+wx*rr*cos(ang)),h+wz*rr*sin(ang)))
                path=[(cx+sign*.018,h-.098),(cx+sign*.032,h-.035)]+path
                ribbon(b,f'Open scroll {k+1} {sign} {j}',path,.0125,-.072,'scroll highlight')
            # Tendrils connect the open spirals to the upper and lower rails.
            for branch,pts in enumerate((
                [(0,.229),(.04,.244),(.096,.298),(.129,.359),(.119,.402)],
                [(.245,.698),(.240,.652),(.217,.608),(.164,.569),(.119,.540)],
                [(.237,.235),(.223,.28),(.205,.303),(.186,.325),(.177,.348)],
                [(.026,.695),(.065,.682),(.102,.657),(.096,.628),(.069,.615),(.047,.632)])):
                ribbon(b,f'Anchored tendril {k+1} {sign} {branch}',[(cx+sign*x,z) for x,z in pts],.011,-.062,'scroll highlight')
        for j in range(3):
            cx2=cx+(j-1)*.157;path=[(cx2-.068,.773),(cx2-.042,.744),(cx2,.732),(cx2+.046,.744),(cx2+.067,.773)]
            ribbon(b,f'Upper small loop {k+1} {j+1}',path,.008,-.052)
def add_building(b,lod=False):
    brickwork(b,lod);joinery(b,lod);skirt(b,lod)
