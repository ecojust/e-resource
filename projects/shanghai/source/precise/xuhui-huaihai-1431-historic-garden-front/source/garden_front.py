"""The garden elevation recorded in the Basset photographs, in an independent local frame."""
from math import sqrt
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade

WALL = 'warm lime plaster'
STONE = 'pale limestone'
SHADE = 'shaded stone'
GLASS = 'grey blue glass'
SASH = 'deep timber joinery'
BRONZE = 'dark finial metal'
ROOF = 'weathered grey brown tile'
RIDGE = 'raised tile rolls'
BASE = 'coursed foundation stone'
PALETTE = {
    WALL: dict(color=[.780,.742,.650],roughness=.90),
    STONE: dict(color=[.851,.821,.727],roughness=.83),
    SHADE: dict(color=[.672,.636,.548],roughness=.89),
    GLASS: dict(color=[.289,.351,.351],roughness=.33,metallic=.13),
    SASH: dict(color=[.251,.241,.204],roughness=.70),
    BRONZE: dict(color=[.271,.257,.194],roughness=.54,metallic=.36),
    ROOF: dict(color=[.253,.237,.200],roughness=.87),
    RIDGE: dict(color=[.353,.329,.270],roughness=.82),
    BASE: dict(color=[.692,.666,.596],roughness=.92),
}


def window(face, hole, columns, rows, label):
    x0,z0,x1,z1 = hole.bounds
    bars = [box(x0+(x1-x0)*i/columns-.025,z0,x0+(x1-x0)*i/columns+.025,z1)
            for i in range(1,columns)]
    bars.extend(box(x0,z0+(z1-z0)*i/rows-.023,x1,z0+(z1-z0)*i/rows+.023)
                for i in range(1,rows))
    face.prism(hole,-.19,-.165,GLASS,label+' glazing')
    inner = hole.buffer(-.064,join_style=2)
    face.prism(hole.difference(inner.difference(unary_union(bars))),-.146,-.074,SASH,label+' sash')
    face.prism(box(x0-.065,z0-.075,x1+.065,z0-.014),-.042,.100,STONE,label+' sill')


def slab(b,x0,x1,y0,y1,z0,z1,mat,label):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=label)


def flat_wall(b,a,c,height,holes,label):
    f=Facade(b,a,c,label)
    f.wall(0,height,holes=holes,thickness=.32,material=WALL)
    return f


def turned(b,x,y,z,low,label):
    p=[(0,.102),(.070,.104),(.112,.073),(.17,.058),(.28,.091),(.37,.083),(.48,.052),(.525,.087),(.567,.090)]
    b.lathe((x,y),[(z+h,r) for h,r in p],STONE,segments=8 if low else 14,label=label)


def outward_curve(width,base,reach,n):
    return [(-width+2*width*i/n,base-reach*sqrt(max(0,1-(-1+2*i/n)**2))) for i in range(n+1)]


def curved_band(b,line,depth,z0,z1,material,label):
    # All passes share an identical projected arc at a given LOD.
    poly=Polygon([*line,*[(x,y+depth) for x,y in reversed(line)]])
    b.plan_prism(poly,z0,z1,material,label)


