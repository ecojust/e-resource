"""Cast physically bounded rays into the serialized gable, glazing, stone entry and brick courses."""
import argparse,json,math,runpy,sys
from pathlib import Path
import numpy as np

HERE=Path(__file__).absolute().parent;SRC=HERE.parents[2]/'source/precise/changning-yuyuan-lane-865-timber-gable'
sys.path.insert(0,str(SRC/'source'));from projection import world
INSPECT=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']
def cases():
    m=SRC/'measurements';beds=json.loads((m/'brick-courses.json').read_bytes())['read_bed_centres_m']
    glass=json.loads((m/'central-glazing.json').read_bytes())
    rows=[];brick=['Old rose brick','Pale fired brick','Iron red brick','Muted red brick','Dark fired brick']
    glazes=['Cool blue grey glass','Smoky glass','Dark grey reflection','Blue reflected panes']
    def ray(label,org,vec,length,mats,span):
        rows.append(dict(name=label,origin=list(map(float,org)),direction=list(map(float,vec)),length=length,allowed=mats,range_m=span))
    def front(label,x,z,mats,span):ray(label,[x,-.35,z],[0,1,0],1.10,mats,span)
    for j,z in enumerate(beds):
        for i,x in enumerate([1.275,1.535]):
            front(f'mortar bed {j+1}/{i+1}',x,z,['Lime mortar'],[.366,.368])
        if j+1<len(beds):
            for i,x in enumerate([1.28,1.53]):
                front(f'brick face {j+1}/{i+1}',x,(z+beds[j+1])/2,brick,[.342,.348])
    for i,x in enumerate([-.76,-.67,.73,.78]):
        for j,z in enumerate([.44,.76,1.19,1.72,1.93]):
            front(f'stone jamb {i+1}/{j+1}',x,z,['Grey dressed surround'],[.311,.313])
    for i,x in enumerate([-.42,-.23,.06,.32,.51]):
        front(f'square outer lintel {i+1}',x,2.225,['Grey dressed surround'],[.311,.313])
    for i,x in enumerate([-.21,-.05,.13,.29]):
        for j,z in enumerate([.47,.64,1.32,1.55]):
            front(f'deep wooden leaf {i+1}/{j+1}',x,z,['Door panel recess'],[1.036,1.040])
    for i,x in enumerate([-.17,-.07,.04,.15,.258]):
        front(f'arched inner head {i+1}',x,2.08,['Stone in reveal'],[.973,.977])
    for i,v in enumerate([.07,.17,.28,.46]):
        ray(f'left reveal inner face {i+1}',[-.34,v,1.72],[-1,0,0],.30,['Grey dressed surround'],[.190,.194])
    ray('doorbell face in reveal',[-.34,.28,1.27],[-1,0,0],.3,['Faded brass'],[.127,.135])
    # Several field samples on each side of the tall opening in the rectified reference.
    for j,v in enumerate([475,553,593,657]):
        for i,u in enumerate([56,111,355,412]):
            x=-2+u*4.25/509;z=8.85-v*6.1/731
            front(f'black timber upright {j+1}/{i+1}',x,z,['Tarred structural timber'],[.269,.273])
    for j,(u,v)in enumerate([(30,537),(83,466),(140,485),(278,382),(323,484),(383,475),(453,579),(81,652),(198,649),(263,648)]):
        front(f'cream panel {j+1}',-2+u*4.25/509,8.85-v*6.1/731,['Cream lime infill'],[.349,.351])
    for i,(u,v)in enumerate([(33,465),(76,526),(109,583),(323,636),(361,549),(393,501),(435,451),(219,271),(251,271)]):
        front(f'swept timber brace {i+1}',-2+u*4.25/509,8.85-v*6.1/731,['Tarred structural timber'],[.269,.273])
    xy=np.array(glass['fitted_edges_xy_m']);zz=np.sort(glass['fitted_transom_levels_m'])
    for i,(a,b)in enumerate(zip(xy,xy[1:])):
        d=b-a;n=np.array([d[1],-d[0]])/np.linalg.norm(d)
        for j,z in enumerate(zz):
            for k,t in enumerate([.25,.75]):
                px=a+t*d;org=[*(px+n*.08),z]
                ray(f'high window transom {i+1}/{j+1}/{k+1}',org,[*(-n),0],.14,['Dull steel glazing bars'],[.053,.060])
            if j+1<len(zz):
                for k,t in enumerate([.27,.72]):
                    px=a+t*d;org=[*(px+n*.08),(z+zz[j+1])/2]
                    ray(f'high window reflection {i+1}/{j+1}/{k+1}',org,[*(-n),0],.14,glazes,[.078,.081])
    for i,(u,v)in enumerate([(207,229),(230,189),(249,154),(269,118),(282,94),(295,85),(325,109),(357,132),(381,148),(400,157),(420,162)]):
        x,z=world([[u,v]],-.21)[0];ray(f'upper roof rim {i+1}',[x,-.14,z+.12],[0,0,-1],.25,['Weathered grey roof rim'],[.114,.126])
    return rows
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    for k in ['raw','full','lod','output']:ap.add_argument(k,type=Path)
    args=ap.parse_args();probes=cases();res={k:INSPECT(getattr(args,k),probes)for k in ['raw','full','lod']}
    args.output.write_text(json.dumps(res,ensure_ascii=False,separators=(',',':'))+'\n')
    print(len(probes),{k:[p['name']for p in v['cases']if not p['passed']]for k,v in res.items()})
    assert all(v['passed']for v in res.values())
