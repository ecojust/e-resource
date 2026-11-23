"""Frame the reconstructed courtyard and its recorded photographic details in author Z-up coordinates."""
import json,math,struct
from pathlib import Path
HERE=Path(__file__).resolve().parent
def unit(v):
    length=math.sqrt(sum(x*x for x in v))
    return [x/length for x in v]
def dot(a,b):
    return sum(x*y for x,y in zip(a,b))
def cross(a,b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
def rotation_transpose_multiply(R,v):
    return [sum(R[i][j]*v[i] for i in range(3)) for j in range(3)]
def frame_crop(name,cam,rect,range_m):
    x0,y0,x1,y1=rect
    K,R,eye=(cam[k] for k in ('K','R','C'))
    uv=[((x0+x1)/2-K[0][2])/K[0][0],((y0+y1)/2-K[1][2])/K[1][1],1]
    direction=unit(rotation_transpose_multiply(R,uv))
    target=[c+d*range_m for c,d in zip(eye,direction)]
    up=[0,0,1]
    right=unit(cross(direction,up))
    true_up=unit(cross(right,direction))
    # A square of this angular size contains all four image-crop corners.
    # The near-square mobile canvas and wider desktop share these presets.
    spread=0
    for x in (x0,x1):
        for y in (y0,y1):
            ray=unit(rotation_transpose_multiply(R,[(x-K[0][2])/K[0][0],(y-K[1][2])/K[1][1],1]))
            twice=max(abs(dot(right,ray)),abs(dot(true_up,ray)))/dot(direction,ray)
            spread=max(spread,twice)
    return dict(name=name,eye=eye,target=[round(x,5) for x in target],fov=round(math.degrees(2*math.atan(1.08*spread)),3))
def make(mesh):
    data=mesh.read_bytes();size=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+size])
    xyz=[doc['accessors'][q['attributes']['POSITION']] for q in doc['meshes'][0]['primitives']]
    xlo=min(a['min'][0] for a in xyz);xhi=max(a['max'][0] for a in xyz)
    ylo=-max(a['max'][2] for a in xyz);yhi=-min(a['min'][2] for a in xyz)
    zlo=min(a['min'][1] for a in xyz);zhi=max(a['max'][1] for a in xyz)
    center=[(a+b)/2 for a,b in [(xlo,xhi),(ylo,yhi),(zlo,zhi)]]
    # Fit a sphere around the true source bounding box, including mobile crop.
    radius=math.sqrt((xhi-xlo)**2+(yhi-ylo)**2+(zhi-zlo)**2)/2
    direction=unit([-.29,-1,.21]);distance=1.16*radius/math.sin(math.radians(20))
    eye=[p+d*distance for p,d in zip(center,direction)]
    views=[dict(name='庭院立面与双坡屋顶全景',eye=eye,target=center,fov=40)]
    cams=json.loads((HERE/'portico-camera-pair.json').read_bytes())['stations']
    cams['atlas']=json.loads((HERE/'joint-court-roof.json').read_bytes())['atlas_camera']
    for name,key,rect,distance in [
        ('施工照片机位','atlas',(48,14,352,293),17),('庭院远照机位','wide',(75,71,424,345),14),
        ('双柱门廊','portrait',(57,180,1193,1845),7),('门楣砖券与铁花','portrait',(385,650,944,996),7),
        ('柱脚蓝色门牌','portrait',(229,1370,337,1537),5),('墙上历史建筑铭牌','portrait',(77,979,242,1128),8),
        ('双扇老虎窗','atlas',(110,39,190,105),18),('陡山墙与屋脊交会','wide',(255,51,417,176),22),
        ('楼梯间正窗与错层侧窗','atlas',(211,67,319,239),16)]:
        views.append(frame_crop(name,cams[key],rect,distance))
    return views
