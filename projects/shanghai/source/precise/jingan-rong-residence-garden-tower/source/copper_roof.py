"""Panelled red dome with inset ribs, horizontal joints and the finial in the two exterior views."""
from math import cos, pi, sin
from pathlib import Path
from garden_tower import OCHRE, RIB, ROOF

TEXTURE=Path(__file__).with_name('copper-panel-courses.png')


def make_texture(path):
    import numpy as np
    from PIL import Image
    rng=np.random.default_rng(1861918)
    width,height=768,384
    noise=np.asarray(Image.fromarray(rng.integers(0,256,(21,62),dtype='uint8')).resize((width,height), Image.Resampling.BICUBIC),float)
    finish=np.empty((height,width,3),float)
    yy,xx=np.indices((height,width))
    for row in range(9):
        band=(yy*9//height==row)
        columns=max(8,28-2*row)
        u=(xx/width*columns+(row%2)*.5)
        pick=np.floor(u).astype(int)%columns
        tone=rng.normal(0,10,(columns,1))
        patina=rng.normal(0,2.2,(columns,3))
        base=np.array([148,103,86])+(tone+patina)[pick]
        joint=(np.mod(u,1)<.029)|(np.mod(yy*9/height,1)<.046)
        wash=(noise-128)*.076+rng.normal(0,2.8,(height,width)) - joint*20
        finish[band]=(base+wash[:,:,None])[band]
    im=Image.fromarray(np.clip(finish,0,255).astype('uint8'))
    im.quantize(colors=128,dither=Image.Dither.NONE).save(path,optimize=True)


def dome(builder, dims, lod):
    if not TEXTURE.is_file():make_texture(TEXTURE)
    builder.palette[ROOF]={'color':[1,1,1],'metallic':.35,'roughness':.71,'texture':str(TEXTURE)}
    roof=dims['fitted_elevations_m'];base=roof['parapet']-.09;top=roof['finial']
    axis=(0,dims['dome_axis_setback_m'])
    courses=9 if lod else 22
    sectors=32 if lod else 64
    # The broad red cap ends in a neck and a two-stage taper, visible above the garden and road.
    cap_height=top-base-.65
    radius=2.13
    def profile(fraction):
        a=fraction*pi/2
        return radius*(.17+.83*cos(a)**.76),base+cap_height*sin(a)
    vertices=[];faces=[];uv=[]
    for j in range(courses+1):
        radius_j,z=profile(j/courses)
        for k in range(sectors+1):
            a=2*pi*k/sectors
            vertices.append((axis[0]+radius_j*cos(a),axis[1]+radius_j*sin(a),z))
            uv.append((k/sectors,1-j/courses))
    for j in range(courses):
        for k in range(sectors):
            n=j*(sectors+1)+k
            faces.append((n,n+1,n+sectors+2,n+sectors+1))
    builder.add(vertices,faces,ROOF,'Copper dome / staggered panel field')
    builder.parts[-1]['texcoords']=uv
    for k in range(8):
        a=2*pi*k/8
        points=[]
        for j in range(courses+1):
            r,z=profile(j/courses)
            points.append((axis[0]+(r+.012)*cos(a),axis[1]+(r+.012)*sin(a),z))
        builder.tube(points,.027 if lod else .022,RIB,5 if lod else 7,'Copper dome / standing ribs')
    builder.lathe(axis,[(base-.015,2.135),(base+.05,2.14),(base+.105,2.11)],RIB,sectors,'Copper dome / rolled bottom rim')
    neck=base+cap_height
    builder.lathe(axis,[(neck-.04,.37),(neck+.04,.37),(neck+.084,.307),(neck+.105,.19),
                        (neck+.155,.225),(neck+.21,.235),(neck+.25,.16),(neck+.265,.10),
                        (neck+.31,.128),(neck+.37,.144),(neck+.44,.111),(top-.10,.038),(top,.013)],
                  OCHRE,16 if lod else 32,'Copper dome / pedestal double knop and finial')
