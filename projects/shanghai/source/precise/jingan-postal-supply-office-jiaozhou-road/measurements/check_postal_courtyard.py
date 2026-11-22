"""Read the signed GLB first surfaces in the facade openings, endwall, eave sections and photo sites."""
from pathlib import Path
import argparse,hashlib,json,sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
import west_masonry as wall
import postal_window_sashes as windows

def check(mesh):
    scene=SerialScene(mesh);checks=[];photo=[]
    glazing={windows.FIXED,windows.SASH,windows.SHADE,windows.PALE,windows.SKY}
    def ray(out,name,origin,direction,limit,allowed,mask=None,**meta):
        hit=scene.ray(np.asarray(origin,float),np.asarray(direction,float),limit,mask)
        found=hit and hit['material'];out.append(dict(feature=name,origin=np.round(origin,5).tolist(),direction=np.round(direction,6).tolist(),surface=found,accepted=allowed,passed=found in allowed,**meta))
    for end,openings in [(False,wall.OPENINGS),(True,wall.LAYOUT['south_windows'])]:
        label='south end 'if end else'west ';D=[-1,0,0]if end else[0,1,0]
        for o in openings:
            u=o['x0']+.278*(o['x1']-o['x0']);z=o['z0']+.269*(o['z1']-o['z0'])
            O=[wall.SOUTH+1.35,u,z]if end else[u,-1.55,z]
            ray(checks,label+o['id']+' sash or glazing',O,D,3.,sorted(glazing))
            ray(checks,label+o['id']+' through the masonry opening',O,D,2.7,[None],mask=lambda m:m==wall.PLASTER)
            z=o['z1']+.038
            O=[wall.SOUTH+1.35,u,z]if end else[u,-1.55,z]
            ray(checks,label+o['id']+' physical lintel',O,D,3.,[wall.IVORY])
            if o['storey']>1:
                z=o['z0']-.068;O=[wall.SOUTH+1.35,u,z]if end else[u,-1.55,z]
                ray(checks,label+o['id']+' projecting sill',O,D,3.,[wall.IVORY])
    for side,bays in [('west',wall.LAYOUT['west_bays']),('south',wall.LAYOUT['south_bays'])]:
        for b in bays:
            if b.get('omit_lower'):continue
            a,c=b['span'];u=a+.18*(c-a);z=.43;O=[u,-1.4,z]if side=='west'else[wall.SOUTH+1.4,u,z];D=[0,1,0]if side=='west'else[-1,0,0]
            allowed=['Door porch | warm grey stone'] if side=='west' and b['name']=='C' else [wall.PLINTH]
            ray(checks,side+' base '+b['name'],O,D,3.,allowed)
    for o in wall.LAYOUT['south_eave_corbel_centres_m']:
        ray(checks,'south eave corbel nose',[wall.SOUTH+.9,o,17.595],[-1,0,0],1.,[wall.IVORY])
    for u in [1.55,3.3,6.9,10.6]:
        ray(checks,'south parapet coping top',[wall.SOUTH-.16,u,19.4],[0,0,-1],1.8,[wall.IVORY])
    ray(checks,'raised pier cap upper plane',[1.14,1.52,19.5],[0,0,-1],1.,[wall.IVORY])
    ray(checks,'entry door behind stone wings',[-13.34,-1.8,2.19],[0,1,0],3.,[wall.DOOR])
    ray(checks,'front west wall opening for the door',[-13.34,-1.8,2.19],[0,1,0],3.,[None],mask=lambda m:m==wall.PLASTER)
    calc=json.loads((HERE/'southern-endwall-photo-registration.json').read_text());P=np.array(calc['reference']['P'])
    eye=np.linalg.solve(-P[:,:3],P[:,3])
    # These pixels are picked in the original January 2015 photograph after the camera pose is frozen.
    # Copper sash bars and glass jointly identify a physical opening, separate from the pale end wall.
    for detail,pts,allowed in [
        ('end A ground glazing',[[452,572],[454,582]],sorted(glazing)),
        ('end A second glazing',[[458,431],[464,442]],sorted(glazing)),
        ('end A third glazing',[[461,307],[459,319]],sorted(glazing)),
        ('end A fourth glazing',[[469,206],[467,215]],sorted(glazing)),
        ('end B third glazing',[[526,345],[528,357]],sorted(glazing)),
        ('end B fourth glazing',[[529,246],[534,258]],sorted(glazing)),
        ('recess flank beside the narrow fourth-storey end window',[[528,258]],[wall.PLASTER]),
        ('end C third glazing',[[569,364],[571,376]],sorted(glazing)),
        ('end C fourth glazing',[[572,279],[573,286]],sorted(glazing)),
        ('render between south end openings',[[492,308],[506,326],[493,442],[499,261]],[wall.PLASTER])]:
        for uv in pts:
            direction=np.linalg.solve(P[:,:3],[*uv,1.])
            ray(photo,detail,eye,direction,85.,allowed,native_uv=uv)
    return dict(asset=scene.asset,sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),physical_count=len(checks),photo_count=len(photo),physical_passed=sum(q['passed']for q in checks),photo_passed=sum(q['passed']for q in photo),checks=checks,photo_first_hits=photo)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mesh',type=Path);ap.add_argument('report',type=Path);a=ap.parse_args()
    j=check(a.mesh);a.report.write_text(json.dumps(j,indent=1)+'\n')
    print(j['physical_passed'],j['physical_count'],j['photo_passed'],j['photo_count'],[(q['feature'],q['surface'])for q in j['checks']+j['photo_first_hits']if not q['passed']][:16])
    raise SystemExit(int(j['physical_count']!=j['physical_passed']))
