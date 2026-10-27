"""Observed exterior detail; approximate dimensions are declared in model-input."""
from pathlib import Path
import math
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from common.photo_architecture import Facade, opening, pieces


def roof_builder(b, data, parts, mode='full'):
    h=data['heights_in_door_units'];eave=h['main_eave'];ridge=h['main_ridge']
    front_y=parts['main_core'][2]-.09;ridge_y=.18
    slope=(ridge-eave)/(ridge_y-front_y)
    holes=[]
    for key in ('south_west_projected_bay','south_east_projected_bay'):
        xa,xb,ya,yb=parts[key];xm=(xa+xb)/2
        peak=h['front_gable_peaks'][key]
        yp=front_y+(peak-eave)/slope
        holes.append(Polygon([(xa,ya-.06),(xb,ya-.06),(xb,front_y),(xm,yp),(xa,front_y)]))
    cross_holes=unary_union(holes)
    def panel(points,label):
        pp=np.asarray(points,float)
        normal=np.cross(pp[1]-pp[0],pp[2]-pp[0])
        if abs(normal[2])<1e-8:raise ValueError('Roof requires nonvertical plane')
        a,c=-normal[:2]/normal[2];k=pp[0,2]-a*pp[0,0]-c*pp[0,1]
        poly=Polygon(pp[:,:2])
        if label=='main/front-roof':poly=poly.difference(cross_holes)
        if '/cross-roof-' in label:
            xmin,ymin,xmax,ymax=poly.bounds
            yc=lambda x:front_y+(a*x+k-eave)/(slope-c)
            poly=poly.intersection(Polygon([(xmin,-100),(xmax,-100),(xmax,yc(xmax)),(xmin,yc(xmin))]))
        mapper=lambda x,y,d:(x,y,a*x+c*y+k+d)
        b.prism(poly,-.022,0,mapper,'slate-like plain roof',label+'/cropped-roof-skin')
        if mode=='lod':return
        # Course exposures remain visible relief; tiles intersect only the
        # supported roof domain, including actual valley-plane cut boundaries.
        across=.205;along=.145
        step_x,step_y=(across,along) if abs(c)>=abs(a) else (along,across)
        if 'curved-roof-strip' in label:
            step_x=max(poly.bounds[2]-poly.bounds[0],.006);step_y=across
        xmin,ymin,xmax,ymax=poly.bounds
        row=0;y=ymin
        while y<ymax-1e-6:
            x=xmin-step_x*.5*(row%2);column=0
            while x<xmax-1e-6:
                tile=poly.intersection(box(x+.003,y+.003,min(x+step_x-.003,xmax),min(y+step_y-.003,ymax)))
                if tile.area>1e-5:
                    b.prism(tile,.001,.010,mapper,'slate-like plain roof',label+f'/slate-course-{row}-{column}')
                x+=step_x;column+=1
            y+=step_y;row+=1
    return panel


