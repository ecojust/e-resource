from round_window_bay import *
def test(tri,names,hit):
    out=[]
    def cast(u,z,material,n):
        t=u/R;origin=np.array(pos(u,z,.64));direction=np.array([-np.sin(t),np.cos(t),0.]);a=hit(tri,names,origin,direction)
        assert a and a[0]==material,(u,z,material,a);out.append(dict(label=n,material=material,point=a[1]))
    for c in [-.75,.75]:
        for dx in [-.415,0,.402]:
            for z in [.94,1.19,1.55,1.72,2.18,2.31]:cast(c+dx,z,GLASS,'Glass behind sash bars')
        for dx in [-.179,.179]:
            for z in [1.08,1.50,2.14]:cast(c+dx,z,FRAME,'Vertical painted steel mullion')
        for z in [1.31,1.91]:cast(c,z,FRAME,'Horizontal sash bar')
    for u in COL:
        for z in [.82,1.01,1.39,1.57,1.85,2.19,2.31,2.413]:cast(u,z,STONE,'Pale engaged shaft')
        for z in [.38,.467,.55]:cast(u,z,RED,'Red oval panel')
    for u in np.linspace(-1.68,1.68,19):
        for z in [.141,.747,2.637,3.082]:
            column_foot=z==.747 and min(abs(u-x) for x in COL)<.145
            cast(u,z,STONE if z==2.637 or column_foot else GREY,'Column foot in front of sill' if column_foot else 'Curved projecting mouldings')
    return out
