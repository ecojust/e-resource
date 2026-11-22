"""Editable entrance, wrought-iron scroll, street plaque and open-leaf camera poses."""
from material_coordinates import texture_coordinates,WOOD,PANEL
MAIN='01 Street entrance and west wall'
CAMERAS={MAIN:((-2.8,-13,4.10),(-1.12,.12,2.14),8.12),
  '02 Hanging timber oval':((-.65,-5.5,3.38),(.02,.20,3.43),3.65),
  '03 Three west wall plaques':((-3.7,-6.20,2.10),(-3.31,-.02,1.96),2.56),
  '04 Memorial cast relief':((-2.94,-3.8,2.20),(-2.59,-.02,1.994),1.0),
  '05 Inward open east leaf':((-.4,-5.80,2.40),(1.43,.77,1.37),3.98),
  '06 Courtyard looking out':((-.2,9.6,3.44),(-1.05,.28,2.12),7.45)}
MATERIALS={WOOD:('oval-grain.png','Hanging oval timber grain'),PANEL:('cement-panel.png','Rendered plaque wall')}
UV_NAME='Qinyuan exterior surface coordinates'

def uv_for_face(material,vertices,object_name):
    return [texture_coordinates(material,v,object_name) for v in vertices]
