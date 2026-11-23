"""The grain field covers the observed north street wall in local surveying coordinates."""
STONE='Weathered dark granite ashlar'
def stone_uv(label,vertex):
    return ((vertex[0]+.40)/10.,(vertex[2]+.30)/13.)
