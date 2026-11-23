"""Street entrance at 200 South Shanxi Road, local metres along the western wall.

x increases north from the OSM southwest endpoint. y is positive toward the
street. z is above pavement. Standalone part; the host authors the street wall.
"""
from math import cos, hypot, pi, sin

OPENING = dict(x=(41.80, 49.86), y=(-0.83, 0.0), z=(0.0, 5.04))
# Linear values are supplied by the host's material factory from these sRGB chips.
MATERIALS = {
    "nh_entry_walnut": "#462E28", "nh_entry_woodlight": "#724B37",
    "nh_entry_darkglass": "#242A2B", "nh_entry_shadow": "#29221E",
    "nh_entry_sill": "#A59A85", "nh_entry_canopy": "#564435",
    "nh_entry_bronze": "#947556", "nh_entry_burnished": "#BF995F",
    "nh_entry_plaqueface": "#494635", "nh_post_green": "#173A31",
    "nh_post_black": "#122721", "nh_post_notice": "#D8D7BE",
    "nh_post_ink": "#324751",
}
W="nh_entry_walnut"; T="nh_entry_woodlight"; G="nh_entry_darkglass"
D="nh_entry_shadow"; S="nh_entry_sill"; C="nh_entry_canopy"; B="nh_entry_bronze"
H="nh_entry_burnished"; P="nh_entry_plaqueface"
GREEN="nh_post_green"; BLACK="nh_post_black"; PAPER="nh_post_notice"; INK="nh_post_ink"

def prism(b, name, material, xz, back, front):
    """Extrude a convex front elevation patch, keeping outward face winding."""
    pts=list(xz)
    area=sum(x*z1-x1*z for (x,z),(x1,z1) in zip(pts,pts[1:]+pts[:1]))
    if area>0:pts.reverse()
    n=len(pts);verts=[(x,y,z) for y in (back,front) for x,z in pts]
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    b.mesh(name,material,verts,faces)

def rail(b, name, mat, a, c, width, back, front):
    dx=c[0]-a[0];dz=c[1]-a[1];length=hypot(dx,dz)
    ux=-dz/length*width/2;uz=dx/length*width/2
    prism(b,name,mat,[(a[0]+ux,a[1]+uz),(c[0]+ux,c[1]+uz),
                      (c[0]-ux,c[1]-uz),(a[0]-ux,a[1]-uz)],back,front)

def turned(b,name,mat,cx,cy,profile,n):
    verts=[];faces=[]
    for radius,z in profile:
        verts.extend((cx+radius*cos(2*pi*i/n),cy+radius*sin(2*pi*i/n),z) for i in range(n))
    faces.append(tuple(range(n-1,-1,-1)))
    for k in range(len(profile)-1):
        for i in range(n):
            j=(i+1)%n;faces.append((k*n+i,k*n+j,(k+1)*n+j,(k+1)*n+i))
    faces.append(tuple(range((len(profile)-1)*n,len(profile)*n)))
    b.mesh(name,mat,verts,faces)

def frame(b,name,mat,x0,x1,z0,z1,back,front,thick):
    for key,l,r,bot,top in (
        ("south",x0,x0+thick,z0,z1),("north",x1-thick,x1,z0,z1),
        ("sill",x0+thick,x1-thick,z0,z0+thick),
        ("lintel",x0+thick,x1-thick,z1-thick,z1)):
        b.box(name+"-"+key,mat,l,r,back,front,bot,top)

def paired_doors(b,name,x0,x1,depth,detail):
    box=b.box;center=(x0+x1)/2
    frame(b,name+"-surround",W,x0,x1,.085,3.38,depth-.09,depth+.045,.095)
    for index,(lo,hi) in enumerate(((x0+.091,center-.010),(center+.010,x1-.091))):
        pre=name+"-"+str(index)
        box(pre+"-closed-glass",G,lo,hi,depth-.09,depth-.059,.17,3.29)
        frame(b,pre+"-leaf",T,lo,hi,.16,3.30,depth-.058,depth+.037,.061)
        box(pre+"-kick",W,lo+.041,hi-.041,depth-.04,depth+.039,.165,.39)
        box(pre+"-bar",T,lo+.041,hi-.041,depth-.03,depth+.046,2.29,2.34)
        for idx,base in enumerate((1.16,1.25) if detail else (1.205,)):
            outer=lo+.045 if index==0 else hi-.045
            inner=hi-.045 if index==0 else lo+.045
            rail(b,pre+"-chevron-"+str(idx),B,(outer,base),(inner,base+.24),.027 if detail else .045,depth+.048,depth+.105)
    box(name+"-transom-glass",G,x0+.085,x1-.085,depth-.10,depth-.065,3.40,3.79)
    box(name+"-transom-bar",W,x0+.075,x1-.075,depth-.085,depth+.038,3.36,3.43)

