"""Generate an original running-bond brick and weathered lime finish in metre coordinates."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMAGE = HERE / 'weathered-shanghai-brick.png'
MATERIAL = 'Blue and red warehouse brick with lime residue'
SPAN = 37.0
HEIGHT = 19.0
SIZE = (1296, 720)


def uv(point):
    x, _, z = point
    return .5 + x / SPAN, 1. - (z + .20) / HEIGHT


def field(random, columns, rows):
    import numpy as np
    from PIL import Image
    values = random.integers(0, 256, (rows, columns), dtype=np.uint8)
    return np.asarray(Image.fromarray(values).resize(SIZE, Image.Resampling.BICUBIC), dtype=float) / 255.


def generate():
    import numpy as np
    from PIL import Image
    rng = np.random.default_rng(19021295)
    width, height = SIZE
    x = ((np.arange(width) + .5) / width - .5) * SPAN
    z = (1 - (np.arange(height) + .5) / height) * HEIGHT - .20
    xx, zz = np.meshgrid(x, z)
    # Each course has its own small alignment error. The brick centres keep
    # a half-bond offset from the neighbouring row even across the broad lime patches.
    rows = np.floor((zz + 1.0) / .082).astype(int)
    offsets = rng.uniform(-.012, .012, rows.max() + 1)[rows]
    progress = (xx + 22.0 + .133 * (rows % 2) + offsets) / .266
    cols = np.floor(progress).astype(int)
    keys = (rows.max()+1, cols.max()+1)
    ceramic = rng.normal(0, 7, keys)[rows, cols]
    restored = field(rng, 37, 19)
    coarse = field(rng, 92, 54)
    grain = field(rng, 239, 137)
    patina = .47 * restored + .34 * coarse + .19 * grain
    joint_x = np.minimum(progress % 1., 1 - progress % 1.) * .266
    joint_z = np.minimum((zz + 1.0) % .082, .082 - (zz + 1.0) % .082)
    mortar = np.clip((.013 - np.minimum(joint_x, joint_z)) / .013, 0., 1.)
    # The reddish layer is strongest immediately below both belt courses,
    # around the perforated attic and in isolated surviving lower patches.
    red_zone = .20 + .47*np.exp(-((zz-7.55)/.37)**2) + .30*np.exp(-((zz-12.9)/1.23)**2)
    red = np.clip((red_zone + .60 * restored + .31*coarse - .69)*2.6, 0., 1.)
    rgb = (1-red[...,None])*np.array([128,127,118]) + red[...,None]*np.array([162,116,95])
    rgb += ceramic[...,None]
    lime = np.clip(.23+(patina-.39)*1.2,.13,.74)
    rgb = rgb * (1-lime[...,None]) + lime[...,None] * np.array([191,187,173])
    rgb += (14 * (coarse-.5) + rng.normal(0,3.2,(height,width)))[...,None]
    light = np.clip(.42 + .48*coarse,0,1)*mortar
    rgb = rgb*(1-light[...,None]) + light[...,None]*np.array([189,184,168])
    skirt = np.exp(-np.maximum(zz,0)/.57) * (.28+.21*coarse)
    rgb = rgb*(1-skirt[...,None]) + skirt[...,None]*np.array([83,85,75])
    # Micro-relief is measured from the actual blind pier in Livelikerw's
    # 2015 CC BY-SA photograph. The sampled patch contains only brickwork.
    sample=np.asarray(Image.open(HERE/'original-brick-sample.png').convert('L'),dtype=float)
    tw=x[None,:]/1.12; th=(zz+.17)/.95
    uu=np.broadcast_to(tw % 1.,zz.shape).copy();vv=th%1.
    uu=np.where((np.floor(tw)+np.floor(th))%2==0,uu,1.-uu)
    vv=np.where(np.floor(tw)%2==0,vv,1.-vv)
    intensity=sample[(vv*(sample.shape[0]-1)).astype(int),(uu*(sample.shape[1]-1)).astype(int)]
    relief=np.clip(intensity-np.median(sample),-51.,59.)
    rgb += (.64*relief)[...,None]
    Image.fromarray(rgb.clip(0,255).astype(np.uint8)).quantize(colors=120,dither=Image.Dither.NONE).save(IMAGE, optimize=True)


def apply(builder):
    if not IMAGE.exists():
        generate()
    builder.palette[MATERIAL] = dict(color=[1.,1.,1.],roughness=.92,metallic=0.,texture=str(IMAGE))
    for part in builder.parts:
        if part['material'] == MATERIAL:
            part['texcoords'] = [uv(point) for point in part['vertices']]
            assert all(0<=u<=1 and 0<=v<=1 for u,v in part['texcoords'])


if __name__ == '__main__':
    generate()
