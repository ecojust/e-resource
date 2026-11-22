from four_chevron_sashes import *
def test(t,names,hit):
    rows=[]
    def r(x,z,m,label):
        a=hit(t,names,np.array([x,-.8,z]),np.array([0.,1,0]))
        assert (a[0] if a else None)==m,(x,z,m,a)
        rows.append(dict(label=label,material=a[0] if a else None,point=a[1] if a else None))
    heights=np.linspace(LOW+.047,HIGH-.046,5)
    for i in range(4):
        c=(i-1.5)*P
        for j,(base,top) in enumerate(zip(heights,heights[1:])):
            mid=(base+top)/2
            for sign in (-1,1):
                r(c+sign*(P/2-.026)/2,mid,BAR,'Diagonal at half-height of one cell')
                r(c+sign*.147,mid,GLASS,'Pane beside a diagonal')
            r(c,mid,BAR,'Central upright')
        for z in heights[1:-1]:r(c+.072,z,BAR,'Horizontal glazing rail')
        for z in (.56,1.03,1.60):r(c+P/2-.014,z,FRAME,'Outer stile of each shutter')
    for x in (-1.13,1.15):
        for z in (.12,.44,.91,1.34,1.81,2.15):r(x,z,WALL,'Ochre masonry beside the opening')
    return rows
