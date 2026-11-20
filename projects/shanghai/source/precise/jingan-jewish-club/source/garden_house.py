"""South garden house, as photographed at 722 Nanjing West Road."""
from math import cos, pi, sin
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from photo_architecture import Facade,opening

HALF=28.43
BACK=15.86
MIDDLE=6.60
END=20.52
PALETTE={
    'buff masonry':{'color':[.69,.505,.358],'roughness':.91},
    'rose masonry':{'color':[.64,.451,.325],'roughness':.91},
    'pale masonry':{'color':[.744,.570,.420],'roughness':.90},
    'lime joints':{'color':[.55,.47,.387],'roughness':.94},
    'dressed ground stone':{'color':[.677,.636,.544],'roughness':.89},
    'warm dressed stone':{'color':[.732,.687,.603],'roughness':.82},
    'cream cornice':{'color':[.843,.787,.686],'roughness':.79},
    'balcony stone':{'color':[.73,.71,.642],'roughness':.85},
    'honed granite':{'color':[.39,.387,.357],'roughness':.73},
    'window sash':{'color':[.076,.069,.053],'roughness':.61},
    'old glass':{'color':[.211,.265,.258],'roughness':.31,'metallic':.12},
    'panel wood':{'color':[.212,.122,.073],'roughness':.71},
    'iron grille':{'color':[.124,.108,.081],'roughness':.66,'metallic':.33},
    'roof red tile':{'color':[.585,.242,.119],'roughness':.94},
    'terracotta roll':{'color':[.645,.301,.158],'roughness':.92},
    'grey flat roof':{'color':[.426,.432,.413],'roughness':.94},
    'plain return':{'color':[.598,.548,.474],'roughness':.92},
    'dormer metal':{'color':[.278,.292,.282],'roughness':.65,'metallic':.14},
}
def stone_courses(f,surface,lod,upper=True):
    lo,z0,hi,z1=surface.bounds
    step=.286 if upper else .635
    width=.68 if upper else 1.54
    # The full mesh expresses narrow masonry beds and the larger dressed-stone courses below.
    # LOD keeps continuous wall colour and the shaped architectural surrounds.
    if lod:return
    mat=['buff masonry','buff masonry','pale masonry','rose masonry']if upper else ['dressed ground stone','dressed ground stone','warm dressed stone']
    for row in range(int((z1-z0)/step)+1):
        z=z0+row*step;left=lo-width*(row%2)/2
        for j in range(int((hi-left)/width)+1):
            u=left+j*width;piece=box(u+.013,z+.009,u+width-.009,z+step-.010)
            q=piece if surface.covers(piece)else surface.intersection(piece)
            if q.area>.006:f.prism(q,.002,.019,mat[(7*j+11*row+(j*row)%5)%len(mat)],'masonry face units')
def cornice(f,x,z,w,depth,label):
    for dz,extra,h,extend,mat in [(-.20,-.07,.09,.025,'warm dressed stone'),(-.105,.01,.085,.065,'cream cornice'),(0,.08,.13,.115,'balcony stone'),(.115,.19,.09,.19,'cream cornice')]:
        f.box(x,z+dz,w+extra,h,depth+extend,.06+extend/2,mat,label)
def surround(f,ap,amount,low,hi,mat,lab):
    f.prism(ap.buffer(amount,join_style=2).difference(ap),low,hi,mat,lab)
def sash(f,ap,x,z,w,h,lod,label,cols=3):
    f.window(ap,cols,3 if lod else 4,'window sash',False,'old glass',label=label)
    surround(f,ap,.112,.021,.135,'warm dressed stone',label+'/surround')
    f.box(x,z-.074,w+.29,.128,.25,.093,'cream cornice',label+'/sill')
