"""South gable and the measured three-window group below the arcaded upper balcony."""
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from curved_veranda import add_veranda,veranda_interface
from garden_sashes import garden_window_group,registered_openings
from house_layout import DECK_Z,FIT,LAYOUT,U,Z,D
from materials import PLASTER,STONE
def add_front(f,lod):
    holes=registered_openings();view=veranda_interface(LAYOUT)
    section=Polygon(view['main_wall_clear_opening_xz'])
    span=box(U(-.765),0,U(.765),DECK_Z)
    underside=unary_union([*holes.values(),section])
    # The fitted corners refer to the outer wood frame. The photographed casements sit just behind the rendered wall.
    windows=f.face(0,D(FIT['shared_window_parameters']['depth'])-.041,1,0)
    windows.solid(span.difference(underside),-.23,0,PLASTER,'south gable | white render forward wall')
    garden_window_group(windows,holes)
    add_veranda(f.b,lod,LAYOUT)
