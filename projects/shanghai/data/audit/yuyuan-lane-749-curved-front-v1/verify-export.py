"""Sample the circular coping, photographed brick pattern, six windows and both open lower leaves."""
import argparse,json,math,runpy
from pathlib import Path
import numpy as np

HERE=Path(__file__).absolute().parent
SOURCE=HERE.parents[2]/'source/precise/changning-yuyuan-lane-749-curved-front'
D=json.loads((SOURCE/'source/dimensions.json').read_bytes())
MEASURE=json.loads((SOURCE/'measurements/vertical-brick-pier.json').read_bytes())
SWING=json.loads((SOURCE/'measurements/lower-casement-fit.json').read_bytes())
INSPECT=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']

def cases():
    tests=[]
    def ray(name,origin,direction,length,materials,span):
        tests.append(dict(name=name,origin=list(map(float,origin)),direction=list(map(float,direction)),length=length,allowed=materials,range_m=span))
    r=D['radius_m'];top=D['cap_top_m'];coping=D['coping_bottom_m']
    def facing(name,theta,u,z,start,base,materials,span):
        n=np.array([math.sin(theta),-math.cos(theta),0.]);axis=np.array([math.cos(theta),math.sin(theta),0.])
        point=np.array([0.,r,z])+(r+base+start)*n+u*axis
        ray(name,point,-n,start+.55,materials,span)
    for k,theta in enumerate(np.linspace(-1.104,.939,26)):
        facing(f'curved dark cap {k+1}',theta,0,top-.032,.23,0,['Weathered dark cap'],[.144,.151])
        facing(f'sweeping cornice face {k+1}',theta,0,top-.28,.23,0,['Brown grey rendered coping'],[.179,.186])
        facing(f'continuous cornice drip {k+1}',theta,0,coping-.008,.23,0,['Coping lower drip'],[.164,.173])
    for k,theta in enumerate([-1.095,-.875,-.517,-.201,.198,.473,.817,.944]):
        facing(f'grey aggregate beyond recorded openings {k+1}',theta,0,1.84,.22,0,['Yuyuan grey washed aggregate'],[.218,.228])
    fired=['Clinker brown','Dark umber brick','Plum brown brick','Old chestnut brick']
    beds=MEASURE['photographed_beds_z_m'];pi=MEASURE['pier_width_m']
    for k,(lo,hi) in enumerate(zip(beds,beds[1:])):
        z=(lo+hi)/2
        facing(f'measured pier brick face {k+1}',-.327,0,z,.18,0,fired,[.149,.156])
        for j,u in enumerate([-.265*pi,.265*pi]):
            facing(f'measured pier course {k+1}, vertical break {j+1}',-.327,u,z,.18,0,
                   fired if k%2 else ['Cool grey brick mortar'],[.149,.156]if k%2 else[.162,.169])
    for k,z in enumerate(beds):
        facing(f'continuous mortar bed {k+1}',-.327,0,z,.18,0,['Cool grey brick mortar'],[.162,.169])
    for bay,(theta,width)in enumerate(zip(D['bay_angles_rad'],D['bay_widths_m'])):
        plane=r*(math.cos(math.asin(width/(2*r)))-1)
        for storey,(bottom,high) in enumerate([(0.,1.60),(D['lower_window_top_m']-D['lower_window_height_m'],D['lower_window_top_m'])]):
            sill_u=width*.43 if bay==0 and storey==0 else 0
            facing(f'bay {bay+1} stone sill {storey+1}',theta,sill_u,bottom-.065,.22,plane,['Dark weathered sill'],[.134,.142])
            if bay==1 and storey==1:continue
            frames=['Charcoal steel'] if storey==0 or bay==2 else ['Brown steel']
            material=([['Mauve tinted glass','Dusty plum glazing'],['Blue reflected sky','Pale blue glass','Slate blue reflection'],['Silvery glazing','Pale blue glass']][bay]
                     if storey==0 else [['Oxide curtain','Pale backing cloth'],[],['Cool grey glass','Silvery glazing']][bay])
            for k,zt in enumerate(([.13,.38,.64,.86] if storey==0 else [.21,.62,.90])):
                for j,q in enumerate([-.32,.16,.39]):
                    facing(f'{bay+1}/{storey+1} visible glazing {k+1}/{j+1}',theta,width*q,bottom+zt*(high-bottom),.24,plane,material,[.359,.367])
            for k,t in enumerate(([.255,.510,.768] if storey==0 else [.45,.79])):
                facing(f'{bay+1}/{storey+1} dark steel cross rail {k+1}',theta,width*.36,bottom+(high-bottom)*t,.24,plane,frames,[.311,.319])
    leaves=SWING['world_xyz']
    for i,corners in enumerate(leaves):
        lt,rt,rb,lb=np.array(corners)
        tangent=rt-lt;tangent/=np.linalg.norm(tangent);normal=np.array([tangent[1],-tangent[0],0])
        for j,frac in enumerate([.18,.72]):
            for k,t in enumerate([.22,.49,.78]):
                o=(1-frac)*lt+frac*rt;o[2]=lb[2]+t*(lt[2]-lb[2])
                ray(f'open lower leaf {i+1} glass {j+1}/{k+1}',o+.15*normal,-normal,.45,
                    ['Light blue casement reflection'if i==0 else'Dark casement reflection'],[.165,.169])
        for k,t in enumerate([.22,.48,.79]):
            o=.975*lt+.025*rt;o[2]=lb[2]+t*(lt[2]-lb[2])
            ray(f'open lower leaf {i+1} bronze edge {k+1}',o+.15*normal,-normal,.45,['Faded bronze casement'],[.135,.141])
    x=(leaves[0][1][0]+leaves[1][0][0])/2;plane=r*(math.cos(math.asin(D['bay_widths_m'][1]/(2*r)))-1)
    for k,t in enumerate([.20,.46,.72]):
        facing(f'recess between lower moving sashes {k+1}',0,x,D['lower_window_top_m']-t*D['lower_window_height_m'],
               .30,plane,['Dark window reveal'],[.606,.614])
    q=D['bay_angles_rad'][0]-.20/r
    for k,z in enumerate([-.51,-.29,-.11]):
        facing(f'left bay external condenser case {k+1}',q,.38,z,.72,0,['Pale condenser enamel'],[.220,.226])
    return tests

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ['raw','full','lod','output']:ap.add_argument(key,type=Path)
    args=ap.parse_args();tests=cases()
    out={k:INSPECT(getattr(args,k),tests)for k in ['raw','full','lod']}
    args.output.write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n')
    assert all(v['passed']for v in out.values()),{k:[p['name']for p in v['cases']if not p['passed']]for k,v in out.items()}
    print(len(tests),'checks per serialized file')
