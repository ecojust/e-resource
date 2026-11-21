"""Independently measure the photographed plate and the recessed gaps in the exported mesh."""
from pathlib import Path
import json,runpy,argparse,math
HERE=Path(__file__).resolve().parent
inspect=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']
BLUE='Blue enamel field';BRASS='Raised warm brass';LIGHT='Polished edges';AGED='Recessed aged brass'
def measured_cases():
    cases=[]
    def add(n,o,d,length,allowed=None,span=None):
        cases.append(dict(name=n,origin=o,direction=d,length=length,allowed=allowed,range_m=span))
    for side in [-1,1]:
        cx=side*1.04
        for face in ('front','inner'):
            if face=='front':
                def start(u,z):return [cx+u,-.42,z]
                direction=[0,1,0]
            else:
                def start(u,z):return [cx-side*.42,-side*u,z]
                direction=[side,0,0]
            def cast(n,x,y,lo,hi,mats):
                u=(x-200)*.455/400;z=3.13+(200-y)*.455/400
                add(f'{side} {face} {n}',start(u,z),direction,.115,mats,[.1-hi,.1-lo])
            for n,x,y,lo,hi,mat in [
               ('lectern left upright',115,206,.0065,.009,[BRASS]),('lectern right upright',295,216,.0065,.009,[BRASS]),
               ('left plinth edge',129,259,.0085,.0105,[LIGHT]),('right upper slab',292,169,.009,.011,[LIGHT]),
               ('telescope pivot',183,129,.014,.016,[LIGHT]),('telescope tripod left leg',161.4,212,.0094,.0115,[BRASS]),
               ('hanging pan left',216,229,.010,.012,[LIGHT]),('hanging pan right',254,228,.010,.012,[LIGHT]),
               ('balance post',236.7,234,.009,.011,[BRASS]),('open book',176,285,.007,.009,[BRASS]),
               ('inner blue gap under telescope',169,211,.0013,.0023,[BLUE]),('blue gap between scales',226,212,.0013,.0023,[BLUE]),
               ('blue lower field',210,335,.0013,.0023,[BLUE]),('five pointed left star',74,291,.006,.008,[BRASS]),
               ('five pointed right star',329,294,.006,.008,[BRASS]),('sun hub',210,12,.013,.0165,[BRASS,LIGHT]),
               ('cast square border',398,201,.0045,.006,[BRASS])]:
                cast(n,x,y,lo,hi,mat)
        for z in [.48,1.45,2.20,2.74]:
            add(f'polished shaft {side} {z}',[cx,-.54,z],[0,1,0],.35,['Warm stone shaft'],[.219,.221])
        for dx in [-.11,0,.11]:
            add(f'projecting upper plaster {side} {dx}',[cx+dx,-.56,3.55],[0,1,0],.45,['Lime white mouldings'],[.10,.21])
            add(f'open between shafts {side} {dx}',[side*.49+dx,-.6,1.7],[0,1,0],.98)
    for x in [-2.00,-.42,.44,2.00]:
        for z in [1.25,2.25,3.08]:
            add(f'rear wall {x} {z}',[x,-.6,z],[0,1,0],1.38,['Soft white plaster'],[1.138,1.142])
        add(f'below wall cornice {x}',[x,-.60,.85],[0,1,0],1.4,[AGED],[1.083,1.095])
    for x in [-2.35,2.35]:add(f'beyond wall section {x}',[x,-.8,1.32],[0,1,0],2.0)
    return cases
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for key in ('raw','full','lod','output'):p.add_argument(key,type=Path)
    args=p.parse_args();expected=measured_cases()
    report={k:inspect(getattr(args,k),expected)for k in ('raw','full','lod')}
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=1)+'\n')
    for role,part in report.items():print(role,len(part['cases']),[(x['name'],x['first_hit'])for x in part['cases']if not x['passed']][:12],flush=True)
    raise SystemExit(not all(v['passed']for v in report.values()))
