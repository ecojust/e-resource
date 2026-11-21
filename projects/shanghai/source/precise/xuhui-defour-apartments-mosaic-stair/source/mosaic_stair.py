"""Four cropped treads with the tile divisions visible in the restoration photograph."""
from collections import defaultdict

PITCH = 0.027
WIDTH = 40 * PITCH
GOING = 10 * PITCH
RISE = 6 * PITCH
GROUT = 0.0018
COLOURS = {
    'warm grey grout': (103,91,82), 'charcoal grout': (72,68,65),
    'graphite tile': (58,56,55), 'grey umber tile': (65,61,57),
    'umber end tile': (137,88,57), 'ochre end tile': (149,96,63),
    'dark bullnose': (70,66,62), 'pale worn strip': (161,157,146),
    'russet cheek tile': (107,72,64), 'dark skirt tile': (61,67,63),
}
def linear(value):
    value /= 255
    return value/12.92 if value <= .04045 else ((value+.055)/1.055)**2.4
PALETTE = {name: {'color': [linear(c) for c in rgb], 'roughness': .86 if 'grout' in name else .52} for name,rgb in COLOURS.items()}


class TileSheet:
    def __init__(self, builder, name):
        self.builder = builder
        self.name = name
        self.surfaces = defaultdict(list)

    def tile(self, material, corners):
        self.surfaces[material].append(corners)

    def finish(self):
        for material, panels in self.surfaces.items():
            vertices = [point for panel in panels for point in panel]
            faces = [(i,i+1,i+2,i+3) for i in range(0,len(vertices),4)]
            self.builder.add(vertices,faces,material,self.name+' / '+material)


def tile_colour(col,row,step):
    lighter = (col*7 + row*3 + step*11) % 17 in (1,5,13)
    if col < 6 or col >= 34:
        return 'ochre end tile' if lighter else 'umber end tile'
    return 'grey umber tile' if lighter else 'graphite tile'


def tile_field(sheet, columns, rows, to_xyz, shade):
    half_joint = GROUT/2
    for row in range(rows):
        bottom,top = row*PITCH+half_joint,(row+1)*PITCH-half_joint
        for col in range(columns):
            left,right = col*PITCH+half_joint,(col+1)*PITCH-half_joint
            sheet.tile(shade(col,row),[to_xyz(left,bottom),to_xyz(right,bottom),to_xyz(right,top),to_xyz(left,top)])


def add_building(builder,lod=False):
    left = -WIDTH/2
    for i in range(4):
        front,top = i*GOING,(i+1)*RISE
        step = 'Step '+str(i+1)
        builder.box((0,front+GOING/2,top/2),(WIDTH,GOING,top),'warm grey grout',label=step+' bed')
        tiles = TileSheet(builder,step)
        def horizontal(x,y):
            return (left+x,front+y,top+.0014)
        def vertical(x,z):
            return (left+x,front-.0015,top-RISE+z)
        shade = lambda col,row: tile_colour(col,row,i)
        if not lod or i==0:
            tile_field(tiles,40,10,horizontal,shade)
            tile_field(tiles,40,6,vertical,shade)
        else:
            # At distance keep the real changes of colour at each side of the central run.
            for a,b,material in ((0,6,'umber end tile'),(6,34,'graphite tile'),(34,40,'umber end tile')):
                x0,x1=a*PITCH,b*PITCH
                for y in range(10):
                    y0,y1=y*PITCH+GROUT/2,(y+1)*PITCH-GROUT/2
                    tiles.tile(material,[horizontal(x0,y0),horizontal(x1,y0),horizontal(x1,y1),horizontal(x0,y1)])
                for z in range(6):
                    z0,z1=z*PITCH+GROUT/2,(z+1)*PITCH-GROUT/2
                    tiles.tile(material,[vertical(x0,z0),vertical(x1,z0),vertical(x1,z1),vertical(x0,z1)])
        tiles.finish()
        # The pale nose crosses the charcoal central field. It stops at the two brown end fields.
        nose=TileSheet(builder,step+' rounded nose')
        count=28 if not lod else 7
        radius=.007; sections=6 if not lod else 3
        from math import sin,cos,pi
        for col in range(count):
            a=left+6*PITCH+28*PITCH*col/count+GROUT/2
            b=left+6*PITCH+28*PITCH*(col+1)/count-GROUT/2
            def point(x,t):
                return (x,front-.002-radius*sin(t),top+.002-radius*(1-cos(t)))
            for j in range(sections):
                angle1=j*pi/(2*sections);angle2=(j+1)*pi/(2*sections)
                nose.tile('pale worn strip' if j<sections//2 else 'dark bullnose',
                          [point(a,angle1),point(a,angle2),point(b,angle2),point(b,angle1)])
        nose.finish()
        for side in (-1,1):
            x=side*WIDTH/2
            builder.box((x+side*.015,front+GOING/2,top+.117),(.03,GOING,.234),'charcoal grout',label=step+' stair cheek')
            sidewall=TileSheet(builder,step+(' left wall' if side<0 else ' right wall'))
            for row in range(8):
                for col in range(10 if not lod else 1):
                    a=front+col*GOING/(10 if not lod else 1)+GROUT/2
                    b=front+(col+1)*GOING/(10 if not lod else 1)-GROUT/2
                    low=top+row*.234/8+GROUT/2;high=top+(row+1)*.234/8-GROUT/2
                    coords=[(x-side*.0008,a,low),(x-side*.0008,b,low),(x-side*.0008,b,high),(x-side*.0008,a,high)]
                    sidewall.tile('dark skirt tile' if row<3 else 'russet cheek tile',coords if side==-1 else coords[::-1])
            sidewall.finish()
