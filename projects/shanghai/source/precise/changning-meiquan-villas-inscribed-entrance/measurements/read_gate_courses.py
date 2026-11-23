"""Recover the vertical pitch of primary bed joints from independently marked image rows."""
from pathlib import Path
import json
import numpy as np
from register_gate import Camera
DATA={'8-1502':(214,[413,426,440,455,469,483,497,511,525,539,554,567]),
      '9-1310':(281,[373,384,394,405,416,427,438,448,459,470,480,491]),
      '9-2002':(385,[387,396,403,411,419,427,435,442,451,459,466,475,482])}
def read():
    out={}
    for n,(x,rows)in DATA.items():
        cam=Camera(n);zz=[float(cam.wall([x,y])[2]) for y in rows]
        out[n]={'column_u':x,'primary_joint_rows':rows,'reprojected_z':zz,'median_pitch_m':float(np.median(-np.diff(zz)))}
    return out
if __name__=='__main__':
    import argparse
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('output',type=Path);a=cli.parse_args();a.output.write_text(json.dumps(read(),indent=2)+'\n')
