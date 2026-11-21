# 武康大楼东侧副楼临淮海中路立面

1930年增建的五层副楼与1924年的八层武康大楼主楼相接。市房管局的第二批优秀历史建筑2D012把“东美特公寓／武康大楼”登记在淮海中路1842至1858号。陈保平2023年发表的建筑史将东侧“新武康大楼”单列在1828至1834号，记载建筑面积约1700平方米。上海老底子的街区沿革也区别五层副楼、八层老楼及武康路435号的原汽车间。2024年杨宝宝拍摄的大隐书局开业图片中，可以直接读到淮海中路1834号的绿牌，以及同一店面的1834号-1标记。[房管局第二批名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) [陈保平《“登陆船”西来东泊》](https://www.thepaper.cn/newsDetail_forward_23993403) [街区沿革](https://m.thepaper.cn/baijiahao_12171415) [书店门面及门牌照片](https://imagecloud.thepaper.cn/thepaper/image/305/704/715.jpg)

沿淮海中路向东北看，八层主楼的券廊结束处接上副楼的红砖商铺。2020年2月18日的街景提供五层外墙的整体比例，2024年5月照片补足门侧字牌、黑色店框、开敞门洞和邻接的陈列窗。前两层是砖墙，上三层横向钢窗在两端向内转弯。每层的浅色窗间墙和窗台跟着转折，设备罩位置逐层变化。模型中门洞向内表现约1.6米的门槛、两侧与顶面，再以中性截面收住。门牌与店招用可编辑的原创立体字近似现场字形。[书店开业报道](https://www.thepaper.cn/newsDetail_forward_27433871) [实取史料、街景机位、授权与SHA-256](reference-review.json)

冻结来源320与开放地图w1204055641对应，足迹交并比98.89%，面积332.4平方米。临街墙长24.49米。制作深度3.64米，女儿墙顶约18.66米。高度、窗格间距和设备罩尺寸依据照片估算。底图22.40米是对原楼的整体估高。模型以街面中点东经121.43409223度、北纬31.20637358度定位，局部X沿街向东北，Y指向楼内。保留原生背街屋面、后墙、内部和435号院落。[底图与街景机位配准](footprint-review.json) [OpenStreetMap原始建筑环](https://www.openstreetmap.org/way/1204055641)

原武康大楼V5含三个翼端、两个凹口和八层临街券廊。副楼与这套模型分别使用来源320和1235。旧主楼近景的416,668个三角面及远景的283,394个三角面逐档核过，新裁切与其实际几何保留至少0.052米间距。独立入口现有的主楼可继续切换两档。[原武康大楼](../../../index.html#landmark=xuhui-wukang-mansion&mode=overview) [主楼三档保留检查](../../../data/audit/wukang-east-annex-v1/main-building-preservation.json)

[查看副楼模型](../../../wukang-east-annex.html) · [上海地图](../../../index.html#landmark=xuhui-wukang-mansion-east-annex&mode=overview) · [原始与压缩模型、Blender工程](../../../assets/models/candidates/xuhui-wukang-mansion-east-annex/manifest.json) · [几何和地图核验](../../../data/audit/wukang-east-annex-v1/README.md)

## 复建

需要 Python 3、NumPy、Shapely、fontTools、Node.js、Blender、gltfpack、ImageMagick 7 的 `magick` 和 Open Image Denoise 2.5 的 `oidnDenoise`。在 `projects/shanghai` 目录运行以下命令。Blender会重新打开工程并逐材质比对真实三角面。网页近远两档也会分别解压再核对。

```sh
python -B source/precise/xuhui-wukang-mansion-east-annex/source/build_model.py --out /tmp/wukang-annex-model --audit /tmp/wukang-annex-native --decoded /tmp/wukang-annex-decoded --gltfpack gltfpack --oidn oidnDenoise
python -B source/precise/xuhui-wukang-mansion-east-annex/source/check_surfaces.py --manifest /tmp/wukang-annex-model/manifest.json --out /tmp/wukang-annex-surfaces.json
```

几何、材料、脚本按项目MIT许可。门牌和招牌的Noto中文子集按SIL OFL 1.1授权。比对使用的照片、街景及新闻影像由各自权利人持有，工程以原创几何和自制材质表现其外观。底图使用OpenStreetMap和Overture Maps的开放数据。[字体来源](source/fonts/provenance.json) [字体授权书](source/fonts/OFL-and-attribution.txt)
