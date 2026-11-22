"""Upper iron crest of the photographed garden gate. Control points refer to the credited crop."""
from math import hypot
BASE_COLOURS={'painted steel frame':[.055,.053,.052],'black flat-iron scroll':[.036,.038,.039],'weathered iron edge':[.116,.095,.077],'black leaf terminals':[.080,.078,.072],'black lower sheet':[.048,.051,.054],'rivet heads':[.125,.107,.087]}
PALETTE={name:{'color':rgb,'roughness':.65} for name,rgb in BASE_COLOURS.items()}
# Pixel pairs in a 820-pixel wide view of the native rectangle (2010,1060,3500,2135).
UPPER=((64,401),(256,356),(540,180),(749,163))
LOWER=((64,529),(247,498),(533,360),(753,328))
# Each made-on-site flat is followed separately. The open terminal and the turn onto the next flat are retained.
ORNAMENTS=[
 ('left edge upper inward scroll',[(79,437),(87,391,128,389,146,405),(165,425,165,452,151,456),(136,462,142,435,154,441)]),
 ('left bottom spiral',[(78,444),(89,463,101,474,107,466),(119,450,97,448,89,459),(68,479,84,510,102,513),(118,517,128,488,111,484),(103,482,98,488,99,495)]),
 ('lower narrow upright with rolled end',[(121,517),(149,517,174,511,181,497),(194,481,180,466,169,476),(159,487,170,497,177,487)]),
 ('second bay outside curl',[(185,502),(206,476,207,435,208,416),(210,381,240,350,277,342),(304,338,333,354,337,382),(344,421,325,454,306,460),(287,467,285,447,298,448)]),
 ('second bay top leaf and curling end',[(205,414),(204,391,230,371,250,379),(263,385,261,405,249,411),(235,416,236,397,248,393)]),
 ('second bay right upward return',[(277,342),(272,360,275,385,289,395),(302,404,316,393,312,380),(311,367,294,361,291,373)]),
 ('second bay lower fork',[(211,464),(214,436,232,420,250,424),(271,430,278,452,267,461),(258,467,253,450,261,448)]),
 ('second bay base return',[(220,480),(216,462,232,443,245,447),(254,449,252,462,245,465)]),
 ('third bay left ascending return',[(338,420),(334,391,336,368,349,337),(367,297,397,282,420,302),(432,314,431,341,414,345),(399,348,392,336,405,329)]),
 ('third bay facing inward leaf',[(342,355),(345,336,362,321,376,322),(397,321,411,334,410,347),(410,356,404,345,394,345)]),
 ('third bay lower C',[(338,426),(355,446,388,432,398,420),(409,406,395,394,385,401),(377,409,386,414,393,407)]),
 ('centre tall return',[(383,415),(415,400,452,390,473,369),(494,344,498,306,485,283),(474,259,441,263,427,280),(407,300,423,334,441,335),(457,335,462,315,451,311)]),
 ('centre base flower',[(384,417),(413,419,445,399,453,381),(464,355,444,349,436,362),(427,375,437,384,446,371)]),
 ('right of centre fork',[(490,360),(488,333,498,303,515,297),(530,291,545,304,540,321),(536,335,520,333,521,324)]),
 ('right paired bottom curl',[(491,360),(507,377,529,367,530,348),(530,337,518,335,513,343)]),
 ('large right-hand C',[(533,363),(573,358,618,343,638,317),(662,286,654,243,628,229),(605,217,578,231,573,250),(566,273,581,292,598,285),(609,279,603,264,596,264)]),
 ('small right-hand return',[(556,355),(545,342,547,322,562,318),(575,313,583,325,577,333)]),
 ('end bay outside curl',[(643,327),(643,300,650,273,665,247),(679,221,701,205,723,212),(744,217,751,241,737,254),(724,265,701,253,705,237)]),
 ('end bay smaller curl',[(645,315),(639,302,643,280,655,270),(673,253,690,267,682,280),(677,291,668,291,666,283)]),
 ('right lower fork',[(650,311),(660,338,686,339,700,328),(717,315,703,291,690,296),(678,302,682,318,692,317)]),
 ('crest left short S',[(225,354),(210,347,196,343,200,323),(205,299,230,286,249,292),(259,298,248,308,243,307),(240,312,249,323,255,321)]),
 ('crest first broad S',[(224,355),(245,352,262,340,267,324),(264,311,257,297,267,282),(274,265,289,266,293,284),(295,292,291,301,286,298)]),
 ('crest tall sweep and leaf tight curl',[(262,337),(302,331,318,302,327,269),(338,231,359,181,393,174),(424,168,447,199,443,227),(440,250,412,276,390,262),(373,252,374,224,393,217),(407,212,412,231,401,235)]),
 ('crest central small ring',[(429,249),(453,248,471,232,473,213),(475,197,460,191,450,201),(442,211,450,219,458,216)]),
 ('crest inward bud',[(468,228),(483,235,514,225,521,207),(532,187,521,164,506,165),(491,166,486,187,495,195)]),
 ('crest middle upper return',[(521,216),(536,199,530,180,545,158),(557,139,577,136,592,143),(608,153,611,172,600,178)]),
 ('crest central nested S',[(533,194),(546,213,565,214,574,203),(584,191,570,177,561,181),(553,185,557,195,563,194)]),
 ('crest upper rising sweep',[(552,153),(577,133,596,137,622,142),(641,145,674,131,679,105),(685,80,662,67,646,76),(629,84,624,104,637,114),(644,120,656,115,658,106)]),
 ('crest central top ring',[(601,142),(588,135,582,128,585,116),(587,102,606,97,612,108),(615,113,610,121,605,118)]),
 ('crest end summit and descending curve',[(648,139),(667,131,676,122,678,102),(681,79,694,57,714,56),(736,55,759,78,759,105),(759,124,753,136,748,142)]),
 ('crest summit leaf',[(678,110),(681,127,700,132,710,122),(721,113,716,96,710,94)])]
