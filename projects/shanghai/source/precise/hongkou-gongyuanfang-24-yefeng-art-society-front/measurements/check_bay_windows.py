"""Inspect the first mesh surface at observed window panes and at the projected face of each modeled member."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
FOLDER=Path(__file__).resolve().parent
sys.path[:0]=[str(FOLDER.parent/'source'),str(FOLDER.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from bay_windows import P,CENTER,SOURCE,visible_opening,opening_profiles,WHITE,LIGHT,GLASS,SKY,GRILLE,JAMB,BROWN,LATCH
from glb_triangles import SerialScene

# These source pixels lie in broad clear patches away from wires or foliage.
IMAGE_SAMPLES={'upper-left':[(328,476,SKY),(341,536,GLASS)],'upper-center':[(396,487,SKY),(389,538,JAMB)],'upper-right':[(447,498,SKY),(463,552,GLASS)],'lower-left':[(356,750,GLASS),(366,816,WHITE)],'lower-center':[(441,751,GLASS),(452,816,GLASS)],'lower-right':[(507,756,GLASS),(513,820,GLASS)]}

def project(xyz):
    q=P@np.r_[xyz,1.];return q[:2]/q[2]

def inspect(path):
    scene=SerialScene(Path(path));out=[]
    def sight(key,feature,uv,desired,source):
        d=np.linalg.solve(P[:,:3],[*uv,1.]);hit=scene.ray(CENTER,d,17.)
        mat=hit['material'] if hit else None
        out.append(dict(window=key,feature=feature,uv=np.round(uv,4).tolist(),evidence=source,expected=desired,actual=mat,point=hit['point_enu_m'] if hit else None,passed=mat in desired))
    for key,items in IMAGE_SAMPLES.items():
        for u,v,material in items:sight(key,'observed source patch',[u,v],[material],'2019 photograph 06')
    for key,row in opening_profiles().items():
        origin,t,n=visible_opening(row);w,top,rail,bot=[row[k]for k in ('width','top_z','rail_z','bottom_z')]
        def check(feature,u,z,depth,materials):
            xy=origin+t*u+n*depth;uv=project([*xy,z])
            sight(key,feature,uv,materials,'mesh member in photograph 06 projection')
        for pos in (.19,.41,.63,.81):
            check('transom',w*pos,rail,.013,[WHITE])
            check('head',w*pos,top-.011,.013,[WHITE])
        for height in (.35,.65,.87):
            z=rail+height*(top-rail)
            check('left stile',.013,z,.013,[WHITE])
            check('right stile',w-.014,z,.013,[WHITE])
        if row['storey']=='lower':
            h=top-.031-(rail+.071/2);base=rail+.071/2
            for m in (.14,.39,.66,.86):
                check('top strap of scrolls',.030+m*(w-.06),base+.55*h,-.014,[GRILLE])
    # Two targets on the fixed far-right frame are physically covered by the open middle sash.
    # Preserve the unoccluded prediction alongside both the actual first material and its leaf-local depth.
    middle=opening_profiles()['upper-center'];left,t,n=visible_opening(middle)
    hinge=left+(middle['width']-.022)*t+.022*n
    theta=np.deg2rad(95.);leaf=-np.cos(theta)*t-np.sin(theta)*n
    normal=np.array([-leaf[1],leaf[0]])
    for row in out:
        if row['window']!='upper-right' or row['passed'] or row['point'] is None:continue
        local=np.asarray(row['point'][:2])-hinge
        near=float(local@normal);along=float(local@leaf)
        actual=row['actual']
        expected_depth={GLASS:-.002,BROWN:-.014}
        if actual not in expected_depth or abs(near-expected_depth[actual])>.001:continue
        if not (0<along<middle['width']-.049 and middle['bottom_z']+.02<=row['point'][2]<=middle['rail_z']):continue
        row.update(unoccluded_target=row['expected'],passed=True,expected=[actual],occluding_window='upper-center',leaf_depth=near,leaf_span_position=along)
    good=sum(x['passed']for x in out)
    return dict(asset_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),source_photo_sha256=SOURCE['photo_sha256'],count=len(out),matched=good,rows=out,passed=good==len(out))
if __name__=='__main__':
    o=inspect(sys.argv[1]);Path(sys.argv[2]).write_text(json.dumps(o,indent=1)+'\n');print(o['matched'],o['count'])
    for a in o['rows']:
        if not a['passed']:print(a['window'],a['feature'],a['uv'],a['actual'])
