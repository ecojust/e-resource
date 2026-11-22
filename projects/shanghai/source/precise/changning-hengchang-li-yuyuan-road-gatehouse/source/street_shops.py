"""The changing shop windows and fascia panels immediately east of the gate."""
import json
from pathlib import Path

from shapely.geometry import box
from exterior_sashes import paint

SURVEY = Path(__file__).resolve().parents[1] / 'measurements/registered-east-shopfronts.json'
PREFIX = 'Hengchang shop | '
COLORS = {
    'red': ((156, 51, 45), .75), 'black': ((47, 45, 45), .73),
    'silver': ((173, 173, 164), .59), 'pale': ((207, 202, 183), .76),
    'joint': ((82, 83, 76), .73), 'step': ((144, 138, 126), .87),
    'frame': ((90, 87, 78), .52), 'dark': ((51, 50, 47), .64),
    'brown': ((107, 66, 52), .72), 'blue grid': ((82, 101, 109), .67),
    'white': ((209, 206, 190), .79), 'roll': ((159, 159, 149), .67),
    'clear': ((118, 129, 122), .32), 'shade': ((80, 91, 87), .36),
    'amber': ((143, 114, 82), .46), 'metal': ((128, 128, 117), .57),
}
PALETTE = {PREFIX+k:paint(rgb,rough) for k,(rgb,rough) in COLORS.items()}


def _survey(layout):
    period = '2018' if str(layout.get('period','2022')).startswith('2018') else '2022'
    return json.loads(SURVEY.read_bytes())['periods'][period]


def storefront_openings(layout):
    return {'shop-'+r['id']:box(*r['bounds_xz']) for r in _survey(layout)['openings']}


def add_storefront(b,lod,layout):
    survey = _survey(layout)
    y = layout['front_y']['east']

    def rect(x0, z0, x1, z1, near, far, material, name):
        if x1 <= x0 or z1 <= z0:
            return
        b.prism(box(x0,z0,x1,z1),-far,-near,lambda x,z,d:(x,y-d,z),
                PREFIX+material,'Shop '+name)

    for i,(x0,z0,x1,z1,finish) in enumerate(survey['fascias'],1):
        name = 'fascia '+str(i)
        rect(x0,z0,x1,z1,-.135,-.018,finish,name)
        rect(x0,z0-.041,x1,z0+.012,-.166,-.02,'metal',name+' bottom rail')
        rect(x0,z1-.016,x1,z1+.015,-.151,-.018,'joint',name+' top rebate')
        if finish in ('silver','pale'):
            for j in range(1,max(1,round((x1-x0)/1.42))):
                x=x0+j*(x1-x0)/max(1,round((x1-x0)/1.42))
                rect(x-.007,z0+.018,x+.007,z1-.023,-.141,-.131,'joint',name+' cladding seam '+str(j))

    for r in survey['openings']:
        x0,z0,x1,z1=r['bounds_xz']
        width=x1-x0
        name=r['id']
        style=r['style']
        jamb=.056 if style not in ('wine','white-recess') else .094
        depth=.12 if style not in ('wine','white-recess','dark-door') else .245
        paint_frame={'wine':'brown','white-recess':'white','dark-door':'dark','amber-shop':'dark'}.get(style,'frame')
        rect(x0,z0,x1,z0+.091,-.10,depth+.08,'step',name+' sill and threshold')
        rect(x0,z0+.091,x0+jamb,z1,.005,depth+.055,paint_frame,name+' west reveal')
        rect(x1-jamb,z0+.091,x1,z1,.005,depth+.055,paint_frame,name+' east reveal')
        rect(x0+jamb,z1-.092,x1-jamb,z1,.005,depth+.055,paint_frame,name+' head reveal')
        xa,xb=x0+jamb,x1-jamb
        za,zb=z0+.091,z1-.092
        shutter = style in ('raised-shutter','closed-shutter')
        if shutter:
            foot=za if style=='closed-shutter' else zb-.48
            n=max(2,round((zb-foot)/(.11 if not lod else .21)))
            for i in range(n):
                lo=foot+(zb-foot)*i/n
                hi=foot+(zb-foot)*(i+1)/n
                rect(xa,lo,xb,hi,.056,.078,'roll' if i%2 else 'silver',name+' shutter slat '+str(i+1))
                if not lod:
                    rect(xa,lo,xb,lo+.010,.047,.056,'joint',name+' shutter bead '+str(i+1))
            zb=foot
            if zb<=za:
                continue
        divisions=[xa,*[x0+width*f for f in r['mullion_fractions']],xb]
        for j,(a,c) in enumerate(zip(divisions,divisions[1:])):
            light_a=a if j==0 else a+.024
            light_b=c if j==len(divisions)-2 else c-.024
            metal_grid=style=='white-recess' and j>=len(divisions)-3
            mat='amber' if style=='amber-shop' and j%2 else ('shade' if metal_grid or style in ('wine','dark-door') or j%3==0 else 'clear')
            rect(light_a,za,light_b,zb,depth+.023,depth+.039,mat,name+' light '+str(j+1))
            if j:
                rect(a-.024,za,a+.024,zb,depth-.032,depth+.023,paint_frame,name+' mullion '+str(j))
            if metal_grid:
                pitch=.24 if not lod else .32
                nx=max(2,round((light_b-light_a)/pitch))
                nz=max(2,round((zb-za)/pitch))
                for k in range(nx+1):
                    x=light_a+.016+(light_b-light_a-.032)*k/nx
                    rect(x-.014,za,x+.014,zb,depth-.072,depth-.043,'blue grid',name+f' screen {j} upright {k}')
                for k in range(nz+1):
                    z=za+.015+(zb-za-.030)*k/nz
                    rect(light_a,z-.012,light_b,z+.012,depth-.043,depth-.027,'blue grid',name+f' screen {j} cross rail {k}')
