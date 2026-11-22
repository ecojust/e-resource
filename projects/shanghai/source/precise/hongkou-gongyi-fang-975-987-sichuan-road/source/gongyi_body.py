"""End walls, rear envelope and the envelope under the restored roof."""
import json
from pathlib import Path
from shapely.geometry import box
from shapely.ops import unary_union
from gongyi_materials import BRICK, STONE, TRIM, SOUTH_RECESS


def south_return(b,depth,roof):
    src=Path(__file__).resolve().parents[1]/'measurements/south-short-wall-window-observations.json'
    windows=json.loads(src.read_bytes())['openings']
    def mapping(s,z,d):
        return d,s,z
    mouths=[]
    for w in windows:
        lo=w['s']-w['width']/2;hi=w['s']+w['width']/2;top=w['top_z'];bottom=top-w['height']
        opening=box(lo,bottom,hi,top);mouths.append(opening)
        trim=box(lo-.065,bottom-.075,hi+.065,top+.075).difference(opening)
        b.prism(trim,-.049,.011,mapping,TRIM,w['id']+' margin')
        inner=box(lo+.045,bottom+.045,hi-.045,top-.045)
        b.prism(opening.difference(inner),.135,.203,mapping,TRIM,w['id']+' inner return')
        b.prism(inner,.215,.239,mapping,SOUTH_RECESS,w['id']+' recessed face')
        b.prism(box(lo-.09,top+.065,hi+.09,top+.138),-.12,.018,mapping,TRIM,w['id']+' projecting hood')
        b.prism(box(lo-.06,bottom-.067,hi+.06,bottom-.013),-.085,.022,mapping,STONE,w['id']+' sill')
    skin=box(0,0,depth,roof-.15).difference(unary_union(mouths))
    b.prism(skin,0,.28,mapping,BRICK,'South | retained wall and seven documented openings')
    for s in (4.65,9.6):
        b.prism(box(s-.20,4.54,s+.20,8.47),-.037,.012,mapping,TRIM,'South | lower-storey dressings')
    for lo,hi in [(0,.32),(depth-.27,depth)]:
        b.prism(box(lo,.16,hi,roof-.12),-.042,.012,mapping,TRIM,'South | end dressing')


def add_body(b,layout):
    length=layout['bay_edges'][-1];depth=layout['rear_depth'];roof=layout['street_cornice_z']
    b.plan_prism(box(0,0,length,depth),-.07,0,STONE,'Base | retained street block')
    b.box((length*.5,depth-.15,(roof-.18)*.5),(length,.30,roof-.18),STONE,label='West | rear envelope')
    for north in [False,True]:
        x=length-.14 if north else .14
        which='North' if north else 'South'
        if north:
            b.box((x,depth*.5,(roof-.15)*.5),(.28,depth,roof-.15),BRICK,label=which+' | brick end')
        else:
            south_return(b,depth,roof)
        outside=length+.016 if north else -.016
        # The northern return is visible beside No. 2 in the architect's
        # evening photograph. Its horizontal dressings run past the balcony.
        for i,z in enumerate(layout['balcony_z'],1):
            b.box((outside,depth*.5,z-.08),(.12,depth,.31),STONE,label=which+' | dressing '+str(i))
        b.box((outside,depth*.5,roof-.11),(.13,depth,.19),TRIM,label=which+' | cap')
        b.box((outside,depth*.5,.23),(.072,depth,.43),STONE,label=which+' | lower base')
