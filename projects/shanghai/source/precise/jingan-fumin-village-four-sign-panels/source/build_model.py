"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
import package_architectural_model as package
from letter_rights import write_metadata
from sign_panels import PALETTE,add_building
META={'id': 'jingan-fumin-village-four-sign-panels', 'name': '富民新邨弄口四块字牌与通道过梁', 'scope': '取富民路148—172弄临街入口上方四块浅色方牌。自右向左的“富民新邨”立体深红字、各牌的下缘、过梁底和两侧墙的起端可单独查看。', 'model_scope_zh': '取富民路148—172弄临街入口上方四块浅色方牌。自右向左的“富民新邨”立体深红字、各牌的下缘、过梁底和两侧墙的起端可单独查看。', 'estimated': '依据2017年街面正照取四个字面、石牌与过梁之间的比例。过梁名义全长4.99米，字的凸出高度约2至3厘米，实际未量。', 'viewer_page': 'fumin-village-four-sign-panels.html', 'source_reference_only': False, 'geometry_license': 'Measured photograph-derived shapes of the four claret characters: CC BY-SA 4.0. Original structural model and source code: MIT.', 'copyright': 'Antigng，2017-08-19，《富民新邨》，Wikimedia Commons，CC BY-SA 4.0。 四个红字据实照分色、去除外部电线并补记阴影中的字孔。字的凸出深度为估计。字形改编依CC BY-SA 4.0授权。', 'photo_credit': 'Antigng，2017-08-19，《富民新邨》，Wikimedia Commons，CC BY-SA 4.0。', 'photo_source': 'https://commons.wikimedia.org/wiki/File:%E5%AF%8C%E6%B0%91%E6%96%B0%E9%82%A8.jpg', 'derivative_license_url': 'https://creativecommons.org/licenses/by-sa/4.0'}
if __name__=="__main__":
    write_metadata(package)
    package.build(SOURCE,META,PALETTE,add_building)
