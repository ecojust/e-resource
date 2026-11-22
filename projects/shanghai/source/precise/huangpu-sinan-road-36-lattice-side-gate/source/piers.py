"""Mortared plinth, two stepped piers and the incised vertical decoration."""
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union
from photo_architecture import Facade
from photo_plane import position
from material_names import MATERIAL

LIGHT='Pale yellow mouldings'
SHADOW='Inset groove shadow'
TILE='Charcoal dado'
BASE='Grey boundary plinth'
JOINT='Recessed mortar'
CAP='Fluted cap faces'
FACE_Y=-.18

# Image positions on the 793 x 941 detail. The bottom of the right pier leaves
# the photograph. Its plinth section ends at the same nominal level as the left.
PIERS=[
 {'name':'Left','shaft':[(27,412),(102,394),(98,744),(15,730)],
  'dado':[(15,730),(98,744),(98,892),(12,865)],
  'courses':[
  [(29,412),(102,395),(101,359),(38,370)],
  [(38,370),(101,359),(100,322),(52,333)],
  [(52,333),(100,323),(99,312),(66,321)],
  [(78,319),(102,314),(102,292),(82,296)]],
  'cap':[(65,264),(108,253),(108,287),(66,298)],
  'relief':[(35,392),(42,392),(42,379),(49,378),(49,393),(67,390),(67,371),(72,370),(72,389),(73,399),(47,406),(47,395),(37,399)],
  'flutes':[((58,494),(53,723)),((71,474),(66,728)),((82,492),(79,731))],
  'outer':[(26,413),(35,409),(31,718),(22,718)],
  'blocks':[(30,398,5),(39,378,5),(88,377,5)]},
 {'name':'Right','shaft':[(575,219),(724,188),(806,870),(644,846)],
  'dado':[(644,846),(806,870),(817,1018),(664,998)],
  'courses':[
  [(574,220),(724,188),(720,170),(578,201)],
  [(581,201),(720,172),(713,141),(586,170)],
  [(586,168),(713,140),(710,111),(585,138)],
  [(627,130),(697,116),(692,79),(631,91)]],
  'cap':[(608,40),(683,20),(692,69),(614,87)],
  'relief':[(582,210),(589,208),(587,194),(600,191),(601,210),(618,208),(618,200),(622,198),(625,217),(670,207),(669,190),(680,187),(684,204),(693,202),(689,179),(699,177),(703,207),(680,213),(677,226),(628,237),(619,222),(609,224),(605,212),(594,216),(594,229),(584,232)],
  'flutes':[((653,442),(705,833)),((680,399),(741,855)),((711,442),(771,849))],
  'outer':[(590,235),(603,231),(672,821),(661,825)],
  'blocks':[(578,211,9),(583,183,10),(698,184,10),(693,159,9)]}]

def shape(points,y=FACE_Y):
    return Polygon([position(u,v,y)[[0,2]] for u,v in points]).buffer(0)

