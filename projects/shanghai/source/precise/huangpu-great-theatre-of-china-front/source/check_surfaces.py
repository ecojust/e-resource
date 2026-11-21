"""Check documented wall openings, projecting frames, spires and marquee against the three saved surfaces."""
from pathlib import Path
import runpy
import numpy as np

def check_triangles(triangles,materials,distant):
    project=Path(__file__).resolve().parents[4];rows=[]
    shoot=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['first_hit']
    def ray(label,x,z,material,depth,tol=.035):
        idx,dist,hit=shoot(triangles,np.array([x,-3.4,z]),np.array([0.,1.,0.]))
        found=materials[idx] if np.isfinite(dist) else 'sky'
        assert found==material and abs(3.4-dist-depth)<tol,(label,x,z,found,dist,material,depth)
        rows.append(dict(feature=label,x_m=x,z_m=z,material=str(found),street_projection_m=round(3.4-dist,4)))
    for x in (-4.25,4.25):ray('Ground flanking glass',x-.12,1.69,'recessed amber glazing',-.31)
    for x in (-1.89,-.63,.63,1.89):
        ray('Recessed timber entrance leaf',x,.62,'warm timber door leaves',-.92)
        ray('Glazing in timber leaf',x,2.15,'recessed amber glazing',-.89)
        ray('Door surround',x+.45,2.15,'warm timber door leaves',-.835)
    for i in (-2.48,-1.255,0,1.255,2.48):ray('Dark entrance stile',i,2.13,'dark painted metal',-.81)
    for z,depth in ((4.23,.84),(4.52,.90),(5.53,.74)):ray('Marquee projection',.33,z,'pale carved window stone',depth)
    for x in (-1.58,0.,1.58):
        for z,width,h in ((6.02,.99,3.52),(10.66,.79,1.34)):
            ray('Recessed central glazing',x+.19,z+h*.50,'recessed amber glazing',-.55)
            ray('Metal at central upright',x,z+h*.57,'dark painted metal',-.455)
            ray('Metal transom',x+.19,z+h*.72,'dark painted metal',-.455)
            ray('Projecting stone sill',x+.16,z-.047,'pale carved window stone',-.12)
        ray('Spandrel brick field',x+.12,10.11,'dark red facing brick',-.27)
    for x in (-3.5,3.5):
        for z,width,h in ((6.20,.66,2.1),(10.18,.64,1.48),(15.10,.50,.75)):
            ray('Tower glazing',x+.115,z+h*.5,'recessed amber glazing',-.21)
            ray('Flanking stone surround',x+width/2+.054,z+h*.5,'pale carved window stone',.21)
            ray('Narrow sill toe',x+.11,z-.055,'pale carved window stone',.28)
            ray('Brick tower beside reveal',x+.73,z+h*.5,'dark red facing brick',.09)
            if z<15:ray('Crown of curved hood',x,z+h+.13+width*.82*.64-.016,'pale carved window stone',.32)
        for z,w in [(17.48,1.95),(17.61,2.10),(17.80,1.91),(18.06,1.73),(18.45,1.89)]:
            ray('Stepped tower cap',x+.33,z,'pale carved window stone',(1.53+w-1.73)/2-.27)
        for z in [19.13,20.69,21.83]:
            yfront=-.62+(.175+.62)*(z-18.52)/(22.68-18.52)
            ray('Tapered spire face',x+.035,z,'muted grey spire facing',-yfront)
    for z,depth in [(13.6,-.01),(13.9,.035),(14.23,.085)]:ray('Three horizontal stone bands',.71,z,'pale carved window stone',depth)
    for x in (-1.32,1.32):ray('Pale upper central parapet',x,15.39,'pale carved window stone',-.11)
    for x in (-4.93,4.93):ray('Short adjacent brick strip',x,9.39,'dark red facing brick',-.22)
    for x,z,depth,label in [(0,5.05,.766,'Chinese raised lettering'),(0,3.91,.076,'English raised lettering')]:
        region=(triangles[:,:,0].min(axis=1)>-3.7)&(triangles[:,:,0].max(axis=1)<3.7)&(triangles[:,:,2].min(axis=1)>z-.38)&(triangles[:,:,2].max(axis=1)<z+.38)&np.all(np.isclose(triangles[:,:,1],-depth,atol=.002),axis=1)&(np.array(materials)=='dark painted metal')
        faces=triangles[region];assert len(faces)>30,(label,len(faces))
        for i in np.linspace(0,len(faces)-1,8,dtype=int):
            point=faces[i].mean(axis=0);ray(label,float(point[0]),float(point[2]),'dark painted metal',depth)
    return dict(passes=len(rows),rays=rows,triangles=len(triangles),lod=bool(distant))
