"""Build the three-storey street-elevation section of Xile Apartments, Maoming South Road."""
import argparse
import json
import os
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE))
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from porthole_wall import street_pier
from open_balconies import build_balconies
from air_conditioners import outdoor_units

ID='huangpu-xile-apartments-maoming-portholes'
D=json.loads((SOURCE/'street_section.json').read_bytes())
META=dict(
    id=ID,name='希勒公寓茂名南路三层圆窗与悬挑阳台', viewer_page='xile-apartments-maoming-portholes.html',
    reference_height_m=D['cap_soffit'],status='measured-from-three-maoming-road-street-stations',
    scope='茂名南路116号入口上方，二至四层南列三扇圆窗、紧邻其北的三个开敞阳台半跨和可见的退后门窗。',
    estimated='尺度取自2020年2月22日三处街景。窗台和悬板的位置经过交会，栏杆截面、窗框分格、瓷砖模数及空调设备细部依据图像估计。',
    coordinate_convention='Metres. The origin is the ground projection of the porthole centre line. Positive X runs along the street at 347.06° clockwise from true north, Y is westward into the house, Z is up. The lowest included floor soffit is at 4.11 m.',
    source_register='source/precise/'+ID+'/reference-review.json',photos_embedded=False,third_party_models_embedded=False)

def colour(rgb,rough,metal=0):
    def linear(value):
        u=value/255
        return u/12.92 if u<=0.04045 else ((u+0.055)/1.055)**2.4
    return dict(color=[linear(v) for v in rgb],roughness=rough,metallic=metal)

PALETTE={
    'Pale ochre tile':colour((165,141,109),.76),'Honey buff tile':colour((168,139,105),.78),
    'Old straw tile':colour((171,146,113),.81),'Muted biscuit tile':colour((160,134,103),.82),
    'Tan mortar':colour((127,118,105),.92),'Buff cast-stone ring':colour((201,171,126),.79),
    'Deep bronze sash':colour((47,47,43),.53,.35),'Sash rebate':colour((84,79,65),.57,.29),
    'Blue grey glass':colour((87,102,108),.25,.24),'Casement reflection':colour((98,111,117),.27,.23),
    'Recessed ochre facing':colour((134,111,83),.82),'Recessed pointing':colour((101,92,80),.91),
    'Recess glazing':colour((60,68,69),.35,.18),'Warm dark joinery':colour((71,61,46),.62,.14),
    'Door lower panel':colour((92,79,59),.68),'Side light':colour((82,95,97),.32,.21),
    'Warm grey soffit':colour((164,154,140),.86),'Stone balcony floor':colour((131,126,112),.84),
    'Sandy balcony render':colour((203,178,146),.87),'Buff coping':colour((190,166,128),.83),
    'Dark balcony iron':colour((60,59,52),.54,.42),'Soffit drip':colour((128,118,103),.84),
    'AC enamel':colour((184,184,172),.63,.16),'AC brackets':colour((125,117,99),.68,.34),
    'Fan vent':colour((70,75,73),.62,.28),'Small blue service mark':colour((80,127,150),.59,.10),
    'Service insulation':colour((146,146,128),.85)
}

def add_building(builder,lod):
    street_pier(builder,lod,D)
    build_balconies(builder,lod,D)
    outdoor_units(builder,D,lod)
    # Only the visible underside belongs to this measured section; the model above starts at this elevation.
    x0,x1,y0,y1=D['bay_edge'],D['north_cut'],D['front_edge'],D['balcony_back']
    z=D['cap_soffit']
    builder.add([(x0,y0,z),(x0,y1,z),(x1,y1,z),(x1,y0,z)],[(0,1,2,3)],
                'Warm grey soffit','4F underside of retained upper cornice')

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    opts,rest=parser.parse_known_args()
    os.environ['XILE_MODEL_BLENDER']=opts.blender
    sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
