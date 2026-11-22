"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
import package_architectural_model as package
from academy_windows import PALETTE,add_building
META={'id': 'pudong-sanlin-academy-east-triple-arched-windows', 'name': '三林书院筠修精舍东墙三联红砖拱窗', 'scope': '筠修精舍朝东的灰砖墙上有三樘并列尖拱窗。每樘窗下部的两扇木窗分为四列四行玻璃，上亮中央镶一道菱形木格。红砖拱券包住窗楣，在起拱处向下收作短墩，并与横贯的红砖带相接。', 'model_scope_zh': '筠修精舍朝东的灰砖墙上有三樘并列尖拱窗。每樘窗下部的两扇木窗分为四列四行玻璃，上亮中央镶一道菱形木格。红砖拱券包住窗楣，在起拱处向下收作短墩，并与横贯的红砖带相接。', 'estimated': '依据2024年8月19日东立面照片及同次校园踏查。窗外口的名义宽取1.10米，三窗中心间距约2.12米，绝对尺度、窗膛深度、木料截面和被花木遮住的两端窗下缘待现场实测。', 'viewer_page': 'sanlin-academy-east-triple-arched-windows.html', 'geometry_license': 'MIT', 'source_reference_only': True, 'copyright': '现场踏查和照片由Dragon于2024年8月19日拍摄，东立面见该文图41，南面题额及西立面分别见图40、42。模型按三樘实窗的轮廓与木格重新绘制，原照仅供研究。', 'photo_credit': '现场踏查和照片由Dragon于2024年8月19日拍摄，东立面见该文图41，南面题额及西立面分别见图40、42。模型按三樘实窗的轮廓与木格重新绘制，原照仅供研究。', 'photo_source': 'https://www.meipian.cn/58tbiugu', 'derivative_license_url': 'https://opensource.org/license/mit/'}
if __name__ == '__main__':
    write_json = package.write_json
    def write_with_rights(path,value):
        if path.name=='manifest.json':
            value=dict(value,geometry_license='MIT')
        write_json(path,value)
    package.write_json=write_with_rights
    package.build(SOURCE,META,PALETTE,add_building)
