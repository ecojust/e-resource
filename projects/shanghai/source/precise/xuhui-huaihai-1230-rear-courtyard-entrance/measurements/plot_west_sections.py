"""Draw actual horizontal cuts through two submitted meshes and the five photographic rays."""
from pathlib import Path
from argparse import ArgumentParser
from html import escape
import json
import numpy as np
from check_registered_court import Camera, SerialScene

def section(scene, z):
    material=scene.materials.index("Guangming | grey precast balcony")
    selected=scene.tri[(scene.mi==material)&(scene.lows[:,2]<z)&(scene.highs[:,2]>z)]
    for triangle in selected:
        hit=[]
        for p,q in zip(triangle,np.roll(triangle,-1,axis=0)):
            if (p[2]-z)*(q[2]-z)<0:
                t=(z-p[2])/(q[2]-p[2]);hit.append(p[:2]+t*(q[:2]-p[:2]))
        if len(hit)==2:yield hit

def draw(before,after,dest):
    c=Camera("25"); width=1000
    svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 515">','<rect width="1000" height="515" fill="#f2f0e9"/>',
         '<g font-family="sans-serif" fill="#293532"><text x="20" y="27" font-size="21">西叠台二楼栏板平剖与原机位射线</text>']
    records=[]
    us=[174,181,188,195,202]
    for j,path in enumerate((before,after)):
        scene=SerialScene(path);offset=64+j*214;scale=587
        def xy(point):
            return [24+(point[0]+5.36)*scale,offset+44+(point[1]+.79)*scale]
        def line(a,b,color,thick):
            x,y=xy(a);u,v=xy(b);return f'<line x1="{x:.2f}" y1="{y:.2f}" x2="{u:.2f}" y2="{v:.2f}" stroke="{color}" stroke-width="{thick}"/>'
        svg.append(f'<text x="21" y="{offset-8}" font-size="16">'+('扩建初稿'if j==0 else'修订栏孔')+'</text>')
        svg.append(f'<clipPath id="plot-{j}"><rect x="22" y="{offset}" width="960" height="167"/></clipPath><g clip-path="url(#plot-{j})">')
        for a,b in section(scene,4.43):
            svg.append(line(a,b,"#59594e",4))
        rows=[]
        for ix,u in enumerate(us):
            h=scene.ray(c.c,c.ray((u,328)),65)
            reaches=h is not None and h['point_enu_m'][1]>.12
            a=c.wall((u,328),-.86)
            b=c.wall((u,328),-.60) if reaches else np.asarray(h['point_enu_m'])
            svg.append(line(a,b,'#157a60' if reaches else '#c34e39',2.7))
            x,y=xy(b);svg.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3.8" fill="'+('#157a60' if reaches else '#c34e39')+'"/>')
            rows.append({'u':u,'first_hit':h,'through':reaches})
        svg.append('</g>')
        records.append(rows)
    svg.append('<text x="22" y="490" font-size="15">灰线为实体栏板剖面。红线落在孔侧，绿线穿过栏板到达后墙或窗面。</text></g></svg>')
    dest.write_text('\n'.join(svg)+'\n')
    return records
if __name__=='__main__':
    p=ArgumentParser(description=__doc__);p.add_argument('before',type=Path);p.add_argument('after',type=Path);p.add_argument('svg',type=Path)
    a=p.parse_args();rows=draw(a.before,a.after,a.svg)
    for row in rows:print(sum(v['through']for v in row),len(row))
