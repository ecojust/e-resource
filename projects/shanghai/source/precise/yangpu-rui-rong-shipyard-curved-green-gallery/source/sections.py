from curved_gallery import *
def test(tri,names,hit):
 rows=[]
 def check(u,z,m,label):
    a=u/R;x,y,_=pos(u,z,1);ans=hit(tri,names,np.array([x,y,z]),np.array([-sin(a),cos(a),0.]))
    assert ans and ans[0]==m,(u,z,label,ans)
    rows.append(dict(label=label,material=m,point=ans[1]))
 for level in FLOORS:
    for center in WINDOWS:
        for dx in (-.126,.126):
            for z in(.74,.92,1.044,1.225,1.310):check(center+dx,level+z,GLASS,'Tall corner window above the guardrail')
        check(center,level+.95,SASH,'Central vertical glazing bar')
        check(center,level+1.146,SASH,'Heavy transom')
    for u in(-1.55,-.91,-.45,-.13,.15,.53,.88,1.36):
        check(u,level+.65,BAR,'Upper green rail at a known angle')
        check(u,level+.14,CAP,'Curved rim of the gallery floor')
    for u in(-1.27,-.423,.423,1.27):check(u,level+.422,BAR,'Middle of hanging arc')
 return rows
