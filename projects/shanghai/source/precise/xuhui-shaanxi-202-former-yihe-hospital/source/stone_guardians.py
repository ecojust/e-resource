"""Carved lions and grey plinths at 202 South Shaanxi Road, in courtyard metres."""
from math import cos, sin, pi
from shapely.geometry import Polygon

STONE = 'Yihe guardians | warm pale carved stone'
RELIEF = 'Yihe guardians | sheltered stone recess'
PLINTH = 'Yihe guardians | grey granite plinth'
EDGE = 'Yihe guardians | grey dressed coping'
PALETTE = {
    STONE:dict(color=[.81,.784,.68],roughness=.88),
    RELIEF:dict(color=[.715,.69,.61],roughness=.91),
    PLINTH:dict(color=[.486,.481,.451],roughness=.91),
    EDGE:dict(color=[.552,.541,.511],roughness=.88),
}

class Carving:
    def __init__(self,b,x,y,base,height,side,lod):
        self.b,self.cx,self.cy,self.base,self.h,self.side,self.lod=b,x,y,base,height,side,lod
    def at(self,x,y,z):
        return (self.cx+x*self.h,self.cy+y*self.h,self.base+z*self.h)
    def label(self,name):
        return 'Entrance lion | '+self.side+' | '+name
    def rings(self,rows,name,material=STONE):
        sides=len(rows[0]);v=[self.at(*xyz) for row in rows for xyz in row]
        f=[tuple(range(sides-1,-1,-1))]
        for i in range(len(rows)-1):
            for j in range(sides):
                a=i*sides+j;c=i*sides+(j+1)%sides;f.append((a,c,c+sides,a+sides))
        f.append(tuple((len(rows)-1)*sides+j for j in range(sides)))
        self.b.add(v,f,material,self.label(name))
    def loft(self,sections,name,material=STONE,n=None):
        n=n or (8 if self.lod else 14)
        self.rings([[(x+rx*cos(2*pi*i/n),y+ry*sin(2*pi*i/n),z) for i in range(n)]
                    for z,x,y,rx,ry in sections],name,material)
    def egg(self,c,r,name,material=STONE,n=None,levels=None):
        x,y,z=c;rx,ry,rz=r;lat=levels or (4 if self.lod else 6)
        # Flat, very small polar caps avoid duplicated apex vertices.
        seq=[-.49*pi+i*.98*pi/lat for i in range(lat+1)]
        self.loft([(z+rz*sin(a),x,y,rx*cos(a),ry*cos(a)) for a in seq],name,material,n)
    def strip(self,points,r,name,material=STONE):
        self.b.tube([self.at(*p) for p in points],r*self.h,material,5 if self.lod else 7,self.label(name))
    def slab(self,width,depth,levels,name,material):
        def outline(scale,z):
            x,y=width*.5*scale,depth*.5*scale;c=.04*min(width,depth)
            return [(u,v,z) for u,v in [(-x+c,-y),(x-c,-y),(x,-y+c),(x,y-c),(x-c,y),(-x+c,y),(-x,y-c),(-x,-y+c)]]
        self.rings([outline(scale,z) for z,scale in levels],name,material)
    def apron(self,side=False):
        outline=[(-.188,.322),(.187,.322),(.163,.285),(.025,.088),(-.096,.166)]
        if side:
            # This side flap is visible on both lions in the Commons oblique view.
            def mapper(u,z,t):return self.at(-.221-t,-u,z)
            poly=Polygon([(-u,z) for u,z in outline])
        else:
            def mapper(u,z,t):return self.at(u,-.273-t,z)
            poly=Polygon(outline)
        self.b.prism(poly,0,.009,mapper,STONE,self.label('triangular draped apron, '+('side' if side else 'front')))
        if not side:
            self.strip([(-.167,-.286,.304),(.159,-.286,.304),(.023,-.286,.110)],.0035,'incised apron border',RELIEF)
            if not self.lod:
                for dx,z in [(-.065,.255),(.042,.245),(.005,.175)]:
                    self.strip([(dx-.03,-.285,z-.018),(dx-.013,-.288,z+.01),
                                (dx+.016,-.288,z+.016),(dx+.03,-.285,z+.002)],.004,'woven apron spray')

def carved_seat(g):
    g.slab(.454,.537,[(0,.91),(.012,1),(.044,1),(.052,.94)],'low carved foot',STONE)
    g.slab(.420,.480,[(.035,1),(.085,.90),(.133,.83),(.193,.86),(.258,.95)],'seat waist',RELIEF)
    g.slab(.463,.553,[(.236,.86),(.257,.99),(.304,1),(.326,.964)],'upper stone cushion',STONE)
    for face in ['front','west','east']:
        for i,t in enumerate([-.157,-.054,.054,.157]):
            for z,s in [(.090,1),(.216,.78)]:
                if face=='front':c=(t,-.239,z);r=(.049*s,.034,.055*s)
                else:c=((-1 if face=='west' else 1)*.200,t*1.25,z);r=(.029,.054*s,.056*s)
                g.egg(c,r,'rounded seat lobe '+face+' '+str(i),n=8,levels=4)
    g.apron();g.apron(side=True)

