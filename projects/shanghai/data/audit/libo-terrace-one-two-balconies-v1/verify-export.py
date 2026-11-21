"""Check the adjoining homes, separate balcony decks, rail openings, plaques and raised roof division."""
from pathlib import Path
from math import cos, pi, sin
import argparse
import json
import runpy

HERE=Path(__file__).resolve().parent
trace=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']


def cases():
    """Independent points on the two balcony levels, rail ornaments, entrance openings and roof break."""
    out=[]
    def ray(name,origin,direction,material=None,distance=None,length=5):
        allowed=None if material is None else [material]
        out.append(dict(name=name,origin=list(origin),direction=list(direction),length=length,allowed=allowed,range_m=distance))
    def front(name,x,z,material,distance=None,length=5):
        ray(name,(x,-3,z),(0,1,0),material,distance,length)
    for side in (-1,1):
        cx=side*1.225
        for floor,opening_height in ((3.98,2.12),(7.23,2.28 if side<0 else 2.17)):
            label=f'{side:+}/{floor}'
            guard=.795
            for cell,(start,next_start) in enumerate(((0.,.450),(.450,.906))):
                left=cx-1+2*start
                repeat=2*(next_start-start)
                for u,v in ((.598,.25),(.594,.742)):
                    front(f'{label} square ornament {cell} at {v}',left+u*repeat,floor+.047+(1-v)*guard,
                          'Aged black iron',[2.435,2.46])
                ray(f'{label} lower wire of upper plaque frame {cell}',(left+.36*repeat,-.8,floor+.047+.63*guard),
                    (0,1,0),'Aged black iron',[.258,.270],.34)
                ray(f'{label} open iron field below rectangle {cell}',(left+.36*repeat,-.8,floor+.047+.574*guard),
                    (0,1,0),length=.34)
                for u in (.286,.896):
                    for vertical in (.459,.555):
                        front(f'{label} supporting vertical under and over panel {cell}/{u}/{vertical}',
                              left+u*repeat,floor+.047+vertical*guard,'Aged black iron',[2.446,2.477])
                front(f'{label} horizontal border around plaque {cell}',left+.41*repeat,
                      floor+.047+(1-.134)*guard,'Aged black iron',[2.45,2.48])
            for band,(start,end) in enumerate(((0.,.086),(.450,.541),(.906,1.))):
                for u,v in ((.72,.123),(.62,.606)):
                    lane_fraction=1-u if band==1 else u
                    x=cx-1+2*(start+(end-start)*lane_fraction)
                    z=floor+.047+(1-v+.096)*guard
                    front(f'{label} top of nested ornament, band {band}/{v}',x,z,'Aged black iron',[2.438,2.468])
            front(label+' outer post',cx-1,floor+.32,'Aged black iron',[2.43,2.47])
            front(label+' continuous handrail',cx+.42,floor+.88,'Weathered iron edges',[2.42,2.45])
            front(label+' stepped slab',cx,floor-.028,'Pale cement balcony edges',[2.44,2.47])
            ray(label+' upper face of slab',(cx+.56,-.31,floor+.22),(0,0,-1),'Pale cement balcony edges',[.204,.226])
            front(label+' revealed upper glass',cx+.19,floor+opening_height-.17,'Cool reflected window glass',[3.20,3.23])
            front(label+' transom rail',cx+.19,floor+opening_height-.39,'Grey green door frames',[3.03,3.08])
            crest=floor+opening_height+.038
            if floor<5:
                front(label+' awning in front of the moulding',cx+.30,crest,'Green awning cloth',[2.65,2.69])
                ray(label+' shoulder behind the awning',(cx+.30,-.17,crest),(0,1,0),
                    'Light rendered hood and door surround',[.12,.15],.31)
            else:
                front(label+' shoulder surround',cx+.30,crest,'Light rendered hood and door surround',[2.94,2.98])
        front(f'Upper projecting cornice of home {side}',cx+.20,7.23+(2.28 if side<0 else 2.17)+.09,
              'Light rendered hood and door surround',[2.80,2.82])
        front(f'Ground opening {side} to shaded door',cx+.09,1.32,'Umber entrance doors',[4.12,4.15])
        front(f'Outer ground arch {side}',cx,2.79,'Light rendered hood and door surround',[2.93,2.97])
        ray(f'Upper green fabric at {side}',(cx,-.27,6.55),(0,0,-1),'Green awning cloth',[.35,.45])
        ray(f'Metal pipe at outer wall {side}',(side*2.54,-1,3.10),(0,1,0),'Grey metal downpipes',[1.45,1.49],2)
    for floor in (3.98,7.23):
        ray(f'Separation between the slabs at {floor}',(0,-.80,floor-.10),(0,1,0),length=.66)
        front(f'Wall in the gap at {floor}',0,floor-.10,'Green grey roughcast',[2.987,3.01])
    front('Central rendered firewall above eave',0,10.08,'Green grey roughcast',[2.60,2.64])
    ray('Street-facing cap of the fire separation',(0,-.06,11.0),(0,0,-1),'Pale caps of fire separation',[.59,.68])
    return out

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('raw','full','lod','output'):
        parser.add_argument(key,type=Path)
    args=parser.parse_args()
    result={role:trace(getattr(args,role),cases())for role in ('raw','full','lod')}
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n')
    for role,row in result.items():
        print(role,len(row['cases']),[(v['name'],v['first_hit']) for v in row['cases']if not v['passed']],flush=True)
    raise SystemExit(not all(row['passed']for row in result.values()))