def canopy(b,name,x0,x1,reach,detail):
    b.box(name+"-underside",C,x0,x1,-.045,reach,3.785,3.875)
    b.box(name+"-front-rim",B,x0-.012,x1+.012,reach-.055,reach+.015,3.790,3.922)
    for end,x in enumerate((x0,x1-.040)):
        b.box(name+"-edge-"+str(end),B,x,x+.040,.025,reach-.045,3.807,3.916)
    if detail:
        # Diaper cutouts seen along the leading edge in the distributor's close view.
        n=max(2,round((x1-x0)/.20));step=(x1-x0-.07)/n
        for i in range(n):
            x=x0+.035+step*i
            rail(b,name+"-vein-"+str(i),C,(x,3.804),(x+step*.45,3.900),.012,reach+.016,reach+.024)

def word(b,name,text,cx,z,y,height,mat):
    """Raised Latin plaque characters, read left to right from the street."""
    strokes={
        'M':[[(0,0),(0,1),(.35,.49),(.70,1),(.70,0)]],
        'E':[[(0,0),(0,1),(.64,1)],[(0,.51),(.52,.51)],[(0,0),(.62,0)]],
        'T':[[(0,1),(.71,1)],[(.355,1),(.355,0)]],
        'R':[[(0,0),(0,1),(.44,1),(.64,.82),(.61,.63),(.46,.53),(0,.53)],[(.30,.53),(.68,0)]],
        'O':[[ (.18,0),(0,.23),(0,.77),(.18,1),(.51,1),(.67,.78),(.67,.22),(.50,0),(.18,0)]],
        'P':[[(0,0),(0,1),(.45,1),(.64,.81),(.59,.62),(.43,.51),(0,.51)]],
        'L':[[(0,1),(0,0),(.63,0)]],
    }
    step=.88*height;start=cx+((len(text)-1)*step+.70*height)/2
    for i,ch in enumerate(text):
        for j,poly in enumerate(strokes[ch]):
            for k,(a,c) in enumerate(zip(poly,poly[1:])):
                p=(start-(i*.88+a[0])*height,z+a[1]*height);q=(start-(i*.88+c[0])*height,z+c[1]*height)
                rail(b,f"{name}-{i}-{j}-{k}",mat,p,q,height*.065,y,y+.008)

def plaque(b,detail):
    x0,x1=39.08,40.94;z0,z1=1.03,2.76
    b.box("hotel-bronze-plaque",P,x0,x1,.025,.095,z0,z1)
    frame(b,"hotel-plaque-step",B,x0-.035,x1+.035,z0-.035,z1+.035,.017,.112,.049)
    if detail:frame(b,"hotel-plaque-inner",B,x0+.055,x1-.055,z0+.055,z1-.055,.092,.105,.015)
    cx=(x0+x1)/2
    # Three contiguous rising strokes reproduce the visible stepped hotel crest.
    for i,(xo,h) in enumerate(((.16,.24),(0,.385),(-.155,.31))):
        left=cx+xo-.062;right=cx+xo+.062
        prism(b,"hotel-crest-column-"+str(i),H,[(left,2.00),(right,2.015),(right,2+h),(left,1.95+h)],.096,.123)
    rail(b,"hotel-crest-crown",H,(cx+.10,2.31),(cx-.04,2.39),.035,.099,.128)
    word(b,"hotel-plaque-METROPOLO","METROPOLO",cx,1.70,.098,.156,H)

