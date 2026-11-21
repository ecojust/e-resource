"""Three of the seven paired bays on the trading house at 6–8 East Jinling Road."""
import argparse
from pathlib import Path
import json,os,sys
from shapely.geometry import box
from shapely.ops import unary_union
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
sys.path.insert(0,str(SOURCE.parents[2]/'hongkou-general-post-office/source/common'))
from package_architectural_model import build
import trefoil_arch
import vestibule
import stone_finish
from jinling_facade import Front,PALETTE as FRONT_PALETTE,PLINTH,upper_storey,upper_frieze,shop
from trefoil_arch import CHALK,LIMESTONE,FILLET,RECESS
from vestibule import IRON,STEP

ID='huangpu-jinling-eight-trefoil-front'
SCOPE='金陵东路6–8号南立面中央三跨，含六座尖券花饰窗楣、两层成对方窗、临街铁栅、门厅木门及左右铺面。'
dims=json.loads((SOURCE/'dimensions.json').read_bytes())
META={'id':ID,'name':'金陵东路原洋行南立面尖券窗与入口','scope':SCOPE,'model_scope_zh':SCOPE,'viewer_page':'jinling-eight-trefoil-front.html',
      'status':'three-photographed-central-bays','reference_height_m':dims['parapet'],
      'coordinate_convention':'Metres. Local X west along the south facade from its east endpoint, Y south onto East Jinling Road, Z up.',
      'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':'木门前后及门槛；楼梯、居住空间和后屋另查。',
      'copyright':'Original geometry and masonry artwork. Font subset: SIL OFL 1.1. Photographs remain at their original sources.'}
PALETTE={**trefoil_arch.PALETTE,**vestibule.PALETTE,**FRONT_PALETTE}

def piers(front,mids,edges,d,detail):
    sill=d['gable_window_sill'];head=d['rectangular_head'];apex=d['stone_apex']
    for k,axis in enumerate(mids):
        # Between the twin windows the narrow pier supports a flowered capital.
        half=.125
        front.box('Paired window central pier',LIMESTONE,axis-half,axis+half,-.10,.13,sill,head-.23)
        trefoil_arch.capital(front,'Slender paired pier',axis,head-.30,.43,.09,detail)
    for axis in edges:
        # Full bays are separated by broader pilasters with a recessed panel.
        w=.49
        front.box('Broad bay pier',CHALK,axis-w/2,axis+w/2,-.11,.086,sill,apex+.05)
        front.box('Shallow pilaster panel',RECESS,axis-.13,axis+.13,.087,.094,sill+.25,head-.26)
        front.box('Pale recessed-panel face',LIMESTONE,axis-.100,axis+.100,.094,.108,sill+.31,head-.33)
        trefoil_arch.capital(front,'Wide leaf capital',axis,head-.33,.67,.091,detail)
    for left,right in [(min(edges)+.30,max(edges)-.30)]:
        front.box('Window-head stringcourse',FILLET,left,right,-.10,.064,head+.02,head+.07)

def add_building(builder,lod):
    d=json.loads((SOURCE/'dimensions.json').read_bytes());detail=not lod
    length=d['osm_south_edge_m']
    east,west=[length-v for v in reversed(d['west_station_extent'])]
    front=Front(builder,(east,west))
    pairs=[[length-v for v in pair]for pair in d['pairs_west_to_east']]
    mids=[sum(pair)/2 for pair in pairs]
    edges=[east,*[length-v for v in reversed(d['interior_piers_from_west'])],west]
    c=length-d['door_from_west']
    pierced=[]
    for j,x in enumerate(mids):
        if j==1:
            pierced.append(vestibule.build(front,c,0,d['street_door_height'],d['ground_opening'],0.,detail,d['entry_transom_base'],d['entry_transom_head']))
        else:
            pierced.append(shop(front,f'Ground shop {j+1}',x,d['shop_width_by_bay'][j],0,d['street_door_height']-.12,j==0,detail))
    for i,pair in enumerate(pairs):
        mid=mids[i]
        for j,x in enumerate(pair):
            pierced.append(trefoil_arch.model(front,f'Bay {i+3} window {j+1}',x,d['gable_window_sill'],d['rectangular_head'],
                                              d['apex_per_window'][i][j],d['second_widths'][2*i+j],0.,detail,d['glass_head']))
        for level,name in [(3,'third'),(4,'fourth')]:
            lights=d['surveyed_upper_windows'][name][2*i:2*i+2]
            pierced+=upper_storey(front,f'Bay {i+3} L{level}',lights,level,detail,d['third_hood_top'])
    base=box(east,0,west,d['parapet']-.11)
    wall=base.difference(unary_union(pierced))
    front.profile('Limewashed street wall',CHALK,wall,-.46,0)
    for k,axis in enumerate(edges):
        width=.26 if k in [0,3] else .38
        a=max(east,axis-width/2);b=min(west,axis+width/2)
        front.box('Street pilaster stone base',PLINTH,a,b,-.11,.104,.03,.31)
    piers(front,mids,edges,d,detail)
    upper_frieze(front,east,west,d['fourth'][0]-.56,detail)
    front.box('Under second-storey sill',FILLET,east,west,-.14,.16,d['gable_window_sill']-.11,d['gable_window_sill']-.027)
    for delta,over,thick in [(-.26,.095,.086),(-.16,.19,.056),(-.11,.14,.11)]:
        front.box('Flat roof cornice',LIMESTONE,east,west,d['back_of_cap'],over,d['parapet']+delta,d['parapet']+delta+thick)
    stone_finish.apply(builder)

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args();os.environ['JINLING_TRADE_BLENDER']=args.blender
    sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
