"""Current exterior of the former Chung Wei Bank, including the north water-tower stages."""
from math import cos,pi,sin
from shapely.geometry import Point,Polygon,box
from shapely.geometry.polygon import orient
from photo_architecture import Facade,opening

RED='weathered deep red facing'; BRICK='brick red tower'; WHITE='pale grey facade facing'
STONE='warm grey base stone'; DARK='dark aluminium frames'; GLASS='recessed blue-grey glazing'
METAL='dark bronze'; ROOF='weathered flat roof'; STEEL='galvanised mast'
PALETTE={
 RED:{'color':[.385,.172,.139],'roughness':.89},BRICK:{'color':[.426,.174,.137],'roughness':.89},
 WHITE:{'color':[.647,.65,.635],'roughness':.79},STONE:{'color':[.597,.562,.504],'roughness':.84},
 DARK:{'color':[.138,.139,.136],'metallic':.42},
 GLASS:{'color':[.146,.198,.222],'metallic':.23,'roughness':.33},
 METAL:{'color':[.252,.203,.144],'metallic':.60},ROOF:{'color':[.385,.385,.367],'roughness':.88},
 STEEL:{'color':[.428,.451,.443],'metallic':.60,'roughness':.46}}
# +Y follows the east wall toward Yanan East Road. The short south elevation
# fronts Jinling East Road; the shoulders and four northern facets follow the
# real footprint rather than a rectangular box.
SW=(-14.96,-36.10);SW2=(-8.38,-35.43);SE=(16.55,-32.77);NE=(16.56,28.25)
NNE=(8.94,35.03);NN=(-.88,36.52);NNW=(-10.70,33.37);NW=(-17.94,25.20)
RING=[SW,SW2,SE,NE,NNE,NN,NNW,NW]
PLAN=orient(Polygon(RING),1);BASE=5.20;STEP=3.63;TOP=31.36


def inset(f,hole,columns=2,rows=1,lod=False):
    f.window(hole,columns=1 if lod else columns,rows=1 if lod else rows,trim=False,frame=DARK,glass=GLASS,label='recessed window')


def rail(f,u,z,width,lod):
    f.box(u,z,width,.22,.93,.27,WHITE,'balcony projecting slab')
    f.box(u,z+1.03,width-.10,.07,.085,.67,DARK,'balcony handrail')
    for i in range(5 if lod else 10):
        count=5 if lod else 10
        f.box(u+((i+.5)/count-.5)*(width-.19),z+.55,.043,.91,.06,.67,DARK,'balcony metal uprights')
    for side in [-1,1]:
        f.box(u+side*(width/2-.10),z+.57,.06,.96,.67,.33,DARK,'balcony return rail')


def base(f,style,lod):
    length=f.length
    count=max(1,round(length/(4.7 if style in ['east','south']else 5.7)))
    holes=[]
    for i in range(count):
        u=(i+.5)*length/count-length/2
        center_gate=style=='north central' and i==count//2
        width=min(3.10,length/count*.66)
        if center_gate:
            h=opening(u,.10,width,4.54,arch=.95,segments=10 if lod else 20)
            f.prism(h.buffer(.004),-.68,-.58,METAL,'north main arched bronze portal')
            for hand in [-1,1]:f.box(u+hand*width*.21,1.75,width*.36,2.64,.08,-.49,GLASS,'north gate glazing')
            f.prism(h.buffer(.19).difference(h),-.16,.18,STONE,'deep stone arch surround')
        else:
            h=opening(u,.62,width,3.24);inset(f,h,2,2,lod)
        holes.append(h)
    face=f.wall(0,BASE,holes,.37,STONE)
    for z in [1.05,2.06,3.09,4.15]:
        j=face.intersection(box(-length/2,z,length/2,z+.033))
        f.prism(j,-.01,.02,WHITE,'base stone bed joints')
    f.box(0,BASE-.13,length+.015,.25,.56,.06,STONE,'ground-storey cornice')


def strip_storeys(f,style,lod):
    base(f,style,lod)
    length=f.length
    if style=='east':
        # The 2015 east view has six windows surrounded by red panels in each
        # long pale band, smaller red end bays and a vertical balcony stack.
        positions=[(-.44,.045),(-.35,.060),(-.235,.064),(-.135,.064),(-.035,.064),(.065,.064),(.165,.064),(.265,.064),(.374,.054),(.452,.049)]
    elif style=='south':positions=[(-.36,.15),(-.13,.15),(.12,.16),(.36,.16)]
    else:
        count=max(1,round(length/4.3));positions=[((i+.5)/count-.5,.53/count)for i in range(count)]
    for n in range(7):
        z=BASE+n*STEP;h0=z+.55;h1=z+2.80
        holes=[]
        for frac,rel in positions:
            width=length*rel;u=frac*length
            h=opening(u,h0,width,h1-h0);holes.append(h);inset(f,h,2,1,lod)
        face=f.wall(z,z+STEP,holes,.32,RED)
        street=style in ['east','south']
        if street:
            # Continuous pale facing conceals sections of the original red
            # brick. Exposed rectangular panels remain between the windows.
            left,right=(-.291*length,.322*length)if style=='east'else(-.50*length,.50*length)
            for a,b in [(z,h0+.07),(h1-.06,z+STEP)]:
                f.prism(box(left,a,right,b),.003,.10,WHITE,'continuous pale horizontal facing')
            if style=='east':
                for a,b in [(-.5*length,-.402*length),(-.302*length,-.276*length)]:
                    f.prism(face.intersection(box(a,z,b,z+STEP)),.003,.085,WHITE,'end-bay pale facing')
                if n in range(1,7):rail(f,-.355*length,z+.45,2.96,lod)
            elif style=='south':
                for x in [-.50*length,-.255*length,0,.254*length,.50*length]:
                    f.prism(face.intersection(box(x-.22,h0,x+.22,h1)),.003,.085,WHITE,'south window bay mullion')
        else:
            if style!='west':f.box(0,z+STEP-.06,length,.11,.23,.035,WHITE,'return horizontal course')
    f.wall(BASE+7*STEP,TOP,(),.28,RED)
    f.box(0,TOP-.14,length+.017,.24,.47,.065,STONE,'roof coping')