def postbox(b,detail):
    # Independent round cast-iron street pillar with a projecting collection card.
    x,y=38.49,.45;n=24 if detail else 12
    turned(b,"post-pillar-body",GREEN,x,y,[(.24,.055),(.267,.16),(.237,.24),(.235,1.37),(.249,1.43)],n)
    turned(b,"post-pillar-foot",BLACK,x,y,[(.305,.018),(.305,.075),(.281,.105),(.273,.16)],n)
    turned(b,"post-cast-crown",BLACK,x,y,[(.249,1.37),(.301,1.42),(.309,1.468),(.284,1.49),(.273,1.536),(.23,1.56),(.025,1.585)],n)
    b.box("post-hood",GREEN,x-.151,x+.151,y+.17,y+.271,1.265,1.325)
    b.box("post-mouth",BLACK,x-.131,x+.131,y+.224,y+.266,1.217,1.266)
    b.box("post-card-rim",BLACK,x-.141,x+.141,y+.206,y+.263,.765,1.107)
    b.box("post-collection-card",PAPER,x-.124,x+.124,y+.262,y+.268,.784,1.092)
    if detail:
        for i in range(4):
            b.box("post-card-line-"+str(i),INK,x-.101,x+.088,y+.268,y+.271,.81+i*.047,.818+i*.047)
        for i,(a,c) in enumerate((((x+.108,.525),(x-.045,.525)),((x+.090,.56),(x-.020,.56)),
                                 ((x+.080,.592),(x+.011,.592)),((x-.040,.525),(x-.088,.608)),
                                 ((x+.008,.560),(x-.038,.641)))):
            rail(b,"post-wing-mark-"+str(i),H,a,c,.018,y+.220,.004+y+.245)

def build(b, detail=True):
    x0,x1=OPENING["x"];box=b.box
    box("entry-interior-shadow",D,x0,x1,-.825,-.775,.05,5.02)
    box("entry-porch-floor",S,x0,x1,-.77,.083,.018,.077)
    box("entry-ceiling",D,x0,x1,-.77,.021,4.17,4.23)
    for tag,x in (("south",x0),("north",x1-.105)):
        box("entry-reveal-"+tag,W,x,x+.105,-.77,.065,.076,4.27)
    # Chevrons over each outer leaf and the broad central dark vestibule are visible in 2018/2019.
    bays=(("south",41.97,44.17,-.31),("north",47.69,49.69,-.31))
    for name,lo,hi,y in bays:paired_doors(b,"door-"+name,lo,hi,y,detail)
    for label,lo,hi in (("outer-south",41.80,41.98),("middle-south",44.17,44.52),
                         ("middle-north",47.30,47.69),("outer-north",49.69,49.86)):
        box("walnut-pier-"+label,W,lo,hi,-.685,.083,.08,4.30)
        box("light-pier-foot-"+label,S,lo+.003,hi-.003,-.04,.085,.08,.36)
    box("middle-vestibule-glass",G,44.52,47.30,-.677,-.638,.08,3.82)
    frame(b,"middle-vestibule-frame",W,44.52,47.30,.08,3.82,-.69,-.617,.084)
    box("middle-transom",T,44.57,47.25,-.65,-.615,2.83,2.897)
    box("middle-sill",B,44.60,47.22,-.68,-.59,.078,.096)
    box("entry-fascia-base",W,x0,x1,-.24,.077,3.83,5.025)
    box("entry-fascia-cap",B,x0,x1,.061,.103,4.948,5.032)
    for index,(lo,hi) in enumerate(((42.05,43.94),(44.55,47.22),(47.82,49.61))):
        count=max(4,round((hi-lo)/(.073 if detail else .18)))
        for i in range(count):
            x=lo+(i+.5)/count*(hi-lo)
            box(f"entry-flute-{index}-{i}",B,x-.011,x+.011,.078,.096,4.11,4.923)
    for i,x in enumerate((44.35,47.49)):
        box("entry-medallion-square-"+str(i),W,x-.19,x+.19,.078,.106,4.12,4.87)
        prism(b,"entry-medallion-"+str(i),B,[(x+.145*cos(k*pi/8),4.57+.145*sin(k*pi/8))for k in range(16)],.105,.125)
    for name,lo,hi,depth in (("south",41.84,44.19,.91),("middle",44.42,47.41,1.22),("north",47.65,49.82,.91)):
        canopy(b,"entry-canopy-"+name,lo,hi,depth,detail)
    plaque(b,detail);postbox(b,detail)
