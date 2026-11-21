"""Inspect eight street arches, two six-window central bays, visible southwest return and tiled roof in signed GLBs."""
import argparse
import json
import math
import runpy
from pathlib import Path
import numpy as np
HERE=Path(__file__).absolute().parent
SOURCE=HERE.parents[2]/'source/precise/hongkou-huoshan-119-121-arcaded-front/source'
D=json.loads((SOURCE/'dimensions.json').read_bytes())
INSPECT=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']
U,V=D['tangent_enu'];ROT=np.array([[U,-V],[V,U]])


def cases():
    out=[];d=D
    def test(name,x,y,z,direction,mat,interval,maximum):
        pt=ROT@[x-d['cornice_width']/2,y];vec=ROT@direction[:2]
        out.append(dict(name=name,origin=[*pt,z],direction=[*vec,direction[2]],length=maximum,allowed=[mat]if isinstance(mat,str)else mat,range_m=interval))
    def front(name,x,z,mat,a,b):test(name,x,-2.3,z,[0,1,0],mat,[a,b],4.)
    def down(name,x,y,height,mat,err=.10):test(name,x,y,18.,[0,0,-1],mat,[18.-height-err,18.-height+err],17.)
    glass=['Smoky grey-blue glazing','Blue-grey reflected light']
    for idx,x in enumerate(d['gallery_axes']):
        for lev in ['middle','upper']:
            layer=d['gallery_levels'][lev];spring=layer['spring'];sill=layer['sill'];rise=layer['rise'];rx=d['gallery_span']/2
            name=f'{lev} street arch {idx+1}'
            mid=.5*(sill+layer['apron_bottom'])
            front(name+' pale apron',x,mid,'Cream painted apron',2.446,2.475)
            front(name+' stone sill',x,sill-.035,'Grey stone trim',2.355,2.405)
            for angle in [28.,56.,118.,150.]:
                t=math.radians(angle)
                front(name+' radial brick '+str(angle),x+(rx+.094)*math.cos(t),spring+(rise+.094)*math.sin(t),['Dull red facing brick','Burnt red brick','Arch joint mortar'],2.15,2.219)
            front(name+' crown keystone',x,spring+rise+.132,'Grey stone trim',2.115,2.155)
            if lev=='upper':
                hs=[sill+.061,sill+(spring-.067-sill)*.73,spring-.122]
                for side in (-1,1):
                    for j,(lo,hi) in enumerate(zip(hs,hs[1:])):
                        front(name+f' pane {j},{side}',x+side*.247,(lo+hi)/2,glass,2.539,2.56)
                fan='Red-brown upper fan panel' if idx<2 else 'Smoky grey-blue glazing'
                front(name+' upper fan panel',x+.343,spring+.247,fan,2.484,2.51)
            else:
                top=spring-.295
                width=d['gallery_span']*.89
                edges=[sill+.061,*[sill+(top-sill)*k for k in (.25,.5,.75)],top-.055]
                for c in range(4):
                    px=x-width/2+.059+(width-2*.059)*(c+.5)/4
                    for j,(lo,hi) in enumerate(zip(edges,edges[1:])):
                        front(name+f' lower pane {c},{j}',px,(lo+hi)/2,glass,2.535,2.561)
                for c in range(5):
                    w=d['gallery_span']-.065
                    px=x-w/2+.059+(w-.118)*(c+.5)/5
                    front(name+' transom light '+str(c),px,(top+spring-.067)/2,glass,2.536,2.564)
                front(name+' open radial light',x+.343,spring+.245,'Smoky grey-blue glazing',2.484,2.510)
        for side in(-1,1):
            for z in(4.44,8.94):
                if side==(-1 if idx%2==0 else 1):
                    front(f'Outer brick jamb {idx},{z}',x+side*(d['gallery_span']/2+.059),z,['Dull red facing brick','Burnt red brick','Huoshan variegated grey brickwork'],2.152,2.31)
    for aa,bb in zip(d['gallery_axes'][::2],d['gallery_axes'][1::2]):
        x=(aa+bb)/2
        for v in d['gallery_levels'].values():
            front('Cream centre post '+str((aa,v['sill'])),x,v['sill']+.39,'Cream painted apron',2.346,2.376)
            front('Pair springing capital '+str((aa,v['sill'])),x,v['spring']-.005,'Dull red facing brick',2.142,2.179)
    for i,x in enumerate(d['square_axes']):
        for lev,(sill,head)in d['square_levels'].items():
            for side in(-1,1):
                for frac in(.28,.85):
                    front(f'Centre {i} {lev} {side} {frac}',x+side*.244,sill+(head-sill)*frac,glass,2.281,2.308)
            front(f'Centre {i} {lev} sill',x,sill-.059,'Grey stone trim',1.973,2.027)
            front(f'Centre {i} {lev} splayed head',x,head+.128,['Burnt red brick','Dull red facing brick','Arch joint mortar'],1.995,2.060)
    for x in [1.01,1.53,4.75,11.28,14.59,15.19]:
        for y in(.19,.47):
            z=d['cornice_z']+.115+3.22*(y+.11)/(d['section_depth']+.11)
            down(f'Front roof tile {x},{y}',x,y,z+.052,['Dark rust clay tile','Muted clay tile','Dark roof edge'])
    for i,x in enumerate(d['dormer_axes']):
        for offset in(-.29,.29):
            front(f'Dormer {i} glass {offset}',x+offset,13.02,glass,3.24,3.27)
        down(f'Dormer {i} central clipped roof',x,.89,d['dormer_z'],'Dark roof edge',.036)
    center=d['middle_axis']
    for x in [d['middle_left']+.16,center,d['middle_right']-.22]:
        front('Raised central parapet masonry '+str(x),x,14.46,['Huoshan variegated grey brickwork','Burnt red brick'],1.967,2.145)
    for y in(.92,1.42):
        test('Southwest return glass '+str(y),-1.55,y,8.48,[1,0,0],glass,[1.78,1.819],3.2)
    return out

if __name__=='__main__':
    pa=argparse.ArgumentParser()
    for k in ('raw','full','lod','out'):pa.add_argument(k,type=Path)
    args=pa.parse_args();report={k:INSPECT(getattr(args,k),cases())for k in ('raw','full','lod')}
    args.out.write_text(json.dumps(report,ensure_ascii=False,separators=(',',':'))+'\n')
    for k,v in report.items():print(k,len(v['cases']),[(n['name'],n['first_hit'])for n in v['cases']if not n['passed']][:24])
    raise SystemExit(int(not all(v['passed']for v in report.values())))
