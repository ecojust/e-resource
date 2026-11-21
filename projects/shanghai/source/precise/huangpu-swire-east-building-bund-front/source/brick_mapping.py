"""The whole raster spans the front elevation. The underlying GLB uses clamped UVs."""
BRICK='Swire riverfront red brick'
def brick_uv(label,vertex):
    return ((vertex[0]+.50)/32.0,(vertex[2]+.40)/29.0)
