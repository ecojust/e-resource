"""Intersect the actual serialized terrace, joints, floor noses, rails and chair tubes."""
from pathlib import Path
import json,runpy,sys
import numpy as np
HERE=Path(__file__).resolve().parent
SRC=HERE.parents[2]/'source/precise/changning-hongqiao-sanatorium-sun-terraces'
INSPECT=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']

def cases():
    frame=json.loads((SRC/'measurements/terrace-frame.json').read_bytes());chairs=json.loads((SRC/'measurements/chair-profiles.json').read_bytes())['chairs']
    z=frame['floor_to_roof_z_m'];edges=frame['south_edges_x_m'];ref=frame['grid_i_at_post_row'];first,last=frame['longitudinal_bounds_grid_j'];p=frame['estimated_tile_pitch_m'];length=(last-first)*p
    rows=[]
    def add(name,start,ray,extent,allow=None,limit=None):
        rows.append(dict(name=name,origin=list(np.asarray(start,float)),direction=list(np.asarray(ray,float)),length=extent,allowed=allow,range_m=limit))
    for level,(edge,zz) in enumerate(zip(edges,z),1):
        for j,y in enumerate([.59,3.62,7.17,10.813,14.92]):
            add(f'Level {level} concrete terrace edge {j+1}',[edge+.085,y,zz-.119],[-1,0,0],.16,['Pale deck fascia'],[.073,.077])
            if level<4:
                add(f'Level {level} solid front {j+1}',[edge+.05,y,zz+.395],[-1,0,0],.16,['Sunlit pale mineral render'],[.059,.065])
                add(f'Level {level} open terrace above solid {j+1}',[edge+.1,y,zz+1.05],[-1,0,0],.70)
                add(f'Level {level} balcony paving {j+1}',[edge-.41,y,zz+.078],[0,0,-1],.12,['Exposed cement paving'],[.066,.070])
    for i in [-3,-1,2,5,8,11,14]:
        for j in [0,4,9,14,19,26,32,39,47,55,62]:
            x=(i-ref)*p;y=(j+.5-first)*p
            for dx,label,mat,interval in [(p*.5,'tile','Jointed two-tone terrace paving',[.043,.047]),(0.,'open mortar seam','Slate toned cement joint',[.056,.061])]:
                add(f'Upper {label} {i}/{j}',[x+dx,y,z[3]+.054],[0,0,-1],.09,[mat],interval)
    for n,height in enumerate([.28,.47,.66,.91],1):
        for k,y in enumerate([1.06,4.19,6.58,9.12,12.47,14.51]):
            add(f'Upper long round rail {n}/{k+1}',[edges[3]+.036,y,z[3]+height],[-1,0,0],.18,['Light painted tubular guard'],[.117,.130])
            if n<4:add(f'View through horizontal rails {n}/{k+1}',[edges[3]+.04,y,z[3]+height+.082],[-1,0,0],.32)
        for k,x in enumerate([2.01,2.70,3.81,4.24]):
            add(f'Upper end round rail {n}/{k+1}',[x,length+.038,z[3]+height],[0,-1,0],.18,['Light painted tubular guard'],[.120,.136])
    for role,study in chairs.items():
        normal=np.r_[study['second_side_displacement_xy'],0.];normal=normal/np.linalg.norm(normal)
        for name in ['outer_rocker','arm','back_tube']:
            trace=study['lifted_traces'][name]
            for i in range(1,len(trace)-1,2):
                hit=np.array(trace[i])+[0,0,z[3]+.02]
                add(f'{role} visible {name} observation {i}',hit-normal*.045,normal,.09,['Aged bright steel tube'],[.030,.043])
    plants=json.loads((SRC/'measurements/potted-evergreens.json').read_bytes())['pots']
    for pot in plants:
        x,y=pot['base_xy_m'];height=pot['pot_height_m'];rim=pot['pot_width_m']/2
        for i,offset in enumerate([-.052,.052]):
            add(pot['name']+' pot external face '+str(i),[x+rim+.055,y+offset,z[3]+.01+height*.54],[-1,0,0],.14,['Weathered dark plant pot'],[.064,.112])
    return rows
if __name__=='__main__':
    args=list(map(Path,sys.argv[1:]));roles=['raw','full','lod'] if len(args)==4 else ['model'];assert len(args)==len(roles)+1
    results={k:INSPECT(path,cases())for k,path in zip(roles,args)};args[-1].write_text(json.dumps(results,ensure_ascii=False,separators=(',',':'))+'\n');print([(k,v['triangles'],len(v['cases']),[(c['name'],c['first_hit'])for c in v['cases']if not c['passed']][:16])for k,v in results.items()]);assert all(x['passed']for x in results.values())
