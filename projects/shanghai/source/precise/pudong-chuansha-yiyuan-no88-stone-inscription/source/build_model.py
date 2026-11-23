"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
import package_architectural_model as package
from plaque import PALETTE,add_building
META={'id': 'pudong-chuansha-yiyuan-no88-stone-inscription', 'name': '川沙以园北城壕路88号四字石额', 'scope': '88号门上方有一块横向浅色石额。槽内四组旧字留有阴影，匾外从高起的窄唇，经斜面、圆线和小凹线退入字面。模型保留在2018年和2021年两张照片上都能辨认的字形和框线。', 'model_scope_zh': '88号门上方有一块横向浅色石额。槽内四组旧字留有阴影，匾外从高起的窄唇，经斜面、圆线和小凹线退入字面。模型保留在2018年和2021年两张照片上都能辨认的字形和框线。', 'estimated': '2021年照片中匾高约九个砖皮。取每皮约6.6厘米作展示尺度，外框约1.86×0.60米；石额的真实厚度、浅浮雕深度及已磨失的笔端仍是估计。', 'viewer_page': 'chuansha-yiyuan-no88-stone-inscription.html', 'geometry_license': 'MIT', 'source_reference_only': True, 'copyright': '2018年1月30日新浪新闻转刊的以园报道附刻石近照。行走江湖的土豆于2021年1月分享的照片同时拍到88号与原匾。报道按画面从左到右记为“宏德以道”。摄影作品版权归原权利人；公开模型采用独立绘制的断面与笔迹。', 'photo_credit': '2018年1月30日新浪新闻转刊的以园报道附刻石近照。行走江湖的土豆于2021年1月分享的照片同时拍到88号与原匾。报道按画面从左到右记为“宏德以道”。摄影作品版权归原权利人；公开模型采用独立绘制的断面与笔迹。', 'photo_source': 'https://k.sina.com.cn/article_6430516229_17f49e405001002jbj.html', 'derivative_license_url': 'https://opensource.org/license/mit/'}
if __name__ == '__main__':
    write_json = package.write_json
    def write_with_rights(path,value):
        if path.name=='manifest.json':
            value=dict(value,geometry_license='MIT')
        write_json(path,value)
    package.write_json=write_with_rights
    package.build(SOURCE,META,PALETTE,add_building)
