# 台湾银行大楼东门厅与九江路街面

中山东一路16号台湾银行大楼位于九江路北角，1924年动工，1927年竣工。《黄浦区志》记四层钢筋混凝土建筑。上海市房屋管理局第二批优秀历史建筑名录2A006对应“台湾银行／工艺品进出口公司／中山东一路16号”，又称工艺大楼。项目采用2014年1月14日外滩街角照片可见的四根圆柱、三开间门厅、两排上窗，以及沿九江路的六根方柱、七开间高街墙。檐上的招商银行字样和街角标识取自这张照片。[照片、早期影像和区志](reference-review.json)

东面约18.11米，街墙约40米，主檐顶约24米。高度、柱饰、窗框、石料色泽和端部收边据照片估算；屋顶设备、西端较低的一段、北侧字林大楼及街南华俄道胜银行另列。西端比例由斜视航片和街角透视共同约束。当前OSM记录六层，区志记四层，模型按街面可见层次制作。[地块测量、视角拟合与影像](footprint-review.json)

[打开独立模型](../../../bank-of-taiwan.html) · [下载可编辑Blender、原始GLB、网页近景和远景](../../../assets/models/candidates/huangpu-bank-of-taiwan-building/manifest.json) · [模型与街道实测](../../../data/audit/bank-of-taiwan-v1/README.md)

## 重建

在上海项目目录下运行。需要Python、NumPy、Shapely、FontTools、Blender、gltfpack、ImageMagick和Open Image Denoise。程序将“招商银行”和英文标识制作成有厚度的可编辑轮廓。字体字形取自SIL OFL 1.1授权的Noto Serif CJK SC子集。[字体来源](source/fonts/provenance.json)

```sh
python source/precise/huangpu-bank-of-taiwan-building/source/build_model.py --out /tmp/bank16-assets --audit /tmp/bank16-audit --decoded /tmp/bank16-decoded --blender blender --gltfpack gltfpack --oidn oidnDenoise
python data/audit/bank-of-taiwan-v1/check-street-elevations.py --project . --manifest /tmp/bank16-assets/manifest.json --decoded /tmp/bank16-decoded --out /tmp/bank16-audit/wall-checks.json
python data/audit/bank-of-taiwan-v1/verify-placement.py --manifest /tmp/bank16-assets/manifest.json --work /tmp/bank16-placement --out /tmp/bank16-audit
```
