"""Check the original and decoded meshes with street-facing and upward rays."""
from pathlib import Path
import json,sys,runpy
import numpy as np
HERE=Path(__file__).absolute().parent
P=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').exists())
SOURCE=P/'source/precise/huangpu-huade-building-scroll-parapet'
sys.path.insert(0,str(SOURCE/'source'))
from photo_plane import trace,level
inspect=runpy.run_path(str(P/'data/audit/central-reserve-bank-changshu-front-v1/verify-export.py'))['inspect']
def cases():
    checks=[]
    def frontal(tag,x,y,material):
        xx,zz=trace(x,y,0)
        checks.append(dict(name=tag,origin=[xx,-1.2,zz],direction=[0,1,0],length=1.44,allowed=material,range_m=None))
    for right,dx,dy,sx in [('near',756,289.4,1),('far',1457,299.4,.926)]:
        for j,off in enumerate([-27,-15,0,15,27]):
            frontal(right+' upper aperture '+str(j),dx+sx*off,dy-8,None)
            frontal(right+' stone below upper aperture '+str(j),dx+sx*off,dy+6,['Ivory washed limestone'])
        for j,off in enumerate([-8,0,8]):
            frontal(right+' lower aperture '+str(j),dx+5+sx*off,dy+75,None)
            frontal(right+' lower stone '+str(j),dx+5+sx*off,dy+87,['Ivory washed limestone'])
        for j,(off,y) in enumerate([(-109,-30),(-70,-45),(0,-70),(55,-40),(109,-10)]):
            frontal(right+' chest of fret '+str(j),dx+sx*off,dy+y,['Ivory washed limestone'])
        for j,(off,y) in enumerate([(-165,-107),(158,-108),(-177,-89),(163,-95)]):
            frontal(right+' open shoulder '+str(j),dx+sx*off,dy+y,None)
    for x in (300,357,427,501,1034,1104,1194,1235):
        for y in (189,238,262):frontal('pier '+str(x)+' '+str(y),x,y,['Square stone uprights'])
    for group,points in [('Near',[(565,2678),(593,2691),(620,2703),(530,2690),(557,2702),(586,2714),(495,2702),(523,2715),(551,2728)]),('Far',[(826,2804),(850,2816),(873,2826),(792,2816),(816,2828),(840,2840),(759,2828),(784,2839),(806,2848)])]:
        for idx,(u,v) in enumerate(points):
            x,y,z=level(u-253,v-2350,-.195)
            checks.append(dict(name=group+' observed roundel '+str(idx+1),origin=[x,y,-1.2],direction=[0,0,1],length=1.4,allowed=['Soffit roundel face','Roundel turned bevel'],range_m=[1.004,1.050]))
    return checks
if __name__=='__main__':
    args=list(map(Path,sys.argv[1:])); roles=['raw','full','lod']if len(args)==4 else ['model']
    reports={role:inspect(mesh,cases())for role,mesh in zip(roles,args[:-1])}
    args[-1].write_text(json.dumps(reports,indent=1)+'\n')
    failures={role:[(e['name'],e['first_hit']and e['first_hit']['material'])for e in r['cases']if not e['passed']]for role,r in reports.items()}
    print('triangles',[(k,d['triangles'])for k,d in reports.items()],'rays',len(cases()),'misses',failures)
    sys.exit(int(any(failures.values())))