def balustrade(b,f,x0,x1,y,z,lod,label):
    run=x1-x0;n=round(run/.41);zs=z+.13
    b.box(((x0+x1)/2,y,z+.082),(run+.20,.36,.164),'balcony stone',label=label+'/lower rail')
    b.box(((x0+x1)/2,y,z+.971),(run+.26,.40,.17),'cream cornice',label=label+'/handrail')
    for i in range(n+1):
        u=x0+run*i/n
        if i in (0,n,round(n/2)):
            b.box((u,y,z+.516),(.29,.34,.73),'balcony stone',label=label+'/piers');continue
        heights=[(zs,.117),(zs+.114,.120),(zs+.158,.073),(zs+.235,.080),(zs+.359,.111),
            (zs+.491,.090),(zs+.573,.058),(zs+.640,.073),(zs+.727,.117),(zs+.769,.118)]
        if lod:heights=[heights[j]for j in [0,2,4,6,9]]
        b.lathe((u,y),heights,'balcony stone',7 if lod else 12,label+'/bottle balusters')
def tuscan(b,x,y,bottom,top,r,lod,label):
    pf=[(bottom,r*1.38),(bottom+.12,r*1.38),(bottom+.18,r*1.12),(bottom+.26,r*1.29),
        (bottom+.35,r),(top-.38,r*.88),(top-.30,r*1.08),(top-.21,r*1.15),(top-.14,r*1.34)]
    b.lathe((x,y),pf,'warm dressed stone',9 if lod else 17,label+'/turned shaft')
    b.box((x,y,top-.065),(r*2.90,r*2.90,.13),'cream cornice',label=label+'/abacus')
def arcade(b,s,lod):
    left,right=sorted([s*MIDDLE,s*END]);width=right-left;f=Facade(b,(left,.38),(right,.38),'Garden gallery')
    pitch=width/5;centers=[(i-2)*pitch for i in range(5)];holes=[]
    for u in centers:
        ap=opening(u,.30,pitch-.31,3.62,1.12,12 if lod else 22);holes.append(ap)
        f.window(ap,3,4,'window sash',False,'old glass',label='round-headed glazed bay')
        surround(f,ap,.102,.029,.178,'warm dressed stone','arcade/arched band')
        # Thin radial fan over the main impost and three tall vertical panes.
        for n in range(1,6):
            a=n*pi/6;ray=LineString([(u,2.78),(u+1.24*cos(a),2.78+1.17*sin(a))]).buffer(.020)
            f.prism(ap.intersection(ray),-.257,-.195,'window sash','fanlight/radial bars')
        f.box(u,2.76,pitch-.36,.089,.13,-.174,'iron grille','gallery/transom rail')
    lower=f.wall(.16,4.43,holes,.50,'dressed ground stone');stone_courses(f,lower,lod,False)
    for i in range(6):tuscan(b,left+i*pitch,.28,.08,2.78,.153,lod,'Gallery/Tuscan arcade')
    b.box(((left+right)/2,2.33,4.50),(width,4.36,.19),'balcony stone',label='Gallery/terrace deck')
    cornice(f,0,4.51,width,.32,'projecting terrace stringcourse')
    balustrade(b,f,left+.09,right-.09,.32,4.60,lod,'Terrace garden-side')
    upper=Facade(b,(left,4.48),(right,4.48),'Recessed upper gallery');cuts=[]
    for u in centers:
        ap=box(u-.62,4.60,u+.62,7.42);cuts.append(ap);sash(upper,ap,u,4.6,1.24,2.82,lod,'upper glazed doors',2)
    wall=upper.wall(4.55,8.46,cuts,.43,'buff masonry');stone_courses(upper,wall,lod)
    for i in range(6):upper.box(-width/2+i*pitch,6.52,.17,3.79,.22,.067,'cream cornice','upper slender pilasters')
    cornice(upper,0,8.49,width,.40,'upper eaves')
    for x in [left+.11,right-.11]:
        b.box((x,2.55,6.50),(.21,3.85,3.96),'buff masonry',label='Terrace/short solid return')
