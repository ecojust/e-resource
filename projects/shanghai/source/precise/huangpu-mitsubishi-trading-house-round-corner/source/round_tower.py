"""Street-facing part of the round tower at 102 Guangdong Road, January 2015."""
from math import ceil, cos, floor, pi, sin, tau
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening

STONE = 'weathered buff facing'
TRIM = 'pale ochre carved stone'
RECESS = 'deep warm joints'
METAL = 'dark painted metal'
GLASS = 'muted street glazing'
WOOD = 'reddish brown entry doors'
ROOF = 'grey flat roof'
PALETTE = {name: {'color': rgb, 'roughness': roughness}
           for name, rgb, roughness in [
               (STONE, [.65, .535, .415], .88), (TRIM, [.75, .63, .50], .87),
               (RECESS, [.43, .35, .28], .93), (METAL, [.20, .22, .22], .66),
               (GLASS, [.26, .32, .33], .40), (WOOD, [.43, .23, .18], .79),
               (ROOF, [.44, .44, .41], .84)]}
RADIUS = 2.62
DRUM_RADIUS = 2.41
AXES = (-.87, 0., .87)


def polar(angle, radius, height):
    return radius*sin(angle), -radius*cos(angle), height


class CurvedWall:
    """Unroll the front surface into arc length and height to cut the actual openings."""
    def __init__(self, builder, radius, lod):
        self.builder = builder
        self.radius = radius
        self.step = pi*radius/(16 if lod else 40)
        self.lod = lod

    def position(self, u, z, depth):
        return polar(u/self.radius, self.radius+depth, z)

    def relief(self, polygon, low, high, material, name):
        x0, z0, x1, z1 = polygon.bounds
        for i in range(floor(x0/self.step), ceil(x1/self.step)):
            piece = polygon.intersection(box(i*self.step, z0-.02, (i+1)*self.step, z1+.02))
            if piece.area > 1.e-7:
                self.builder.prism(piece, low, high, self.position, material, name)

    def band(self, z, height, projection, name, material=TRIM):
        width = self.radius*pi/2
        self.relief(box(-width, z, width, z+height), -.25, projection, material, name)

    def window(self, center, bottom, width, height, rise, upper):
        aperture = opening(center, bottom, width, height, rise, 12 if self.lod else 24)
        label = 'Drum' if upper else 'Tower'
        self.relief(aperture.buffer(.012,join_style=2), -.275, -.25, GLASS, label+' / glazing')
        x0, z0, x1, z1 = aperture.bounds
        transom = z0+height*(.77 if rise else .58)
        bars = [box(center-.032,z0,center+.032,z1), box(x0,transom-.033,x1,transom+.033)]
        if upper:
            bars.append(box(x0,z0+height*.31-.025,x1,z0+height*.31+.025))
        frame = aperture.buffer(-.015,join_style=2)
        panes = aperture.buffer(-.080,join_style=2).difference(unary_union(bars))
        self.relief(frame.difference(panes), -.215, -.105, METAL, label+' / sash bars')
        return aperture


def entrance(b, lod):
    width, plane, height = 4.88, -1.44, 4.96
    front = Facade(b,(-width/2,plane),(width/2,plane),'Portal')
    arch = opening(0.,.12,2.46,3.78,1.23,16 if lod else 32)
    front.wall(0.,height,[arch],.43,STONE)
    # The first tier cuts to a flat plane. These sides end at the cut through the existing walls.
    for side in (-1,1):
        b.box((side*(width/2-.095),-.44,height/2),(.19,2.,height),STONE,label='Portal / wall return')
    b.box((0,.48,height/2),(width,.20,height),RECESS,label='Portal / rear junction')
    for distance,depth,material in [(.18,.14,TRIM),(.105,.23,STONE),(.062,.285,TRIM)]:
        outer = arch.buffer(distance,join_style=1)
        front.prism(outer.difference(arch).intersection(box(-3,0,3,height)),depth-.10,depth,material,'concentric stone arch')
    frame = box(-1.87,0,1.87,4.49).boundary.buffer(.046,join_style=2)
    front.prism(frame.difference(arch.buffer(.19)).intersection(box(-3,0,3,height)),-.01,.065,TRIM,'square outer frame')
    for x in (-1.48,1.48):
        disk=Point(x,4.09).buffer(.151,quad_segs=8 if lod else 16)
        front.prism(disk.difference(disk.buffer(-.034)),.013,.081,TRIM,'spandrel roundels')
    front.prism(Polygon([(-.215,3.86),(.215,3.86),(.29,4.51),(-.29,4.51)]),.14,.32,TRIM,'prominent keystone')
    front.prism(arch.buffer(.009,join_style=2),-.374,-.342,WOOD,'closed arched door')
    spring = 2.67
    front.box(0,spring,2.44,.09,.08,-.278,METAL,'transom')
    front.box(0,1.38,.036,2.60,.092,-.27,METAL,'paired door joint')
    for x in (-.62,.62):
        frame = box(x-.48,.31,x+.48,2.50)
        front.prism(frame.difference(frame.buffer(-.056,join_style=2)),-.32,-.226,WOOD,'recessed door panels')
    front.box(0,.075,2.70,.15,.71,-.07,STONE,'stone threshold')
    front.box(0,4.84,width+.13,.17,.72,.075,TRIM,'flat door cornice')
    plan = Polygon([(-width/2,plane),(width/2,plane),(width/2,.56),(-width/2,.56)])
    b.plan_prism(plan,4.88,5.02,STONE,'Portal / cut transition')


