"""Independently back-project the right returns of the western balcony from Masa25."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
from register_court import Camera

STATION="masa-43034625-650"
SOURCE_SHA="4ad01b07ae017279cc1901ce37b6c7c8056611e6ea99c4607aa80d0d882bfb98"
# Front and rear endpoints of a line extending in depth, selected at a common elevation.
RETURNS=[
 ("top enclosure head",[229,82],[242.3,86.5]),
 ("fourth-floor enclosure sill",[224,128],[238.2,139]),
 ("underside of fourth-floor slab",[225,153.5],[237,165]),
 ("underside of third-floor slab",[220,246.5],[232,251.3]),
 ("second-floor front parapet cap",[211,312.2],[227,317.7]),
 ("lower edge of second-floor apron",[209,341.2],[225,343.1])]
PIXELS=[
 ("ground skirt",[155,437],"grey base",1),("ground pale window pane",[163,398],"pane",2),
 ("lower terrace deep aperture",[211,282],"recess",2),("east edge of second-floor panel",[207,324],"cast",2),
 ("second-floor right return",[217,328],"return",2),
 ("first visible slot",[174,328],"slit",2),("second visible slot",[181,328],"slit",2),
 ("third visible slot",[188,328],"slit",2),("fourth visible slot",[195,328],"slit",2),
 ("fifth visible slot",[202,328],"slit",2),("third-floor grey sill skirt",[213,237],"cast",2),
 ("third-floor closed front glass",[207,186],"pane",2),("third-floor closed side glass",[231,195],"side pane",2),
 ("fourth-floor grey front skirt",[201,144],"cast",2),("fourth-floor pale closed pane",[215,107],"pane",2),
 ("fourth-floor west blue pane",[171,118],"pane",2),("fourth-floor dark central opening",[187,115],"dark opening",2)]
def measure():
    c=Camera("25")
    pairs=[]
    for name,front,rear in RETURNS:
        back=c.wall(rear,0)
        r=c.ray(front)
        ix=[0,2]
        t=np.dot((back-c.c)[ix],r[ix])/np.dot(r[ix],r[ix])
        lead=c.c+t*r
        pairs.append(dict(label=name,front_pixel=front,return_pixel=rear,
                          coincident_xz_front=lead.tolist(),rear_point=back.tolist(),
                          discrepancy_m=float(np.linalg.norm((lead-back)[ix]))))
    return {'station':STATION,'photo_sha256':SOURCE_SHA,'size':[650,487],
            'corners_on_orthogonal_returns':pairs,
            'balcony_front_y_m':-.79,'evidence_width_m':[2.66,3.02],
            'part_mouth_xz':[-6.72,.84,-3.82,12.95],
            'observed_slots':{'row_y':328,'u_centres':[174,181,188,195,202],
                              'x_centres_m':[float(c.wall((x,328),-.79)[0])for x in [174,181,188,195,202]]},
            'limits':['Single station. The rear point is constrained to the known wall plane. The roof corner has a 0.25m XZ discrepancy and receives lower confidence than the other five returns.',
                      'Only the five slots visible east of the tree canopy are represented. Foliage hides the rest of the lower panel.',
                      'The fourth-floor second bay from the west is dark, increasingly recessed relative to the flanking glazed bays. Sliding/open state is plausible; the swing angle is unconstrained.',
                      'The right return of the white third-floor window is visible and separate. The shaded west return and rear of the dark opening use simple closure.'],
            'first_hit_controls':[{'name':n,'xy':xy,'role':r,'tol_native_px':t} for n,xy,r,t in PIXELS]}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);a=p.parse_args()
    a.output.write_text(json.dumps(measure(),ensure_ascii=False,indent=2)+'\n')
