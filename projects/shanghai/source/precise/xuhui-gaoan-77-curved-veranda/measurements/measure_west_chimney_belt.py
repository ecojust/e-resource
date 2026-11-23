"""Reconstruct the top and bottom edges of the chimney belt on its slightly projecting front."""
import json
from pathlib import Path
import numpy as np

root=Path(__file__).absolute().parent
cameras=json.loads((root/'west-eave-photo-control.json').read_bytes())['cameras']
stations=json.loads((root/'west-eave-visible-pixels.json').read_bytes())['stations']
edges={'commons2013':(1768,1203,1235.5),'paper2022':(351,266,276.5),'sina26':(437,294.5,303.5),'sina39':(457,198.6,210.3)}
rows={}
for name,(x,top,bottom) in edges.items():
    spec=cameras[name];w,h=spec['native_size'];H=np.asarray(spec['plane_to_pixel'])
    f=stations[name]['assumed_focal_px'];K=np.array([[f,0,w/2],[0,f,h/2],[0,0,1.]])
    ax,az=np.linalg.inv(K)@H[:,0],np.linalg.inv(K)@H[:,1]
    normal=np.cross(ax,az);normal*=np.sqrt(np.linalg.norm(ax)*np.linalg.norm(az))/np.linalg.norm(normal)
    P=np.column_stack((H[:,0],K@normal,H[:,1],H[:,2]))
    eye=-np.linalg.solve(P[:,:3],P[:,3])
    if eye[1]<0:P[:,1]*=-1;eye=-np.linalg.solve(P[:,:3],P[:,3])
    # Probe the same front face at three plausible reliefs to expose depth sensitivity.
    results={}
    for depth in [.10,.158,.22]:
        def back(y):
            ray=np.linalg.solve(P[:,:3],[x,y,1.]);return (eye+ray*((depth-eye[1])/ray[1]))[[0,2]]
        t=back(top);b=back(bottom)
        results[str(depth)]={'top':t.tolist(),'bottom':b.tolist(),'height':float(t[1]-b[1])}
    rows[name]={'coordinates_on_registered_image':{'top':[x,top],'bottom':[x,bottom]},'estimates':results}
out={'datum':'Unscaled fitted wall units, s increases toward the garden and z is measured from the six stone saddles. The physical scale is supplied by west-eave-delivery-frame.json.','observation':'The pale horizontal belt extends over the entire photographed shaft. The 2018 and principal 2013 exposures show a lower projection beneath its wider shoulder only. Top/bottom were independently picked in a vertical column out of the projecting return; face relief sensitivity is listed.','stations':rows}
import argparse
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path);args=parser.parse_args();args.output.write_text(json.dumps(out,indent=2)+'\n')
for k,row in rows.items():print(k,row['estimates']['0.158'])
