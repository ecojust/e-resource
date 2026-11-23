"""The limestone-coloured entrance porch on the north side of house nine's lawn gable."""
import json
from pathlib import Path

from shapely.geometry import Polygon, box
from garden_fabric import BRASS, GLASS, JOINT, LEDGE, METAL, STONE, TREAD, WOOD, block, face

SURVEY = Path(__file__).parent.parent / 'measurements/nine-entrance-portico.json'


def dimensions():
    return json.loads(SURVEY.read_bytes())['fitted']


def rear_wall_opening():
    d = dimensions()
    z = d['door_head_z']
    return box(d['door_left_x'] - .115, -.01,
               d['door_left_x'] + d['door_width'] + .115, z + .59)


def add_portico(b, lod, layout):
    d = dimensions()
    left, right = d['left_post_outer_x'], d['right_post_outer_x']
    wide, y = d['post_width'], d['front_y']
    stone_top, fascia, base = d['capital_z'], d['terrace_cornice_z'], d['balcony_plinth_z']
    hand = d['top_rail_z']
    back = d['door_plane_y']
    door_l, door_w = d['door_left_x'], d['door_width']
    head = d['door_head_z']

    def stone(name, x0, x1, y0, y1, z0, z1, material=STONE):
        block(b, x0, x1, y0, y1, z0, z1, material, '9 | porch '+name)

    stone('one-step landing', left-.30, right+.30, y-.42, back+.15, -.01, .055, TREAD)
    for side, x in [('left', left), ('right', right-wide)]:
        stone(side+' square shaft', x, x+wide, y, y+wide, .055, stone_top-.145)
        stone(side+' stone foot', x-.014, x+wide+.014, y-.014, y+wide+.014, .055, .155, LEDGE)
        for band, lo, hi, lip in [('neck',-.15,-.095,.022),('capital fillet',-.095,-.072,.042),
                                   ('capital band',-.072,-.021,.057),('abacus',-.021,.015,.076)]:
            stone(side+' '+band, x-lip, x+wide+lip, y-lip, y+wide+lip, stone_top+lo, stone_top+hi, LEDGE)
    for level, low, high, projection, material in [
            ('front lintel',stone_top,fascia-.38,.012,STONE),
            ('drip course',fascia-.38,fascia-.325,.060,LEDGE),
            ('recessed bed',fascia-.325,fascia-.275,.038,JOINT),
            ('upper fascia',fascia-.275,fascia-.085,.098,STONE),
            ('terrace lip',fascia-.085,fascia,.20,LEDGE)]:
        stone(level,left-projection,right+projection,y-projection,y+wide+.028,low,high,material)
        if level=='terrace lip':
            stone('terrace slab',left-.10,right+.10,y+wide+.028,back+.15,low,high,TREAD)
        else:
            # The two side fasciae return to the rear wall. Together with the
            # front band they leave the underside of the porch open.
            for side,x in [('left',left),('right',right-wide)]:
                stone(side+' return '+level,x-projection,x+wide+projection,
                      y+wide+.028,back+.15,low,high,material)
    stone('parapet plinth',left-.12,right+.12,y-.052,y+.23,fascia,base,JOINT)
    stone('parapet coping',left-.115,right+.115,y-.067,y+.245,base-.03,base+.025,LEDGE)
    mid=(left+right)/2; panel=d['centre_panel_width']
    pl,pr = mid-panel/2,mid+panel/2
    stone('solid centre tablet',pl,pr,y+.02,y+.19,base+.015,hand-.044,STONE)
    # Recessed face has mitred lower corners in the 2015 original.
    px=.102; l,r=pl+px,pr-px;lo=base+.094;hi=hand-.129;t=.044
    outline=Polygon([(l+t,lo),(r-t,lo),(r,lo+t),(r,hi),(l,hi),(l,lo+t)])
    face(b,outline.difference(outline.buffer(-.026,join_style=2)),y-.009,y+.025,LEDGE,
         '9 | porch chamfered tablet border')
    stone('front handrail',left-.09,right+.09,y-.026,y+.165,hand-.065,hand,LEDGE)
    for side,a,c in [('left',left-.075,pl),('right',pr,right+.075)]:
        for i in range(5):
            x=a+(c-a)*(.08+.84*i/4)
            stone(side+' front iron baluster',x-.019,x+.019,y+.048,y+.087,base+.020,hand-.031,METAL)
    for side,x in [('left',left-.052),('right',right+.052)]:
        stone(side+' side parapet base',x-.075,x+.075,y+.21,back-.03,fascia,base,JOINT)
        stone(side+' returning handrail',x-.065,x+.065,y+.12,back-.045,hand-.063,hand,LEDGE)
        count=8 if not lod else 6
        for i in range(count):
            pos=y+.31+(back-y-.46)*i/(count-1)
            stone(side+' side iron baluster',x-.019,x+.019,pos-.018,pos+.018,base,hand-.035,METAL)

    outer=rear_wall_opening();left_jamb,_,right_jamb,transom_head=outer.bounds
    for name,strip in [('left jamb',box(left_jamb,.05,door_l,transom_head)),
                       ('right jamb',box(door_l+door_w,.05,right_jamb,transom_head)),
                       ('transom head',box(door_l,transom_head-.085,door_l+door_w,transom_head))]:
        face(b,strip,back+.032,back+.157,WOOD,'9 | entrance '+name)
    face(b,box(door_l,head,door_l+door_w,head+.112),back+.056,back+.147,WOOD,
         '9 | entrance transom bar')
    face(b,box(door_l,head+.112,door_l+door_w,transom_head-.075),back+.18,back+.202,
         GLASS,'9 | entrance single dark overlight')
    half=door_w/2
    for leaf in range(2):
        x=door_l+leaf*half+.006;end=x+half-.012
        holes=[]
        for col in range(2):
            l=x+.075+col*(half-.13)/2;r=x+.075+(col+1)*(half-.13)/2-.035
            for row in range(4):
                bot=.18+row*(head-.245)/4;top=bot+(head-.245)/4-.051
                aperture=box(l,bot,r,top);holes.append(aperture)
                face(b,aperture,back+.16,back+.177,GLASS,'9 | door recessed pane')
        wood=box(x,.055,end,head)
        for aperture in holes:wood=wood.difference(aperture)
        face(b,wood,back+.068,back+.145,WOOD,'9 | door four-by-two leaf '+str(leaf+1))
        handle=end-.052 if leaf==0 else x+.052
        for z in (.92,1.21):
            stone('pull fixing',handle-.022,handle+.022,back-.035,back+.073,z-.023,z+.023,BRASS)
        stone('pull handle',handle-.017,handle+.017,back-.046,back-.018,.913,1.225,BRASS)


