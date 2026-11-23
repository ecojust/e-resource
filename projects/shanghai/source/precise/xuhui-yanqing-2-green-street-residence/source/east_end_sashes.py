"""Two small upper sashes on the recessed, numbered end wall of Yanqing Road 2."""
from shapely.geometry import box
from shapely.ops import unary_union

from street_entry import DARK, GLASS, STEEL, STONE


# Local facade X, Z. The source observations remain tied to wall Y = 2.40.
# The lower slit with the second number plate belongs to street_entry.
UPPER_SASHES = (
    ("middle", (6.523, 5.094, 6.975, 6.164), 4),
    ("top", (6.465, 8.119, 6.922, 9.125), 3),
)


def openings():
    """Open holes in the recessed front wall; polygons are in facade X, Z."""
    return [box(*bounds) for _, bounds, _ in UPPER_SASHES]


def add_upper_sashes(builder, lod=False, right_wall_y=2.40):
    """Add steel casements, heads, sills and the pale three-sided panel frame."""
    def prism(shape, depth, back, material, name):
        builder.prism(shape, 0, back-depth,
                      lambda x,z,t: (x,right_wall_y+back-t,z),
                      material, 'East recessed wall | '+name)

    for floor, (left,sill,right,head), rows in UPPER_SASHES:
        inner = box(left+.034,sill+.036,right-.034,head-.035)
        frame = box(left,sill,right,head).difference(inner)
        centre = (left+right)/2
        bars = [frame,box(centre-.011,sill+.022,centre+.011,head-.022)]
        for i in range(1,rows):
            z=sill+(head-sill)*i/rows
            bars.append(box(left+.022,z-.012,right-.022,z+.012))
        prism(unary_union(bars),.071,.102,STEEL,floor+' narrow steel sash')
        prism(inner,.120,.134,GLASS,floor+' recessed glazing')
        prism(box(left-.069,sill-.080,right+.085,sill+.009),-.083,.025,
              STONE,floor+' projecting pale sill')
        prism(box(left-.062,head-.003,right+.063,head+.087),-.061,.025,
              STONE,floor+' pale flat head')
        if not lod:
            # The top and left reveals are discernible in the closer winter view.
            band=box(left+.004,sill+.002,right-.002,head-.001).difference(
                box(left+.019,sill+.002,right-.002,head-.018))
            prism(band,.013,.070,DARK,floor+' shaded inner reveal edge')

    # The narrow panel between storeys has pale uprights and a pale upper band.
    # The untouched render remains visible between them.
    left,right=6.465,6.965
    base,top=6.249,8.038
    pieces=[box(left-.047,base,left+.051,top),
            box(right-.048,base,right+.044,top),
            box(left-.045,top-.095,right+.042,top)]
    prism(unary_union(pieces),-.043,.007,STONE,'pale inter-storey panel frame')
