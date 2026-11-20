"""Three photographed elevations of the 501 Yongjia Road residence. X west, Y south."""
import math
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening

EAST = -7.12  # The eastern end of the 16.83 m source row is outside the photograph's coverage.
WEST = 8.31
DEPTH = 8.34
EAVE = 7.35
MATERIALS = {
    'pebble render': (.698,.669,.595), 'red fired brick': (.51,.235,.17),
    'dark red brick': (.426,.172,.123), 'light mortar': (.695,.594,.493),
    'weathered stone': (.493,.474,.439), 'ochre limestone': (.698,.651,.566),
    'dark timber': (.236,.174,.144), 'old steel sash': (.202,.234,.203),
    'window glass': (.202,.276,.264), 'red clay tile': (.528,.272,.194),
    'shadowed clay tile': (.434,.213,.16), 'painted zinc': (.416,.442,.435),
    'oxide green': (.197,.291,.212), 'neutral section': (.592,.571,.514)
}
PALETTE = {k: dict(color=list(v),roughness=.39 if k=='window glass' else .8)
           for k,v in MATERIALS.items()}


def brick_rim(f, hole, lod, arch=0):
    x0,z0,x1,z1=hole.bounds
    surround=hole.buffer(.152,join_style='mitre').difference(hole)
    f.prism(surround,-.009,.038,'red fired brick','window arch and jambs')
    if not lod:
        for side in (x0,x1):
            for n in range(1,int((z1-z0-arch)/.137)+1):
                z=z0+.137*n
                f.box(side+(-.073 if side==x0 else .073),z,.146,.009,.025,.045,
                      'light mortar','brick bed joints')
        if arch:
            arcseg=14
            spring=z1-arch;mid=(x0+x1)*.5
            for k in range(1,arcseg):
                theta=k*math.pi/arcseg
                dx,dy=math.cos(theta),math.sin(theta)
                u,z=mid+(x1-x0)*.5*dx,spring+arch*dy
                joint=LineString([(u+.018*dx,z+.018*dy),(u+.143*dx,z+.143*dy)]).buffer(.005)
                f.prism(joint,.037,.044,'light mortar','radial arch joints')
    f.box((x0+x1)/2,z0-.044,x1-x0+.13,.073,.105,.017,'ochre limestone','window sill')


def sash(f, poly, cols, rows, lod, arch=0):
    brick_rim(f,poly,lod,arch)
    f.window(poly,cols,rows,frame='old steel sash',trim=False,glass='window glass',label='recessed steel window')


def diamond(f,u,z,w,h):
    poly=Polygon([(u,z+h/2),(u+w/2,z),(u,z-h/2),(u-w/2,z)])
    for factor,thick in [(1,.081),(.56,.060)]:
        from shapely.affinity import scale
        q=scale(poly,xfact=factor,yfact=factor,origin=(u,z))
        f.prism(q.difference(q.buffer(-thick,join_style='mitre')),.015,.048,
                'red fired brick','inlaid brick diamond')


def wall_face(f, ground, upper, motifs, lod):
    all_openings=[]
    for z,group in [(.99,ground),(4.62,upper)]:
        for u,w,h,arch in group:
            all_openings.append((opening(u,z,w,h,arch,24 if not lod else 16),arch,w))
    f.wall(0,EAVE,[q for q,_,_ in all_openings],.34,'pebble render')
    base=box(-f.length/2,0,f.length/2,.79)
    f.prism(base,.004,.035,'weathered stone','granite basement and plinth')
    for q,arch,w in all_openings:sash(f,q,3 if w>1.5 else 2,3,lod,arch)
    for u,z,w,h in motifs:diamond(f,u,z,w,h)
    for sign in (-1,1):
        edge=sign*(f.length/2-.12)
        f.box(edge,4.01,.24,6.63,.06,.024,'red fired brick','brick corner strips')
        for n in range(7,47,2):
            f.box(edge-sign*.08,n*.151,.34,.145,.057,.034,'red fired brick','stepped brick quoins')
    f.box(0,EAVE-.06,f.length+.13,.14,.31,.074,'dark timber','timber fascia')
    n=math.floor(f.length/.69)
    for k in range(n):
        u=(k-(n-1)/2)*.69
        a=f.point(u,7.22,.12);b=f.point(u,6.74,.034)
        f.builder.tube([a,b],.047,'ochre limestone',5,'eaves/carved bracket')
        f.box(u,7.20,.085,.085,.28,.123,'ochre limestone','bracket cap')