def porch_lighting(b,lod):
    from math import cos, pi, sin
    survey=json.loads((SURVEY.parent/'nine-porch-lamps.json').read_bytes())
    back=dimensions()['door_plane_y']
    for j,(x,y,z) in enumerate(survey['front_sconce_centres_xyz'],1):
        name='9 | door lantern '+str(j)
        block(b,x-.052,x+.052,back-.019,back+.009,z-.11,z+.095,METAL,name+' wall plate')
        b.tube([(x,back-.01,z+.057),(x,y+.025,z+.112),(x,y,z+.111)],.018,METAL,6,name+' bracket')
        b.lathe((x,y),[(z-.14,.044),(z-.106,.063),(z+.070,.100)],GLASS,6,name+' lantern glass')
        b.lathe((x,y),[(z+.064,.115),(z+.096,.119),(z+.151,.072),(z+.166,.037)],
                METAL,6,name+' faceted hood')
        b.lathe((x,y),[(z+.164,.029),(z+.226,.011),(z+.235,.004)],
                METAL,6,name+' upper finial')
        b.lathe((x,y),[(z-.204,.009),(z-.153,.043),(z-.133,.057)],METAL,6,name+' base finial')
        for i in range(6):
            a=i*pi/3
            b.tube([(x+.063*cos(a),y+.063*sin(a),z-.106),
                    (x+.101*cos(a),y+.101*sin(a),z+.071)],.0057,METAL,5 if lod else 7,name+' glass rib')
    x,y,z=survey['ceiling_bowl']['visible_centre_xyz']
    b.lathe((x,y),[(z-.057,.016),(z-.049,.071),(z-.023,.122),(z+.008,.160),(z+.036,.1775)],
            WOOD,12 if lod else 28,'9 | suspended bowl opal glass')
    b.lathe((x,y),[(z+.036,.178),(z+.052,.181),(z+.065,.079)],METAL,12 if lod else 26,
            '9 | bowl metal rim')
    b.tube([(x,y,z+.064),(x,y,dimensions()['terrace_cornice_z']-.084)],.012,METAL,6,
           '9 | bowl suspension')