def curved_front(b, lod):
    wall = CurvedWall(b,RADIUS,lod)
    limit = RADIUS*pi/2
    holes=[]
    for angle in AXES:
        x = RADIUS*angle
        for z,w,h,rise in [(5.64,1.21,2.60,0.),(10.24,1.21,2.52,.61),(14.54,1.19,1.98,0.)]:
            hole = wall.window(x,z,w,h,rise,False)
            holes.append(hole)
            if rise:
                rim=hole.buffer(.13,join_style=1).difference(hole)
                wall.relief(rim,-.012,.128,TRIM,'Arched tier / stone surround')
                upper_rim=hole.buffer(.255,join_style=1).difference(hole.buffer(.188,join_style=1))
                wall.relief(upper_rim.intersection(box(x-1,z+h-.64,x+1,z+h+.29)),
                            .032,.126,STONE,'Arched tier / second archivolt')
                wall.relief(box(x-.092,z+h-.015,x+.092,z+h+.302),.061,.204,TRIM,'Arched tier / key')
            else:
                wall.relief(box(x-w/2-.07,z-.10,x+w/2+.07,z-.003),
                            -.012,.109,TRIM,'Tower / individual sill')
        # The inset rectangular panel and its roundel are visible beneath every arched window.
        panel=box(x-.68,8.87,x+.68,10.13)
        wall.relief(panel.difference(panel.buffer(-.070,join_style=2)),.016,.092,TRIM,'Tower / framed spandrels')
        disk = Point(x,9.53).buffer(.383,quad_segs=8 if lod else 17)
        wall.relief(disk.difference(disk.buffer(-.077)),.026,.118,TRIM,'Tower / round medallions')
        if not lod:
            for j in range(8):
                a=tau*j/8
                petal=Point(x+.135*cos(a),9.53+.135*sin(a)).buffer(.080,quad_segs=5)
                wall.relief(petal,.028,.079,STONE,'Tower / medallion rosettes')
    wall.relief(box(-limit,4.95,limit,17.64).difference(unary_union(holes)),
                -.34,0,STONE,'Tower / cut curved wall')
    # Shallow relief panels cross the lower sill band in the January 2015 close view.
    # The lower belt is continuous beneath the separate window openings.
    for center in (-2.29, 0., 2.29):
        panel=box(center-.69,5.07,center+.69,5.52)
        wall.relief(panel.difference(panel.buffer(-.048,join_style=2)),.017,.080,TRIM,'Lower belt / panel frames')
        for j in range(-2,3):
            cx=center+j*.245
            diamond=Polygon([(cx-.106,5.295),(cx,5.414),(cx+.106,5.295),(cx,5.176)])
            wall.relief(diamond.difference(diamond.buffer(-.035,join_style=2)),
                        .022,.093,TRIM,'Lower belt / linked diamonds')
    for center in (-.435*RADIUS,.435*RADIUS):
        # A central boss and diverging carved leaves occupy the spandrel between pairs of arches.
        boss=Point(center,13.13).buffer(.102,quad_segs=7 if lod else 12)
        wall.relief(boss,.024,.122,TRIM,'Arched tier / carved bosses')
        for direction in (-1,1):
            leaf=Polygon([(center+direction*.08,13.15),(center+direction*.21,13.36),
                          (center+direction*.51,13.43),(center+direction*.37,13.27)])
            wall.relief(leaf,.020,.091,TRIM,'Arched tier / carved leaves')
    # Arcades above the spandrels have engaged piers with small capitals and a continuous springing band.
    for angle in (-1.315,-.435,.435,1.315):
        u=RADIUS*angle
        wall.relief(box(u-.09,9.97,u+.09,12.92),-.01,.098,TRIM,'Arched tier / slender piers')
        wall.relief(box(u-.166,12.73,u+.166,12.93),-.012,.147,TRIM,'Arched tier / capitals')
    for z,h,pr,m in [(4.965,.18,.17,TRIM),(5.22,.08,.085,TRIM),(8.29,.12,.10,TRIM),
                      (8.53,.075,.06,RECESS),(8.66,.112,.12,TRIM),
                      (13.39,.15,.125,TRIM),(13.62,.12,.18,TRIM),(13.77,.085,.09,STONE),
                      (16.92,.09,.075,TRIM),(17.15,.17,.165,STONE),(17.54,.18,.32,TRIM)]:
        wall.band(z,h,pr,'Tower / curved belt courses',m)
    # Masons laid the upper tier in horizontal courses. Each line stops at the window reveal.
    for z in (14.18,14.51,14.87,15.24,15.61,15.98,16.35,16.72):
        groove=box(-limit,z,limit,z+.025).difference(unary_union(holes))
        wall.relief(groove,.001,.008,RECESS,'Tower / shallow stone joints')
    for i in range(19):
        u=(i/18-.5)*(2*limit-.14)
        wall.relief(box(u-.062,17.32,u+.062,17.53),.038,.233,TRIM,'Tower / cornice dentils')
    b.box((0,.083,11.21),(2*RADIUS,.166,12.52),STONE,label='Tower / preserved wall junction')


