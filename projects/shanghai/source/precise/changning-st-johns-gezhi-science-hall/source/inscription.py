"""Original simplified calligraphic outlines for the three photographed, right-to-left characters."""
from shapely.geometry import LineString
from shapely.ops import unary_union

# The three character centres and bounding box were measured on the ECUPL west photograph.
# Coordinates within each 20-unit square are authored strokes, not digitised photo pixels.
WOOD_RADICAL=[[(1,6),(8,6)],[(5,2),(4.8,17.7),(4,19)],[(4.8,7),(3.3,11.1),(.8,14.8)],[(5.3,8.1),(7.5,11)]]
GE=WOOD_RADICAL+[[ (12.5,1),(10.5,4.8),(8.2,7)],[(11.4,3.6),(17.5,3.3),(15.2,7.2),(11.4,10),(8.1,11.5)],[(10.7,5.2),(13.8,8.6),(19.5,10.7)],[(10.1,12.1),(17,12),(17,18),(9.9,18),(10.1,12.1)]]
ZHI=[[(.6,3),(9.8,2.5)],[(5.3,3.6),(2.1,8.0),(8.1,7.3)],[(6.8,5.5),(9.2,8.5)],[(5.4,8.3),(5.3,15.8)],[(1.2,11),(9.1,10.5)],[(.7,17),(9.4,15.2)],[(14,1.6),(12.1,6.3),(9.7,9.3)],[(12.6,5.3),(19,4.9)],[(16.7,5.7),(15.1,10.4),(13.5,14.2),(10.2,18.7)],[(11.3,8.4),(13.5,12.7),(16.2,16.0),(19.6,18.1)]]
LOU=WOOD_RADICAL+[[(10,3.1),(17.6,3),(17.6,6),(10,6),(10,3.1)],[(13.7,.5),(13.6,11.8)],[(8.5,7.8),(19.4,7.6)],[(10.4,8.7),(10.4,10.4),(17.3,10.4),(17.3,8.6)],[(12.9,11.0),(10.8,14.9),(14.5,16.1),(18.7,18.7)],[(16.8,12.3),(15.5,15.5),(12.2,17.8),(8.5,19)],[(8,13),(19.4,12.8)]]

def add_inscription(builder,wall,x,z):
    for char,strokes,u in [('樓',LOU,303.9),('致',ZHI,324.1),('格',GE,345.0)]:
        centre=x(u);base=z(280.4);height=z(269.1)-base;width=.40
        segments=[]
        for stroke in strokes:
            points=[(centre+(sx-10)*width/20,base+(20-sy)*height/20) for sx,sy in stroke]
            segments.append(LineString(points).buffer(.017,cap_style='round',join_style='round',quad_segs=2))
        wall(builder,unary_union(segments),-.187,-.165,'Science Hall | dark casement timber','entrance tablet / raised '+char)
