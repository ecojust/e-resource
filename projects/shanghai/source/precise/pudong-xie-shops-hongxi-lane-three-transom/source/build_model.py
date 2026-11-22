"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
import package_architectural_model as package
from door_fretwork import PALETTE,add_building
META={'id': 'pudong-xie-shops-hongxi-lane-three-transom', 'name': '谢氏商铺洪西街二弄3号门上透空回纹木格', 'scope': '洪西街二弄3号居室入口的木门上方保留透空格心。左段用短横、短竖木条相接，折出大小相套的直角回纹。上方有竖板和横梁，下沿有一道突出的细木线。', 'model_scope_zh': '洪西街二弄3号居室入口的木门上方保留透空格心。左段用短横、短竖木条相接，折出大小相套的直角回纹。上方有竖板和横梁，下沿有一道突出的细木线。', 'estimated': '原照片中的透空左段约跨14格，实物长度按名义0.96米估算。绝对尺寸、型材深度与侧面收口未取得现场尺量。左下角有电线遮挡，右侧背光格扇落在本段范围以外。', 'viewer_page': 'xie-shops-hongxi-lane-three-transom.html', 'geometry_license': 'MIT', 'source_reference_only': True, 'copyright': 'Dragon在2017年9月3日和9月10日踏查洪西街，第六节第14图记录谢氏商铺居室。其绿牌可读“3／洪西街二弄”，同节另有两张官方登记牌的照片。木作按实照观察重新绘制，照片仅供研究。', 'photo_credit': 'Dragon在2017年9月3日和9月10日踏查洪西街，第六节第14图记录谢氏商铺居室。其绿牌可读“3／洪西街二弄”，同节另有两张官方登记牌的照片。木作按实照观察重新绘制，照片仅供研究。', 'photo_source': 'https://www.meipian.cn/m4bea7k', 'derivative_license_url': 'https://opensource.org/license/mit/'}
if __name__ == '__main__':
    write_json = package.write_json
    def write_with_rights(path,value):
        if path.name=='manifest.json':
            value=dict(value,geometry_license='MIT')
        write_json(path,value)
    package.write_json=write_with_rights
    package.build(SOURCE,META,PALETTE,add_building)
