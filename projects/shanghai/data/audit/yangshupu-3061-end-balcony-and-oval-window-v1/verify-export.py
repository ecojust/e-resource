"""Check window openings, brick courses, the outward-moving sash and roof against signed GLBs."""
import argparse
import json
import math
from pathlib import Path
import runpy
import numpy as np

HERE=Path(__file__).absolute().parent
SOURCE=HERE.parents[2]/'source/precise/yangpu-yangshupu-3061-end-balcony-and-oval-window/source'
D=json.loads((SOURCE/'dimensions.json').read_bytes())
INSPECT=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']
GLASS=['Blue green glass','Smoky old glass']


def cases():
    out=[];d=D
    def ray(name,origin,direction,materials,limits,length):
        out.append(dict(name=name,origin=list(map(float,origin)),direction=list(map(float,direction)),length=length,
                        allowed=materials if isinstance(materials,list)else [materials],range_m=limits))
    def straight(name,x,z,mat,lo,hi):
        ray(name,[x,-.16,z],[0,1,0],mat,[lo,hi],.6)
    def section(name,x,y,z,axis,normal,mat,limits,dist=.24):
        hit=np.array(axis)*x+np.array(y)
        ray(name,[*(hit+dist*np.array(normal)),z],[*-np.array(normal),0],mat,limits,.8)
    def pane_samples(center,bottom,width,height,ncol,nrow):
        stile=.036 if width>.50 else .022
        for i in range(ncol):
            for j in range(nrow):
                yield i,j,center-width/2+stile+(width-2*stile)*(i+.5)/ncol,bottom+stile+(height-2*stile)*(j+.5)/nrow
    case=.060;w=d['upper_width'];h=d['upper_height'];sill=d['upper_sill'];edge=case
    for index,(share,cols,nrows) in enumerate(zip((.260,.244,.231,.265),(4,3,2,4),(5,4,4,5))):
        leaf=(w-2*case)*share;cx=edge+leaf/2;edge+=leaf
        for part,bt,ht,rows in [('lower',sill+case,.76-case,3),('upper',sill+.805,h-case-.805,nrows)]:
            for i,j,x,z in pane_samples(cx,bt,leaf-.012,ht,cols,rows):
                straight(f'upper casement {index+1} {part} {i+1}/{j+1}',x,z,GLASS,.280,.295)
        straight(f'upper cross rail {index+1}',cx,sill+.780,'Red painted wood',.178,.205)
    for x in [.027,w-.027]:straight('full-frame edge '+str(x),x,sill+1.12,'Red painted wood',.17,.192)
    for index,pair in enumerate(d['ground_jamb_xy']):
        a,b=np.array(pair);w=np.linalg.norm(b-a);axis=(b-a)/w;norm=[axis[1],-axis[0]];center=(a+b)/2
        base=d['ground_sill'];h=d['ground_window_top']-base;course=base+h*.685;clear=w-.103
        for n,sgn in enumerate([-1,1]):
            cx=sgn*clear/4
            for label,bottom,height,nr in [('body',base+.05,course-base-.059,6),('transom',course+.223,base+h-.049-course-.223,1)]:
                for i,j,u,z in pane_samples(cx,bottom,clear/2-.009,height,2,nr):
                    section(f'ground {index+1} leaf {n+1} {label} {i+1}/{j+1}',u,center,z,axis,norm,GLASS,[.365,.385])
        section(f'ground {index+1} transom divider',0,center,course+.10,axis,norm,'Warm sill paint',[.19,.21])
        section(f'ground {index+1} pier',w/2+.073,center,base+h*.39,axis,norm,'Lane 3061 ivory limewash',[.22,.26])
    # Inspect both radial arches and straight jambs of the photographed side window.
    x=d['corner_x'];axis=d['oval_axis'];bottom=d['oval_bottom'];top=d['oval_top'];r=d['oval_width']/2;rise=d['oval_rise'];band=d['oval_brick_width']
    def end(name,y,z,mat,limits):
        ray(name,[x+.36,y,z],[-1,0,0],mat,limits,.8)
    for upper in [True,False]:
        center=top-rise if upper else bottom+rise
        for k in [12,31,56,78,103,131,154,169]:
            t=math.radians(k+(0 if upper else 180))
            end(('head'if upper else'foot')+' radial brick '+str(k),axis+(r-band*.52)*math.cos(t),center+(rise-band*.52)*math.sin(t),
                ['Rose facing brick','Weathered brick','Light lime pointing'],[.306,.343])
    n=max(6,round((top-bottom-2*rise)/.062))
    for k in range(1,n,2):
        z=bottom+rise+(k+.5)*(top-bottom-2*rise)/n
        for sign in [-1,1]:end(f'course {sign}/{k}',axis+sign*(r-band/2),z,['Rose facing brick','Weathered brick'],[.303,.324])
    end('blind red field in arched head',axis,top-band-.11,'Painted red infill',[.385,.415])
    end('blind red apron',axis,bottom+band+.255,'Painted red infill',[.385,.415])
    end('straight brown sill above rounded foot',axis,bottom+band+.154,'Warm glazing bead',[.336,.357])
    end('pale segment under painted apron',axis,bottom+band+.085,'Warm sill paint',[.381,.404])
    angle=math.radians(d['open_sash_degrees']);ww=2*(r-band)-.036;sw=np.array([math.sin(angle),math.cos(angle)])
    sn=np.array([sw[1],-sw[0]]);hinge=np.array([x-.016,axis-ww/2]);mid=hinge+sw*ww/2
    for i,j,u,z in pane_samples(0,d['side_glazed_base']+.017,ww,d['side_glazed_head']-d['side_glazed_base']-.034,2,3):
        section(f'projecting casement glass {i+1}/{j+1}',u,mid,z,sw,sn,GLASS,[.279,.296])
    for i in range(1,21,2):
        ax=d['rail_left']+(d['rail_right']-d['rail_left'])*i/21;c=(ax-d['rail_left'])/(d['rail_right']-d['rail_left']);y=-.39-.29*(1-(2*c-1)**2)
        ray('balcony picket '+str(i),[ax,y-.22,d['rail_base']+.45],[0,1,0],'Black balcony iron',[.199,.222],.5)
    for i,(x0,y0) in enumerate([(-.38,.37),(.46,.63),(2.59,.45),(2.76,.87),(3.34,1.64),(3.50,2.46),(2.54,2.65)]):
        top=d['eave']+d['roof_pitch']*min(y0+.19,d['corner_x']+.16-x0)
        ray('pitched tile '+str(i),[x0,y0,10.8],[0,0,-1],['Dark terracotta tile','Sunlit tile'],[10.8-top-.082,10.8-top+.01],4.)
    dormer_sill=d['eave']+d['roof_pitch']*(d['dormer_y']+.19)+.002
    roof_head=dormer_sill+d['dormer_glazed_height']
    for sign in (-1,0,1):
        ax=d['dormer_x']+sign*d['dormer_width']*.34
        ray('solid dormer lintel '+str(sign),[ax,d['dormer_y']-.16,roof_head+.16],[0,1,0],'Warm sill paint',[.152,.172],.38)
    return out


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('raw','full','lod','output'):p.add_argument(k,type=Path)
    q=p.parse_args();tests=cases();report={k:INSPECT(getattr(q,k),tests)for k in ('raw','full','lod')}
    q.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    assert all(v['passed']for v in report.values()),[(key,[c['name']for c in v['cases']if not c['passed']])for key,v in report.items()]
    print(len(tests),'casts per model')
