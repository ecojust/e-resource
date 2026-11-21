"""Probe the exported cupola meridian, eight seams, gallery opening, street windows, roof dormers and fanlight."""
from pathlib import Path
import argparse,json,math,runpy
import numpy as np

HERE=Path(__file__).resolve().parent;S=HERE.parents[2]/'source/precise/hongkou-young-allen-court-gilded-corner/source'
inspect=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']
p=json.loads((S/'plan.json').read_bytes());a=math.radians(p['east_axis_bearing_from_east_deg'])
A=np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])
def cases():
    result=[]
    def probe(label,pt,d,material,iv,limit=3.):
        pos=[*(A@pt[:2]),pt[2]];direction=[*(A@d[:2]),d[2]]
        result.append(dict(name=label,origin=list(map(float,pos)),direction=list(map(float,direction)),
                           allowed=material if isinstance(material,list) or material is None else [material],range_m=iv,length=limit))
    def wall(label,anchor,normal,along,z,offset,material,iv,length=2.):
        n=np.array(normal);t=np.array([-n[1],n[0]])
        xy=np.asarray(anchor)+n*offset+t*along
        probe(label,[*xy,z],[-n[0],-n[1],0.],material,iv,length)
    N=[0,1];W=[-1,0];s=p['shell']
    for i,x in enumerate(p['north_bays'],1):
        upper=(p['north_short_sills'][i-1],p['north_short_heights'][i-1]) if i<=2 else (7.53,2.05)
        for floor,(sill,h) in enumerate(((3.86,2.08),upper),2):
            wall(f'North {i} floor {floor} pane',[x,s['north']],N,.156,sill+.56,1.,'Recessed window glass',[1.222,1.238])
            wall(f'North {i} floor {floor} meeting stile',[x,s['north']],N,0,sill+.46,1.,'Red-brown wood joinery',[1.075,1.091])
            wall(f'North {i} floor {floor} sill',[x,s['north']],N,.18,sill-.048,1.,'Buff projecting sills',[.751,.77])
    for i,x in enumerate(p['north_dormers'],1):
        z=p['eave']+1.43
        wall(f'Roof dormer {i} glass',[x,p['dormer_front']],N,.17,z+.44,1.,'Recessed window glass',[1.218,1.235])
        wall(f'Roof dormer {i} frame',[x,p['dormer_front']],N,0,z+.40,1.,'Red-brown wood joinery',[1.081,1.098])
        wall(f'Roof dormer {i} rendered tympanum',[x,p['dormer_front']],N,.13,p['dormer_apex']-.43,1.,'Pale dormer render',[.99,1.01])
        probe(f'Roof dormer {i} ridge tile',[x,p['dormer_front']-.62,p['dormer_apex']+.79],[0,0,-1.],'Orange tile arrises',[.69,.78])
    r=p['tower_radius'];NW=np.array([-1.,1.])/math.sqrt(2.);anchor=NW*r*math.cos(math.pi/8)
    for x in [-.19,.17]:
        wall('Dark inner northwest gallery '+str(x),anchor,NW,x,12.26,1.,'Dark storefront backing',[1.665,1.69])
        wall('Pale gallery beam '+str(x),anchor,NW,x,12.80,1.,'Buff projecting sills',[.780,.80])
        for lo in (3.72,7.48):wall('Tower lower casement '+str((x,lo)),anchor,NW,x,lo+.36,1.,'Recessed window glass',[1.222,1.238])
    for n in (N,W):
        face=np.array(n)*r*math.cos(math.pi/8);wall('Side blind arch '+str(n),face,n,.14,12.03,1.,'Young Allen grey facing brick',[1.166,1.19])
    z0=p['dome_skirt'];height=p['dome_cap']-z0
    for k in range(8):
        phi=k*math.pi/4
        n=np.array([math.cos(phi),math.sin(phi)])
        for frac,rad in ((.22,.875),(.45,.806),(.65,.419),(.81,.145)):
            # At a face centre the curved, folded side is inside the octagonal arris.
            expected=p['gold_radius']*rad*(math.cos(math.pi/8)+.033)
            wall(f'Gold octagon {k+1} meridian {frac}',[0.,0.],n,0,z0+height*frac,2.35,'Ochre-gold cupola sheet',[2.35-expected-.042,2.35-expected+.042],3.)
        theta=phi+math.pi/8;n=np.array([math.cos(theta),math.sin(theta)])
        wall(f'Gold standing seam {k+1}',[0.,0.],n,0,z0+.45*height,2.35,'Folded gold ribs',[1.17,1.25],2.7)
    for k,(axis,reach) in enumerate(zip(p['west_oriels'],[.79,.63])):
        for z in (4.12,8.57):
            wall('West oriel glass '+str((k,z)),[s['west']-reach,-axis],W,.17,z,1.,'Recessed window glass',[1.222,1.239])
    x=s['west']-.79;y=-p['west_oriels'][0]
    wall('Fanlight radial timber',[x,y],W,0,5.71,1.,'Red-brown wood joinery',[1.075,1.09])
    wall('Fanlight grey crown',[x,y],W,0,6.31,1.,'Young Allen grey facing brick',[.85,.92])
    for u in (-.33,.34):
        wall('Curved gable render '+str(u),[s['west']-.12,y],W,u,p['eave']+1.72,1.,'Pale dormer render',[.99,1.01])
    for x in (4.,11.,22.,35.):
        yr=(s['north']+s['south'])*.5+.46
        probe('Main ridge '+str(x),[x,yr,p['ridge']+1.],[0.,0.,-1.],'Orange tile arrises',[.86,.90],1.5)
    for x in p['roof_cross_cappings']:
        y=s['north']-.89
        probe('Cross-slope ridge '+str(x),[x,y,p['eave']+3.],[0.,0.,-1.],'Buff projecting sills',[1.08,1.11],1.6)
    shop=NW*1.67
    for xx in (-1.52,-.91):
        wall('Grey corner shop street facing pier '+str(xx),shop,NW,xx,1.65,1.,'Young Allen grey facing brick',[.992,1.009])
    for xx in (-.14,.86,1.25):
        wall('Corner shop recessed opening '+str(xx),shop,NW,xx,1.92,1.,'Dark storefront backing',[1.359,1.38])
    tangent=np.array([-NW[1],NW[0]])
    for xx in (-.26,.2,.69,1.20):
        xy=shop+tangent*xx+NW*.57
        probe('Rose awning slope '+str(xx),[*xy,3.40],[0.,0.,-1.],'Faded rose awning cloth',[.528,.553],.84)
    for x in (3.12,4.86,6.80):
        wall('North timber fascia '+str(x),[x,s['north']],N,0,3.28,1.,'Sienna wood fascia',[.695,.81])
    for x,y in [(-4.,4.),(42.,-6.),(18.,-20.)]:
        probe('Outside registered building '+str((x,y)),[x,y,20.],[0.,0.,-1.],None,None,21.)
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for k in ('raw','full','lod','output'):parser.add_argument(k,type=Path)
    o=parser.parse_args();rr={k:inspect(getattr(o,k),cases()) for k in ('raw','full','lod')}
    o.output.write_text(json.dumps(rr,ensure_ascii=False,indent=1)+'\n')
    for k,v in rr.items():print(k,len(v['cases']),[(c['name'],c['first_hit'])for c in v['cases'] if not c['passed']])
    raise SystemExit(int(not all(v['passed']for v in rr.values())))
