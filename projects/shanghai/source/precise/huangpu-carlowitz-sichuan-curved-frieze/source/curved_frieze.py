"""Curved belt course at 670 Middle Sichuan Road, based on the 2016 street photograph.

All vertical courses share an estimated radius. The shallow ornamental loops
and pendent drops lie on the convex face, between a moulded cap and stone tiles.
"""
from math import ceil,cos,pi,sin
def paint(rgb):
    def linear(v):
        x=v/255
        return x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4
    return dict(color=[linear(v)for v in rgb],roughness=.81,metallic=0.)
PALETTE={k:paint(v)for k,v in {
    'mortar':(125,98,91),'brick vermilion':(132,77,65),'aged rose brick':(145,86,72),
    'purple brick':(113,68,64),'dentil brick':(105,64,54),'deep brick fascia':(118,74,66),
    'stone course':(183,184,178),'aged course':(174,175,170),'weathered course':(164,167,161),
    'moulded cap':(203,203,193),'ornament ground':(176,178,172),
    'pale relief':(203,202,190),'shaded return':(151,154,147)}.items()}
BRICK=('aged rose brick','brick vermilion','purple brick');STONE=('stone course','aged course','weathered course');R=5.9;HALF=2.28
def xyz(s,d,z):
    a=s/R
    return ((R-d)*sin(a),R-(R-d)*cos(a),z)
def sweep(b,name,left,right,profile,m,n):
    ring=len(profile);vs=[];fs=[]
    for j in range(n+1):
        s=left+(right-left)*j/n
        vs.extend(xyz(s,d,z)for d,z in profile)
    fs.extend([tuple(range(ring-1,-1,-1)),tuple(n*ring+i for i in range(ring))])
    for j in range(n):
        for i in range(ring):
            a=j*ring+i;c=j*ring+(i+1)%ring;fs.append((a,c,c+ring,a+ring))
    b.add(vs,fs,m,name)
def strip(b,name,a,c,front,back,z1,z2,mat,n):
    sweep(b,name,a,c,[(front,z1),(back,z1),(back,z2),(front,z2)],mat,n)
def ornament(b,name,profile,front,back,m):
    # Trace the ornament in unrolled wall coordinates before bending it.
    n=len(profile);vs=[xyz(s,d,z)for d in (front,back)for s,z in profile]
    fs=[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)]
    # Separate narrow quadrilaterals along the descending and ascending vine.
    for i in range(n//2-1):
        j=n-1-i;fs.extend([(i,i+1,j-1,j),(n+j,n+j-1,n+i+1,n+i)])
    b.add(vs,fs,m,name)
def add_building(b,lod=False):
    n=18 if lod else 50;h=HALF
    strip(b,'curved brick substrate',-h,h,.012,.20,0,.94,'mortar',n)
    length=.225
    for course,z in enumerate((.021,.105,.750,.830)):
        start=-h-(length/2 if course%2 else 0);i=0
        while start<h:
            left=max(-h,start+.003);right=min(h,start+length-.002)
            if right>left:
                strip(b,'bonded course '+str(course),left,right,-.002,.018,z,z+.072,BRICK[(i+course*2)%3],1 if lod else 2)
            start+=length;i+=1
    strip(b,'lower red brick fascia',-h,h,-.042,.019,.151,.241,'deep brick fascia',n)
    for j in range(36):
        a=-h+.013+j*.126; strip(b,'alternating brick dentil',a,a+.066,-.089,.0,.167,.231,'dentil brick',1 if lod else 2)
    sweep(b,'underside of projecting belt',-h,h,[(-.134,.245),(.008,.235),(.008,.265),(-.146,.272)],'shaded return',n)
    for j in range(19):
        a=-h+j*.24;c=a+.239;strip(b,'light vertical stone joint '+str(j),a,c,-.145,.008,.265,.527,STONE[j%3],1 if lod else 3)
    strip(b,'background to carved ornament',-h,h,-.167,.012,.524,.679,'ornament ground',n)
    for j in range(32):
        stride=2*h/32;c=-h+(j+.5)*stride;seg=7 if lod else 16
        pts=[(c-.061+.122*i/seg,.627-.062*sin(pi*i/seg))for i in range(seg+1)]
        # The lower moulded return remains visible in the shallow, uneven light
        # on the original band. Its face lies behind the upper relief.
        ornament(b,'lower return of carved loop '+str(j),
                 [(x,z+.005)for x,z in pts]+[(x,z-.018)for x,z in reversed(pts)],
                 -.178,-.164,'shaded return')
        ornament(b,'shallow U-shaped carved loop '+str(j),[(x,z+.010)for x,z in pts]+[(x,z-.010)for x,z in reversed(pts)],-.188,-.163,'pale relief')
        if not lod:
            pts=[(c-.012,.564),(c-.005,.548),(c+.005,.548),(c+.012,.564),(c+.005,.572),(c-.005,.572)]
            ornament(b,'pendant under carved loop '+str(j),pts,-.187,-.166,'pale relief')
    sweep(b,'curving cap with drip edge',-h,h,[(-.201,.667),(-.183,.644),(.003,.644),(.003,.712),(-.195,.720),(-.212,.707)],'moulded cap',n)
    strip(b,'thin return above carved belt',-h,h,-.111,.02,.712,.744,'shaded return',n)
