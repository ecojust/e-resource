from arched_recess import *
def test(tri,materials,hit):
 rows=[]
 def at(x,z,m,label):
  a=hit(tri,materials,np.array([x,-3,z]),np.array([0.,1.,0.]));assert a and a[0]==m,(x,z,m,a)
  rows.append(dict(label=label,material=a[0],point=a[1]));return a[1][1]
 for x in (-1.28,-.87,-.36,.55,.72):
  for z in (.33,.79,1.34,1.93,2.44,3.01,3.49,3.87,4.22):
   assert abs(at(x,z,WALL,'Pierced outer face')+.08)<.001
 for x in (-.13,.083,.294):
  for z in (.78,1.13,1.67,2.24,2.8,3.105):assert abs(at(x,z,INSIDE,'Deep straight reveal and recess back')-.54)<.001
 for x in (-.117,-.05,.10,.23,.32):
  at(x,3.37,INSIDE,'Arched head opening');at(x,3.56,WALL,'Solid render above the arch')
 for x in (-1.27,-.85,-.42,0,.42,.68):
  at(x,4.535,CEMENT,'Shallow lower eaves line');at(x,5.48,CEMENT,'Upper pale relief band')
 for x in np.arange(-1.513,.755,.207):
  at(x,5.251,WALL,'Recess visible through a scallop');at(x+.099,5.251,CEMENT,'Solid tooth between two scallops')
 return rows