LEAVES=[(102,495),(152,440),(248,393),(293,373),(405,329),(449,311),(706,237),(401,235),(495,195),(658,106),(710,94)]
def position(u,v):
    # Vertical ribs become slightly taller towards the latch. A .80 scale at left is assumed.
    t=(u-62)/692;scale=.80+.20*t
    return (2.12*t/scale, (533-86*t-v)*.00315/scale)
def sample(seg,count):
    p=seg[0];out=[p]
    for x1,z1,x2,z2,x3,z3 in seg[1:]:
        x0,z0=p
        for i in range(1,count+1):
            t=i/count;s=1-t
            out.append((s**3*x0+3*s*s*t*x1+3*s*t*t*x2+t**3*x3,s**3*z0+3*s*s*t*z1+3*s*t*t*z2+t**3*z3))
        p=(x3,z3)
    return out
def ribbon(b,points,width,y0,y1,material,label):
    points=[position(x,z)for x,z in points];verts=[]
    for i,(x,z) in enumerate(points):
        a=points[max(0,i-1)];d=points[min(len(points)-1,i+1)];dx,dz=d[0]-a[0],d[1]-a[1];length=hypot(dx,dz)
        nx,nz=-dz/length*width/2,dx/length*width/2
        verts.extend([(x+nx,y0,z+nz),(x-nx,y0,z-nz),(x-nx,y1,z-nz),(x+nx,y1,z+nz)])
    faces=[(0,2,1),(0,3,2)];k=len(verts)-4
    faces.extend([(k,k+1,k+2),(k,k+2,k+3)])
    for j in range(0,k,4):
        for a in range(4):
            c=(a+1)%4;faces.extend([(j+a,j+c,j+4+c),(j+a,j+4+c,j+4+a)])
    b.add(verts,faces,material,label)
def edge(which,t):
    a,b,c,d=which;s=1-t
    return tuple(s**3*a[i]+3*s*s*t*b[i]+3*s*t*t*c[i]+t**3*d[i]for i in range(2))
def add_building(b,lod):
    n=24 if lod else 64
    for i,curve in enumerate([UPPER,LOWER]):
        pts=[edge(curve,j/n)for j in range(n+1)]
        ribbon(b,pts,.044 if i==0 else .040,-.036,.015,'painted steel frame',('sweeping top transom','lower scroll transom')[i])
    for j,(name,spine) in enumerate(ORNAMENTS):
        ribbon(b,sample(spine,13 if j in (14,15) else 9 if lod else 15),.010 if j<20 else .009,-.016,.010,'black flat-iron scroll',name)
    for i,(u,v) in enumerate(LEAVES):
        pts=[(u-6,v+4),(u-4,v-3),(u+1,v-8),(u+7,v-7),(u+4,v-2),(u+2,v+5)]
        verts=[(position(x,z)[0],y,position(x,z)[1])for y in (-.025,.005)for x,z in pts];k=len(pts);faces=[]
        for j in range(1,k-1):faces.extend([(0,j,j+1),(k,k+j+1,k+j)])
        for j in range(k):
            a=(j+1)%k;faces.extend([(j,k+j,k+a),(j,k+a,a)])
        b.add(verts,faces,'black leaf terminals','forged terminal '+str(i+1))
    for ix,(u,top,base)in enumerate([(62,395,560),(752,143,361)]):
        ribbon(b,[(u,top),(u+2,base)],.041,-.039,.018,'painted steel frame','hinge side head' if ix==0 else 'latch side head')
    verts=[];faces=[]
    for j in range(n+1):
        u,v=edge(LOWER,j/n);x,z=position(u,v);verts.extend([(x,.019,z),(x,.019,z-.110),(x,.035,z-.110),(x,.035,z)])
    for j in range(0,n*4,4):
        for a in range(4):
            c=(a+1)%4;faces.extend([(j+a,j+c,j+4+c),(j+a,j+4+c,j+4+a)])
    k=4*n;faces.extend([(0,2,1),(0,3,2),(k,k+1,k+2),(k,k+2,k+3)])
    b.add(verts,faces,'black lower sheet','visible top of door skin')
    for j in range(10):
        x,z=position(*edge(LOWER,(j+.23)/10.1))
        b.tube([(x,-.040,z),(x,-.046,z)],.008,'rivet heads',7 if lod else 10,'lower transom rivets')
