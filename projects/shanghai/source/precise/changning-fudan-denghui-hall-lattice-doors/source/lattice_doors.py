"""Two adjoining upper lattice and lower panel leaves at Denghui Hall, Shanghai."""
from shapely.geometry import box

def finish(rgb,roughness=.79):
    def linear(c):
        x=c/255
        return x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4
    return dict(color=[linear(c) for c in rgb],roughness=roughness,metallic=0)

PALETTE={
    'red lacquer':finish((106,47,41),.70),
    'panel field':finish((111,53,45),.77),
    'shadow moulding':finish((77,38,34),.78),
    'rubbed red arris':finish((133,67,54),.77),
    'openwork dark wood':finish((69,57,47),.80),
    'aged exposed edge':finish((94,74,57),.82),
    'threshold timber':finish((83,55,43),.85),
}
CENTRES=(-.293,.293)
TOP=2.89
LIGHT_BOTTOM=1.204
LIGHT_TOP=2.728
LIGHT_WIDTH=.460
CELL_X=LIGHT_WIDTH/6
CELL_Z=(LIGHT_TOP-LIGHT_BOTTOM)/13

def add_building(b,lod=False):
    def slab(name,x0,z0,x1,z1,y0,y1,material):
        b.prism(box(x0,z0,x1,z1),-y1,-y0,lambda x,z,d:(x,-d,z),material,name)
    def surround(name,x0,z0,x1,z1,thick,y0,y1,material):
        shape=box(x0,z0,x1,z1).difference(box(x0+thick,z0+thick,x1-thick,z1-thick))
        b.prism(shape,-y1,-y0,lambda x,z,d:(x,-d,z),material,name)
    for i,c in enumerate(CENTRES):
        tag='west leaf ' if i==0 else 'east leaf '
        # Paired timber stiles and pegged rails keep the upper lattice perforated.
        for sign in (-1,1):
            edge=c+sign*.265
            slab(tag+'edge stile '+str(sign),edge-.027, .079,edge+.027,2.852,.0,.096,'red lacquer')
            if not lod:
                slab(tag+'rubbed inner corner '+str(sign),edge-sign*.023-.0025,.113,
                     edge-sign*.023+.0025,2.80,-.002,.003,'rubbed red arris')
        for label,bot,top in [('head rail',2.733,2.852),('lock rail',1.048,1.198),('lower rail',.120,.279)]:
            slab(tag+label,c-.240,bot,c+.240,top,.001,.094,'red lacquer')
            if not lod:
                slab(tag+label+' lower bead',c-.238,bot+.011,c+.238,bot+.017,-.007,.001,'shadow moulding')
                slab(tag+label+' upper bead',c-.238,top-.016,c+.238,top-.009,-.006,.001,'rubbed red arris')
        slab(tag+'inset wooden panel',c-.242,.26,c+.242,1.062,.031,.082,'panel field')
        surround(tag+'lower panel raised frame',c-.243,.257,c+.243,1.063,.031,.003,.048,'shadow moulding')
        surround(tag+'outer lip at panel',c-.242,.258,c+.242,1.062,.011,-.008,.014,'red lacquer')
        if not lod:
            surround(tag+'raised inner bead',c-.214,.286,c+.214,1.034,.006,.011,.038,'rubbed red arris')
        surround(tag+'lattice socket',c-.242,1.192,c+.242,2.74,.012,.002,.074,'red lacquer')
        x0=c-LIGHT_WIDTH/2
        # The coarse lattice resolves in the photograph as long rows and uprights.
        # Alternate bays carry partial return bars; the precise concealed joinery is unknown.
        for col in range(1,6):
            x=x0+col*CELL_X
            slab(tag+'lattice upright '+str(col),x-.0062,LIGHT_BOTTOM,x+.0062,LIGHT_TOP,.027,.057,'openwork dark wood')
            if not lod:
                slab(tag+'upright light edge '+str(col),x-.0062,LIGHT_BOTTOM,x-.004,LIGHT_TOP,.025,.029,'aged exposed edge')
        for row in range(1,13):
            z=LIGHT_BOTTOM+row*CELL_Z
            slab(tag+'lattice crossbar '+str(row),x0,z-.0058,x0+LIGHT_WIDTH,z+.0058,.022,.051,'openwork dark wood')
        for row in range(13):
            z=LIGHT_BOTTOM+row*CELL_Z
            for col in range(6):
                if (row+col)%2:continue
                x=x0+col*CELL_X
                near=x+CELL_X*.50;start=z+CELL_Z*.50
                slab(tag+'offset short uprights '+str(row),near-.0046,start,near+.0046,z+CELL_Z,.030,.052,'openwork dark wood')
                slab(tag+'half-width returns '+str(row),x+CELL_X*.50,start-.0046,x+CELL_X,start+.0046,.027,.050,'openwork dark wood')
    slab('sill beneath both leaves',-.612,.023,.612,.119,-.031,.151,'threshold timber')
    slab('dark upper lintel behind leaves',-.609,2.846,.609,TOP,.021,.157,'shadow moulding')
    if not lod:
        slab('lower sill nosing',-.610,.076,.610,.093,-.039,-.017,'rubbed red arris')
        slab('surviving head bead',-.604,2.848,.604,2.861,.012,.028,'red lacquer')
