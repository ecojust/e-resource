"""Rear extent from the red line of the cadastral plan and front walls from garden views."""
from shapely.geometry import Polygon, box
from house_fabric import Wall, STONE, PLINTH, CONCRETE, STAIR, BRONZE
from round_veranda import round_veranda,portico,balcony_awning
from sunroom_terrace import add_sunroom

def add_shell(b,lod,layout):
    outline=[(.15,1.27),(5.45,1.27),(5.45,3.6),(10.48,3.6),(10.48,8.92),(8.06,8.92),(8.06,17.58),(7.59,19.54),(.65,19.54),(.65,21.85),(-4.18,21.85),(-4.18,10.99),(-.44,10.99)]
    for j,(bottom,top) in enumerate([(0,.26),(3.67,3.87),(7.23,7.41)]):
        b.plan_prism(Polygon(outline),bottom,top,PLINTH if j==0 else CONCRETE,'House | floor or ceiling '+str(j+1))
    rear=[(8.29,17.58),(7.59,19.54),(.65,19.54),(.65,21.85),(-4.18,21.85),(-4.18,10.99),(-.44,10.99),(.15,1.27)]
    for j,(start,end) in enumerate(zip(rear,rear[1:])):
        wall=Wall(b,start,end)
        if j==0:
            ops=[(.32,.96,wall.length-.29,3.10),(.35,4.82,wall.length-.31,6.55)]
            wall.masonry(.20,7.45,ops,'East wing | north angled return')
            for k,opening in enumerate(ops):
                wall.sash(opening,2,3,'Return | window '+str(k+1),lod)
        else:
            wall.masonry(.20,7.45,[],'Survey envelope | wall '+str(j+1))
        wall.rect(0,.05,wall.length,.43,-.28,.032,PLINTH,'Survey envelope | plinth '+str(j+1))
    for start,end in [((5.45,3.60),(5.45,0)),((10.52,3.60),(5.45,3.60))]:
        w=Wall(b,start,end);w.masonry(7.10,7.43,[],'Sunroom | wall junction')
    round_veranda(b,lod,layout);balcony_awning(b,lod,layout);portico(b,lod,layout);add_sunroom(b,lod,layout)
    for j,(x,y) in enumerate([(8.34,12.60),(10.55,3.55),(.195,1.17)]):
        b.tube([(x-.17,y,7.45),(x-.17,y,7.24),(x,y,7.06),(x,y,.48),(x+.12,y,.35)],.042,BRONZE,8,'Rainwater | return '+str(j+1))
    # The approach is retained only where the garden photographs establish a walking surface.
    b.plan_prism(Polygon([(10.75,8.40),(14.4,7.6),(14.9,12.8),(10.56,13.69)]),-.065,.0,STAIR,'Garden | portico approach')