def paws_and_body(g,is_right):
    # The haunches sit behind the forelegs. The chest and neck lean towards the court.
    g.loft([(.315,0,.066,.118,.105),(.36,0,.080,.170,.130),(.45,0,.064,.176,.14),
            (.55,0,.012,.144,.142),(.635,0,-.033,.161,.129),(.705,0,-.058,.177,.123),
            (.752,0,-.063,.142,.106),(.790,0,-.073,.109,.087)],'seated trunk and throat')
    raised=-1 if is_right else 1
    for sign in [-1,1]:
        x=sign*.126
        g.egg((sign*.135,.075,.437),(.073,.128,.126),'seated hind thigh')
        g.egg((sign*.144,.075,.343),(.062,.101,.040),'hind foot under haunch')
        foot=.395 if sign==raised else .331
        g.loft([(foot,x,-.165,.05,.045),(foot+.048,x,-.145,.045,.046),
                (.493,sign*.121,-.105,.039,.044),(.587,sign*.129,-.082,.051,.059),
                (.658,sign*.119,-.047,.060,.065)],'raised foreleg' if sign==raised else 'straight foreleg')
        g.egg((x,-.180,foot+.014),(.061,.065,.027),'forepaw')
        for j in (-1,0,1):
            g.egg((x+j*.033,-.222+.006*abs(j),foot+.004),(.019,.032,.021),'front claw',n=8,levels=4)
    if is_right:
        xc=-.125
        g.egg((xc,-.182,.355),(.073,.072,.066),'embroidered ball under anatomical right paw')
        if not g.lod:
            g.egg((xc,-.253,.353),(.015,.006,.015),'ball knot',n=8,levels=4)
            for i in range(8):
                a=2*pi*i/8
                g.strip([(xc+.013*cos(a),-.253,.353+.012*sin(a)),
                         (xc+.039*cos(a+.12),-.244,.354+.036*sin(a+.12)),
                         (xc+.060*cos(a+.21),-.219,.355+.053*sin(a+.21))],.004,'ribbon radiating from ball knot')
    else:
        g.loft([(.317,.124,-.17,.067,.069),(.349,.126,-.178,.065,.061),
                (.375,.128,-.173,.054,.048),(.390,.132,-.166,.040,.038)],
               'visible compact support below left lion paw, subject unresolved',n=9)

def head_treatment(g,is_right):
    # The right lion's open mouth is a recess between separately sculpted lip bands.
    g.loft([(.656,0,-.066,.122,.108),(.720,0,-.067,.141,.122),
            (.780,0,-.088,.153,.134),(.874,0,-.084,.151,.135),(.927,0,-.063,.122,.112),
            (.959,0,-.046,.088,.082)],'neck ruff and skull')
    g.egg((0,-.186,.802),(.101,.073,.042),'lower muzzle')
    g.egg((0,-.233,.815),(.098,.040,.016),'mouth shadow',RELIEF)
    for sign in (-1,1):
        g.egg((.047*sign,-.220,.837),(.062,.072,.039),'curled upper lip')
    g.egg((0,-.206,.864),(.077,.100,.051),'broad projecting nose')
    for sign in (-1,1):
        g.egg((.045*sign,-.287,.862),(.018,.010,.009),'shallow nostril',RELIEF,n=8)
        g.egg((.081*sign,-.184,.896),(.041,.039,.027),'eye surround')
        g.egg((.082*sign,-.221,.897),(.015,.009,.014),'carved eye',RELIEF,n=8)
        g.strip([(.029*sign,-.199,.909),(.060*sign,-.213,.925),(.087*sign,-.207,.940),
                 (.117*sign,-.179,.935)],.016,'arched brow')
        g.egg((.134*sign,-.027,.917),(.049,.046,.041),'rounded ear')
    count=8 if g.lod else 13
    for i in range(count):
        a=-.78*pi+1.56*pi*i/(count-1)
        x=.146*sin(a);y=-.055+.110*cos(a)
        z=.946-.064*(abs(sin(a))**1.4)
        g.egg((x,y,z),(.048,.044,.047),'crown mane coil',n=8,levels=4)
    for i in range(5 if is_right else 4):
        g.egg(((i-2)*.052,-.112,.963-abs(i-2)*.011),(.038,.045,.037),'front crown roll',n=8,levels=4)
    for sign in (-1,1):
        for i,(x,y,z) in enumerate([(.142,-.102,.911),(.161,-.082,.869),
                                     (.153,-.058,.824),(.146,-.049,.783),(.140,-.028,.745)]):
            g.egg((sign*x,y,z),(.043,.055,.042),'mane cheek scroll',n=8,levels=4)
            if not g.lod and (is_right or sign==-1):
                g.strip([(sign*(x+.029*cos(a)) ,y-.047,z+.025*sin(a))
                        for a in [-2.1,-1.2,-.3,.6,1.4,2.1]],.0048,'curl carved in cheek')
    collar=[(-.164,-.089,.694),(-.138,-.166,.664),(-.061,-.207,.638),
            (0,-.213,.632),(.070,-.202,.640),(.137,-.162,.663),(.166,-.090,.696)]
    g.strip(collar,.016,'carved collar rim')
    g.egg((0,-.216,.607),(.031,.024,.035),'chest pendant')

def add_guardians(builder,lod=False,layout=None):
    """Attach separately observed left and right carvings; centres refer to the grey bases."""
    l=layout or {}
    for k,v in PALETTE.items():builder.palette.setdefault(k,v)
    centers=l.get('centers',[(-2.782,-2.403),(.408,-2.403)])
    for i,(x,y) in enumerate(centers):
        base=l.get('plinth_top',.301);h=l.get('carved_heights',(.906,.920))[i]
        g=Carving(builder,x,y,base,h,['left seen from court','right seen from court'][i],lod)
        width=l.get('plinth_widths',(.66,.66))[i];depth=l.get('plinth_depth',.72)
        builder.box((x,y,base*.47),(width-.036,depth-.041,base*.94),PLINTH,label=g.label('grey squared support'))
        builder.box((x,y,base-.034),(width,depth,.068),EDGE,label=g.label('overhanging coping on grey support'))
        carved_seat(g);paws_and_body(g,i==1);head_treatment(g,i==1)
