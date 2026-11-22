"""The eastern roof corner of House One, Hongqiao. All tiles and exposed timber are original solids."""
from math import exp,cos,sin,pi,sqrt
def pigment(rgb):
    def linear(n):
        v=n/255
        return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
    return {'color':[linear(n) for n in rgb],'roughness':.89,'metallic':0}
PALETTE={name:pigment(rgb) for name,rgb in {
 'gray clay bed':(97,98,91),'charcoal tile':(85,88,84),'gray cover tile':(95,98,94),'light cover tile':(103,106,101),
 'rim of cover tile':(138,139,128),'inside of cover tile':(62,66,64),'bedded gray ridge':(131,130,119),
 'weathered timber':(109,74,54),'shadowed timber':(80,57,45),'rafters and barge':(130,91,60),'plaster bead':(188,182,157)
}.items()}
L=1.950; D=.890; PITCH=.118
def zroof(x,y):
    return .860+.56*min(x,y)+.65*exp(-max(x,y)/.38)*exp(-min(x,y)/.40)
def place(side,a,b,z):
    return (a,b,z) if side==0 else (b,a,z)
def grid(builder,label,rows,material,reverse=False):
    n=len(rows[0]);v=sum(rows,[]);faces=[]
    for i in range(len(rows)-1):
        for j in range(n-1):
            f=(i*n+j,(i+1)*n+j,(i+1)*n+j+1,i*n+j+1)
            faces.append(tuple(reversed(f)) if reverse else f)
    builder.add(v,faces,material,label)
def roof_face(b,side,lod):
    nx,ny=(27,13)if lod else(37,16)
    top=[];bottom=[]
    for j in range(ny+1):
        y=D*j/ny;row=[];lower=[]
        for i in range(nx+1):
            x=y+(L-y)*i/nx;z=zroof(x,y)
            row.append(place(side,x,y,z));lower.append(place(side,x,y,z-.073))
        top.append(row);bottom.append(lower)
    grid(b,'gray tile bed face '+str(side),top,'gray clay bed',side==0)
    grid(b,'timber sheathing beneath face '+str(side),bottom,'weathered timber',side!=0)
    grid(b,'outer bed edge '+str(side),[bottom[0],top[0]],'gray clay bed',side==0)
    grid(b,'short rear cut '+str(side),[top[-1],bottom[-1]],'gray clay bed',side==0)
    grid(b,'end face of bed '+str(side),[[row[-1]for row in top],[row[-1]for row in bottom]],'gray clay bed',side!=0)
def swept_beam(b,label,path,width,height,material):
    ux,uy=width
    v=[]
    for x,y,z in path:v.extend([(x-ux,y-uy,z),(x+ux,y+uy,z),(x+ux,y+uy,z-height),(x-ux,y-uy,z-height)])
    f=[(3,2,1,0)]
    for i in range(len(path)-1):
        for k in range(4):
            a=4*i+k;m=4*i+(k+1)%4;f.append((a,m,m+4,a+4))
    back=4*(len(path)-1);f.append(tuple(back+k for k in range(4)));b.add(v,f,material,label)
def cover(b,side,column,lod):
    x=(column+.5)*PITCH
    end=min(x-.051,D)
    if end<.024:return
    n=6 if lod else 12;div=1 if lod else max(1,round(end/.21))
    for j in range(div):
        y0=-.028 if j==0 else end*j/div-.014;y1=end*(j+1)/div
        raised=.006*(j%2) if not lod else 0.
        outer=[];inner=[]
        for f in range(4):
            y=y0+(y1-y0)*f/3
            rz=zroof(x,max(0,y))+raised
            def arc(rad,rise):
                return [place(side,x+rad*cos(pi*i/n),y,rz+rise*sin(pi*i/n))for i in range(n+1)]
            outer.append(arc(.043,.041));inner.append(arc(.033,.030))
        k='tile '+str(column+1)+' on slope '+str(side)
        mat=('gray cover tile','charcoal tile','light cover tile')[(column+2*side+j)%3]
        grid(b,k+' top',outer,mat,side!=0);grid(b,k+' soffit',inner,'inside of cover tile',side==0)
        grid(b,k+' raised front rim',[outer[0],inner[0]],'rim of cover tile',side==0)
        grid(b,k+' back',[inner[-1],outer[-1]],mat,side==0)
        for si in (0,-1):
            grid(b,k+' toe',[[line[si] for line in outer],[line[si]for line in inner]],mat, (si==0) != (side==0))
def add_building(b,lod=False):
    for side in (0,1):
        roof_face(b,side,lod)
        for column in range(16):cover(b,side,column,lod)
        steps=20 if lod else 46;path=[];stripe=[]
        for j in range(steps+1):
            x=L*j/steps;z=zroof(x,0)
            path.append(place(side,x,-.033,z-.050));stripe.append(place(side,x,-.06,z-.053))
        width=(0,.028) if not side else (.028,0)
        swept_beam(b,'swept timber fascia '+str(side),path,width,.108,'rafters and barge')
        swept_beam(b,'edge bead '+str(side),stripe,tuple(n*.19 for n in width),.017,'plaster bead')
        for i in range(15):
            x=.13+i*.122;end=min(D-.035,x-.048)
            if end<.06:continue
            path=[]
            for j in range(8 if lod else 16):
                y=-.021+(end+.021)*j/(7 if lod else 15)
                path.append(place(side,x,y,zroof(x,max(y,0))-.100))
            w=(.024,0) if side==0 else (0,.024)
            swept_beam(b,'exposed rafter '+str(side)+' '+str(i+1),path,w,.066,'weathered timber')
    path=[];rpath=[]
    for i in range(28 if lod else 57):
        q=-.064+(D+.064)*i/(27 if lod else 56);z=zroof(max(q,0),max(q,0))
        curl=.063*max(0.,-q)/.064
        path.append((q,q,z-.097+curl));rpath.append((q,q,z+.058+curl))
    swept_beam(b,'upturned diagonal corner timber',path,(.049,-.049),.141,'shadowed timber')
    swept_beam(b,'bedded diagonal hip cover',rpath,(.060,-.060),.062,'bedded gray ridge')
    for side in (-1,1):
        ridge=[(x+.041*side,y-.041*side,z+.012)for x,y,z in rpath]
        swept_beam(b,'edge roll of hip '+str(side),ridge,(.011,-.011),.028,'gray cover tile')
    # The terminal timber narrows and is kicked upward beyond the last tile.
    section=[]
    n=10 if lod else 22
    for i in range(n+1):
        t=i/n;q=-.045-.157*t
        z=zroof(0,0)-.027+.219*(t**1.45)
        width=.049*(1-t)+.007*t
        height=.129*(1-t)+.017*t
        section.extend([(q-width,q+width,z),(q+width,q-width,z),
                        (q+width,q-width,z-height),(q-width,q+width,z-height)])
    surfaces=[(3,2,1,0)]
    for i in range(n):
        for k in range(4):
            a=4*i+k;b1=4*i+(k+1)%4;surfaces.append((a,b1,b1+4,a+4))
    a=4*n;surfaces.append((a,a+1,a+2,a+3))
    b.add(section,surfaces,'rafters and barge','tapering tip of corner barge')
