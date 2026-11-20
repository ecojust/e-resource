from pathlib import Path
import numpy as np,math,json
import shapely as sg
from shapely.geometry import LineString,Point
s=Path('/tmp/mitsui118/ray-camera.py').read_text();exec(s[:s.index('measure=')])
# Use the actual map pitch, zoom and a desktop viewport of 870 by 660 CSS pixels.
cases=[('blocked street',55,342.09672719592436-8,20.5,10.8,.75),('visible upper view',31,342.09672719592436-18,20.0,14.,2.4)]
cases +=[(f'new {zoom:.2f} {pitch} {bearing}',pitch,bearing,zoom,8.7,.72)for zoom in (20.05,20.20,20.35,20.50,20.65,20.80)for pitch in (24,28,30,33,36,39,42,45,48)for bearing in (322,326,330,334,338,342,346)]
rows=[]
for name,pit,b,zoom,z0,center_y in cases:
 dist=1.5*660*2*math.pi*k/(512*2**zoom);aim=np.array([0,center_y])@R;cam=aim+dist*math.sin(pit*rad)*np.array([-math.sin(b*rad),-math.cos(b*rad)]);camh=z0+dist*math.cos(pit*rad)
 rays=np.array([LineString([np.array([x,y])@R,cam])for x,y,z in samples],dtype=object);i,j=np.nonzero(sg.intersects(rays[:,None],gs[None,:]));minimum=[500.]*len(rays);who=[None]*len(rays)
 for a0,k0 in zip(i,j):
  z=samples[a0][2];dst=Point(rays[a0].coords[0]).distance(rays[a0].intersection(gs[k0]));v=z+(camh-z)*dst/rays[a0].length-heights[k0]
  if v<minimum[a0]:minimum[a0]=v;who[a0]=ids[k0]
 rows.append(dict(name=name,pitch=pit,bearing=b,zoom=zoom,center=[0,center_y],elevation=z0,eye_height_m=camh,min_clearance_m=min(minimum),ground_clearance_m=min(minimum[::3]),limit=who[int(np.argmin(minimum))]))
valid=[r for r in rows[2:] if r['min_clearance_m']>=7 and r['ground_clearance_m']>=9];sel=sorted(valid,key=lambda r:(-r['zoom'],abs(r['bearing']-330),abs(r['pitch']-33)))[0];out=dict(scope='Offline checks of 15 facade sightlines against actual mapped neighboring heights. Browser observation pending.',previous=rows[:2],selected=sel,selection_count=len(valid),tested_count=len(rows)-2);print(out,flush=True);(Path('/tmp/mitsui118')/'alternate-camera.json').write_text(json.dumps(out,indent=2)+'\n')