def detail_window(b,f,shape,label,cols=3,rows=3,mode='full'):
    inner=shape.buffer(-.033,join_style=2)
    if inner.is_empty:raise ValueError('Invalid window interior')
    f.prism(inner,-.115,-.108,'window glass',label+'/recessed-glass')
    f.prism(shape.difference(inner),-.10,-.012,'dark timber',label+'/frame-depth')
    x0,z0,x1,z1=inner.bounds
    f.prism(shape.buffer(.022,join_style=2).difference(shape),-.01,.018,
            'dark timber',label+'/outer-reveal-bead')
    for j in range(1,cols):
        x=x0+(x1-x0)*j/cols
        f.prism(inner.intersection(box(x-.016,z0,x+.016,z1)),-.09,-.025,
                'dark timber',label+'/structural-mullion')
    # Present-day photos support narrow light metal glazing bars within
    # dark major frames. These are actual strips with recessed glass behind.
    subcols=cols*(2 if x1-x0>.65 else 1)
    subrows=max(rows,4) if z1-z0>.5 else max(rows,2)
    if mode=='lod':subcols=cols;subrows=min(3,subrows)
    for j in range(1,subcols):
        x=x0+(x1-x0)*j/subcols
        if j%(subcols//cols)==0:continue
        f.prism(inner.intersection(box(x-.004,z0,x+.004,z1)),-.085,-.065,
                'window lead',label+'/fine-glazing-bar-vertical')
    for j in range(1,subrows):
        z=z0+(z1-z0)*j/subrows
        f.prism(inner.intersection(box(x0,z-.004,x1,z+.004)),-.085,-.065,
                'window lead',label+'/fine-glazing-bar-horizontal')
    f.box((x0+x1)/2,z0-.045,x1-x0+.15,.065,.20,.020,'dark timber',label+'/projecting-sill')
    if mode!='lod':
        for j in range(cols):
            x=x0+(x1-x0)*(j+.83)/cols
            f.box(x,(z0+z1)/2,.012,.065,.018,-.025,'dark metal',label+'/casement-handle')


def curve_beam(b,face,points,width,label):
    """Solid rectangular swept timber, preserving its actual curved outline."""
    q=np.asarray(points,float);verts=[]
    for i,p in enumerate(q):
        tangent=q[min(i+1,len(q)-1),:2]-q[max(i-1,0),:2]
        tangent/=np.linalg.norm(tangent)
        side=np.array([-tangent[1],tangent[0]])*width/2
        for sign,depth in [(-1,-.005),(1,-.005),(1,.060),(-1,.060)]:
            uv=p[:2]+side*sign
            verts.append(face.point(uv[0],uv[1],depth))
    faces=[(3,2,1,0),(4*(len(q)-1),4*(len(q)-1)+1,4*(len(q)-1)+2,4*(len(q)-1)+3)]
    for i in range(len(q)-1):
        for j in range(4):faces.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
    b.add(verts,faces,'dark timber',label)


def enrich(b,data,parts,mode='full'):
    h=data['heights_in_door_units']
    # Replace abbreviated spatial chimney blocks with rebuilt exterior form.
    b.parts=[p for p in b.parts if not p['label'].startswith('main-chimney/')
             and p['label']!='north-service/provisional-repaired-chimney']
    def chimney(cx,cy,basebottom,basetop,top,width,label):
        # White base with low stepped shoulders, then red ribbed shaft.
        b.box((cx,cy,(basebottom+basetop)/2),(width*.91,width*.98,basetop-basebottom),
              'white plaster',label=label+'/white-plastered-base')
        shaftbottom=basetop-.08
        b.box((cx,cy,(shaftbottom+top)/2),(width,width,top-shaftbottom),
              'brick mortar',label=label+'/recessed-mortar-core')
        if mode=='lod':
            b.box((cx,cy,(shaftbottom+top)/2),(width+.002,width+.002,top-shaftbottom),
                  'red brick silhouette',label=label+'/shaft')
        else:
            rowh=.035;brickw=.12
            rows=max(1,round((top-shaftbottom)/rowh));rowh=(top-shaftbottom)/rows
            faces=[Facade(b,(cx-width/2,cy-width/2),(cx+width/2,cy-width/2),label+'/south'),
                   Facade(b,(cx+width/2,cy-width/2),(cx+width/2,cy+width/2),label+'/east'),
                   Facade(b,(cx+width/2,cy+width/2),(cx-width/2,cy+width/2),label+'/north'),
                   Facade(b,(cx-width/2,cy+width/2),(cx-width/2,cy-width/2),label+'/west')]
            for face in faces:
                for row in range(rows):
                    u=-width/2-brickw*.5*(row%2)
                    while u<width/2-1e-7:
                        left=max(u,-width/2)+.0015;right=min(u+brickw,width/2)-.0015
                        if right-left>.005:
                            face.box((left+right)/2,shaftbottom+(row+.5)*rowh,right-left,rowh-.003,
                                     .009,.004,'red brick silhouette','individual-brick-relief')
                        u+=brickw
        # Narrow vertical ribs make the source chimney's fluting readable.
        if label=='main-chimney-west':
            for d in (-width*.40,width*.40):
                b.box((cx+d,cy-width/2-.018,(shaftbottom+top)/2),
                      (.046,.042,top-shaftbottom-.04),'red brick silhouette',label=label+'/observed-south-rib')
                b.box((cx-width/2-.018,cy+d,(shaftbottom+top)/2),
                      (.042,.046,top-shaftbottom-.04),'red brick silhouette',label=label+'/observed-west-rib')
        # Flared brick shoulder/corbel under shaft; profile sampled, not box.
        levels=[(basetop-.20,width*1.28),(basetop-.14,width*1.19),
                (basetop-.075,width*1.10),(basetop,width)]
        for (z0,w0),(z1,w1) in zip(levels,levels[1:]):
            vs=[(cx+sx*w/2,cy+sy*w/2,z) for z,w in [(z0,w0),(z1,w1)]
                for sx,sy in [(-1,-1),(1,-1),(1,1),(-1,1)]]
            b.add(vs,[(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],
                  'red brick silhouette',label+'/flared-brick-shoulder')
        for z,w,hh in [(top+.015,width*1.07,.04),(top+.06,width*1.18,.045),
                       (top+.10,width*1.12,.035)]:
            b.box((cx,cy,z),(w,w,hh),'red brick silhouette',label=label+'/crown-course')
        # Dark shallow top cavity is not a fabricated metal chimney pot.
        b.box((cx,cy,top+.12),(width*.58,width*.58,.006),'dark metal',label=label+'/flue-shadow')
    for x in (-4.05,4.05):chimney(x,.20,2.10,4.30,6.00,.48,'main-chimney-'+('west' if x<0 else 'east'))
    # Separate triangular brick cap lower on the western white chimney wall.
    f=Facade(b,(-4.05-.24,.20-.25),(-4.05+.24,.20-.25),'west-chimney-low-triangle')
    f.prism(Polygon([(-.18,2.65),(.18,2.65),(0,3.15)]),0,.045,'red brick silhouette','observed-triangular-cap')
    sr=parts['north_service']
    chimney((sr[0]+sr[1])/2,sr[3]-.55,2.80,3.28,4.12,.35,'north-service/reconstructed-chimney-estimated')

    # The photographed entrance side has a shallow continuous upper-storey
    # projection, with visible stone corbels, rather than flush window decals.
    core=parts['main_core'];xa,xb,ya,yb=core
    b.parts=[p for p in b.parts if not p['label'].startswith('main-core/north/')]
    nf=Facade(b,(xb,yb),(xa,yb),'north-current/ground')
    lower=opening(-2.4,.35,1.15,.91)
    nf.wall(.07,1.42,[lower],.12,'white plaster')
    detail_window(b,nf,lower,'observed-brick-bordered-window',2,4,mode)
    for side in (-1,1):
        for row in range(12):
            nf.box(-2.4+side*(.575+.040+(.020 if row%2 else 0)),.36+row*.077,
                   .105 if row%2 else .065,.067,.035,.018,'red brick silhouette','brick-toothed-reveal')
    nf.box(-2.4,1.29,1.35,.08,.04,.02,'red brick silhouette','brick-header')
    uf=Facade(b,(xb,yb+.08),(xa,yb+.08),'north-current/projecting-upper')
    windows=[(opening(-2.4,1.97,1.45,.86),3,'left-three-casements'),
             (opening(.02,1.65,.66,.86),2,'partly-observed-middle-window'),
             (opening(2.0,1.97,.90,.86),2,'right-two-casements')]
    # Tops remain beneath the actual2.72 eave; source apparent tall windows
    # are bounded within the estimated wall rhythm, not metrically calibrated.
    windows=[(shape.intersection(box(-4,1.43,4,2.64)),cols,label) for shape,cols,label in windows]
    uf.wall(1.42,h['main_eave'],[x[0] for x in windows],.12,'white plaster')
    for shape,cols,label in windows:detail_window(b,uf,shape,label,cols,4,mode)
    # Commons entrance photo: three narrow white panels below the left
    # three-casement window, bounded by existing outer posts and two stiles.
    b.parts=[p for p in b.parts if p['label']!='north-current/projecting-upper/left-three-casements/projecting-sill']
    uf.box(-2.4,1.925,1.70,.085,.20,.020,'dark timber','observed-left-spandrel-continuous-rail')
    for u in (-3.25+1.70/3,-3.25+2*1.70/3):
        uf.box(u,1.675,.065,.46,.07,.035,'dark timber','observed-left-spandrel-internal-stile')
    # The left casement of the right-hand photographed window opens outward.
    # Remove its coplanar glass portion before adding the angled leaf.
    label='north-current/projecting-upper/right-two-casements/recessed-glass'
    b.parts=[p for p in b.parts if p['label']!=label]
    uf.prism(box(2.018,2.003,2.417,2.607),-.115,-.108,'window glass','right-casement-fixed-glass')
    hinge=uf.point(1.583,0,-.06);direction=uf.t*math.cos(.50)+uf.n*math.sin(.50)
    tip=hinge+direction*.40
    leaf=Facade(b,hinge[:2],tip[:2],'north-current/outward-open-casement')
    detail_window(b,leaf,opening(0,1.97,.40,.67),'visible-left-leaf',1,4,mode)
    for z in (1.42,h['main_eave']-.045):uf.beam(z,.09,.04,'dark timber',label='continuous-jetty-tie')
    for u in (-3.9,-3.25,-1.55,-.65,.75,1.45,2.6,3.7):
        uf.box(u,2.06,.065,1.28,.07,.035,'dark timber','observed-post-rhythm')
    for u in (-3.3,-1.55,-.65,1.0,3.5):
        nf.box(u,1.32,.13,.16,.19,.07,'spatial ground base','light-stone-jetty-corbel')
        nf.box(u,1.23,.10,.06,.13,.04,'spatial ground base','corbel-step')
    for u0,u1 in [(-3.8,-3.2),(-1.45,-.7)]:
        uf.line((u0,1.47,.04),(u1,2.62,.04),.037,'dark timber',4,'straight-brace')
    curve_beam(b,uf,[(2.65-.48*t,1.50+.43*(2*t-t*t),.04) for t in np.linspace(0,1,13)],
               .075,'north-current/observed-right-window-curved-brace')

    # Curved braces are placed only in photographed main gable/upper-bay
    # zones; the porch infill remains the observed straight-post pattern.
    for key in ('south_west_projected_bay','south_east_projected_bay'):
        xa,xb,ya,yb=parts[key];width=xb-xa
        f=Facade(b,(xa,ya),(xb,ya),key+'/detailed-timber')
        for sign in (-1,1):
            pts=[]
            for t in np.linspace(0,1,13 if mode!='lod' else 5):
                start=width/2-.12
                end=data['bay_attic_window_widths_in_door_units'][key]/2+.02
                u=sign*(start-(start-end)*(2*t-t*t))
                z=h['main_eave']+.83*t
                pts.append((u,z,.04))
            curve_beam(b,f,pts,.085,key+'/photographed-curved-brace-'+str(sign))
        for u in (-width/2+.07,width/2-.07):
            f.box(u,1.42,.13,.12,.14,.07,'dark timber','jetty-bearing-block')
            f.box(u,1.35,.09,.06,.10,.06,'dark timber','jetty-bearing-step')
            if mode!='lod':
                for z in (1.42,2.67):
                    f.line((u-.02,z,.13),(u-.02,z,.145),.012,'dark timber',8,'visible-timber-peg')
        # Bay side return glazing is visible in the restored western closeup.
        # Keep east return opaque where source visibility is insufficient.
        if key=='south_west_projected_bay':
            for x,rev in [(xa,True),(xb,False)]:
                ff=Facade(b,(x,yb),(x,ya),key+'/return-west') if rev else Facade(b,(x,ya),(x,yb),key+'/return-east')
                shape=opening(0,1.62,max(.12,yb-ya-.16),.83)
                # Remove the small solid return and substitute a real opening.
                b.parts=[p for p in b.parts if not(p['label']==key+'/bay-return' and
                         abs(np.mean(np.asarray(p['vertices'])[:,0])-x)<.02)]
                ff.wall(.07,h['main_eave'],[shape],.09,'white plaster')
                detail_window(b,ff,shape,'narrow-return-glazing',1,4,mode)

    # Door leaf boards and moulded arch trim use actual recess geometry.
    core=parts['main_core'];f=Facade(b,(core[0],core[2]),(core[1],core[2]),'south-entrance-detail')
    door=opening(0,.07,.62,1.0,arch=.24,segments=24)
    for i in range(1,8):
        u=-.31+i*.62/8
        f.prism(door.intersection(box(u-.002,.07,u+.002,1.07)),-.105,-.100,'dark timber','board-joint')
    f.box(.19,.52,.025,.085,.025,-.075,'dark metal','door-handle')
    f.prism(door.buffer(.085).difference(door.buffer(.04)).intersection(box(-1,.02,1,2)),
            -.035,.02,'spatial ground base','arch-moulding-outer')
    for i in range(2):f.box(0,.04-i*.018,.83+i*.20,.04,.25+i*.18,.11+i*.06,'spatial ground base','threshold-step')

    # North porch has straight vertical/diagonal-free infill, shallow scallop
    # in its tie underside and recessed door panels, as visible in Commons.
    xa,xb,ya,yb=parts['current_north_entry_porch']
    f=Facade(b,(xb,yb),(xa,yb),'north-porch-detail');width=xb-xa
    # Retain the filled upper gable but open its covered external threshold.
    # Opaque side returns avoid pretending dark, unobserved areas are windows.
    b.parts=[p for p in b.parts if not p['label'].startswith('current-north-entry-porch/front/')]
    upper=Polygon([(-width/2,1.4),(width/2,1.4),(0,2.4)])
    f.prism(upper,-.10,0,'white plaster','upper-gable-white-infill')
    for u in (-width/2+.045,width/2-.045):
        f.box(u,.75,.11,1.40,.14,.025,'dark timber','front-porch-post')
    f.beam(1.4,.10,.05,'dark timber',label='front-porch-tie')
    f.line((-width/2,1.4,.04),(0,2.4,.04),.047,'dark timber',4,'porch-verge-left')
    f.line((0,2.4,.04),(width/2,1.4,.04),.047,'dark timber',4,'porch-verge-right')
    f.line((0,1.4,.04),(0,2.4,.04),.035,'dark timber',4,'porch-king-post')
    f.box(0,1.90,width*.5,.075,.075,.04,'dark timber','observed-porch-middle-crossbeam')
    rear_y=yb-.58
    back=Facade(b,(xb,rear_y),(xa,rear_y),'north-porch/recessed-entry-wall')
    entry=opening(0,.08,.72,1.12,arch=.12,segments=20)
    back.wall(.07,1.4,[entry],.10,'white plaster')
    back.prism(entry,-.08,-.04,'door wood','recessed-door-leaf')
    back.prism(entry.buffer(.04).difference(entry),-.02,.035,'dark timber','door-surround')
    for xx in (xa,xb):
        b.box((xx,(yb+rear_y)/2,.74),(.09,yb-rear_y,1.34),
              'dark timber',label='north-porch/opaque-side-return')
    b.box(((xa+xb)/2,(yb+rear_y)/2,.055),(width,yb-rear_y,.04),
          'spatial ground base',label='north-porch/external-recess-floor')
    for u in (-width*.25,width*.25):
        top=2.4-abs(u)/(width/2)
        f.box(u,(1.4+top)/2,.055,top-1.4,.07,.04,'dark timber','straight-upper-post')
    for u in np.linspace(-width*.44,width*.44,9):
        f.box(float(u),1.355+.012*math.cos(float(u)*8),width*.10,.045,.09,.035,'dark timber','shallow-tie-underside')
    for z in (.38,.77):
        back.box(0,z,.52,.24,.025,-.015,'door wood','recessed-door-panel')
    back.box(.23,.59,.022,.10,.023,.025,'dark metal','entry-door-handle')
    back.box(0,.98,.16,.19,.018,.005,'window glass','observed-small-door-light')
    for u in (-.083,0,.083):back.box(u,.98,.009,.20,.022,.018,'dark metal','door-light-frame')
    for i in range(2):f.box(0,.04-i*.014,1.0+i*.18,.05,.30+i*.20,.13+i*.06,'spatial ground base','north-threshold-step')
    # Central exterior lantern is visible on the porch timber, not an
    # inferred light on every wall. It is opaque glass for exterior display.
    f.box(0,1.58,.09,.16,.085,.11,'window glass','porch-lantern-glass')
    for u in (-.049,.049):f.box(u,1.58,.012,.19,.10,.11,'dark metal','porch-lantern-frame')
    for z in (1.48,1.68):f.box(0,z,.13,.025,.12,.11,'dark metal','porch-lantern-cap')

    # Two source-visible west roof hoods and the restored north roof dormer
    # have independently estimated positions and differentiated light groups.
    panel=roof_builder(b,data,parts,mode)
    def west_hood(x,y,z,width,depth,height,label,columns,rows):
        face=Facade(b,(x,y+width/2),(x,y-width/2),label+'/front')
        win=opening(0,z,width-.13,height-.12)
        face.wall(z-.06,z+height,[win],.06,'white plaster')
        detail_window(b,face,win,'roof-hood-glazing',columns,rows,mode)
        for yy in (y-width/2,y+width/2):
            b.box((x+depth/2,yy,z+height/2),(depth,.045,height+.1),'white plaster',label=label+'/side-cheek')
        panel([(x-.06,y-width/2-.05,z+height+.035),(x+depth,y-width/2-.05,z+height+.12),
               (x+depth,y+width/2+.05,z+height+.12),(x-.06,y+width/2+.05,z+height+.035)],label+'/hood-roof')
    west_hood(-3.30,-2.20,3.45,.67,.34,.48,'west-upper-roof-hood-estimated',2,4)
    west_hood(-4.90,-1.35,1.69,.58,.28,.29,'west-low-roof-hood-estimated',2,1)
    x=-2.0;y=1.67;z=3.72;w=1.04
    face=Facade(b,(x+w/2,y),(x-w/2,y),'north-current-roof-dormer/front')
    win=opening(0,z-.19,w-.14,.48)
    face.wall(z-.29,z+.37,[win],.07,'white plaster')
    detail_window(b,face,win,'two-light-dormer',2,3,mode)
    for xx in (x-w/2,x+w/2):
        b.box((xx,y-.28,z+.04),(.055,.56,.66),'white plaster',label='north-dormer/white-cheek')
    panel([(x-w/2-.07,y+.07,z+.39),(x+w/2+.07,y+.07,z+.39),
           (x+w/2+.07,y-.60,z+.46),(x-w/2-.07,y-.60,z+.46)],'north-dormer/low-top')

    # Roof drainage is an exterior construction detail, at photographed
    # main eaves. No speculative pipe network on hidden service elevations.
    for y in (core[2]-.085,core[3]+.085):
        b.tube([(core[0]-.05,y,h['main_eave']-.025),(core[1]+.05,y,h['main_eave']-.025)],
               .026,'dark metal',8,'main-eave/gutter')
    for x,y in [(core[0]-.02,core[3]+.07),(core[1]+.02,core[2]-.06)]:
        b.tube([(x,y,h['main_eave']-.06),(x,y,.15)],.019,'dark metal',8,'main/downpipe')

    # Clear lower west-wing glazing in the official photo is a real opening,
    # distinct from its two roof hoods. Foliage-obscured east wing stays closed.
    xa,xb,ya,yb=parts['west_low_wing']
    b.parts=[p for p in b.parts if p['label']!='west_low_wing/west/continuous-open-wall']
    west=Facade(b,(xa,yb),(xa,ya),'west-low-wing/observed-ground-glazing')
    opening_shape=opening(.45,.20,1.55,.81)
    west.wall(.07,h['low_wing_eave'],[opening_shape],.12,'white plaster')
    detail_window(b,west,opening_shape,'wide-three-light-window',3,4,mode)
    for u in (-2.1,-.37,1.27,2.1):
        west.box(u,.66,.065,1.18,.065,.035,'dark timber','lower-wall-post')
    west.beam(1.18,.075,.025,'dark timber',label='lower-eave-tie')

    # Three separate solid bird ornaments; double-sided thickness prevents
    # them disappearing from the reverse camera side like spatial markers.
    b.parts=[p for p in b.parts if not p['label'].startswith('three-birds/')]
    gx=-2.50;gy=-2.72;gz=4.85
    b.tube([(gx,gy,4.58),(gx,gy,gz+.39)],.012,'dark metal',8,'three-birds/slender-support')
    outline=Polygon([(-.14,.01),(-.03,.025),(.10,.17),(.14,.15),(.07,-.015),
                     (.025,-.035),(-.015,-.02),(-.11,-.045)])
    for i,(dx,dz) in enumerate([(-.17,.12),(.13,.34),(.15,-.04)]):
        b.prism(outline,-.012,.012,lambda u,z,d:(gx+dx+u,gy-d,gz+dz+z),
                'dark metal','three-birds/solid-wing-body-'+str(i))


def apply_atlas(b,root):
    names=['white plaster','dark timber','slate-like plain roof','red brick silhouette',
           'window glass','spatial ground base','door wood','dark metal']
    aliases={'unverified service plaster':'white plaster','window lead':'white plaster',
             'brick mortar':'spatial ground base'}
    for name in list(b.palette):
        tile_name=aliases.get(name,name)
        if tile_name not in names:continue
        b.palette[name].update(color=[1.,1.,1.],roughness=1.,metallic=1.,
           texture=str(root/'textures/hudec-original-basecolor.png'),
           normal_texture=str(root/'textures/hudec-original-normal.png'),
           orm_texture=str(root/'textures/hudec-original-orm.png'),normal_scale=.35,
           extras={'atlas_tile':names.index(tile_name),'texture_origin':'original deterministic procedural material; no photograph pixels'})
    for part in b.parts:
        name=aliases.get(part['material'],part['material']);idx=names.index(name)
        verts=np.asarray(part['vertices'],float);lo=verts.min(0);span=np.maximum(verts.max(0)-lo,1e-7)
        newv=[];newuv=[];newtri=[]
        for tri in part['triangles']:
            xyz=verts[list(tri)];n=np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]);axis=int(np.argmax(abs(n)))
            axes=[a for a in range(3) if a!=axis]
            # Local planar projection for each face preserves nondegenerate
            # UVs on top, side and return surfaces of every solid detail.
            uv=(xyz[:,axes]-lo[axes])/span[axes]
            # Leave 9 pixels from cell edge; gutter itself is8pixels.
            pixel=9+uv*110
            pixel[:,0]+=(idx%4)*128;pixel[:,1]+=(idx//4)*128
            uv=pixel/np.array([512,256])
            first=len(newv);newv.extend(xyz.tolist());newuv.extend(uv.tolist());newtri.append((first,first+1,first+2))
        part.update(vertices=newv,triangles=newtri,texcoords=newuv)
