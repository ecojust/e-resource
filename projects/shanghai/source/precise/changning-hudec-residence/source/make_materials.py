"""Original deterministic generic PBR atlas; reads no reference photographs."""
from pathlib import Path
import hashlib, json
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'textures';OUT.mkdir(exist_ok=True)
TILE=128;W,H=512,256
names=['white plaster','dark timber','slate-like plain roof','red brick silhouette',
       'window glass','spatial ground base','door wood','dark metal']
colors=[(.81,.80,.74),(.19,.17,.13),(.39,.37,.33),(.48,.25,.17),
        (.26,.34,.35),(.48,.47,.42),(.30,.23,.14),(.19,.21,.20)]
roughness=[.88,.78,.86,.89,.25,.90,.70,.58]
metallic=[0,0,0,0,.22,0,0,.45]
rng=np.random.default_rng(1291930)
base=np.zeros((H,W,3),np.uint8);orm=np.zeros_like(base);normal=np.zeros_like(base)
Y,X=np.mgrid[0:TILE,0:TILE]
for i,(name,color) in enumerate(zip(names,colors)):
    noise=rng.normal(0,1,(TILE,TILE))
    grain=.4*np.sin(X*.6 + np.sin(Y*.045)*1.5)+.15*np.sin(X*1.9+Y*.025)
    variation=noise*.018
    height=noise*.025
    if name in ['dark timber','door wood']:
        variation+=grain*.055;height+=grain*.11
    elif name=='slate-like plain roof':
        lamina=np.sin(Y*.20+np.sin(X*.04))*.5+np.sin(Y*.72)*.13
        variation+=lamina*.025;height+=lamina*.065
    elif name=='red brick silhouette':
        variation+=np.sin(X*.16)*np.sin(Y*.22)*.018;height+=noise*.035
    elif name=='window glass':
        variation=noise*.002+(Y/TILE-.5)*.025;height*=0
    rgb=np.clip(np.asarray(color)[None,None,:]+variation[...,None],0,1)
    dy,dx=np.gradient(height)
    vec=np.stack([-dx,-dy,np.ones_like(dx)],axis=-1)
    vec/=np.linalg.norm(vec,axis=-1)[...,None]
    n=np.clip((vec*.5+.5)*255,0,255).astype(np.uint8)
    o=np.zeros_like(n);o[:,:,0]=255
    o[:,:,1]=np.clip((roughness[i]+noise*.01)*255,0,255).astype(np.uint8)
    o[:,:,2]=int(metallic[i]*255)
    # Eight-pixel duplicated gutter protects every tile from mip bleeding.
    for arr in (rgb,n,o):
        arr[:8]=arr[8];arr[-8:]=arr[-9]
        arr[:,:8]=arr[:,8:9];arr[:,-8:]=arr[:,-9:-8]
    y=(i//4)*TILE;x=(i%4)*TILE
    base[y:y+TILE,x:x+TILE]=(rgb*255).astype(np.uint8)
    normal[y:y+TILE,x:x+TILE]=n;orm[y:y+TILE,x:x+TILE]=o
files=[]
for name,arr in [('basecolor',base),('normal',normal),('orm',orm)]:
    p=OUT/f'hudec-original-{name}.png';Image.fromarray(arr).save(p,optimize=True)
    files.append({'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
report={'schema':'original-procedural-pbr-atlas-v1','author':'agent','license':'MIT',
        'reference_pixels_read':False,'photogrammetry':False,'random_seed':1291930,
        'dimensions':[W,H],'tile_size':TILE,'gutter_pixels':8,'materials':names,'files':files}
aliases={'unverified service plaster':'white plaster','window lead':'white plaster','brick mortar':'spatial ground base'}
report['material_cells']={}
for name in names+list(aliases):
    i=names.index(aliases.get(name,name));x=(i%4)*TILE;y=(i//4)*TILE
    report['material_cells'][name]={'cell_index':i,'cell_pixel_origin':[x,y],
        'gltf_uv_min':[(x+9)/W,(y+9)/H],'gltf_uv_max':[(x+119)/W,(y+119)/H],
        'roughness_byte_center':round(roughness[i]*255),'metallic_byte':int(metallic[i]*255)}
report.update(gltf_v_direction='Positive V goes down the PNG image; no custom V inversion in raw GLB.',
    native_v_policy='Standard Blender glTF importer UV conversion; native verifier compares after standard conversion.',
    uv_projection='Each solid triangle uses its dominant-normal planar axes and per-part bounds; UVs stay9px inside its material tile.',
    uv_interior_margin_pixels=9,wrapS=33071,wrapT=33071,blender_extension='EXTEND',
    base_color_factor=[1,1,1,1],roughness_factor=1,metallic_factor=1,normal_scale=.35,occlusion_strength=.35,
    texture_color_spaces={'basecolor':'sRGB','normal':'Non-Color','orm':'Non-Color'},
    generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(OUT/'ATLAS.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
