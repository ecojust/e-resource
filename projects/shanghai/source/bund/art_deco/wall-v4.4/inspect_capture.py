import bpy,sys,json,math,hashlib
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from arguments import PACKAGE,workdir
P=workdir();S=PACKAGE/'baseline-source';sys.path.insert(0,str(S))
import architecture as A,build_art_deco as G
records=[];contacts=[];arch_old=A.Facade.arch;oculus_old=A.Facade.oculus;panel_old=A.Facade.panel;box_old=A.Facade.box

def panel(self,*args,**kw):
 self._structural_panel=True
 try:return panel_old(self,*args,**kw)
 finally:self._structural_panel=False

def box(self,u,z,w,h,depth,m,d=0):
 structural=getattr(self,'_structural_panel',False)or(m==14 and abs(d+.12)<1e-8 and abs(depth-.48)<1e-8)
 if structural and w>0 and h>0:
  records.append({'builder':self.b.name,'face_ids':list(range(len(self.b.f),len(self.b.f)+5)),'vertex_ids':list(range(len(self.b.v),len(self.b.v)+8)),'a':list(self.a),'u':list(self.u),'n':list(self.n),'bounds':[u-w/2,u+w/2,z-h/2,z+h/2,d-depth,d],'material':m,'kind':'panel'if getattr(self,'_structural_panel',False)else'recessed_spandrel'})
 return box_old(self,u,z,w,h,depth,m,d)
def arch(self,u,zbase,spring,r,top,cell0,cell1,*args,**kw):
 contacts.append({'builder':self.b.name,'a':list(self.a),'u':list(self.u),'n':list(self.n),'u_breaks':[u-r+2*r*i/24 for i in range(25)],'z_breaks':[spring,spring+r]})
 return arch_old(self,u,zbase,spring,r,top,cell0,cell1,*args,**kw)
def oculus(self,u,z,r,cell0,cell1,z0,z1,*args,**kw):
 contacts.append({'builder':self.b.name,'a':list(self.a),'u':list(self.u),'n':list(self.n),'u_breaks':[u-r+2*r*i/24 for i in range(25)],'z_breaks':[z-r,z,z+r]})
 return oculus_old(self,u,z,r,cell0,cell1,z0,z1,*args,**kw)
A.Facade.panel=panel;A.Facade.box=box;A.Facade.arch=arch;A.Facade.oculus=oculus
report=[]
for bid,fun in [('bund19',G.south),('bund20',G.north),('bund23',G.bank)]:
 records.clear();contacts.clear();builders,data,meta=fun();captured=json.loads(json.dumps(records))
 bpy.ops.wm.open_mainfile(filepath=str(PACKAGE/'baseline'/f'{bid}.blend'))
 rows=[]
 for b in builders:
  obj=bpy.data.objects.get(b.name)
  if obj is None:
   matches=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(b.name[:48])];assert len(matches)==1,(b.name,[o.name for o in matches]);obj=matches[0]
  for rec in captured:
   if rec['builder']==b.name:rec['object']=obj.name
  if obj is None:
   rows.append({'builder':b.name,'missing':True});continue
  mesh=obj.data;vv=[(x,y,max(0,z))for x,y,z in b.v]
  maxerr=max((abs(float(mesh.vertices[i].co[k])-vv[i][k])for i in range(min(len(vv),len(mesh.vertices)))for k in range(3)),default=0)
  badfaces=sum(tuple(p.vertices)!=tuple(f)or p.material_index!=m or p.use_smooth!=s for p,f,m,s in zip(mesh.polygons,b.f,b.m,b.sm))
  rows.append({'builder':b.name,'native_vertices':len(mesh.vertices),'source_vertices':len(vv),'native_faces':len(mesh.polygons),'source_faces':len(b.f),'maximum_vertex_delta_m':maxerr,'different_face_order_material_smooth':badfaces,'matrix_world':[list(row)for row in obj.matrix_world]})
 out={'id':bid,'captured':captured,'objects':rows,'contacts':contacts,'native_source_sha256':hashlib.sha256((PACKAGE/'baseline'/f'{bid}.blend').read_bytes()).hexdigest()};(P/f'{bid}-capture.json').write_text(json.dumps(out,ensure_ascii=False))
 print('CAPTURE',bid,len(captured),json.dumps(rows))