def end_pavilion(b,s,lod):
    # The three front planes and their upper fenestration are visible at both ends of the 2020 roof view.
    coords=[(END,1.67),(END+1.56,-.08),(HALF-1.62,-.08),(HALF,1.58),(HALF,BACK),(END,BACK)]if s==1 else [(-HALF,1.58),(-HALF+1.62,-.08),(-END-1.56,-.08),(-END,1.67),(-END,BACK),(-HALF,BACK)]
    for i in range(3):
        a,c=coords[i:i+2];f=Facade(b,a,c,'Polygonal end pavilion');width=f.length
        locations=[-.94,.0,.94]if i==1 else [0];cuts=[]
        for u in locations:
            w=.61 if i==1 else .70
            for z,h in [(.58,2.82),(4.93,2.40)]:
                ap=box(u-w/2,z,u+w/2,z+h);cuts.append(ap);sash(f,ap,u,z,w,h,lod,'end casement',2)
        low=box(-width/2,0,width/2,4.47).difference(unary_union(cuts));high=box(-width/2,4.47,width/2,8.45).difference(unary_union(cuts))
        f.prism(low,-.39,0,'dressed ground stone','end ground wall');f.prism(high,-.39,0,'buff masonry','end upper wall')
        stone_courses(f,high,lod);cornice(f,0,4.47,width,.28,'middle sill band');cornice(f,0,8.49,width,.40,'end eave')
    side=Facade(b,(s*HALF,1.61),(s*HALF,BACK),'short end')if s==1 else Facade(b,(s*HALF,BACK),(s*HALF,1.61),'short end')
    windows=[]
    for u in [-3.82,.0,3.82]:
        for z,h in [(.69,2.36),(4.96,2.33)]:
            ap=box(u-.51,z,u+.51,z+h);windows.append(ap);sash(side,ap,u,z,1.02,h,lod,'side casement',2)
    side.wall(0,8.44,windows,.38,'buff masonry');cornice(side,0,8.49,side.length,.28,'end eave return')
    # The outer roof joins the gallery ridge without a hip at the arcade junction.
def wing_roof(b,side,lod):
    low,high=8.61,10.97
    def pt(x,y,z=low):return (side*x,y,z)
    left=pt(MIDDLE,4.27);inner=pt(END,4.27);chamfer=pt(END,1.67);a=pt(END+1.56,-.08)
    e=pt(HALF-1.62,-.08);c=pt(HALF,1.58);back=pt(HALF,BACK);tail=pt(MIDDLE,BACK)
    q=pt((END+HALF)/2,4.12,high);junction=pt((END+HALF)/2,10.065,high);ridge_start=pt(MIDDLE,10.065,high)
    faces=[[left,inner,junction,ridge_start],[tail,ridge_start,junction,back],[c,back,junction,q],
          [a,e,q],[e,c,q],[chamfer,a,q],[inner,chamfer,q,junction]]
    for n,poly in enumerate(faces):
        # Orient roof pitches consistently upward in both mirrored wings.
        normal=(poly[1][0]-poly[0][0])*(poly[2][1]-poly[0][1])-(poly[1][1]-poly[0][1])*(poly[2][0]-poly[0][0])
        order=tuple(range(len(poly))) if normal>0 else tuple(reversed(range(len(poly))))
        b.add(poly,[order],'roof red tile','Roof/continuous gallery and end slopes')
        if not lod:
            outer,other,z1,z0= (poly[0],poly[1],poly[2],poly[-1]) if n!=1 else (poly[3],poly[0],poly[1],poly[2])
            for i in range(1,14):
                t=i/15
                points=[tuple(o[j]+t*(z[j]-o[j]) for j in range(3)) for o,z in [(outer,z0),(other,z1)]]
                if sum((points[0][j]-points[1][j])**2 for j in range(3))>.02:
                    b.tube(points,.020,'terracotta roll',4,'Roof/shallow tile courses')
    for a,c in [(a,q),(e,q),(chamfer,q),(c,q),(q,junction),(junction,ridge_start),(inner,junction),(junction,back)]:
        b.tube([a,c],.072,'terracotta roll',7,'Roof/connected hipped ridges')
