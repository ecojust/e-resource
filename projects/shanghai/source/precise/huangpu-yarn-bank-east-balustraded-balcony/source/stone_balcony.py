"""The eastern bow balcony on the former Shanghai Yarn Bank, viewed from Yan'an East Road."""
from math import sin,cos,pi

def finish(rgb):
    s=[v/255 for v in rgb]
    return dict(color=[v/12.92 if v<.04045 else ((v+.055)/1.055)**2.4 for v in s],roughness=.83,metallic=0)
PALETTE={k:finish(v) for k,v in [
    ('warm grey limestone',(181,178,166)),('light recessed course',(196,192,180)),('dark weathered bed',(145,143,134)),
    ('sunlit rail moulding',(202,198,185)),('baluster body',(190,187,176)),('shadow fillet',(152,150,140)),
    ('scroll face',(179,177,166)),('cut stone return',(171,168,157)),('edge of scroll',(188,185,172))]}

def box(b,name,x0,x1,y0,y1,z0,z1,mat):
    v=[(x,y,z) for z in (z0,z1) for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]]
    b.add(v,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat,name)

def location(t):
    return (1.64*sin(t),-.05-.78*cos(t))

def bowed_course(b,name,z0,z1,overhang,inset,material,segments):
    # The front is part of an ellipse, flattened where it meets each end pier.
    v=[]
    for j in range(segments+1):
        a=(-.5+j/segments)*pi;x,y=location(a)
        v.extend([(x+sin(a)*overhang,y-cos(a)*overhang,z0),
                  (x+sin(a)*overhang,y-cos(a)*overhang,z1),
                  (x-sin(a)*inset,y+cos(a)*inset,z1),
                  (x-sin(a)*inset,y+cos(a)*inset,z0)])
    f=[(0,1,2,3),(4*segments+3,4*segments+2,4*segments+1,4*segments)]
    for i in range(segments):
        for k in range(4):f.append((4*i+k,4*(i+1)+k,4*(i+1)+(k+1)%4,4*i+(k+1)%4))
    b.add(v,f,material,name)

def platform(b,name,z0,z1,rim,mat,n):
    outline=[location((i/n-.5)*pi)for i in range(n+1)]
    edge=[(x+sin((i/n-.5)*pi)*rim,y-cos((i/n-.5)*pi)*rim)for i,(x,y) in enumerate(outline)]
    edge += [(edge[-1][0],.13),(edge[0][0],.13)]
    count=len(edge);verts=[(x,y,z)for z in (z0,z1) for x,y in edge]
    faces=[tuple(range(count-1,-1,-1)),tuple(range(count,2*count))]
    faces += [(i,(i+1)%count,count+(i+1)%count,count+i) for i in range(count)]
    b.add(verts,faces,mat,name)

def turning(b,name,x,y,z,profile,n):
    v=[(x+r*cos(2*pi*k/n),y+r*sin(2*pi*k/n),z+h)for h,r in profile for k in range(n)]
    f=[tuple(range(n-1,-1,-1)),tuple(range((len(profile)-1)*n,len(profile)*n))]
    f.extend((j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k)for j in range(len(profile)-1)for k in range(n))
    b.add(v,f,'baluster body',name)

def bracket(b,x,number,lod):
    p=[(.04,.06),(-.04,.06),(-.13,.095),(-.17,.16),(-.19,.24),(-.25,.34),(-.37,.43),(-.51,.455),(-.55,.49),(-.55,.56),(.06,.56)]
    s=len(p);v=[(x+w,y,z)for w in (-.14,.14) for y,z in p];f=[tuple(range(s-1,-1,-1)),tuple(range(s,2*s))]
    f.extend((i,(i+1)%s,s+(i+1)%s,s+i)for i in range(s));b.add(v,f,'cut stone return','bracket with rolled nose '+str(number))
    # A thin annular raised line follows the carved scroll on each exposed flank.
    for side in (-1,1):
        strips=[];n=14 if lod else 24
        for i in range(n+1):
            tau=i/n;theta=1.5*pi+2.1*pi*tau;rr=.074*(1-.78*tau)
            strips.extend((x+side*.144,-.405+(rr+dw)*cos(theta),.465+(rr+dw)*sin(theta))for dw in (-.006,.006))
        b.add(strips,[(2*i,2*i+1,2*i+3,2*i+2) for i in range(n)],'edge of scroll','spiral flank %s %s'%(number,side))

def add_building(b,lod=False):
    n=22 if lod else 44
    for i,x in enumerate([-.59,.59]):bracket(b,x,i,lod)
    platform(b,'underside with rounded nose',.54,.60,.018,'cut stone return',n)
    platform(b,'curved balcony bed',.60,.70,.048,'warm grey limestone',n)
    bowed_course(b,'projecting lower drip',.665,.695,.075,.038,'shadow fillet',n)
    platform(b,'walking surface',.70,.736,.03,'light recessed course',n)
    bowed_course(b,'continuous toe course',.736,.855,.018,.139,'warm grey limestone',n)
    bowed_course(b,'stepped foot of rail',.855,.894,.036,.145,'sunlit rail moulding',n)
    profile=[(0,.065),(.030,.065),(.045,.050),(.066,.045),(.091,.058),(.116,.072),(.163,.079),(.21,.071),(.265,.048),(.305,.039),(.326,.047),(.35,.053),(.378,.054),(.39,.072),(.425,.072)]
    if lod:profile=[profile[i] for i in [0,1,3,5,6,7,9,11,13,14]]
    for j in range(11):
        theta=(-.5+(j+1)/12)*pi;x,y=location(theta);x-=.050*sin(theta);y+=.050*cos(theta)
        box(b,'square baluster plinth '+str(j),x-.076,x+.076,y-.07,y+.07,.894,.93,'light recessed course')
        turning(b,'turned stone baluster '+str(j),x,y,.93,profile,8 if lod else 14)
        box(b,'baluster abacus '+str(j),x-.077,x+.077,y-.073,y+.073,1.355,1.395,'warm grey limestone')
    for i,side in enumerate((-1,1)):
        x=side*1.60
        for j,(z0,z1,r,mat) in enumerate([(.73,.88,.17,'dark weathered bed'),(.88,1.38,.14,'warm grey limestone'),(1.38,1.46,.17,'light recessed course')]):
            box(b,'termination pier %s %s'%(i,j),x-r,x+r,-.12,.12,z0,z1,mat)
    for i,(lo,hi,edge,inside,mat) in enumerate([(1.395,1.428,.026,.125,'shadow fillet'),(1.428,1.48,.055,.15,'warm grey limestone'),(1.48,1.517,.071,.17,'sunlit rail moulding')]):
        bowed_course(b,'bowed top rail '+str(i),lo,hi,edge,inside,mat,n)
