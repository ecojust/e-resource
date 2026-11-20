"""Build the photographed east front and southeast tower at 375 North Shaanxi Road."""
from pathlib import Path
from shapely.affinity import translate
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening
from sign_lettering import lettering_shapes

WIDTH = 12.236
BACK = 4.12
PALETTE = {
    'tower face brick': {'color':[.366,.101,.067], 'roughness':.85},
    'burnt header': {'color':[.290,.076,.053], 'roughness':.86},
    'warm stretcher': {'color':[.396,.124,.077], 'roughness':.82},
    'dark mortar': {'color':[.250,.081,.066], 'roughness':.93},
    'cream coping': {'color':[.767,.743,.642], 'roughness':.81},
    'white painted plaster': {'color':[.734,.720,.646], 'roughness':.86},
    'window steel': {'color':[.115,.143,.126], 'roughness':.48},
    'dark glazing': {'color':[.102,.161,.177], 'roughness':.25, 'metallic':.15},
    'inner dark timber': {'color':[.073,.045,.034], 'roughness':.76},
    'terracotta roof tiles': {'color':[.380,.152,.098], 'roughness':.84},
    'cross vermilion': {'color':[.628,.024,.019], 'roughness':.46, 'metallic':.14},
    'neutral section': {'color':[.475,.425,.363], 'roughness':.89},
}

def sash(face, outline, ncols, nrows, name, detail=True):
    l,b,r,t=outline.bounds
    inset=outline.buffer(-.057,join_style='mitre')
    grid=[box(l+(r-l)*i/ncols-.023,b,l+(r-l)*i/ncols+.023,t) for i in range(1,ncols)]
    grid.extend(box(l,b+(t-b)*i/nrows-.028,r,b+(t-b)*i/nrows+.028) for i in range(1,nrows))
    panes=inset.difference(unary_union(grid))
    face.prism(outline.buffer(.01,join_style='mitre'),-.305,-.282,'dark glazing',name+' glass')
    face.prism(outline.buffer(-.012,join_style='mitre').difference(panes),-.247,-.15,'window steel',name+' steel grid')
    if detail:
        face.prism(panes.difference(panes.buffer(-.026,join_style='mitre')),-.274,-.235,'inner dark timber',name+' pane rebates')