def window_circle(f,u,z,r,lod):
    ap=Point(u,z).buffer(r,quad_segs=8 if lod else 17)
    f.prism(ap.buffer(.014),-.295,-.26,'old glass','circular window/recess')
    surround(f,ap,.135,.018,.19,'cream cornice','circular ring and opening')
    ring=ap.difference(ap.buffer(-.065))
    bars=unary_union([box(u-.028,z-r,u+.028,z+r),box(u-r,z-.027,u+r,z+.027)])
    f.prism(unary_union([ring,bars]).intersection(ap),-.253,-.179,'window sash','circle sash')
    return ap
def main_portico(b,lod):
    f=Facade(b,(-MIDDLE,1.25),(MIDDLE,1.25),'Central house');holes=[]
    entry=opening(0,-.03,3.15,3.86,1.20,14 if lod else 28);holes.append(entry)
    for s in [-1,1]:
        u=s*4.72;holes.append(window_circle(f,u,2.97,.51,lod))
        low=box(u-.62,.87,u+.62,1.78);holes.append(low);sash(f,low,u,.87,1.24,.91,lod,'low rectangular window',3)
    low=f.wall(0,4.58,holes,.51,'dressed ground stone');stone_courses(f,low,lod,False)
    # One deep opening with paired shafts, semicircular archivolt and a physically recessed door.
    pf=Facade(b,(-3.22,-.28),(3.22,-.28),'Main entrance porch');outer=opening(0,-.05,3.39,3.97,1.31,15 if lod else 28)
    porch=pf.wall(0,4.37,[outer],.42,'dressed ground stone');stone_courses(pf,porch,lod,False);surround(pf,outer,.201,.029,.23,'warm dressed stone','portal/arch surround')
    for axis in [-1,1]:
        for shift in [-.34,.34]:tuscan(b,axis*2.35+shift,-.22,.04,2.68,.207,lod,'Portal/paired Tuscan columns')
        pf.box(axis*2.36,2.76,1.61,.23,.65,.10,'cream cornice','portal/paired impost')
    f.prism(entry.buffer(.015,join_style=2),-.39,-.34,'panel wood','inset doorway')
    frame=entry.difference(entry.buffer(-.093,join_style=2));f.prism(frame,-.32,-.235,'warm dressed stone','inset door frame')
    for j in [-.96,-.32,.32,.96]:
        for z in [.65,1.48,2.31]:f.box(j,z,.47,.63,.118,-.28,'panel wood','door field panel')
    for u in [-2.91,2.91]:b.box((u,.48,2.12),(.27,1.49,4.24),'dressed ground stone',label='Portal/reveals')
    b.box((0,.50,4.40),(6.45,1.83,.23),'warm dressed stone',label='Portal/upper balcony slab')
    balustrade(b,pf,-3.12,3.12,-.16,4.51,lod,'Central doorway/balcony')
    upper=Facade(b,(-MIDDLE,.91),(MIDDLE,.91),'Central first floor');cuts=[]
    for u in [-4.68,-1.11,1.11,4.68]:
        w=1.29 if abs(u)>3 else 1.63;ap=box(u-w/2,4.82,u+w/2,7.49);cuts.append(ap);sash(upper,ap,u,4.82,w,2.67,lod,'central casement',2)
    high=upper.wall(4.60,8.52,cuts,.40,'buff masonry');stone_courses(upper,high,lod);cornice(upper,0,8.59,2*MIDDLE,.43,'eave');cornice(f,0,4.48,2*MIDDLE,.34,'principal floor band')
