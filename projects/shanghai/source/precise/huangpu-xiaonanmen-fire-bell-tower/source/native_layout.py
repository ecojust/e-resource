"""Blender coordinates are in metres, with the entrance side toward negative Y."""
MAIN = '01 Whole tower from the courtyard'
CAMERAS = {
    MAIN: ((17, -47, 23), (0, 0, 17.2), 42),
    '02 Street-side arch and tapered feet': ((8, -29, 8), (0, -4.7, 5.0), 17),
    '03 Spiral stair and protective cage': ((12, -16, 15), (0, 0, 13), 10),
    '04 Braced intermediate platforms': ((22, -30, 20), (0, 0, 20), 17),
    '05 Lookout glazing and parapet': ((11, -20, 33), (0, 0, 31.5), 11),
    '06 Roof from above': ((8, -12, 53), (0, 0, 32), 11),
}
CONCRETE = 'Weathered cast concrete'
UV_NAME = 'Tower roughcast courses'
SHADER_NAME = 'Original weathered concrete'
TEXTURE = 'weathered-concrete.png'

def native_uv(point):
    x, y, z = point
    return (.5 + (x + 1.17 * y) * .027, (z + .12) / 35.6)
