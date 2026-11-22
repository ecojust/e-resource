"""The shallow curved entrance canopy and paired step cheeks of the Yuxiu Building."""
import math


def surface(rgb,rough=.88):
    return {'color':[c/3294.6 if c<=10 else ((c/255+.055)/1.055)**2.4 for c in rgb],'roughness':rough,'metallic':0}


PALETTE={n:surface(c) for n,c in [('limestone',(191,182,158)),('stone tread',(178,170,145)),('tread joint',(141,134,119)),
    ('mortar',(155,146,123)),('dun brick',(133,113,91)),('rose brick',(154,110,88)),('gray brick',(127,119,102)),
    ('trim',(130,93,71)),('soffit',(211,207,189)),('wood',(95,58,47)),('recessed wood',(81,51,43)),
    ('glazing',(88,105,99)),('dark metal',(75,65,52)),('lamp glass',(206,186,137))]}


def prism_yz(b,x0,x1,outline,mat,name):
    n=len(outline);vertices=[(x,y,z) for x in (x0,x1) for y,z in outline]
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]
    faces.extend((j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n))
    b.add(vertices,faces,mat,name)


def arc_z(x):
    radius=1.68
    return 3.326+math.sqrt(radius*radius-x*x)-radius


def arch_sheet(b,y0,y1,lo,hi,material,steps,label):
    # segmental barrel, in x/z, returns separate top, soffit, front/rear and radial end faces
    vertices=[]
    for i in range(steps+1):
        x=-1.04+2.08*i/steps;z=arc_z(x)
        vertices.extend([(x,y0,z+lo),(x,y1,z+lo),(x,y1,z+hi),(x,y0,z+hi)])
    faces=[]
    for i in range(steps):
        k=4*i
        faces.extend([(k,k+4,k+5,k+1),(k+1,k+5,k+6,k+2),(k+2,k+6,k+7,k+3),(k+3,k+7,k+4,k)])
    faces.extend([(0,1,2,3),(4*steps+3,4*steps+2,4*steps+1,4*steps)])
    b.add(vertices,faces,material,label)


def pier(b,x,side,lod):
    base=.65;w=.420;y0=1.30;y1=1.89;top=3.02
    b.box((x,(y0+y1)/2,(top+base)/2),(w-.013,y1-y0-.014,top-base),'mortar',label='bound brick pier '+str(side))
    for course in range(21):
        z=base+course*.112+.053
        cols=2 if course%2 else 1
        for j in range(cols):
            l=x-w*.5+w*j/cols;r=x-w*.5+w*(j+1)/cols
            name=('rose brick','dun brick','gray brick','dun brick')[(course+2*j+(side>0))%4]
            b.box(((l+r)/2,1.312,z),(r-l-.009,.038,.103),name,label='face brick '+str((side,course,j)))
        # Exposed return on the opening side is shaded and set behind the front bed.
        for k in range(1 if lod else 2):
            n=1 if lod else 2;ya=y0+.041+(y1-y0-.041)*k/n;yb=y0+.041+(y1-y0-.041)*(k+1)/n
            b.box((x-side*(w/2-.010),(ya+yb)/2,z),(.023,yb-ya-.010,.104),'gray brick',label='return brick '+str((side,course,k)))
    b.box((x,1.515,2.946),(w+.09,.73,.084),'limestone',label='stone impost '+str(side))
    # This tapered block projects from the front of the pier to carry the flat wing of the canopy.
    prism_yz(b,x-.173,x+.173,[(1.30,2.61),(1.30,2.99),(.73,2.99),(.87,2.76)],'trim','canopy bracket '+str(side))


def add_building(b,lod=False):
    for i in range(4):
        low=.163*i;high=low+.163;y0=i*.32;y1=1.45
        b.box((0,(y0+y1)/2,(low+high)/2),(1.84,y1-y0,high-low),'stone tread',label='riser '+str(i+1))
        b.box((0,y0+.155,high-.008),(1.84,.345,.025),'limestone',label='tread nosing '+str(i+1))
        for x in ((-.43,.32) if i%2 else (-.19,.56)):
            b.box((x,y0+.14,high+.005),(.008,.30,.0018),'tread joint',label='stone joint '+str((i,x)))
    b.box((0,1.462,.619),(1.85,.32,.072),'limestone',label='door landing')
    for side in (-1,1):
        x=side*1.125
        b.box((x,-.070,.17),(.43,.45,.34),'limestone',label='square front foot '+str(side))
        b.box((x,-.070,.355),(.47,.48,.066),'stone tread',label='foot cap '+str(side))
        prism_yz(b,x-.20,x+.2,[(.13,.011),(1.31,.011),(1.31,.938),(.13,.374)],'limestone','inclined cheek '+str(side))
        b.box((x,1.32,.961),(.456,.24,.071),'stone tread',label='raised return cap '+str(side))
        pier(b,x,side,lod)
        b.box((side*1.288,1.175,3.013),(.526,.95,.102),'trim',label='straight canopy wing '+str(side))
    seg=18 if lod else 40
    arch_sheet(b,.70,1.79,-.052,0,'soffit',seg,'curved pale canopy underside')
    arch_sheet(b,.665,1.79,-.003,.08,'trim',seg,'brown edge of canopy')
    for side in (-1,1):
        b.box((side*.868,1.71,1.777),(.083,.21,2.25),'wood',label='door jamb '+str(side))
    b.box((0,1.71,2.859),(1.82,.21,.098),'wood',label='door head')
    # The two high-resolution entrance photographs show a solid, arched timber transom behind the lamp.
    for i in range(seg):
        x0=-.897+1.794*i/seg;x1=-.897+1.794*(i+1)/seg
        z0=2.908+.311*(1-(x0/.897)**2);z1=2.908+.311*(1-(x1/.897)**2)
        panel=[(x0,2.898),(x1,2.898),(x1,z1),(x0,z0)]
        vertices=[(xx,yy,zz) for yy in (1.644,1.74) for xx,zz in panel]
        faces=[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
        b.add(vertices,faces,'recessed wood','curved transom panel '+str(i))
    x=-.427
    b.box((x,1.78,1.749),(.813,.064,2.171),'recessed wood',label='closed left door')
    for p in (x-.354,x,x+.354):b.box((p,1.728,1.755),(.044,.070,2.102),'wood',label='leaf stile '+str(p))
    for z in (.72,1.53,2.77):b.box((x,1.728,z),(.784,.068,.080),'wood',label='leaf rail '+str(z))
    for dx in (-.163,.163):
        b.box((x+dx,1.739,1.131),(.245,.025,.627),'wood',label='lower raised panel '+str(dx))
    b.box((x,1.725,2.122),(.607,.025,.995),'glazing',label='upper glazed opening')
    b.tube([(0,1.07,3.26),(0,1.07,3.062)],.010,'dark metal',6 if lod else 10,'pendant')
    vertices=[];n=8 if lod else 16
    for z,r in [(3.062,.046),(3.025,.096),(2.939,.083),(2.887,.031)]:
        vertices.extend([(r*math.cos(2*math.pi*j/n),1.07+r*math.sin(2*math.pi*j/n),z) for j in range(n)])
    for band in range(3):
        faces=[(band*n+j,band*n+(j+1)%n,(band+1)*n+(j+1)%n,(band+1)*n+j) for j in range(n)]
        b.add(vertices,faces,'dark metal' if band==0 else 'lamp glass','suspended porch lamp '+str(band))
