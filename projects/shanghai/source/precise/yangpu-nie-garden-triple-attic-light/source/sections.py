from gable_lights import *
def test(tri,names,hit):
    rows=[]
    def check(x,z,m,name):
        ans=hit(tri,names,np.array([x,-.61,z]),np.array([0.,1.,0.]));assert ans and ans[0]==m,(x,z,name,ans)
        rows.append(dict(label=name,material=m,point=ans[1]))
    for z in (.64,.81,1.02,1.19,1.34):
        for x in (-.57,-.52,-.414,-.387,-.16,-.079,0,.065,.158,.39,.426,.534,.568):check(x,z,GLASS,'One of the three recessed lights')
        for x in (-.471,.471):check(x,z,FRAME,'Vertical bar in a side light')
        for x in (-.277,.276,-.86,.88):check(x,z,BRICK,'Brick pier or masonry between lights')
    for x in (-.65,-.53,-.29,0,.31,.52,.64):check(x,.529,STONE,'Shared pale projecting sill')
    for z in (1.746,1.77,1.788):check(0,z,STONE,'Pale wedge over the single curved head')
    return rows
