import sys,json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from arguments import PACKAGE,workdir
P=workdir();S=PACKAGE/'baseline-source';sys.path.insert(0,str(S))
import architecture as A,build_art_deco as G
rows=[];old=A.Facade.window;arc=A.Facade.arch;oc=A.Facade.oculus

def sample(f,u,z,w,h,kind):
 for du,dz in [(0,0),(-.23,-.18),(.23,.18)]:rows.append({'builder':f.b.name,'point':list(f.p(u+w*du,z+h*dz,2.0)),'normal':list(f.n),'kind':kind})
def window(f,u,z,w,h,*args,**kw):sample(f,u,z,w,h,'rectangle');return old(f,u,z,w,h,*args,**kw)
def arch(f,u,zbase,spring,r,top,cell0,cell1,*args,**kw):sample(f,u,(zbase+spring)/2,r*2,spring-zbase,'arch');return arc(f,u,zbase,spring,r,top,cell0,cell1,*args,**kw)
def oculus(f,u,z,r,*args,**kw):sample(f,u,z,r,r,'oculus');return oc(f,u,z,r,*args,**kw)
A.Facade.window=window;A.Facade.arch=arch;A.Facade.oculus=oculus
for bid,fun in [('bund19',G.south),('bund20',G.north),('bund23',G.bank)]:
 rows.clear();fun();(P/f'{bid}-aperture-rays.json').write_text(json.dumps(rows,separators=(',',':')));print(bid,len(rows))
