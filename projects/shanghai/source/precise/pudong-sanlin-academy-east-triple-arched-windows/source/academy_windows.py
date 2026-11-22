"""Brick openings and glazed tracery on the east elevation of Junxiu Jingshe."""
from math import hypot

COLORS = {
    'grey bedding': (.218,.226,.209), 'warm grey brick': (.256,.258,.225),
    'grey brick': (.237,.247,.230), 'dark grey brick': (.178,.190,.181),
    'russet bedding': (.316,.171,.093), 'red brick': (.444,.231,.124),
    'lighter red brick': (.489,.257,.147), 'dark red brick': (.377,.185,.104),
    'sash': (.066,.047,.034), 'sash edge': (.092,.066,.046),
    'muntin': (.044,.041,.032), 'window glass': (.188,.221,.202),
    'shaded glass': (.151,.180,.169), 'pale sill': (.419,.415,.360)}
PALETTE = {key: {'color':list(rgb), 'roughness':.29 if 'glass' in key else .78}
           for key,rgb in COLORS.items()}
BAYS = (-2.12,0,2.12)
SPRING = 1.55
INNER_R, INNER_H = .55,.57
OUTER_R, OUTER_H = .815,.805
SILL=.086
# Half widths derived from rows 35–90 of the separate measurement crop.
# The measured curve has a pointed crown and near-vertical springing ends.
PROFILE = [(0,1),(.22,.939),(.42,.823),(.60,.669),(.74,.511),
           (.845,.370),(.920,.229),(.975,.112),(1,0)]

def slab(b, label, profile, y0, y1, material):
    # profile is a convex sequence in the X/Z plane, normal toward the street.
    area = sum(x*profile[(i+1)%len(profile)][1]-z*profile[(i+1)%len(profile)][0]
               for i,(x,z) in enumerate(profile))
    if area<0: profile=list(reversed(profile))
    points=[(x,y,z) for y in (y0,y1) for x,z in profile]
    n=len(profile); faces=[]
    for i in range(1,n-1):
        faces.extend([(0,i,i+1),(n,n+i+1,n+i)])
    for i in range(n):
        j=(i+1)%n;faces.extend([(i,n+i,n+j),(i,n+j,j)])
    b.add(points,faces,material,label)

def rect(b,label,x0,x1,z0,z1,y0,y1,material):
    if x1-x0>.0001 and z1-z0>.0001:
        slab(b,label,[(x0,z0),(x1,z0),(x1,z1),(x0,z1)],y0,y1,material)

def curve(radius,height,lod=False):
    points = PROFILE[::2] if lod else PROFILE
    return [(-radius*x,SPRING+height*z) for x,z in reversed(points[1:])]+[
        (radius*x,SPRING+height*z) for x,z in points]

def contour(b,label,c,inner,outer,y0,y1,material):
    for i,(a,t) in enumerate(zip(inner[:-1],inner[1:])):
        s=outer[i];v=outer[i+1]
        slab(b, f'{label} {i+1}', [(c+p[0],p[1])for p in (a,t,v,s)],y0,y1,material)

def width_at(radius,height,z):
    if z<=SPRING:return radius
    h=(z-SPRING)/height
    if h>=1:return 0.
    for (x0,y0),(x1,y1) in zip(PROFILE,PROFILE[1:]):
        if y0>=h>=y1:return radius*(x0+(x1-x0)*(y0-h)/(y0-y1))
    return 0.

def diagonal(b,label,c,p,q,wide,y0,y1,material):
    dx=q[0]-p[0];dz=q[1]-p[1];length=hypot(dx,dz)
    ex,ez=-dz*wide/(2*length),dx*wide/(2*length)
    slab(b,label,[(c+p[0]+ex,p[1]+ez),(c+q[0]+ex,q[1]+ez),
                  (c+q[0]-ex,q[1]-ez),(c+p[0]-ex,p[1]-ez)],y0,y1,material)

def masonry(b,lod):
    xmin,xmax=-3.24,3.24;top=2.48
    # Straight piers, wall below sill and arched spandrels preserve three actual voids.
    rect(b,'continuous grey masonry below windows',xmin,xmax,0,SILL,0,.285,'grey bedding')
    limits=[xmin]+[v for c in BAYS for v in (c-INNER_R,c+INNER_R)]+[xmax]
    for i in range(0,len(limits),2):
        rect(b,f'grey masonry pier {i//2+1}',limits[i],limits[i+1],SILL,top,0,.285,'grey bedding')
    for k,c in enumerate(BAYS):
        line=curve(INNER_R,INNER_H,lod)
        for j,((x,z),(u,t)) in enumerate(zip(line,line[1:])):
            slab(b,f'masonry above opening {k+1}.{j+1}',[(x+c,z),(u+c,t),(u+c,top),(x+c,top)],0,.285,'grey bedding')
    # Grey brick courses stop at the outer red arch. In the distant mesh broader
    # facing panels take the place of individual joints, keeping the actual opening.
    dz=.077 if not lod else .154
    i=0
    while i*dz<top-.004:
        low=i*dz; high=min((i+1)*dz,top)
        if high-low<.004:break
        # The red jamb ends at the lower red band, as on the photograph.
        half = 0 if high<=SILL else (INNER_R if low<1.0 else width_at(OUTER_R,OUTER_H,low))
        ranges = [(xmin,xmax)] if half==0 else []
        if half:
            last=xmin
            for c in BAYS:
                ranges.append((last,c-half));last=c+half
            ranges.append((last,xmax))
        band=1.00<=(low+high)/2<1.16 or 1.97<=(low+high)/2<2.20
        for index,(left,right) in enumerate(ranges):
            span=.29 if not lod else .58
            x=xmin-span+(i%2)*span/2
            joint=0
            while x<right:
                a=max(x,left);d=min(x+span,right)
                if d-a>.012:
                    color=['grey brick','dark grey brick','grey brick','warm grey brick','grey brick'][(i*7+joint*13+index)%5]
                    if band:color=['red brick','lighter red brick','red brick'][(joint+i)%3]
                    rect(b,f'course {i+1} brick {index+1}.{joint+1}',a+.002,d-.002,low+.002,high-.002,-.006,.001,color)
                x+=span;joint+=1
        i+=1