def add_piers(b,lod):
    f=Facade(b,(-4,0),(4,0),'Boundary')
    for p in PIERS:
        name=p['name']
        grooves=[]
        for i,(top,foot) in enumerate(p['flutes'],1):
            line=LineString([position(*v,FACE_Y)[[0,2]] for v in [top,foot]])
            g=line.buffer(.0048,cap_style=2)
            grooves.append(g)
            f.prism(g,-FACE_Y-.015,-FACE_Y-.012,SHADOW,name+' fine vertical groove '+str(i))
        body=shape(p['shaft']); holes=unary_union(grooves)
        f.prism(body.difference(holes),-.48 if name=='Left' else -.25,-FACE_Y,MATERIAL,name+' roughcast shaft')
        f.prism(body,-.27,-FACE_Y-.017,MATERIAL,name+' groove backing')
        f.prism(shape(p['dado']),-.24,-FACE_Y+.004,TILE,name+' dark glazed base')
        f.prism(shape(p['outer'],FACE_Y-.02),-FACE_Y-.013,-FACE_Y+.021,LIGHT,name+' raised corner strip')
        for i,quad in enumerate(p['courses'],1):
            front=FACE_Y+i*.004
            f.prism(shape(quad,front),-.23,-front,MATERIAL,name+' stepped shoulder '+str(i))
        cap=shape(p['cap'])
        f.prism(cap,-.20,-FACE_Y,CAP,name+' projecting crown')
        for j in range(1,5 if name=='Right' else 6):
            a,d,c,e=p['cap'];n=5 if name=='Right' else 6;t=j/n
            line=LineString([position((1-t)*x[0]+t*y[0],(1-t)*x[1]+t*y[1],FACE_Y-.002)[[0,2]] for x,y in [(a,d),(e,c)]])
            f.prism(line.buffer(.0047,cap_style=2),-FACE_Y+.0005,-FACE_Y+.0025,SHADOW,name+' incised crown joint '+str(j))
        # A square-section step key returns around the top of each shaft.
        f.prism(shape(p['relief'],FACE_Y-.016),-FACE_Y-.015,-FACE_Y+.017,LIGHT,name+' stepped relief field')
        for j,(u,v,k) in enumerate(p['blocks'],1):
            inset=[(u,v),(u+k,v-2),(u+k+1,v+k-2),(u+1,v+k)]
            f.prism(shape(inset,FACE_Y-.013),-FACE_Y-.013,-FACE_Y+.014,LIGHT,name+' shoulder tile '+str(j))
    # The fence is fixed on a low continuous masonry plinth, rather than a
    # pair of movable door leaves. Stepped changes in level remain legible.
    contour=[(97,751),(143,741),(206,749),(281,757),(330,740),(418,751),
             (421,784),(498,781),(586,798),(646,806),(655,990),(98,892)]
    plinth=shape(contour,-.055)
    cuts=[]
    for i,(u,v,bu,bv) in enumerate([(133,746,132,899),(171,747,174,916),(210,756,216,925),(249,752,257,934),(286,752,295,942),(373,749,387,966),(459,786,476,976),(541,791,557,989),(605,804,623,998)],1):
        path=LineString([position(u,v,-.055)[[0,2]],position(bu,bv,-.055)[[0,2]]]).buffer(.0028,cap_style=2)
        cuts.append(path)
    f.prism(plinth.difference(unary_union(cuts)),-.17,.055,BASE,'mortared boundary plinth')
    f.prism(plinth,-.18,.048,JOINT,'plinth joint bed')

NOTICE='Pale removable notice'
NOTICE_EDGE='Weathered notice edging'
def add_notice(builder,lod):
    """Trace the temporary fan-shaped board that occludes the middle lattice."""
    import numpy as np
    def bezier(a,b,c,d):
        t=np.linspace(0,1,10 if lod else 26)[:,None]
        return (1-t)**3*np.array(a)+3*(1-t)**2*t*np.array(b)+3*(1-t)*t*t*np.array(c)+t**3*np.array(d)
    top=bezier((254,425),(292,360),(360,338),(416,406))
    bottom=bezier((375,479),(346,451),(324,444),(294,483))
    y=-.050
    panel=shape([*top,*bottom],y)
    f=Facade(builder,(-4,0),(4,0),'Notice')
    f.prism(panel,.033,-y,NOTICE_EDGE,'fan shaped notice edge')
    f.prism(panel.buffer(-.009),-y,-y+.0018,NOTICE,'pale board seen in front of the iron')
    fine=panel.buffer(-.019)
    f.prism(fine.boundary.buffer(.0016),-y+.0018,-y+.0027,NOTICE_EDGE,'inner painted outline')

def attach_outer_ends(b,lod):
    """Carry the outer bar ends back to their pier on the photographed sightline.

    The photographed extremities are against the returns of the two posts,
    which lie at different depths from the centre of the iron. An assumed
    short cramp closes that depth interval, without inventing a visible face.
    """
    from iron_panel import MEASURED_SECTIONS,IRON
    from shapely.geometry import Point
    import numpy as np
    for j,p in enumerate(PIERS):
        wall=shape(p['shaft'])
        for name,_,points,width,_ in MEASURED_SECTIONS:
            ends=[]
            if name.startswith(('upper crossbar','bottom crossbar')):
                ends=[points[0],points[-1]]
            if name.startswith('outer diagonal'):
                ends=[points[0] if j==0 else points[-1]]
            for uv in ends:
                u,v=uv
                if not (137<u<155 if j==0 else 583<u<639):continue
                origin=position(u,v)
                # Follow the exact sightline into the observed column return.
                ys=np.linspace(0,.48,55) if j==0 else np.linspace(0,-.169,50)
                target=None
                for y in ys:
                    q=position(u,v,y)
                    if wall.contains(Point(q[0],q[2])):
                        target=q;break
                if target is None:
                    # A tip can meet the far limit of a measured return. Its
                    # anchor then extends laterally into the same course.
                    from shapely.ops import nearest_points
                    q=position(u,v,ys[-1])
                    nearest=nearest_points(wall,Point(q[0],q[2]))[0]
                    target=np.array([nearest.x,ys[-1],nearest.y])
                target[0]+=-.014 if j==0 else .014
                if np.linalg.norm(origin-target)>.006:
                    b.tube([origin,target],width*.82,IRON,5 if lod else 8,'Pier fix '+str(j+1)+' '+name)
