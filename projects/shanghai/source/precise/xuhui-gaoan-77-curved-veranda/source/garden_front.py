"""South gable and the measured three-window group below the arcaded upper balcony."""
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from curved_veranda import add_veranda,veranda_interface
from garden_sashes import garden_window_group,registered_openings
from house_layout import DECK_Z,LAYOUT,U,Z,D
from materials import PLASTER,STONE
def add_front(f,lod):
    holes=registered_openings();view=veranda_interface(LAYOUT)
    section=Polygon(view['main_wall_clear_opening_xz'])
    span=box(U(-.765),0,U(.765),DECK_Z)
    underside=unary_union([*holes.values(),section])
    f.solid(span.difference(underside),-.21,0,PLASTER,'south gable | white render forward wall')
    garden_window_group(f,holes)
    add_veranda(f.b,lod,LAYOUT)
    # Short returns bound the front elevation independently of the gallery opening.
    for left,origin,direction in [(U(-.765),D(.63),-1),(U(.765),0,1)]:
        f.face(left,origin,0,direction).rect(0,D(.63),0,DECK_Z,-.12,0,PLASTER,'south gable | sectional return')
    back=f.face(U(.765),D(.63),-1,0)
    back.rect(0,U(.765)-U(-.765),0,DECK_Z,-.13,0,STONE,'south gable | sectional closure')
