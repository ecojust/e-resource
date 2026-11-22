"""Record edges picked on the rectified 2015 street photograph and the corresponding original pixels."""
import json, sys
from pathlib import Path
import numpy as np
root = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'source'))
from photo_plane import pixel
# Visible heads/sills fall slightly with distance in the four-point rectification.
# The fitted slope retains the surveyed photograph edges at the outer bays.
columns = [(-6.46,-5.29),(-4.40,-3.22),(-1.02,-.41),(-.027,1.413),(1.767,2.365),(4.59,5.73),(6.605,7.755)]
rows = [('street',1.016,4.385),('lower',5.92,8.52),('middle',9.98,12.53),('upper',13.88,15.765),('attic',17.98,19.56)]
records=[]
for tier,sill,head in rows:
    for col,(left,right) in enumerate(columns):
        if tier=='street' and 1<col<5:continue
        mid=.5*(left+right)
        drift={'street':-.074,'lower':-.030,'middle':-.004,'upper':.008,'attic':.03}[tier]
        x0,x1=left+drift,right+drift
        def z(height,x):return height-.013*x
        outline=[[x0,z(sill,x0)],[x1,z(sill,x1)],[x1,z(head,x1)],[x0,z(head,x0)]]
        records.append(dict(tier=tier,column=col+1,rectified_xz_m=outline,
               upright_pixels=[pixel((x,0,h)).round(3).tolist() for x,h in outline]))
p=root/'measurements/facade-apertures.json'
p.write_text(json.dumps(dict(photographer='Antigng',source_sha256='69267974363ab360c93adbe6a6290b8b2bbd6e6497a125d61ce89328af65eeff',
   projection='EXIF-upright 2988 x 5312. Front-plane opening corners taken from four-point rectification; obstructions cover portions of central window sills.',
   wall_breadth_m=18.631,openings=records),ensure_ascii=False,indent=2)+'\n')
