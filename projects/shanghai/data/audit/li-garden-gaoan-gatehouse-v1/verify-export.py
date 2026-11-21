"""Check the exported street and garden elevations, open gates and vaulted passage in metres."""
import argparse
import json
import math
from pathlib import Path
import runpy

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
SOURCE=PROJECT/'source/precise/xuhui-li-garden-gaoan-gatehouse'
inspect=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']
arch_cases=runpy.run_path(HERE/'arch_rays.py')['arch_cases']

def cases():
    d=json.loads((SOURCE/'measurements/building-dimensions.json').read_bytes())['model_parameters_m']
    depth=d['tunnel_length'];half=d['half_width'];span=d['clear_width']/2
    sill=d['upper_sill'];w=d['upper_window_width'];window_top=sill+d['upper_window_height']
    spring=window_top-w/2;ridge=d['ridge'];eave=d['eave'];slope=(ridge-eave)/half
    scale=d['model_scale'];passage_half=d['passage_half_width']
    checks=[]
    def add(name,origin,direction,length,material=None,interval=None):
        checks.append(dict(name=name,origin=list(origin),direction=list(direction),length=length,
                           allowed=[material] if material else None,range_m=list(interval) if interval else None))

    for name,y,n in [('Street',0,-1),('Court',depth,1)]:
        checks.extend(arch_cases(y,n,name))
        def facade(description,x,z,surface,material,slop=.009):
            travel=.50-surface
            add(name+' / '+description,(x,y+n*.50,z),(0,-n,0),travel+slop+.012,material,(travel-slop,travel+slop))
        for side in (-1,1):
            facade('lower sash light '+str(side),side*w*.245,sill+.65,-.146,'Smoke blue window glass')
            facade('round head glass '+str(side),side*w*.18,spring+.23,-.146,'Smoke blue window glass')
        facade('meeting stile of paired lights',0,sill+.59,-.067,'Grey green steel window')
        facade('transom below fanlight',w*.25,spring,-.067,'Grey green steel window')
        facade('fine cement window surround',w/2+.031,sill+.73,.012,'Ivory moulded cement')
        facade('projecting sandstone sill',.19,sill-.046,.164,'Dressed grey sandstone')
        facade('square gable vent backing',0,ridge-.562,-.18,'Black green wrought iron')
        for side in (-1,1):
            x=side*half*.61
            facade('roughcast flank '+str(side),x,sill+.35,0,'Ivory roughcast stucco')
            facade('front of sloping coping '+str(side),x,ridge-abs(x)*slope-.031,.102,'Ivory moulded cement')
            x=side*(8+.54)*half/22
            facade('corbel in eaves band '+str(side),x,ridge-abs(x)*slope-.273,.0975,'Ivory moulded cement')
        if name == 'Street':
            # Cast onto the two white numerals, a green counter, the white rim, and a staggered key.
            for digit,x,z in [('6',3.055-.068-.040,3.02+.014-.007),('3',3.055+.061+.035,3.02+.014+.040)]:
                facade('white enamel numeral '+digit,x,z,.035,'White enamel lettering',.002)
            facade('green backing in the six',3.055-.068,3.02-.003,.030,'Green enamel number plate',.002)
            facade('narrow enamel outline',3.055,3.02+.124+.009-.002,.033,'White enamel lettering',.0018)
            for side in (-1,1):
                facade('keyed brick face '+str(side),side*(half-.64+.64/6),3.43,.025,'Deep red plinth brick',.003)
                facade('narrow joint between brick keys '+str(side),side*(half-.64+.64/3),3.43,0,'Ivory roughcast stucco',.005)
        for x,z in [(0,.32),(-1.38,1.12),(1.38,1.12),(-.90,2.85),(.90,2.85),(0,3.33)]:
            add(name+f' / clear through passage {x} {z}',(x,y+n*.48,z),(0,-n,0),depth+.96)

    for side in (-1,1):
        for label,end,normal in [('street',0.,-1.),('courtyard',depth,1.)]:
            ray_length=abs(depth*.50-end)-d['wall_thickness']-.0275
            z=(7.5/15)*d['spring']
            add(f'Passage / {label} jamb from opposite half {side}',(side*(span+.16),depth*.5,z),(0,normal,0),ray_length+.04,
                'Deep red plinth brick',(ray_length-.012,ray_length+.012))
        for fraction in (.36,.69):
            y=depth*fraction
            add(f'Outside wall {side} {fraction}',(side*(half+.55),y,eave*.67),(-side,0,0),.64,
                'Ivory roughcast stucco',(.543,.557))
        for label,z,surface,mat in [('plaster',1.64,passage_half,'Warm lime plaster'),
                                    ('plinth course',.099+3*.083,passage_half-.025,'Deep red plinth brick'),
                                    ('plinth joint',.099+3.5*.083,passage_half-.0065,'Grey lime joints')]:
            start=passage_half-.42
            add(f'Passage {side} / {label}',(side*start,depth*.59,z),(side,0,0),.49,
                mat,(surface-start-.007,surface-start+.007))
        add('Return / green downpipe '+str(side),(side*(half+.45),.12,2.),(-side,0,0),.51,
            'Green rainwater fittings',(.354,.390))
        # Two stiles and an intermediate horizontal rail in each open gate.
        angle=math.radians(82)
        tangent=(-side*math.cos(angle),math.sin(angle))
        inward=(-side*math.sin(angle),-math.cos(angle))
        L=span-.065
        for label,t,z,mat,l in [('hinge',.031,1.82,'Black green wrought iron',.30),
                                ('latch',L-.031,1.81,'Black green wrought iron',.30),
                                ('middle rail',L*.56,.90,'Black green wrought iron',.30),
                                ('opening between pickets',.115+(L-.23)*4.5/10,1.25,None,.46)]:
            x=side*(span-.045)+t*tangent[0];y=.35+t*tangent[1]
            add(f'Leaf {side} / {label}',(x+inward[0]*.23,y+inward[1]*.23,z),(-inward[0],-inward[1],0),
                l if mat else .29,mat,(.18,.21) if mat else None)

    for x in (-1.1,1.1):
        for frac in (.20,.50,.80):
            add(f'Passage / recessed fitting {x} {frac}',(x,depth*frac,3.36),(0,0,1),.40,'Recessed light',(.343,.357))
    for frac in (.27,.55,.73):
        add('Passage / ceiling '+str(frac),(0,depth*frac,3.36),(0,0,1),.40,'Light passage ceiling',(.346,.364))
    for row in (2,5,8):
        y=row*.72+.23;x=(row%2)*.31+.27
        material='Weathered paving' if (row*3)%7==0 else 'Charcoal paving'
        add('Paving / slab '+str(row),(x,y,.33),(0,0,-1),.32,material,(.265,.279))
        x=(row%2)*.31
        add('Paving / recessed joint '+str(row),(x,y,.33),(0,0,-1),.32,'Grey lime joints',(.284,.296))

    lo=.075;hi=depth-.075;n=round((hi-lo)/.185);step=(hi-lo)/n
    for side in (-1,1):
        for i in (5,n//2,n-7):
            x=side*half*.58;y=lo+(i+.5)*step
            top=ridge-abs(x)*slope
            add(f'Roof {side} / cover crest {i}',(x,y,top+.32),(0,0,-1),.48,'Russet clay cover tile',(.398,.420))
            add(f'Roof {side} / tile channel {i}',(x,y+step*.49,top+.32),(0,0,-1),.51,'Weathered clay roof',(.449,.469))
        add('Roof / side gutter '+str(side),(side*(half+.14),depth*.42,eave+.2),(0,0,-1),.52,
            'Green rainwater fittings',(.374,.409))
    for frac in (.18,.53,.83):
        add('Roof / rounded ridge '+str(frac),(0,depth*frac,ridge+.24),(0,0,-1),.39,'Russet clay cover tile',(.251,.275))
    assert len({p['name']for p in checks})==len(checks)
    for item in checks:
        item['origin']=[x*scale for x in item['origin']]
        item['length']*=scale
        if item['range_m']:
            item['range_m']=[x*scale for x in item['range_m']]
    return checks

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for role in ('raw','full','lod','output'):
        p.add_argument(role,type=Path)
    args=p.parse_args();tests=cases()
    result={role:inspect(getattr(args,role),tests) for role in ('raw','full','lod')}
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n')
    for name,r in result.items():
        failures=[(v['name'],v['first_hit']) for v in r['cases'] if not v['passed']]
        print(name,len(tests),'failures',len(failures),failures,flush=True)
    return 0 if all(row['passed'] for row in result.values()) else 1

if __name__=='__main__':
    raise SystemExit(main())
