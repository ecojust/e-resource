"""Probe the five casement axes, Dutch canopy surfaces, gate, two spiral lanterns and the numbered facade."""
from pathlib import Path
import argparse,json,math,runpy
import numpy as np
from shapely.geometry import Polygon

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]/'source/precise/hongkou-yonganli-duolun-174-awning-front/source'
P=json.loads((SOURCE/'dimensions.json').read_bytes())
inspect=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']
angle=math.radians(P['yaw_enu_deg']);rot=np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]])
IRON='Painted ironwork';STONE='Dressed grey sill';WARM='Reflected pale window';GLASS='Cool shopfront glass';SASH='Oxblood timber casements'


def cases():
    out=[]
    def probe(name,xy,z,d,length,mat=None,r=None):
        pos=rot@xy;direction=rot@d
        out.append(dict(name=name,origin=[*pos,z],direction=[*direction,0.],length=length,allowed=[mat] if isinstance(mat,str) else mat,range_m=r))
    def front(name,u,z,mat,iv,length=2.22):
        probe(name,[-1.4,-u],z,[1.,0.],length,mat,iv)
    for n in (2,3):
        sill=P['sill_second'] if n==2 else P['third_sill']
        sh=P['second_sash_height'] if n==2 else P['third_sash_height']
        for idx,u in enumerate(P['sash_centres_u']):
            centre=idx==2;sw=P['central_sash_width'] if centre else P['ordinary_sash_width']
            width=P['central_hood_width'] if centre else P['ordinary_hood_width'];bands=19 if centre else 12
            reach=.84 if centre else .68;rise=.62 if centre else .52
            tag=f'Floor {n}, sash axis {idx+1}'
            for i in (bands//2-2,bands//2,bands//2+2):
                for color,offset in [('Pale woven stripe',.5),('Weathered grey canvas',.80)]:
                    frac=(i+offset)/bands-.5
                    cap=max(0.,(abs(2*frac)-.62)/.38);taper=math.sqrt(max(.026,1-cap*cap))
                    for t in (.64,1.02):
                        z=sill+sh-.135+rise*math.cos(t)*taper-.028*cap
                        dist=1.4-(.061+reach*math.sin(t)*taper)
                        front(f'{tag}, canopy gore {i}:{offset}:{t}',u+frac*width,z,color,[dist-.010,dist+.024])
            # Closed sash: sample both pane lights below the cloth and a joinery rail.
            inner=(sw-.138)/2;x=u+inner*.58
            front(tag+' closed lower pane',x,sill+.36,WARM if centre and n==2 else GLASS,[1.565,1.571])
            front(tag+' casement sill',u+(.47 if idx==3 and n==2 else .13),sill-.055,STONE,[1.246,1.258])
            z=sill+.069+(sh-.138)*.62
            front(tag+' cross rail',x,z,SASH,[1.507,1.523])
            # Separate mullions in addition to the centre jamb held by each opening.
            front(tag+' reveal stile',u+sw/2-.027,sill+.434,SASH,[1.514,1.524])
            if centre and n==2:
                front(tag+' reveal behind open timber sash',u-.041,sill+.48,'Interior timber and shade',[1.856,1.868])
    width=P['portal_inner_clear_width'];gh=P['portal_slab_soffit']-.84
    for side in (-1,1):
        mid=side*width/4;gw=width/2-.046
        for k in range(6):
            u=mid+gw*(k-2.5)/6
            front(f'Gate leaf {side}, iron bar {k+1}',u,.851,IRON,[1.676,1.686])
            if k<5:front(f'Gate leaf {side}, passage gap {k+1}',u+gw/12,.851,None,None,3.60)
        for z in (.43,1.93):
            front(f'Gate {side} cross rail {z}',mid+.031,z,IRON,[1.668,1.684])
        u=side*P['portal_lamp_axes_m']/2
        for j in range(9):
            z=2.052+j*.068
            front(f'Helical shade {side}, level {j+1}',u,z,['Blue-black lamp stripe','Pale lamp glass'],[1.124,1.139])
        front(f'Lantern upper cap {side}',u,2.735,IRON,[1.095,1.121])
    for j in range(17):
        u=-width/2+.08+j*(width-.16)/16
        front(f'Grille in upper transom {j+1}',u,2.952,IRON,[1.671,1.684])
    for x,z in ((-.35,1.28),(.60,1.39)):
        front('Photographed 2020 notice '+str(x),x,z,'Paper on street gate',[1.633,1.642])
    front('Enamel address plate',-1.74,1.909,'Enamel address plate',[1.214,1.225])
    front('Pier history plaque',-1.72,1.45,IRON,[1.214,1.226])
    for key,shape in enumerate(json.loads((SOURCE/'sign-outlines.json').read_bytes())['lane']):
        poly=Polygon(shape[0],shape[1:]);pt=poly.representative_point()
        if poly.area>.004:front(f'Raised name character component {key+1}',pt.x,4.175+.126+pt.y,'Dark name lettering',[1.297,1.307])
    front('Outboard air-conditioning case at east-side shop',P['sash_centres_u'][3]+.13,5.053,'Pale sewn piping',[.965,.971])
    for idx,(x,z0,width,depth)in enumerate(((-4.85,4.50,.99,.50),(-1.32,4.62,.99,.52))):
        h=.44*width
        for j,z in enumerate(np.linspace(z0+.07,z0+h-.07,5)):
            front(f'Guard box {idx+1}: horizontal slat {j+1}',x+.19,z,'Pale sewn piping',[1.4-depth-.031,1.4-depth-.016])
        for z in (z0+h+.12,z0-.10):
            probe(f'Guard box {idx+1}: empty bounds {z}',[-1.4,-x],z,[1,0],1.4-depth+.02)
    return out


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for role in ('raw','full','lod','output'):cli.add_argument(role,type=Path)
    opt=cli.parse_args();report={k:inspect(getattr(opt,k),cases()) for k in ('raw','full','lod')}
    opt.output.write_text(json.dumps(report,ensure_ascii=False,separators=(',',':'))+'\n')
    for k,r in report.items():print(k,len(r['cases']),[(a['name'],a['first_hit']) for a in r['cases'] if not a['passed']][:12])
    raise SystemExit(int(not all(r['passed']for r in report.values())))