def window(b,k,c,lod):
    prefix=f'east opening {k+1}'
    a=curve(INNER_R,INNER_H,lod);t=curve(OUTER_R,OUTER_H,lod)
    contour(b,prefix+' red arch mortar',c,a,t,-.013,.04,'russet bedding')
    for j in range(len(a)-1):
        v0,v1=a[j:j+2];w0,w1=t[j:j+2]
        def mix(p,q,u):return(c+p[0]*(1-u)+q[0]*u,p[1]*(1-u)+q[1]*u)
        slab(b,f'{prefix} radial brick {j+1}',[mix(v0,v1,.014),mix(v0,v1,.986),mix(w0,w1,.986),mix(w0,w1,.014)],-.018,-.012,['red brick','lighter red brick','dark red brick','red brick'][j%4])
    for s in (-1,1):
        x0,x1=sorted((c+s*INNER_R,c+s*OUTER_R))
        rect(b,prefix+' jamb bedding '+str(s),x0,x1,1.085,SPRING,-.013,.03,'russet bedding')
        for i in range(6):
            z=1.085+i*(SPRING-1.085)/6
            rect(b,f'{prefix} jamb brick {s}.{i}',x0+.001,x1-.001,z+.002,z+(SPRING-1.085)/6-.002,-.018,-.012,'red brick' if i%3 else 'lighter red brick')
    # Slight differences in the glass faces convey the four equal lower lights of each row.
    rect(b,prefix+' stone sill',c-.59,c+.59,.037,.086,-.075,.16,'pale sill')
    for s in (-1,1):
        x0,x1=sorted((c+s*.548,c+s*.484));rect(b,prefix+' jamb frame '+str(s),x0,x1,SILL,SPRING,.056,.139,'sash')
    for p,z,h in [('bottom rail',.117,.064),('transom beam',1.461,.099)]:
        rect(b,prefix+' '+p,c-.53,c+.53,z-h/2,z+h/2,.053,.145,'sash')
    for j,(x,wide) in enumerate([(-.246,.021),(0,.092),(.246,.021)]):
        rect(b,f'{prefix} lower vertical {j+1}',c+x-wide/2,c+x+wide/2,.142,1.425,.064,.127,'sash edge' if j==1 else 'muntin')
    for j,z in enumerate([.434,.755,1.080]):
        rect(b,f'{prefix} lower crossbar {j+1}',c-.485,c+.485,z-.012,z+.012,.079,.133,'muntin')
    for j,(x0,x1) in enumerate([(-.49,-.246),(-.246,0),(0,.246),(.246,.49)]):
        for i,(lo,hi) in enumerate(zip([.143,.434,.755,1.080],[.434,.755,1.080,1.421])):
            rect(b,f'{prefix} lower pane {j+1}.{i+1}',c+x0,c+x1,lo,hi,.144,.15,'window glass' if (j+i+k)%3 else 'shaded glass')
    inner=curve(.483,.483,lod);contour(b,prefix+' timber arch',c,inner,a,.054,.14,'sash')
    rect(b,prefix+' rectangular transom foot',c-.484,c+.484,1.501,SPRING,.144,.15,'window glass')
    for j,((x,z),(u,t1)) in enumerate(zip(inner,inner[1:])):
        slab(b,f'{prefix} arched pane {j+1}',[(c+x,z),(c+u,t1),(c+u,SPRING-.001),(c+x,SPRING-.001)],.143,.15,'window glass')
    for j,(x,lo,hi) in enumerate([(-.218,1.5,1.926),(.218,1.5,1.926),(0,1.5,1.555),(0,1.762,2.023)]):
        rect(b,f'{prefix} transom upright {j+1}',c+x-.010,c+x+.010,lo,hi,.080,.14,'muntin')
    for j,z in enumerate([1.609,1.833]):
        half=width_at(.483,.483,z)-.006
        if j:rect(b,prefix+' upper full transom rail',c-half,c+half,z-.009,z+.009,.078,.140,'muntin')
        else:
            for s in (-1,1):
                x0,x1=sorted((c+s*.215,c+s*half))
                rect(b,prefix+' side transom rail '+str(s),x0,x1,z-.009,z+.009,.078,.140,'muntin')
    vertices=[(0,1.555),(.205,1.660),(0,1.765),(-.205,1.660)]
    for j,p in enumerate(vertices):
        diagonal(b,f'{prefix} diamond segment {j+1}',c,p,vertices[(j+1)%4],.022,.073,.138,'muntin')

def add_building(b,lod):
    masonry(b,lod)
    for k,c in enumerate(BAYS):window(b,k,c,lod)