def wings(builder,lod):
    north=Facade(builder,(EAST,0),(WEST,0),'north street elevation')
    # The eastern projection, central group and west tower are distinguishable above the garden wall.
    upper=[(-5.72,1.12,1.6,0),(-3.00,1.31,1.55,0),(-.77,1.5,1.52,0),(1.51,1.68,1.51,0),(3.63,.71,1.30,0)]
    north_ground=[(-4.98,.89,1.76,.32),(-2.62,1.24,1.83,.39),(-.60,1.43,1.72,.32),(1.70,1.42,1.72,.33)]
    wall_face(north,north_ground,upper,[(-5.72,3.60,1.18,1.42)],lod)
    # The long clay-tile awning is visible immediately above the street wall in the 2014 photograph.
    canopy=Facade(builder,(0,-.88),(0,.14),'street side tiled canopy')
    canopy.prism(Polygon([(-.51,3.50),(.51,3.84),(.51,3.91),(-.51,3.57)]),
                 -4.09,4.76,'shadowed clay tile','canopy over north ground openings')
    for j in range(1,6):
        y=-.51+j*.164;z=3.58+j*.054
        canopy.prism(Polygon([(y-.02,z),(y+.02,z+.014),(y+.02,z+.032),(y-.02,z+.02)]),
                     -4.1,4.77,'red clay tile','canopy tile courses')
    for x in [-3.81,-.65,2.31,4.56]:
        builder.tube([(x,-.055,2.91),(x,-.79,3.51)],.033,'dark timber',6,'canopy/diagonal timber bracket')
    # A lower hipped cap and paired brick corner accents distinguish the projecting east bay.
    builder.add([(-7.15,-.26,7.32),(-3.79,-.26,7.32),(-3.79,1.91,7.32),(-7.15,1.91,7.32),
                 (-6.69,1.61,8.34),(-4.35,1.61,8.34)],
                [(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4),(3,2,1,0)],'red clay tile','north east bay/hipped lower eave')
    south=Facade(builder,(WEST,DEPTH),(EAST,DEPTH),'south garden elevation')
    # Upper rectangular casements and broad arched garden openings are recorded in the Tianping archive.
    wall_face(south,[(-4.28,1.22,2.36,.5),(-1.76,1.85,2.42,.54),(1.57,1.88,2.39,.54),(4.50,1.40,2.29,.50)],
              [(-4.40,.91,1.64,0),(-2.50,1.03,1.62,0),(-.78,1.06,1.68,0),
               (1.95,1.34,1.61,0),(3.47,1.35,1.61,0),(5.20,.92,1.55,0)],
              [(-.78,3.97,.70,.86),(4.63,3.93,.61,.86)],lod)
    west_face=Facade(builder,(WEST,0),(WEST,DEPTH),'west gable and annex')
    # The SWF west view shows a particularly narrow vertical upper sash above the square annexe.
    sideholes=[opening(-.55,4.55,1.04,1.74),opening(1.61,4.54,.96,1.71)]
    outline=Polygon([(-DEPTH/2,0),(DEPTH/2,0),(DEPTH/2,7.36),(2.45,8.27),(0,10.42),
                     (-2.45,8.27),(-DEPTH/2,7.36)])
    west_face.wall(0,10.5,sideholes,.30,'pebble render',outline=outline)
    for q in sideholes:sash(west_face,q,2,3,lod)
    for j in (-1,1):
        west_face.box(j*3.97,4.0,.24,6.9,.061,.025,'red fired brick','corner bricks')
    annex=Facade(builder,(WEST+1.37,2.69),(WEST+1.37,6.34),'west annexe')
    win=[opening(-.74,2.04,.52,1.21),opening(.53,2.04,.52,1.21),opening(0,.10,.82,1.16)]
    annex.wall(0,4.31,win,.23,'pebble render')
    for q in win[:2]:sash(annex,q,1,2,lod)
    annex.prism(win[2],-.16,-.14,'old steel sash','lower annexe hatch')
    for y in [2.69,6.34]:
        facade=Facade(builder,(WEST,y),(WEST+1.37,y),'west annexe return')
        facade.wall(0,4.30,material='pebble render')
    builder.box((WEST+.63,4.515,4.37),(1.55,3.83,.14),'weathered stone',label='west annexe/flat cap')
    # The eastern limit is a measured section. The remaining end continues as the original city building.
    cut=Facade(builder,(EAST,DEPTH),(EAST,0),'east neutral section')
    cut.prism(outline,-.015,.015,'neutral section','cut plane')


def roof_profile():
    return [(-.22,7.43),(1.47,8.16),(DEPTH/2,10.47),(DEPTH-1.47,8.16),(DEPTH+.22,7.43)]


