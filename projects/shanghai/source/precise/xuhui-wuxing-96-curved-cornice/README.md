# 吴兴路96号花园住宅圆角檐口与窗罩

从大檐的卷边往下看，釉面砖饰带绕过墙体的圆角。浅色竖条一侧是较低的矩形窗头，另一侧是弧窗。弧窗上方的砖腰向外挑出，最上缘有一道浅色水刷石窄唇。模型依照建筑史刊物配图制作，截面两端为展示断面。

[查看三维构件](../../../wuxing-96-curved-cornice.html) · [出版照片的局部轮廓与取色记录](measurements/published-cornice-detail.json) · [正式名录](measurements/municipal-listing.json)

## 复原依据

东方网2021年12月12日的《老建筑的上海故事》将住宅年代记为约1930年，描述了圆弧转角、釉面砖和窗上水刷石雨檐。配图中可分辨主檐的暗线、浅色窗侧条和弧窗上沿。上海市优秀历史建筑名录将住宅收录为第四批4D043。名录所列领事馆旧称的使用时期仍有争议。[建筑史文章](https://news.qq.com/rain/a/20211212A02HAH00) · [上海市房屋管理局名录](https://fgj.sh.gov.cn/yxlsjz/20200331/e3b99cf457ae48cab87ad5c02aa0fee3.html)

视图使用相对尺度。照片没有提供构件实测尺寸，弧线半径、砖缝宽度、檐底背面和截断处厚度由作者按可见轮廓推定。模型用于独立观察历史装饰细部。

## 生成与检查

在本目录运行下列命令可分别生成可编辑原始网格和远景网格。使用项目的 Python 建模依赖。

```sh
python source/build_model.py --output cornice-full.glb
python source/build_model.py --output cornice-lod.glb --lod
```

如已安装 Blender、gltfpack 和 Open Image Denoise，可执行完整打包。原生文件保留分组、七个相机以及水刷石的贴图和 UV。

```sh
python source/build_model.py --out export --audit audit
```

在原图三道剖线中，窗罩浅色窄唇占罩顶至钢窗上框高度的21%到25%。模型取22%。[三道剖线读数与材料文献](measurements/published-window-hood-finish.json)

水刷石纹理由 `source/washed_finish.py` 生成。近景的圆弧分为48段，远景分为14段。原创釉砖以独立砖块和凹缝表现。截面用模型材料区分釉砖、灰缝、卷边、滴水线、钢窗、玻璃和水刷石。

[正面图](study-views/eaves.jpg) · [弧窗雨檐](study-views/hood-lip.jpg) · [仰看檐底](study-views/soffit.jpg) · [照片和纹理权利](SOURCES-LICENSE.md)
