"""Read the serialized mesh and probe its brick cadence, steel grid, cornice, roof and fittings."""
import argparse
import json
import math
from pathlib import Path
import runpy

HERE=Path(__file__).absolute().parent
SOURCE=HERE.parents[2]/'source/precise/changning-yiding-village-roof-pavilion'
D=json.loads((SOURCE/'source/dimensions.json').read_bytes())
measures=SOURCE/'measurements'
CORNICE=json.loads((measures/'double-cornice-rhythm.json').read_bytes())['front_rows']
WINDOW=json.loads((measures/'steel-window-pattern.json').read_bytes())['columns']
INSPECT=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']

def cases():
    all_tests=[]
    def ray(name,origin,direction,length,mat,span):
        all_tests.append(dict(name=name,origin=origin,direction=direction,length=length,allowed=mat,range_m=span))
    def front(name,x,z,mat,span):
        ray(name,[x,-.15,z],[0,1,0],.65,mat,span)
    def side(name,y,z,mat,span):
        ray(name,[.8,y,z],[-1,0,0],1.5,mat,span)
    h=D['roof_level'];band=D['cornice_height']
    for i,(r,z)in enumerate(zip(CORNICE,[h-band*.16,h-band*.81])):
        centres=r['visible_pale_centres_m']
        for j,x in enumerate(centres):
            front(f'front band {i+1} pale face {j+1}',x,z,['Pale inset in red band'],[.126,.128])
        for j,(a,b)in enumerate(zip(centres,centres[1:])):
            front(f'front band {i+1} red interval {j+1}',(a+b)/2,z,['Muted red cornice tile'],[.129,.133])
    width=D['front_window_width'];left=D['front_window_left'];top=1.55
    for j,r in enumerate(WINDOW):
        x0=left+width*r['left_frac'];x1=left+width*r['right_frac'];x=(x0+x1)/2
        zvals=sorted(top*(1-f) for f in r['rail_fractions_from_top'])
        for k,z in enumerate(zvals):
            front(f'light {j+1} staggered rail {k+1}',x,z,['Aged steel glazing bars'],[.213,.217])
        for k,(lo,hi)in enumerate(zip([.04,*zvals],[*zvals,top-.065])):
            z=(lo+hi)/2
            front(f'light {j+1} pane {k+1}',x,z,['Cream reflected glass','Light behind pale glass'],[.261,.267])
            front(f'light {j+1} upright {k+1}',x0,z,['Aged steel glazing bars'],[.212,.216])
    for j,z in enumerate([.13,.39,.76,1.24,1.44]):
        front(f'front pale jamb {j+1}',left-.044,z,['Buff stone window surround'],[.116,.120])
    for j,x in enumerate([left+.07,left+.53,left+.88]):
        front(f'front sill {j+1}',x,-.061,['Buff stone window surround'],[.058,.062])
    for j,y in enumerate([.42,1.90,3.70,5.42,6.57]):
        side(f'return separating band {j+1}',y,h-.47*band,['Pale projecting ledge'],[.751,.755])
    for j,z in enumerate([.30,.82,1.21]):
        side(f'return round pipe {j+1}',.52,z,['Ivory painted pipe'],[.686,.693])
    side('outdoor condenser case',2.31,1.46,['Faded condenser case'],[.303,.309])
    side('condenser central hub',2.85,1.28,['Faded condenser case'],[.252,.258])
    side('condenser round guard',2.85,1.28+.235,['Weathered fan ring'],[.262,.268])
    near=D['return_window_near'];far=D['return_window_far'];middle=(near+far)/2
    for j,(a,b,angle)in enumerate([(near+.041,middle-.012,.28),(middle+.012,far-.041,-.17)]):
        for k,t in enumerate([.27,.51,.73]):
            dist=(b-a)*t if j==0 else (b-a)*(1-t)
            y=a+dist*math.cos(angle) if j==0 else b-dist*math.cos(angle)
            surface=-.072+dist*abs(math.sin(angle))-.014/math.cos(angle)
            side(f'return glazed casement {j+1}/{k+1}',y, .96,['Dusty side glazing'],[.8-surface-.009,.8-surface+.009])
    for j,x in enumerate([-.78,-2.46,-4.52]):
        for k,y in enumerate([.65,2.31,4.22,6.42]):
            ray(f'pavilion roof {j+1}/{k+1}',[x,y,h+.20],[0,0,-1],.5,['Muted flat roof'],[.192,.196])
    for j,x in enumerate([.26,1.02,1.74,2.39,3.04]):
        for k,y in enumerate([.63,1.48,2.21,3.22,4.34]):
            z=-.22+.329*(y-.28)
            ray(f'adjoining clay tiles {j+1}/{k+1}',[x,y,z+.18],[0,0,-1],.36,
                ['Weathered terracotta pan','Rose clay pan','Dark tile bed'],[.140,.182])
    return all_tests

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ['raw','full','lod','output']:parser.add_argument(key,type=Path)
    args=parser.parse_args();probes=cases()
    out={k:INSPECT(getattr(args,k),probes)for k in ['raw','full','lod']}
    args.output.write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n')
    assert all(v['passed'] for v in out.values()),{k:[p['name']for p in v['cases']if not p['passed']]for k,v in out.items()}
    print(len(probes),'physical checks per serialized mesh')
