"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
import package_architectural_model as package
from copper_dormer import PALETTE,add_building
META={'id': 'changning-xingguo-second-garden-dormer', 'name': '兴国宾馆一号楼园侧第二樘铜包老虎窗', 'scope': '一号楼花园侧有一列五樘老虎窗。从草坪看过去，左起第二樘以浅绿金属包边围住双扇窗。两扇各有一根竖梃与三道横梃，外侧金属颊板有竖向压缝，屋坡与颊板以一条斜泛水相接。', 'model_scope_zh': '一号楼花园侧有一列五樘老虎窗。从草坪看过去，左起第二樘以浅绿金属包边围住双扇窗。两扇各有一根竖梃与三道横梃，外侧金属颊板有竖向压缝，屋坡与颊板以一条斜泛水相接。', 'estimated': '依据2007年西南斜照量取窗格、包边和侧面折线，2015年正面照核验窗数与顺序。窗体名义宽1.30米，窗下部分、右侧覆板深度和接缝折高为估计。', 'viewer_page': 'xingguo-second-garden-dormer.html', 'geometry_license': 'CC BY-SA 4.0', 'source_reference_only': True, 'copyright': 'CyberCop，2007年12月31日拍摄，CC BY 3.0。Legolas1024，2015年3月14日拍摄，CC BY-SA 4.0。模型按两件园侧照片重新绘制，以CC BY-SA 4.0发布。', 'photo_credit': 'CyberCop，2007年12月31日拍摄，CC BY 3.0。Legolas1024，2015年3月14日拍摄，CC BY-SA 4.0。模型按两件园侧照片重新绘制，以CC BY-SA 4.0发布。', 'photo_source': 'https://commons.wikimedia.org/wiki/File:Inside_Radisson_Hotel_Compound_-_panoramio_-_CyberCop.jpg', 'derivative_license_url': 'https://creativecommons.org/licenses/by-sa/4.0/'}
if __name__ == '__main__':
    write_json = package.write_json
    def write_with_rights(path,value):
        if path.name=='manifest.json':
            value=dict(value,geometry_license='CC BY-SA 4.0')
        write_json(path,value)
    package.write_json=write_with_rights
    package.build(SOURCE,META,PALETTE,add_building)