def roof(builder,lod):
    side=Facade(builder,(0,0),(0,DEPTH),'double-pitched roof')
    top=roof_profile()
    for i,((y0,z0),(y1,z1)) in enumerate(zip(top,top[1:])):
        slab=Polygon([(y0-DEPTH/2,z0-.13),(y1-DEPTH/2,z1-.13),(y1-DEPTH/2,z1),(y0-DEPTH/2,z0)])
        side.prism(slab,EAST-.008,WEST+.17,'red clay tile','main roof slopes')
        if not lod:
            count=max(3,int((y1-y0)/.22))
            for j in range(1,count):
                t=j/count;y=y0+(y1-y0)*t-DEPTH/2;z=z0+(z1-z0)*t
                lip=Polygon([(y-.018,z-.001),(y+.021,z+.013),(y+.021,z+.026),(y-.018,z+.011)])
                side.prism(lip,EAST,WEST+.168,'shadowed clay tile','horizontal tile laps')
    builder.box(((EAST+WEST)/2,DEPTH/2,10.48),(WEST-EAST+.2,.13,.095),'red clay tile',label='roof/ridge')
    for north in [True,False]:
        for x in [-3.3,-.72,1.95]:
            y=.81 if north else DEPTH-.81;sgn=1 if north else -1
            fr=Facade(builder,(x-sgn*.85,y),(x+sgn*.85,y),'dormer/'+('north' if north else 'garden'))
            hole=opening(0,7.94,1.02,1.05)
            fr.prism(box(-.77,7.64,.77,9.16).difference(hole),-.18,0,'pebble render','window cheek')
            fr.window(hole,2,2,frame='old steel sash',trim=False,glass='window glass',label='dormer sash')
            for a in [-.77,.77]:
                face=Facade(builder,(x+a,y),(x+a,y+sgn*1.48),'dormer/side cheek')
                cheek=Polygon([(-.74,7.69),(.74,8.73),(.74,9.28),(-.74,9.11)])
                face.prism(cheek,-.037,.037,'red fired brick','side cheek')
            sh=Facade(builder,(x,y),(x,y+sgn*1.62),'dormer/roof')
            slab=Polygon([(-.98,9.07),(.86,9.29),(.86,9.39),(-.98,9.17)])
            sh.prism(slab,-.94,.94,'red clay tile','clay tile hood')
            fr.box(0,9.111,1.89,.101,.18,.10,'dark timber','hood fascia')


def tower(builder,lod):
    cx,cy=6.98,.22
    radius=1.48
    n=42 if lod else 84
    length=2*math.pi*radius
    # Brick-framed slit windows pierce a continuous sweep of the photographed cylindrical staircase.
    angle=-.39
    # One very tall round-headed slit is visible on the western meridian in the 2014 photograph.
    # The uninterrupted pale render on the street-facing quadrant is also documentary evidence.
    holes=[opening(angle*radius,4.88,.60,3.94,.29)]
    hole=holes[0]
    outer=box(-length/2,0,length/2,9.03).difference(unary_union(holes))
    def wrap(u,z,d):
        t=u/radius
        return [cx+(radius+d)*math.cos(t),cy+(radius+d)*math.sin(t),z]
    band=box(-length/2,7.97,length/2,9.16).difference(hole)
    surfaces=[(outer,-.19,0,'pebble render','round staircase wall'),
              (band,.001,.016,'red fired brick','brick frieze with opening')]
    for poly in holes:
        surfaces.extend([(poly.buffer(.086).difference(poly),.017,.032,'red fired brick','slit brick architrave'),
                         (poly,-.13,-.11,'window glass','recessed slit glass')])
    for z in [5.79,6.67,7.54,8.36]:
        surfaces.append((box(angle*radius-.294,z-.018,angle*radius+.294,z+.018),
                         -.105,-.081,'old steel sash','staircase glazing bars'))
    du,dz=.32,.49
    coat=Polygon([(angle*radius,4.51),(angle*radius+du,4.51-dz),(angle*radius,4.51-2*dz),
                  (angle*radius-du,4.51-dz)])
    surfaces.append((coat.difference(coat.buffer(-.075,join_style='mitre')),.008,.029,
                      'red fired brick','brick diamond under tower window'))
    if not lod:
        # Fine masonry joints follow the conical tower's curved exterior rather than a flat texture.
        for j in range(1,12):
            z=7.97+j*.099
            joint=box(-length/2,z-.006,length/2,z+.006).difference(hole.buffer(.09))
            surfaces.append((joint,.016,.020,'dark red brick','tower brick beds'))
    for geom,d0,d1,mat,name in surfaces:
        for j in range(n):
            u0=length*(j/n-.5);u1=length*((j+1)/n-.5)
            part=geom.intersection(box(u0,-.1,u1,9.12))
            if not part.is_empty:builder.prism(part,d0,d1,wrap,mat,'northwest tower/'+name)
    builder.lathe((cx,cy),[(.04,radius+.035),(.72,radius+.035)],'weathered stone',n,'tower/granite base')
    for j in range(32):
        u=length*((j+.5)/32-.5);w=length/32
        poly=Polygon([(u-w*.48,7.99),(u,7.74),(u+w*.48,7.99)]).difference(hole)
        builder.prism(poly,.005,.023,wrap,'red fired brick','tower/hanging brick scallops')
    profile=[(9.10,1.78),(9.18,1.81),(9.42,1.68),(10.10,1.43),(11.37,.93),(12.84,.31),(13.61,.03)]
    builder.lathe((cx,cy),profile,'painted zinc',n,'tower/flared metal cone')
    for i in range(14 if lod else 28):
        a=i*math.tau/(14 if lod else 28)
        builder.tube([(cx+(r+.008)*math.cos(a),cy+(r+.008)*math.sin(a),z)for z,r in profile],
                     .014 if lod else .012,'painted zinc',5,'tower/standing metal seams')
    builder.lathe((cx,cy),[(13.55,.049),(13.74,.032),(13.83,.012)],'painted zinc',12,'tower/finial')


def villa(builder,lod):
    wings(builder,lod)
    roof(builder,lod)
    tower(builder,lod)