def north_facade(f,style,lod):
    base(f,style,lod)
    count=max(1,round(f.length/3.48));holes=[]
    for i in range(count):
        u=((i+.5)/count-.5)*f.length
        for n in range(7):
            h=opening(u,BASE+n*STEP+.62,min(1.81,f.length/count*.55),2.08);holes.append(h);inset(f,h,2,1,lod)
    wall=f.wall(BASE,TOP,holes,.32,BRICK)
    # Tall strips mark the faceted entrance end. The eastern shoulder has pale
    # horizontal bands discernible in the long-lens 2015 east photograph.
    if style=='northeast shoulder':
        for n in range(7):
            z=BASE+n*STEP
            f.prism(wall.intersection(box(-f.length/2,z,f.length/2,z+.54)),.003,.095,WHITE,'faceted return band')
    for x in [-.45*f.length,.45*f.length]:
        f.box(x,17.81,.20,25,.24,.06,WHITE,'slender vertical strip')


def stage(b,center,width,depth,bottom,top,levels,lod,name):
    cx,cy=center;cut=min(1.02,width*.08)
    pts=[(cx-width/2+cut,cy-depth/2),(cx+width/2-cut,cy-depth/2),
         (cx+width/2,cy-depth/2+cut),(cx+width/2,cy+depth/2-cut),
         (cx+width/2-cut,cy+depth/2),(cx-width/2+cut,cy+depth/2),
         (cx-width/2,cy+depth/2-cut),(cx-width/2,cy-depth/2+cut)]
    for a,end in zip(pts,pts[1:]+pts[:1]):
        f=Facade(b,a,end,name);holes=[]
        broad=f.length>2.1
        if broad:
            for row in range(levels):
                bottom_window=bottom+(row+.27)*(top-bottom)/levels
                h=min(1.54,(top-bottom)/levels*.48);w=.72 if width>7 else .41
                u=0
                aperture=opening(u,bottom_window,w,h,arch=.21 if width<9 else .0,segments=7 if lod else 12)
                holes.append(aperture);inset(f,aperture,1,1,lod)
        f.wall(bottom,top,holes,.25,BRICK)
        if broad and width>5:
            for u in [-f.length*.404,f.length*.404]:
                f.box(u,(bottom+top)/2,.125,top-bottom-.1,.22,.09,STONE,'tower vertical pier edge')
            f.box(0,top-.11,f.length+.01,.20,.34,.045,RED,'stepped tower cornice')
    b.plan_prism(Polygon(pts),top-.12,top,ROOF,name+' roof')


def add_building(b,lod):
    for a,end,label in [(SW,SW2,'southwest'),(SW2,SE,'south'),(SE,NE,'east'),(NE,NNE,'northeast shoulder'),
                        (NNE,NN,'north central'),(NN,NNW,'northwest shoulder'),(NNW,NW,'northwest'),(NW,SW,'west')]:
        f=Facade(b,a,end,label)
        if label.startswith('north'):north_facade(f,label,lod)
        else:strip_storeys(f,label,lod)
    b.plan_prism(PLAN,0,.15,STONE,'ground floor')
    b.plan_prism(PLAN,TOP-.17,TOP,ROOF,'filled former courtyard and roof platform')
    # Northern upper floors and the stepped tower are visible from both streets.
    for name,w,d,x,y,z,z2,n in [('north upper offices',21.6,15.4,-.50,25.60,TOP,36.08,1),
                                ('upper apartments',16.45,12.10,-.78,26.21,36.08,41.63,2),
                                ('upper tower',11.78,9.78,-.88,26.60,41.63,47.76,2),
                                ('first water tower stage',7.90,7.25,-.88,26.83,47.76,51.42,1),
                                ('second water tower stage',5.43,5.52,-.88,26.83,51.42,54.82,1),
                                ('upper crown',3.06,3.30,-.88,26.83,54.82,56.79,1)]:
        stage(b,(x,y),w,d,z,z2,n,lod,name)
    tc=(-.88,26.83)
    b.lathe(tc,[(56.79,.79),(57.15,.72),(57.88,.49),(58.72,.36)],RED,
            segments=9 if lod else 16,label='spire masonry and mast plinth')
    b.lathe(tc,[(58.72,.21),(62.10,.133),(67.90,.053)],STEEL,
            segments=6 if lod else 10,label='metal mast')
    # Equipment on the filled roof is approximated from multiple overhead releases.
    for x,y,w,h in [(-4.9,-7.0,5.1,3.0),(-4.0,7.4,4.1,3.6),(4.0,-18.6,3.4,3.5)]:
        b.plan_prism(box(x-w/2,y-h/2,x+w/2,y+h/2),TOP,TOP+.59,ROOF,'low roof plant')
