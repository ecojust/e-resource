from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def palette(base):
    p={k:dict(v) for k,v in base.items()}
    tile=ROOT/'textures';mat={'color':[1.,1.,1.],'roughness':1.,'metallic':1.,
        'texture':str(tile/'bajin-original-pebbledash-basecolor.png'),
        'normal_texture':str(tile/'bajin-original-pebbledash-normal.png'),
        'orm_texture':str(tile/'bajin-original-pebbledash-orm.png'),'normal_scale':.35,
        'extras':{'author':'agent','license':'MIT','repeat_metres':.4,'original_generic_material_not_scan':True,'normal_contract':'No TANGENT; raw V down; encoded G positive PNG derivative','occlusion_strength':.35}}
    p['spatial pebbledash base']=dict(mat);p['unobserved side surface']=dict(mat)
    p['green painted frame']={'color':[.017,.082,.060],'roughness':.66}
    p['white trim']={'color':[.72,.715,.665],'roughness':.84}
    p['spatial glass']={'color':[.075,.115,.115],'roughness':.22,'metallic':.18}
    p['dark door hardware']={'color':[.045,.042,.030],'roughness':.52,'metallic':.25}
    p['estimated plain tile roof']={'color':[.15,.135,.12],'roughness':.92}
    for i,k in enumerate([.94,.97,1.,1.03,1.06]):p[f'flat tile tone {i}']={'color':[.15*k,.135*k,.12*k],'roughness':.90}
    return p
