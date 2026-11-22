"""Three glazed lights cut by two actual stone mullions under a shallow arch on Jiujiang Road."""
from math import sin,cos,pi,atan2,ceil,sqrt,asin

def colour(rgb,metal=0):
    c=[n/255 for n in rgb]
    return dict(color=[v/12.92 if v<.04045 else ((v+.055)/1.055)**2.4 for v in c],
                metallic=metal,roughness=.45 if metal else .86)
PALETTE={name:colour(rgb,m)for name,rgb,m in [
    ('dressed grey facing',(164,161,148),0),('grey stone',(148,146,135),0),('window ledge',(173,169,152),0),
    ('fine mortar',(110,110,103),0),('dark outer casement',(68,71,68),.25),('crossbar',(77,80,75),.29),
    ('window glass',(94,111,115),.24),('deep reveal',(121,120,112),0)]}
R=1.02;H=.72;SPRING=.81;OUT=1.30;TOP=1.92

def prism(b,name,xz,y0,y1,mat):
    count=len(xz);v=[(x,y,z)for y in (y0,y1)for x,z in xz]
    faces=[tuple(range(count)),tuple(range(2*count-1,count-1,-1))]
    faces.extend((i,(i+1)%count,count+(i+1)%count,count+i)for i in range(count))
    b.add(v,faces,mat,name)

def rect(b,name,left,right,bottom,top,y0,y1,mat):
    prism(b,name,[(left,bottom),(right,bottom),(right,top),(left,top)],y0,y1,mat)

def arc(t):return R*cos(t),SPRING+H*sin(t)
def outer(t):
    x=R*cos(t);z=H*sin(t);scale=min(OUT/max(abs(x),1e-9),(TOP-SPRING)/max(z,1e-9))
    return x*scale,SPRING+z*scale

def add_building(b,lod=False):
    # Each dark groove separates real stone courses and continues around the arch.
    for sign in (-1,1):
        a,bound=(R,OUT)if sign==1 else(-OUT,-R)
        rect(b,f'side backing {sign}',a,bound,.02,SPRING,.028,.26,'fine mortar')
        for j,(lo,hi)in enumerate([(.020,.205),(.217,.395),(.408,.594),(.607,.804)]):
            rect(b,f'side ashlar {sign}-{j}',a,bound,lo,hi,-.006,.23,'dressed grey facing')
    for j,(lo,hi,d,mat)in enumerate([(-.105,-.071,-.07,'deep reveal'),(-.071,-.032,-.141,'window ledge'),(-.032,.023,-.16,'window ledge'),(.023,.043,-.105,'grey stone')]):
        rect(b,f'sill course {j}',-1.077,1.077,lo,hi,d,.235,mat)
    # The ring and its backing stop at the opening on their inner edges.
    angles=sorted(set([i*pi/9 for i in range(10)]+[atan2((TOP-SPRING)/H,OUT/R),pi-atan2((TOP-SPRING)/H,OUT/R)]))
    for i,(a,z)in enumerate(zip(angles,angles[1:])):
        pieces=max(1,ceil((z-a)/(pi/(18 if lod else 54))))
        for j in range(pieces):
            t=a+(z-a)*j/pieces;u=a+(z-a)*(j+1)/pieces
            prism(b,f'arch base {i}',[arc(t),outer(t),outer(u),arc(u)],.023,.27,'fine mortar')
            # True joint gaps occur at radial stone boundaries, not at corner splits.
            first=(abs(a/(pi/9)-round(a/(pi/9)))<1e-7)
            last=(abs(z/(pi/9)-round(z/(pi/9)))<1e-7)
            at=t+(.006 if first and j==0 and i>0 else 0)
            end=u-(.006 if last and j+1==pieces and i+1<len(angles)-1 else 0)
            prism(b,f'radial voussoir {i}',[arc(at),outer(at),outer(end),arc(end)],-.006,.202,'dressed grey facing')
    # Rectangular lower lights and elliptical upper lights share the same recess.
    for slot,(left,right)in enumerate([(-1.014,-.383),(-.248,.249),(.384,1.014)]):
        rect(b,f'lower glass {slot}',left,right,.055,SPRING,.137,.151,'window glass')
        steps=6 if lod else 18
        for j in range(steps):
            l=left+(right-left)*j/steps;r=left+(right-left)*(j+1)/steps
            crown=lambda x:SPRING+H*sqrt(max(0.,1-(x/R)**2))
            prism(b,f'curved glazing {slot}',[(l,SPRING),(r,SPRING),(r,crown(r)),(l,crown(l))],.137,.151,'window glass')
        for k,(xa,xb) in enumerate([(left,left+.031),(right-.031,right)]):
            top=SPRING+H*sqrt(max(0,1-(max(abs(xa),abs(xb))/R)**2))
            rect(b,f'casement stile {slot}-{k}',xa,xb,.053,top,.085,.14,'dark outer casement')
        rect(b,f'bottom casement {slot}',left,right,.05,.084,.084,.141,'dark outer casement')
        rect(b,f'high horizontal rail {slot}',left,right,.875,.904,.085,.141,'crossbar')
    for k,(l,r)in enumerate([(-.382,-.247),(.248,.383)]):
        yl=SPRING+H*sqrt(1-(l/R)**2);yr=SPRING+H*sqrt(1-(r/R)**2)
        prism(b,f'stone mullion {k}',[(l,.042),(r,.042),(r,yr),(l,yl)],-.003,.174,'grey stone')
    rect(b,'central vertical glazing bar',-.014,.014,.053,1.496,.084,.141,'crossbar')
    total=18 if lod else 56
    for i in range(total):
        a=i*pi/total;z=(i+1)*pi/total
        def inset(t):return (R-.043)*cos(t),SPRING+(H-.043)*sin(t)
        prism(b,'curved recessed casement rim',[inset(a),arc(a),arc(z),inset(z)],.074,.134,'dark outer casement')