def brickwork(face, outline, lod, name):
    """Fired bricks and open mortar on a bounded face, including true aperture reveals."""
    if lod:return
    left,bottom,right,top=outline.bounds
    face.prism(outline,.006,.012,'dark mortar',name+' thin mortar bed')
    bins={k:[[],[]] for k in ('tower face brick','burnt header','warm stretcher')}
    pitch,height=.329,.161
    rows=int((top-bottom)/height)+1
    for j in range(rows):
        z0=bottom+j*height+.006;z1=min(top-.004,z0+height-.010)
        if z1-z0<.016:continue
        start=left-(.5*pitch if j%2 else 0)
        for i in range(int((right-start)/pitch)+1):
            x0=max(left+.005,start+i*pitch+.006);x1=min(right-.005,start+(i+1)*pitch-.006)
            if x1-x0<.016:continue
            brick=box(x0,z0,x1,z1)
            # Incomplete bricks at curved arch heads are cut to their visible outline.
            if not outline.covers(brick):
                cut=outline.intersection(brick)
                if cut.area>.002:face.prism(cut,.011,.024,'tower face brick',name+' cut brick')
                continue
            tone=(i*7+j*11+j//4)%33
            mat='warm stretcher' if tone<6 else 'burnt header' if tone<9 else 'tower face brick'
            vs,fs=bins[mat];n=len(vs)
            vs.extend(face.point(x,z,d) for d in (.011,.024) for x,z in [(x0,z0),(x1,z0),(x1,z1),(x0,z1)])
            fs.extend(tuple(n+a for a in inds) for inds in [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
    for mat,(vs,fs) in bins.items():
        if fs:face.builder.add(vs,fs,mat,face.label+'/'+name+' brick courses')

def wall(face, outline, holes, lod, name):
    masonry=outline.difference(unary_union(holes))
    face.prism(masonry,-.38,0,'tower face brick',name+' wall')
    brickwork(face,masonry,lod,name)

def edge_course(face, z, width, name):
    for lift,thick,depth,mat in [(-.13,.085,.11,'cream coping'),(0,.16,.22,'white painted plaster'),(.14,.12,.27,'cream coping')]:
        face.beam(z+lift,thick,depth,mat,width=width,label=name)

def bell_face(face, lod):
    z0,z1=.03,11.74
    opening_all=opening(0,6.30,.93,4.90,.22,segments=20 if lod else 36)
    wall(face,box(-face.length/2,z0,face.length/2,z1),[opening_all],lod,'bell tower')
    # Both photographed shaft openings have a lower glazed pair, a white middle
    # panel, and a tall shadowed ventilator under a very shallow arched head.
    lower=box(-.465,6.30,.465,7.93)
    sash(face,lower,2,2,'lower tower lights',not lod)
    face.prism(box(-.475,7.91,.475,9.24),-.31,-.19,'white painted plaster','tower inset spandrel')
    head=opening_all.intersection(box(-.6,9.23,.6,11.3))
    face.prism(head.buffer(.008),-.365,-.34,'inner dark timber','shadow behind ventilator')
    for j in range(7 if lod else 15):
        z=9.26+j*(1.76/(7 if lod else 15));slat=head.intersection(box(-.5,z,.5,z+.046))
        face.prism(slat,-.28,-.171,'window steel','ventilator blades')
    surround=opening_all.buffer(.125,join_style='mitre').difference(opening_all)
    face.prism(surround,-.04,.056,'burnt header','raised tower architrave')
    for level in range(13):
        z=6.46+level*.351
        for s in (-1,1):face.box(s*.547,z,.204,.087,.058,.048,'warm stretcher','projecting staggered jamb bricks')
    face.box(0,6.23,1.18,.12,.24,.03,'burnt header','tower sill')

def add_tower(builder,lod):
    cx=-3.20;hw=1.52;cy=1.88;hy=1.52
    west,east=cx-hw,cx+hw;front,back=cy-hy,cy+hy
    a=Facade(builder,(west,front),(east,front),'tower east street face')
    s=Facade(builder,(west,back),(west,front),'tower south return')
    bell_face(a,lod);bell_face(s,lod)
    for p,q in [((east,front),(east,back)),((east,back),(west,back))]:
        face=Facade(builder,p,q,'unseen tower side');face.wall(.03,11.74,[],.12,'tower face brick')
    for z,w,h,m in [(11.71,3.20,.12,'cream coping'),(11.93,3.11,.34,'white painted plaster'),(12.20,3.17,.13,'cream coping'),(12.36,3.22,.20,'white painted plaster')]:
        builder.box((cx,cy,z),(w,w,h),m,label='tower/square parapet and crown')
    builder.box((cx,cy,13.55),(.14,.16,2.18),'cross vermilion',label='tower/red cross upright')
    builder.box((cx,cy,13.96),(1.68,.16,.145),'cross vermilion',label='tower/red cross arm')

def building(builder,lod):
    half=WIDTH/2
    front=Facade(builder,(-half,.70),(half,.70),'gable and shoulder')
    crest=.29; bottom=5.30;top=8.44;ridge_end=5.81;ridge_start=-5.23
    outline=Polygon([(-half,.02),(half,.02),(half,bottom),(ridge_end,bottom),(crest,top),(ridge_start,bottom),(-half,bottom)])
    # The tower and projecting vestibule obscure the middle of this wall.
    edge=opening(4.72,1.62,.79,2.75,.20,segments=14 if lod else 28)
    wall(front,outline,[edge],lod,'brick shoulders and gable')
    sash(front,edge,2,3,'north shoulder opening',not lod)
    front.prism(edge.buffer(.095).difference(edge),-.035,.055,'burnt header','shoulder architrave')
    # Gable reveal under the rising white cornice, behind the forward flat parapet.
    peak=Polygon([(ridge_start,bottom),(crest,top),(ridge_end,bottom),(ridge_end-.55,bottom),(crest,top-.34),(ridge_start+.55,bottom)])
    front.prism(peak,-.22,.10,'white painted plaster','raking gable cornice')
    for side,xmax in [(ridge_start,crest),(crest,ridge_end)]:
        z0=top if side==crest else bottom;z1=top if xmax==crest else bottom
        q=Polygon([(side,z0),(xmax,z1),(xmax,z1-.16),(side,z0-.16)])
        front.prism(q,-(BACK-.70),-.13,'terracotta roof tiles','front band of pitched nave roof')
        # Red roof channels run down the pitch on the dated oblique street photograph.
        for i in range(9 if lod else 17):
            y=.84+i*(BACK-.90)/(8 if lod else 16)
            builder.tube([(side,y,z0+.024),(xmax,y,z1+.024)],.038,'terracotta roof tiles',6 if lod else 8,'roof/curved tile courses')
    front.beam(5.29,.18,.16,'cream coping',width=WIDTH,label='shoulder eave')
    vestibule=Facade(builder,(-2.0,-.05),(3.55,-.05),'entrance vestibule');w=vestibule.length
    windows=[opening(x,3.33,1.08,1.35,.16,segments=16 if lod else 28)for x in (-1.60,0,1.60)]
    doors=[box(x-.49,.035,x+.49,2.14)for x in (-1.60,0)]
    body=box(-w/2,.02,w/2,6.69)
    wall(vestibule,body,windows+doors,lod,'entrance brickwork')
    white=box(-2.35,.035,2.37,4.70)
    for x,q in zip((-1.60,0,1.60),windows):
        sash(vestibule,q,2,2,'lobby steel casements',not lod)
        white=white.union(q.buffer(.225,join_style='mitre'))
    vestibule.prism(white.difference(unary_union(windows+doors)),.025,.074,'white painted plaster','continuous entry dressings')
    for x,p in zip((-1.60,0),doors):
        vestibule.prism(p.buffer(.012),-.605,-.58,'inner dark timber','recessed visible door leaves')
        vestibule.prism(p.buffer(.004).difference(p.buffer(-.055)),-.56,-.22,'window steel','recessed door lining')
        for off in (-.24,.24):vestibule.box(x+off,.91,.375,1.32,.06,-.535,'inner dark timber','timber door panel')
    font=Path(__file__).with_name('fonts')/'GraceChurchNameSubset.otf'
    # The photographs show one small, widely spaced red character under each sash.
    for x,letter in zip((-1.60,0,1.60),'怀恩堂'):
        for character,glyph in lettering_shapes(letter,.43,.48,font=font):
            vestibule.prism(translate(glyph,xoff=x,yoff=2.70),.081,.11,'cross vermilion','vestibule name '+character)
    edge_course(vestibule,5.35,w+.13,'lower vestibule cornice');edge_course(vestibule,6.69,w+.20,'upper vestibule coping')
    for x0,x1 in [(-2.0,-1.89),(3.44,3.55)]:
        builder.box(((x0+x1)/2,.39,3.34),(x1-x0,.88,6.68),'tower face brick',label='vestibule/short side return')
    builder.box((.775,.42,6.63),(5.55,.94,.14),'cream coping',label='vestibule/top')
    for x in (-half,half):
        builder.box((x+(.06 if x<0 else -.06),(.70+BACK)/2,2.62),(.12,BACK-.70,5.24),'neutral section',label='front/northern or southern section')
    builder.prism(outline,-.11,0,lambda u,z,d:(u,BACK-d,z),'neutral section','front/plain rear section')
    add_tower(builder,lod)
