"""Editable Guandu Lu camera poses and the same per-object material mapping used in the web model."""
from material_coordinates import texture_coordinates
MAIN='01 East tower and paired arches'
CAMERAS={MAIN:((-18,-28,11),(2.45,-.3,8.58),24.3),
    '02 South blind brick panels':((-13,3,13),(-2.70,.72,12.9),6.4),
    '03 Clear arched attic window':((-10,-13,15),(-1.4,-1.4,13.0),9.5),
    '04 Two segmental east windows':((6.85,-17,8.7),(6.7,-1.8,7.1),10.1),
    '05 Wall fans and exterior grille':((4.1,-10,5.3),(4.9,-1.83,4.9),7.3),
    '06 Six-sided grey parapet':((-11,-16,25.7),(0,0,15.2),12.5)}
MATERIALS={'Guandu pressed red brick':('guandu-brick-courses.png','Hand-made pressed brick'),
    'End wall red brick':('guandu-brick-courses.png','Hand-made end wall brick'),
    'Weathered coping stone':('guandu-grey-coping.png','Grey hexagonal coping')}
UV_NAME='Guandu brick and coping coordinates'

def uv_for_face(material,vertices,object_name):
    return [texture_coordinates(material,v,object_name) for v in vertices]
