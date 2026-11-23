"""The two pale knees on the brick front and the blue-grey downpipe beside the 9 plaque."""
import json
from pathlib import Path

from garden_fabric import METAL, paint

PALE='Hongji 8 | weathered pale downpipe'
BLUE='Hongji 9 | blue grey rainwater pipe'
PALETTE={PALE:paint((164,153,128),.76,.09),BLUE:paint((75,98,102),.70,.14)}
DATA=Path(__file__).resolve().parents[1]/'measurements/lawn-front-rainwater-pipes.json'


def add_downpipes(b,number,lod,layout):
    b.palette.update(PALETTE)
    survey=json.loads(DATA.read_bytes())
    names=('eight_left','eight_right') if number==8 else ('nine_south',)
    for name in names:
        x,y=survey[name]['vertical_axis_xy']
        r=.053 if number==9 else .045
        material=BLUE if number==9 else PALE
        n=8 if lod else 14
        e=layout['eave_z']
        if number==8:
            left=name.endswith('left')
            outer=-layout['overhang'] if left else layout['wall_width']+layout['overhang']
            sign=-1 if left else 1
            path=[(x,y-.12,.099),(x,y,.185),(x,y,4.61),
                  (x+sign*.035,y-.05,4.69),(outer,y-.39,5.21),
                  (outer,y-.43,e-.107)]
        else:
            path=[(x,y-.12,.095),(x,y,.19),(x,y,5.02),
                  (x-.025,y-.025,5.13),(x-.10,-.355,5.39),(x-.10,-.408,5.485)]
        tag=f'{number} | '+name.replace('_',' ')+' downpipe '
        b.tube(path,r,material,n,tag+'bent barrel')
        for j,z in enumerate((.52,2.29,4.53),1):
            b.lathe((x,y),[(z-.019,r+.007),(z+.019,r+.007)],material,n,tag+'socket '+str(j))
            if not lod:
                end=.022 if number==8 else .282
                b.tube([(x,y+.022,z),(x,end,z)],.017,METAL,6,tag+'wall pin '+str(j))
