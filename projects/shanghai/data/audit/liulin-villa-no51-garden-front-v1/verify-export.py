"""Trace the first real surfaces of the 15 photographed No.51 wing openings."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
SRC=Path(__file__).resolve().parents[3]/'source/precise/jingan-liulin-villa-no51-garden-front/source'
sys.path.insert(0,str(SRC))
from read_study import decode,hit
from residence_wings import STUDY,Face,LIME,STONE,WOOD,BRICK,GLASS,BLIND
def inspect(path):
    tris,mats,_=decode(path);rows=[]
    for wing,points in STUDY['corner_chains_m'].items():
        order=['outer','middle','inner'] if wing=='left' else ['inner','middle','outer']
        for k,tag in enumerate(order):
            f=Face(None,points[k],points[k+1],wing+' '+tag)
            normal=np.r_[f.n,0.]
            for win in STUDY['facets'].get(wing+'-'+tag,{}).get('openings',[]):
                l,r,b,t=win['inner_sash_rect_m'];ww=r-l;floor=win['floor']
                name=f.tag+' '+str(floor)
                def probe(label,x,z,surfaces,lo,hi):
                    o=np.asarray(f.point(x,z,-.47));direct=hit(tris,mats,o,normal)
                    distance=(float(np.dot(np.asarray(direct[1])-o,normal))-.47) if direct else None
                    good=bool(direct and direct[0] in surfaces and lo-0.001<=distance<=hi+0.001)
                    rows.append(dict(opening=name,feature=label,origin=o.tolist(),direction=normal.tolist(),expected_material=surfaces,depth_interval_m=[lo,hi],material=direct[0] if direct else None,front_relative_to_wall_m=distance,passed=good))
                for z in (b+.21*(t-b),b+.66*(t-b)):
                    probe('outer jamb',l-.078,z,[LIME],-.044,-.042)
                    probe('outer jamb',r+.076,z,[LIME],-.044,-.042)
                for s in (.22,.63):
                    probe('moulded lintel',l+s*ww,t+.182,[LIME],-.062,-.060)
                    probe('projecting stone sill',l+s*ww,b-.073,[STONE],-.137,-.135)
                probe('brick wall over lintel',l+.381*ww,t+.31,[BRICK],-.002,.002)
                trans=(b+.025)+(t-b-.05)*(.76 if floor in (1,2) else .77)
                if tag=='middle':
                    probe('right transom mullion',l+.67*ww,trans+.54*(t-trans),[WOOD],.139,.141)
                for s in (.22,.81):
                    probe('top light glass',l+s*ww,trans+.54*(t-trans),GLASS,.168,.172)
                if wing=='left' and tag=='middle' and floor==2:
                    probe('blinds behind open leaves',l+.48*ww,b+.42*(trans-b),[BLIND],.228,.246)
                else:
                    probe('timber transom rail',l+.41*ww,trans,[WOOD],.103,.105)
    return dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),triangles=len(tris),passed=all(a['passed']for a in rows),cases=rows)
if __name__=='__main__':
    paths=list(map(Path,sys.argv[1:4]));result={}
    for name,p in zip(('raw','full','lod'),paths):result[name]=inspect(p)
    Path(sys.argv[4]).write_text(json.dumps(result,indent=2)+'\n')
    for role,doc in result.items():
        bad=[(x['opening'],x['feature'],x['material'],x['front_relative_to_wall_m'])for x in doc['cases']if not x['passed']]
        print(role,len(doc['cases']),len(bad),bad[:12]);assert not bad