def balcony(b,line,level,low,label,spacing=.283):
    curved_band(b,line,.19,level,level+.11,STONE,label+' lower moulding')
    curved_band(b,[(x,y-.015)for x,y in line],.22,level+.66,level+.77,STONE,label+' cap rail')
    for (x0,y0),(x1,y1) in zip(line,line[1:]):
        length=((x1-x0)**2+(y1-y0)**2)**.5
        count=max(1,round(length/spacing))
        for j in range(count):
            t=(j+.5)/count
            turned(b,x0+(x1-x0)*t,y0+(y1-y0)*t+.094,level+.103,low,label+' turned balusters')
    for j in (0,len(line)//4,len(line)//2,3*len(line)//4,len(line)-1):
        x,y=line[j]
        b.box((x,y+.09,level+.36),(.225,.22,.69),STONE,label=label+' square newels')


def hip(b,u,low):
    left,right=u-4.12,u+4.12
    front,back=-.99,2.18
    eave,ridge=11.22,12.88
    # Visible half of each shallow hipped roof, ending at the archival section through the apex.
    b.add([(left,front,eave),(right,front,eave),(right,back,eave),(u,back,ridge),(left,back,eave)],
          [(0,1,3),(1,2,3),(3,4,0)],ROOF,'hipped wing roof, front and two hips')
    b.add([(left,back,eave),(right,back,eave),(u,back,ridge)],[(0,2,1)],ROOF,'cut face at hip ridge')
    slab(b,left,right,front,back,11.09,11.23,STONE,'thin continuous projecting eave')
    for i in range(1,26 if low else 51):
        count=26 if low else 51
        x=left+(right-left)*i/count
        t=1-abs(x-u)/4.12
        b.tube([(x,front+.025,eave+.022),(x,front+(back-front)*t,eave+(ridge-eave)*t+.022)],
               .037 if low else .047,RIDGE,sides=5 if low else 7,label='round tile rolls on hip')
    for x in [left,right]:
        b.tube([(x,front,eave+.03),(u,back,ridge+.03)],.067,RIDGE,sides=8,label='covered hip ridge')
    b.lathe((u,back),[(ridge,.142),(ridge+.18,.118),(ridge+.24,.185),(ridge+.31,.109),
                      (ridge+.46,.078),(ridge+.78,.052),(ridge+.97,.026),(ridge+1.43,.008)],
            BRONZE,12 if low else 20,label='tall paired roof finials')


def wing(b,u,low):
    # Broad central light and two distinctly narrower flanking lights are visible on both storeys.
    holes=[]
    for z,h in [(2.23,2.44),(6.50,2.18)]:
        for x,w in [(-1.68,.94),(0,1.49),(1.68,.94)]:
            holes.append(box(x-w/2,z,x+w/2,z+h))
    foundation_lights=[box(x-.33,.25,x+.33,1.04) for x in (-1.56,1.49)]
    f=flat_wall(b,(u-3.38,0),(u+3.38,0),10.39,holes+foundation_lights,'projecting end pavilion')
    for j,hole in enumerate(holes):
        window(f,hole,2 if j%3==1 else 1,3,'garden windows')
    for hole in foundation_lights:window(f,hole,2,2,'basement lights')
    for z,h,proj,mat in [(1.30,.11,.11,BASE),(1.46,.10,.16,STONE),(5.58,.12,.19,SHADE),(9.05,.115,.14,STONE),
                         (9.37,.125,.24,STONE),(10.25,.22,.32,SHADE),(10.54,.20,.45,STONE)]:
        f.prism(box(-3.42,z,3.42,z+h),-.22,proj,mat,'horizontal stone courses')
    for x in [-2.89,2.89]:
        f.prism(box(x-.21,5.78,x+.21,9.09),-.02,.09,STONE,'upper pavilion pilasters')
        for z,w,h in [(8.67,.54,.13),(8.84,.62,.16),(9.01,.77,.09)]:
            f.prism(box(x-w/2,z,x+w/2,z+h),.04,.19,STONE,'pilaster capitals')
        for dx in [-.235,.235]:
            # Two short projecting scrolls mark the capital edges in the snow photograph.
            f.builder.lathe((u+x+dx,-.16),[(8.68,.035),(8.75,.074),(8.805,.088),(8.85,.063)],
                            STONE,8 if low else 14,label='capital side volutes')
        if not low:
            for dx in [-.14,0,.14]:
                f.prism(Polygon([(x+dx,8.52),(x+dx-.064,8.67),(x+dx-.032,8.78),
                                 (x+dx,8.73),(x+dx+.046,8.79),(x+dx+.063,8.66)]),
                        .135,.199,STONE,'capital leaf relief')
            for dx in [-.125,0,.125]:
                f.prism(box(x+dx-.022,6.59,x+dx+.022,8.62),.083,.109,SHADE,'inset pilaster channels')
    # Deep eaves with individual projecting brackets, rather than a dark texture.
    b.add([(u-3.42,.035,10.42),(u+3.42,.035,10.42),(u+4.10,-.985,11.105),(u-4.10,-.985,11.105)],
          [(0,1,2,3)],SHADE,'sloped soffit below the hipped roof')
    for x in [-3.31,-2.12,-.94,.25,1.43,2.62,3.28]:
        poly=Polygon([(-.02,9.71),(-.34,9.99),(-.78,10.97),(-.78,11.08),(.15,11.08),(.15,9.71)])
        b.prism(poly,x+u-.065,x+u+.065,lambda y,z,d:(d,y,z),SHADE,'splayed high eave corbels')
    for x in (-2.10,-.73,.73,2.10):
        b.prism(Polygon([(-.08,4.12),(-.23,4.15),(-1.22,5.18),(-1.22,5.46),(.10,5.46),(.10,4.12)]),
                x+u-.105,x+u+.105,lambda y,z,d:(d,y,z),SHADE,'wing balcony corbels')
    ledge=[(u-2.70,-.08),(u-2.52,-1.04),(u-2.32,-1.28),(u+2.32,-1.28),(u+2.52,-1.04),(u+2.70,-.08)]
    b.plan_prism(Polygon([*ledge,(u+2.70,.05),(u-2.70,.05)]),5.44,5.68,STONE,'canted end balconies')
    balcony(b,ledge,5.68,low,'end pavilion balcony')
    hip(b,u,low)


def middle(b,low):
    f=Facade(b,(-3.62,.68),(3.62,.68),'inset central pavilion')
    holes=[box(x-.405,6.48,x+.405,7.86)for x in (-2.44,-1.48,1.48,2.44)]
    opening=box(-2.88,1.47,2.88,5.23)
    f.wall(0,9.05,[opening,*holes],thickness=.31,material=WALL)
    for hole in holes:window(f,hole,1,2,'paired upper windows')
    f.prism(opening,-.34,-.29,SASH,'recessed porch joinery')
    for x in (-1.55,0,1.55):
        f.prism(box(x-.48,2.02,x+.48,4.70),-.266,-.25,GLASS,'glazed recess panels')
    for z,w in [(8.07,.095),(8.74,.16),(9.0,.11)]:
        f.prism(box(-3.67,z,3.67,z+w),-.10,.21,STONE,'central frieze and cornice')
    pts=[(-3.65,.19,9.10),(3.65,.19,9.10),(3.65,2.36,12.10),(-3.65,2.36,12.10)]
    b.add(pts,[(0,1,2,3)],ROOF,'central roof slope to section')
    for i in range(1,21 if low else 43):
        n=21 if low else 43;x=-3.65+7.30*i/n
        b.tube([(x,.20,9.135),(x,2.36,12.13)],.039,RIDGE,sides=5 if low else 7,label='tile rolls across central slope')
    d=Facade(b,(-1.68,.56),(1.68,.56),'continuous roof dormer')
    windows=[box(x-.248,9.88,x+.248,10.74)for x in [-1.16,-.38,.38,1.16]]
    d.wall(9.50,10.98,windows,thickness=.37,material=STONE)
    for h in windows:window(d,h,1,1,'dormer glazed lights')
    slab(b,-1.92,1.92,.24,1.83,11.00,11.15,ROOF,'dormer overhanging shallow eave')
    for x in (-2.,0,2.89):
        slab(b,x-.155,x+.155,2.04,2.35,11.79,12.43,SHADE,'visible short chimney')
        slab(b,x-.19,x+.19,2.02,2.37,12.43,12.51,STONE,'chimney caps')
    line=outward_curve(3.94,-.15,1.93,24 if low else 40)
    poly=Polygon([*line,(3.94,.72),(-3.94,.72)])
    b.plan_prism(poly,0,1.32,BASE,'solid stone plinth supporting the garden porch')
    for z in (.31,.65,.98):
        curved_band(b,[(x,y-.021) for x,y in line],.047,z,z+.032,SHADE,'fine plinth courses')
    b.plan_prism(poly,1.32,1.48,BASE,'curved raised porch landing')
    b.plan_prism(poly,5.25,5.52,SHADE,'arched-plan portico ceiling and fascia')
    curved_band(b,[(x,y-.04)for x,y in line],.23,5.51,5.64,STONE,'lip of central balcony')
    balcony(b,line,5.64,low,'bowed central balustrade',.32)
    for x in (-3.20,-1.12,1.12,3.20):
        y=-.15-1.93*sqrt(1-(x/3.94)**2)+.165
        slab(b,x-.21,x+.21,y-.215,y+.215,1.48,1.58,STONE,'porch column plinth')
        b.lathe((x,y),[(1.575,.175),(1.64,.177),(1.69,.145),(1.75,.132),(4.99,.116),
                       (5.055,.134),(5.09,.164),(5.14,.177),(5.19,.177)],STONE,
                12 if low else 24,label='four free-standing porch columns')
        slab(b,x-.21,x+.21,y-.20,y+.20,5.185,5.254,STONE,'porch abaci')
    for i in range(8):
        top=1.48*(i+1)/8;front=-4.37+.315*i
        slab(b,-1.49,1.49,front,front+.318,0,top,BASE,'central garden stair treads')
    for u in [-1.66,1.66]:
        b.prism(Polygon([(-4.39,0),(-4.39,.21),(-1.85,1.67),(-1.70,1.67),(-1.70,0)]),
                u-.13,u+.13,lambda y,z,d:(d,y,z),STONE,'ramped stone stair cheeks')


def annex(b,u,right,low):
    # Three exposed facets follow the rounded left room; slender glazed facets form the right sunroom.
    if right:
        pts=[(u-1.73,.64),(u-1.43,-.23),(u-.70,-.67),(u+.35,-.72),(u+1.09,-.42),(u+1.65,.22),(u+1.75,.71)]
    else:
        pts=[(u-2.32,.67),(u-1.86,-.12),(u-.99,-.55),(u+.16,-.69),(u+1.32,-.48),(u+2.21,.16),(u+2.40,.67)]
    polygon=Polygon([*pts,(pts[-1][0],1.52),(pts[0][0],1.52)])
    b.plan_prism(polygon,0,1.35,BASE,'low foundations of visible annexes')
    for a,c in zip(pts,pts[1:]):
        f=Facade(b,a,c,'glazed garden annex' if right else 'rounded masonry annex')
        width=f.length*(.86 if right else .65)
        hole=box(-width/2,2.06 if right else 2.11,width/2,4.82 if right else 4.19)
        f.wall(1.35,4.98 if right else 4.94,[hole],thickness=.21,material=SASH if right else WALL)
        window(f,hole,1 if low else 2,3 if right else 2,'annex casements')
    b.plan_prism(polygon,4.94,5.07,STONE,'separate annex cornice')
    if right:
        apex=(u,.92,6.52)
        for a,c in zip(pts,pts[1:]):
            b.add([(*a,5.065),(*c,5.065),apex],[(0,1,2)],ROOF,'faceted conservatory roof')
            b.tube([(*a,5.075),apex],.033,RIDGE,sides=6,label='conservatory roof ridges')
        b.lathe((u,.92),[(6.50,.085),(6.62,.06),(6.86,.014)],BRONZE,10,label='conservatory small finial')
    else:balcony(b,pts,5.07,low,'rounded annex parapet')


def make_front(b,low=False):
    for u in [-6.97,6.97]:wing(b,u,low)
    middle(b,low)
    annex(b,-12.58,False,low)
    annex(b,12.08,True,low)
