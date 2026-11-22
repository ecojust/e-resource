"""The two exposed eaves at the garden house on Wuyi Road, after the courtyard photograph."""
from math import cos,sin,pi
def paint(rgb,rough=.84):
    return {'color':[((n/255+.055)/1.055)**2.4 for n in rgb],'roughness':rough}
PALETTE={k:paint(v) for k,v in {'painted soffit':(221,211,183),'cream bracket':(220,208,179),'cream wall return':(198,188,156),'wine fascia':(104,76,75),'stone grey gutter':(164,164,153),'gutter straps':(180,176,161),'roof tile red':(135,94,74),'roof tile ochre':(151,103,80),'concealed vent shade':(51,49,44),'roof bed':(124,110,93)}.items()}
FRONT=2.22;SIDE=2.54;OUT=.62
VENTS=[('front',-1.56),('side',.62),('side',1.91)]
BRACKETS=[('front',-1.35),('front',-.105),('side',1.38),('side',2.18)]
def xyz(arm,s,r,z):
    return (s,-r,z) if arm=='front' else (r,s,z)
def box(b,arm,s0,s1,r0,r1,z0,z1,mat,label):
    a=xyz(arm,s0,r0,z0);c=xyz(arm,s1,r1,z1)
    b.box(tuple((x+y)/2 for x,y in zip(a,c)),tuple(abs(x-y) for x,y in zip(a,c)),mat,label=label)
def bracket(b,arm,position,divisions):
    # The concave lower edge begins nearly vertical at the wall and approaches the soffit tangentially.
    def curve(t):
        p=[(.018,.115),(.071,.20),(.090,.618),(.53,.663)]
        return tuple((1-t)**3*p[0][i]+3*(1-t)**2*t*p[1][i]+3*(1-t)*t*t*p[2][i]+t**3*p[3][i] for i in (0,1))
    pts=[curve(i/divisions)for i in range(divisions+1)]
    for i,(a,c) in enumerate(zip(pts,pts[1:])):
        poly=[a,c,(c[0],.701),(a[0],.701)]
        v=[xyz(arm,position+side,r,z) for side in (-.031,.031) for r,z in poly]
        f=[(0,1,2),(0,2,3),(4,6,5),(4,7,6)]
        for k in range(4):
            j=(k+1)%4;f.extend([(k,k+4,j+4),(k,j+4,j)])
        if arm=='front':f=[(c,b,a)for a,b,c in f]
        b.add(v,f,'cream bracket','curved eaves bracket '+arm+f' {position:.2f}')
    box(b,arm,position-.045,position+.045,-.005,.03,.101,.173,'cream bracket','small square bracket heel')
def gutter(b,arm,begin,end,lod):
    count=9 if lod else 18;out=.030;cen=.616;z0=.873
    # Open half-round section, separate concave inside and rounded outside.
    profile=[(cen+(out+d)*cos(pi*i/count),z0-(out+d)*sin(pi*i/count))
             for d,inds in [(0,range(count+1)),(-.0035,range(count,-1,-1))]for i in inds]
    n=len(profile);v=[xyz(arm,s,r,z)for s in (begin,end) for r,z in profile];f=[]
    for i in range(n):
        j=(i+1)%n;f.extend([(i,j,j+n),(i,j+n,i+n)])
    b.add(v,f,'stone grey gutter',arm+' half round rainwater gutter')
def add_building(b,lod=False):
    for arm,begin,end in [('front',-FRONT,OUT),('side',0,SIDE)]:
        vents=sorted(s for side,s in VENTS if side==arm);cursor=begin
        for s in vents:
            box(b,arm,cursor,s-.108,0,OUT,.70,.756,'painted soffit',arm+' light soffit')
            for r0,r1 in [(0,.264),(.409,OUT)]:
                box(b,arm,s-.108,s+.108,r0,r1,.70,.756,'painted soffit',arm+' shoulders of ventilation hole')
            box(b,arm,s-.108,s+.108,.264,.409,.745,.758,'concealed vent shade','deep rectangular opening '+arm)
            cursor=s+.108
        box(b,arm,cursor,end,0,OUT,.70,.756,'painted soffit',arm+' light soffit')
        box(b,arm,begin,end,.568,OUT,.733,.857,'wine fascia',arm+' wine coloured edge board')
        box(b,arm,begin,end,-.012,.566,.756,.843,'roof bed',arm+' roof bed')
        box(b,arm,begin,min(end,0) if arm=='front' else end,-.06,.001,-.025,.699,'cream wall return',arm+' visible wall return')
        gutter(b,arm,begin,end,lod)
        # Seams and over-the-lip fasteners are visible at intervals around both arms.
        for s in ([ -1.92,-1.14,-.41,.46] if arm=='front' else [.70,1.37,2.05]):
            b.tube([xyz(arm,s,.625,.877),xyz(arm,s,.643,.856),xyz(arm,s,.629,.836),xyz(arm,s,.613,.828)],.006,'gutter straps',6 if lod else 9,arm+' metal gutter straps')
        # The first strip of shallow red clay tiles seen above the horizontal edge.
        for i in range(round((end-begin)/.125)):
            s0=begin+i*.125;s1=min(s0+.122,end)
            if s1<=s0:continue
            v=[xyz(arm,s,r,z+off)for off in (-.016,0) for s,r,z in [(s0,.512,.852),(s1,.512,.852),(s1,.045,.907),(s0,.045,.907)]]
            b.add(v,[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)],('roof tile red','roof tile ochre')[i%2],arm+' leading visible tile row')
    for arm,p in BRACKETS:bracket(b,arm,p,10 if lod else 24)