def roof_drum(b,lod):
    drum = CurvedWall(b,DRUM_RADIUS,lod)
    limit = DRUM_RADIUS*pi/2
    holes = [drum.window(a*DRUM_RADIUS,18.48,1.04,1.60,0.,True) for a in AXES]
    drum.relief(box(-limit,17.72,limit,20.68).difference(unary_union(holes)),
                -.31,0.,STONE,'Drum / front wall')
    # Plan and historical descriptions resolve the full cylindrical cap, without opening unrecorded rear windows.
    n=32 if lod else 64
    back=Polygon([polar(a*pi/n,DRUM_RADIUS,0)[:2] for a in range(n//2,3*n//2+1)]+
                 [polar(a*pi/n,DRUM_RADIUS-.28,0)[:2] for a in range(3*n//2,n//2-1,-1)])
    b.plan_prism(back,17.72,20.68,STONE,'Drum / rear shell')
    for z,h,r,mat in [(17.63,.17,2.58,TRIM),(18.10,.14,2.49,TRIM),(20.31,.10,2.52,TRIM),
                      (20.61,.18,2.64,TRIM),(20.79,.07,2.55,ROOF)]:
        b.lathe((0,0),[(z,r),(z+h,r)],mat,n,'Drum / circular cap')
    for i in range(32):
        a=tau*i/32; x,y,z=polar(a,2.455,20.48)
        b.box((x,y,z),(.133,.208,.21),TRIM,
              [(cos(a),sin(a),0),(sin(a),-cos(a),0),(0,0,1)],'Drum / roof dentils')
    rail_radius=2.40
    for z in (20.94,21.28,21.49):
        pts=[polar(tau*i/n,rail_radius,z) for i in range(n+1)]
        b.tube(pts,.022 if z<21.49 else .031,METAL,5 if lod else 8,'Roof / railing rings')
    for i in range(28):
        angle=tau*i/28
        b.tube([polar(angle,rail_radius,20.84),polar(angle,rail_radius,21.50)],.020,METAL,
               5 if lod else 7,'Roof / upright balusters')
        if not lod:
            b.tube([polar(angle-.068,rail_radius,21.29),polar(angle,rail_radius,21.04),
                    polar(angle+.068,rail_radius,21.29)],.014,METAL,6,'Roof / open iron diamonds')


def facade(builder,lod=False):
    entrance(builder,lod)
    curved_front(builder,lod)
    roof_drum(builder,lod)
