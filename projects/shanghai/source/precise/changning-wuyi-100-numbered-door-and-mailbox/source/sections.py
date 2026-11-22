from addressed_door import *
def test(tri,names,hit):
    rows=[]
    def check(x,z,mat,text):
        a=hit(tri,names,np.array([x,-.72,z]),np.array([0,1,0.]));assert a and a[0]==mat,(x,z,mat,a)
        rows.append(dict(label=text,material=mat,point=a[1]))
    for u in np.linspace(-.44,.23,9):
        for h in [.30,.64,.90,1.22,1.61,1.861]:check(u,h,DOOR,'Dark entrance leaf behind the reveals')
    for u in [-1.07,-.88,1.043,1.154]:
        for h in [.387,.808,1.17,1.53,1.909,2.27]:check(u,h,BRICK,'Surviving masonry outside the landing')
    for lines,base,mat in texts():
        for c,p in lines:
            for section in getattr(p,'geoms',[p]):
                if section.area<.00005:continue
                q=section.representative_point();check(q.x,q.y,mat,'Visible posted address '+c)
    for h in [.22,.57,.98,1.39,1.78]:check(-.64,h,SAND,'Deep left door reveal')
    for z in [1.297,1.346,1.407,1.463]:check(.684,z,MAIL,'Mailbox enamel front')
    return rows
