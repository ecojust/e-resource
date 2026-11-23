"""Read the two documented courtyard photographs and independently reproduce the finish tiles."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image

HERE = Path(__file__).absolute().parent
sys.path.insert(0, str(HERE.parent/'source'))
import finish_surfaces as finish

PATCHES = {
    '03': {
        'right pink wall below relief': (699,427,730,451),
        'right wall above window head': (638,131,674,144),
        'left foremost column shaft': (296,360,306,412),
        'right foremost column shaft': (477,367,488,392),
        'outer left taller column shaft in shade': (229,289,240,318),
        'landing under the canopy': (354,651,382,658),
        'front stair lip': (385,686,420,691)},
    '05': {
        'bright painted or exposed left wall': (43,154,77,185),
        'recessed wall over the doorway': (428,92,461,106),
        'right wall pier': (734,249,744,279),
        'left taller column': (370,140,383,221),
        'near column shaft': (579,157,591,212),
        'right hand shaft': (683,212,693,256),
        'top landing in partial shade': (504,394,531,398),
        'lower sunny tread': (509,476,534,480)}}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def observations(research):
    sources = {'gao-03':dict(source='https://s15.sinaimg.cn/orignal/001HIrzOzy7MmCNvSJsb2',original_sha256='6eee5065e879bf1ae44685a8d8d4a948b95b9ace0c56b308eb6ea94b64d74e99'),
               'gao-05':dict(source='https://s2.sinaimg.cn/orignal/5d1bdf48gx6DgReH1wB51',original_sha256='3a41c0e71c97114bc04fc0fda430225f4b20fef4c35122489c43261ab6d83a00')}
    records = {}
    for num, boxes in PATCHES.items():
        p = research / ('gao-'+num+'.jpg')
        image = Image.open(p).convert('RGB')
        source = sources['gao-'+num]
        known_work_bytes = {'03':'02b21432250e66ebd71ddcf6cf502acdd00878655f1dfed875dec0e0a8569de8',
                            '05':'86bb365d5a7ba17973d90a380950d90f8b0512d02391d85ef79fcaed8cc90254'}
        if digest(p) not in (source['original_sha256'], known_work_bytes[num]):
            raise ValueError('Photo differs from the approved source')
        samples = []
        for name, box in boxes.items():
            a = np.asarray(image.crop(box)).reshape(-1,3)
            samples.append({'location':name, 'pixel_box_left_top_right_bottom':box,
                'srgb_p10_p50_p90':np.round(np.percentile(a,[10,50,90],axis=0),1).tolist()})
        records[num] = {'image_dimensions':image.size,'url':source['source'],'original_file_sha256':source['original_sha256'],
                        'measured_work_copy_sha256':digest(p),
                        'samples':samples}
    return records


def verify():
    out = {}
    with TemporaryDirectory() as temp:
        scratch = Path(temp)
        finish.generate(scratch)
        for n,rec in finish.SURFACES.items():
            if n == finish.ROOF:
                continue
            colour, normal = finish.FILENAMES[n], finish.NORMAL_FILENAMES[n]
            for name in (colour,normal):
                if (scratch/name).read_bytes() != (finish.HERE/name).read_bytes():
                    raise ValueError(name+' did not reproduce')
            rgb = np.asarray(Image.open(scratch/colour),dtype=float)
            norm = np.asarray(Image.open(scratch/normal),dtype=float)/127.5-1.
            lengths = np.linalg.norm(norm,axis=2)
            if np.max(np.abs(lengths-1))>.007 or norm[:,:,2].min()<=0:
                raise ValueError('Incomplete tangent normal')
            out[n]={'authored_srgb_reference':rec[2], 'roughness':rec[3],
                'repeat_m':rec[1], 'height_field_multiplier_mm':1000*rec[4],
                'mean_colour_srgb':np.round(rgb.mean(axis=(0,1)),2).tolist(),
                'normal_tilt_p95_deg':round(float(np.percentile(np.degrees(np.arccos(
                    np.clip(norm[:,:,2]/lengths,-1.,1.))),95)),2),
                'files':{name:{'sha256':digest(scratch/name), 'bytes':(scratch/name).stat().st_size}
                         for name in (colour,normal)}}
    return out


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('research',type=Path)
    parser.add_argument('report',type=Path)
    args=parser.parse_args()
    report={'photo_observations':observations(args.research), 'original_procedural_finishes':verify(),
        'interpretation_zh':[
           '03正照可区分粉米色的厅外抹面、灰白至青灰的圆柱和较浅的台口。05斜照的柱身更亮，左右受光差异明显，浅色水平踏面与深阴影踢面的边线连续。',
           '05的左侧墙几处高光接近过曝，03的廊内石面明显受冷色天空和深阴影影响。两张照片均无标准色卡，采样记录的是成像后的RGB。',
           '主墙微粗拉毛、柱面磨光细粒、踏面浅色磨耗为程序化外观解释。材料矿种、粒径、真实粗糙度、制作工艺及原始涂层未经现场取样。三种纹理均由种子和模型米制周期生成。',
           '保留两张照片的测区、数字结果和出处；模型文件只嵌自主绘制的连续颜色及切线法线。']}
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
