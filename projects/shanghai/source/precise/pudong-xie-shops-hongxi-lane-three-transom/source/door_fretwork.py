"""The dark, square-joined left field of the entrance transom at lane 2, number 3."""
X=[6,24,41,58,75,92,109,126,143,160,177,194,212,229,246]
Y=[7,24,40,56,71,87]
# Short members between measured intersections, listed independently for each row.
H=[[],[0,1,2,4,5,6,9,11,12],[0,2,3,4,6,7,8,10,11,13],
   [0,2,3,4,6,7,8,9,10,12],[0,1,2,4,5,6,8,10,11,12,13],[]]
V=[[0,3,4,7,8,10,14],[0,1,2,3,4,5,6,7,8,9,10,11,13,14],
   [0,1,2,5,6,8,9,11,12,13,14],[0,1,2,3,4,5,6,7,8,9,10,12,14],
   [0,2,3,4,7,8,9,10,11,13,14]]
SCALE=.004
def x(u):return (u-126)*SCALE
def z(v):return (90-v)*SCALE
COLORS={'aged timber':(.227,.155,.112),'pale timber edge':(.270,.190,.145),
        'weathered timber':(.187,.142,.115),'dark transom head':(.138,.105,.080),
        'faded timber board':(.254,.181,.127),'soft brown board':(.217,.149,.109),
        'board joint':(.100,.081,.069),'wood pin':(.132,.089,.059)}
PALETTE={k:dict(color=list(v),roughness=.83)for k,v in COLORS.items()}
FACES=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
def timber(b,label,u0,u1,v0,v1,front,back,material,bevel=False):
    # Front face normal points into the photographed lane. Shallow bevels catch
    # light at the weathered, exposed face of each stick.
    a,d=x(u0),x(u1);lo,hi=z(v1),z(v0)
    if not bevel:
        p=[(a,front,lo),(d,front,lo),(d,back,lo),(a,back,lo),(a,front,hi),(d,front,hi),(d,back,hi),(a,back,hi)]
        b.add(p,FACES,material,label)
        return
    edge=min(.0016,(d-a)*.13,(hi-lo)*.13)
    ring=[(a,lo+edge),(a+edge,lo),(d-edge,lo),(d,lo+edge),
          (d,hi-edge),(d-edge,hi),(a+edge,hi),(a,hi-edge)]
    midx,midz=(a+d)/2,(lo+hi)/2
    face=[(u + edge*.50*(1 if u<midx else -1),v+edge*.50*(1 if v<midz else -1))for u,v in ring]
    rings=[(face,front),(ring,front+edge),(ring,back)]
    p=[(u,y,v)for outline,y in rings for u,v in outline];f=[]
    for k in range(1,7):f.extend([(0,k,k+1),(16,17+k,16+k)])
    for k in range(2):
        for i in range(8):
            j=(i+1)%8;a0=k*8+i;a1=k*8+j
            f.extend([(a0,a0+8,a1+8),(a0,a1+8,a1)])
    b.add(p,f,material,label)

def add_building(b,lod):
    timber(b,'street side head timber',0,250,-9,8,-.017,.091,'dark transom head',not lod)
    timber(b,'bottom timber of open screen',0,250,85.8,94,-.006,.075,'weathered timber',not lod)
    timber(b,'raised narrow bead below transom',0,250,92,95,-.012,.026,'aged timber',not lod)
    timber(b,'narrow moulding above fretwork',0,250,4.5,8,-.010,.047,'aged timber',not lod)
    # Actual planking of the weatherboard above the lintel. The model stops at
    # the photographed left field; the adjoining, brightly backlit panel is excluded.
    timber(b,'rebate behind upper planks',0,250,-47,-8,.024,.053,'board joint')
    board_edges=[0,24,51,80,105,135,157,181,206,230,250]
    for i,(a,d) in enumerate(zip(board_edges,board_edges[1:])):
        timber(b,f'upper board {i+1}',a+.28,d-.28,-47,-8,-.003+(i%3)*.001,.026,
               ('faded timber board','soft brown board','aged timber')[i%3],not lod)
    for row,indices in enumerate(V):
        for col in indices:
            u=X[col];material=('aged timber','weathered timber','pale timber edge')[(col+row)%3]
            timber(b,f'vertical timber {row+1}.{col+1}',u-1.36,u+1.36,Y[row],Y[row+1],.003,.034,material,not lod)
    for row,indices in enumerate(H):
        for col in indices:
            v=Y[row];material=('aged timber','weathered timber','pale timber edge')[(col+row+1)%3]
            timber(b,f'horizontal timber {row+1}.{col+1}',X[col],X[col+1],v-1.24,v+1.24,.002,.032,material,not lod)
