"""Original finishes for the pebble-dashed villa and the red inset entrance at 517 Fuxing Road."""
from pathlib import Path

SOURCE=Path(__file__).resolve().parent
ROUGH='Washed grey pebbles'
SASH='Dark red timber joinery'
SHUTTER='Oxblood shutter boards'
GLASS='Grey green glazing'
LIGHT='Warm reflected pane'
DARK='Recess shade'
STONE='Light grey cast stone'
SILL='Weathered cement sill'
BRICK='Russet moulded brick'
MORTAR='Dark red brick joints'
BALUST='Pale terrace stone'
BASE='Coarse grey plinth'
WOOD='Inside entrance red'
VINE='Ivy stems'
LEAVES=['Oxide green foliage','Olive green foliage','Shaded ivy']
IRON='Blackened iron'


def colour(rgb,roughness,metallic=0):
    def linear(value):
        s=value/255
        return s/12.92 if s<=.04045 else ((s+.055)/1.055)**2.4
    return {'color':[linear(n)for n in rgb],'roughness':roughness,'metallic':metallic}


PALETTE={
    ROUGH:{'color':[1.,1.,1.],'roughness':.91,'texture':str(SOURCE/'pebble-dash.png')},
    SASH:colour((95,58,48),.67),SHUTTER:colour((107,63,51),.76),
    GLASS:colour((84,101,102),.27,.22),LIGHT:colour((113,120,113),.33,.20),
    DARK:colour((64,63,54),.93),STONE:colour((173,171,155),.82),SILL:colour((138,140,129),.86),
    BRICK:colour((164,96,73),.83),MORTAR:colour((111,76,63),.91),
    BALUST:colour((181,183,173),.84),BASE:colour((129,129,117),.90),
    WOOD:colour((140,59,51),.70),IRON:colour((67,70,61),.62,.39),
    VINE:colour((92,80,62),.92),LEAVES[0]:colour((78,95,68),.89),
    LEAVES[1]:colour((96,105,72),.88),LEAVES[2]:colour((56,78,63),.92)
}


def pebble_uv(x,y,z):
    # Both orthogonal vertical elevations have the same repeat in metres.
    # The affine skew also keeps UVs two-dimensional on short horizontal returns.
    return (x+y)/0.74,(z+0.19*y-0.10*x)/0.74


def add_uvs(builder):
    for part in builder.parts:
        if part['material']==ROUGH:
            part['texcoords']=[(u,1-v) for u,v in (pebble_uv(*pt)for pt in part['vertices'])]