def hip(b,x0,x1,y0,y1,z,rise,lod,label):
    w=x1-x0;d=y1-y0;h=min(w,d)*.46
    if w>=d:q0=(x0+h,(y0+y1)/2,z+rise);q1=(x1-h,(y0+y1)/2,z+rise)
    else:q0=((x0+x1)/2,y0+h,z+rise);q1=((x0+x1)/2,y1-h,z+rise)
    corn=[(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)]
    faces=[[corn[0],corn[1],q1,q0],[corn[1],corn[2],q1],[corn[2],corn[3],q0,q1],[corn[3],corn[0],q0]]if w>=d else [[corn[0],corn[1],q0],[corn[1],corn[2],q1,q0],[corn[2],corn[3],q1],[corn[3],corn[0],q0,q1]]
    for face in faces:b.add(face,[tuple(range(len(face)))],'roof red tile',label)
    for ind,corner in enumerate(corn):
        target=(q0 if ind in ([0,3]if w>=d else [0,1])else q1);b.tube([corner,target],.075,'terracotta roll',6,label+'/hips')
    b.tube([q0,q1],.087,'terracotta roll',7,label+'/ridge')
    if not lod:
        for face in faces:
            a,c=face[0],face[1];e=face[-1];v=face[2]
            for i in range(1,13):
                t=i/14;line=[tuple(o[j]+t*(q[j]-o[j])for j in range(3))for o,q in [(a,e),(c,v)]]
                b.tube(line,.022,'terracotta roll',4,label+'/tile courses')
def garden_house(b,lod):
    main_portico(b,lod)
    for side in [-1,1]:
        arcade(b,side,lod);end_pavilion(b,side,lod)
        left,right=sorted([side*MIDDLE,side*END])
        wing_roof(b,side,lod)
        for y in [6.31,12.0]:
            u=side*27.45;b.box((u,y,10.28),(.65,.78,3.17),'buff masonry',label='Roof/slender side chimneys')
            b.box((u,y,11.91),(.83,.97,.19),'cream cornice',label='Roof/chimney cap')
            b.box((u,y,12.12),(.63,.74,.25),'buff masonry',label='Roof/chimney pot')
    hip(b,-MIDDLE,MIDDLE,.71,8.57,8.75,2.81,lod,'Roof/central projecting block')
    b.box((0,(BACK+8.51)/2,8.35),(2*MIDDLE,BACK-8.51,.23),'grey flat roof',label='Roof/flat portion behind central eave')
    # Central dormer and the flagstaff in the independently photographed elevated view.
    b.box((0,2.55,9.33),(2.04,2.33,1.36),'buff masonry',label='Roof/central dormer')
    dormer=Facade(b,(-1.03,1.38),(1.03,1.38),'Dormer');dormer.box(0,9.38,1.42,.65,.085,.071,'old glass','front pane')
    for x in [-.72,0,.72]:dormer.box(x,9.38,.072,.69,.090,.123,'window sash','front sash')
    for j in [-1,1]:
        a=(j*1.34,1.24,9.82);c=(j*1.34,3.99,9.82);d=(0,4.00,10.70);e=(0,1.24,10.70)
        b.add([a,c,d,e],[(0,1,2,3)]if j==1 else [(3,2,1,0)],'roof red tile','Roof/dormer gable')
    dormer.prism(Polygon([(-1.30,9.77),(1.30,9.77),(0,10.66)]),-.08,.11,'warm dressed stone','triangular gable')
    b.tube([(0,3.85,10.70),(0,3.85,13.10)],.040,'dormer metal',8,'Roof/flagstaff')
    for x in [-5.05,5.05]:
        b.box((x,BACK-2.08,8.58),(1.56,1.33,.30),'dormer metal',label='Roof/low skylights')
    for s in [-1,1]:
        x0,x1=sorted([s*MIDDLE,s*HALF]);b.box(((x0+x1)/2,BACK-.16,4.3075),(x1-x0,.32,8.615),'plain return',label='Rear/closed plain returns at the roof eaves')
        # The gallery roof terminates against the central flat portion. Close its triangular inner cheek
        # exactly at the two roof pitches, without inventing a rear window elevation.
        cheek=Polygon([(4.27,8.41),(BACK,8.41),(BACK,8.61),(10.065,10.97),(4.27,8.61)])
        origin=s*MIDDLE
        b.prism(cheek,-.05,.05,lambda y,z,d:(origin+d,y,z),'plain return','Roof/closed gallery gable ends')
    b.box((0,BACK-.16,4.195),(2*MIDDLE,.32,8.39),'plain return',label='Rear/cut below flat roof')
    b.box((0,8.54,8.602),(2*MIDDLE,.14,.302),'plain return',label='Roof/closed central hipped to flat junction')
