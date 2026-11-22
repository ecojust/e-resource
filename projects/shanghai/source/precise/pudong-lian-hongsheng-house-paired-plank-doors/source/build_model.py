"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
import package_architectural_model as package
from gate_leaves import PALETTE,add_building
META={'id': 'pudong-lian-hongsheng-house-paired-plank-doors', 'name': '连宏生宅石库门双扇木门与斜角锁牌', 'scope': '石库式主门的两扇深色木门由纵向板条拼合。两道圆头铁钉跨过板缝；两块浅色方锁牌角度不同，在中央缝前由铁眼、短搭件和一把小挂锁相连。', 'model_scope_zh': '石库式主门的两扇深色木门由纵向板条拼合。两道圆头铁钉跨过板缝；两块浅色方锁牌角度不同，在中央缝前由铁眼、短搭件和一把小挂锁相连。', 'estimated': '原门没有同平面标尺。按照片透视校正，以门扇总净宽约1.63米估算板宽和钉距。背面与板厚按几何封合；两扇的前后偏差、木纹、铁件厚度和局部磨损均为估算。', 'viewer_page': 'lian-hongsheng-house-paired-plank-doors.html', 'geometry_license': 'MIT', 'source_reference_only': True, 'copyright': '研究依据Dragon发表于美篇的连氏民宅实地记录。作者注明照片均摄于2020年6月26日；引用第16、18、19、20和26张。此页呈现原创模型，照片由原作者保有权利。', 'photo_credit': '研究依据Dragon发表于美篇的连氏民宅实地记录。作者注明照片均摄于2020年6月26日；引用第16、18、19、20和26张。此页呈现原创模型，照片由原作者保有权利。', 'photo_source': 'https://www.meipian.cn/3fwz5d18', 'derivative_license_url': 'https://opensource.org/license/mit/'}
if __name__ == '__main__':
    write_json = package.write_json
    def write_with_rights(path,value):
        if path.name=='manifest.json':
            value=dict(value,geometry_license='MIT')
        write_json(path,value)
    package.write_json=write_with_rights
    package.build(SOURCE,META,PALETTE,add_building)
