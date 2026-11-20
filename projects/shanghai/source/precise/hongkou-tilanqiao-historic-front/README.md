# 提篮桥旧址长阳路门楼

模型呈现长阳路147号门楼在2015年1月街景中的外观。两侧凹槽竖柱之间悬有宽石额。石额下的红砖框逐层向中心退进，落在连续石基上。右侧白底竖牌保留照片中的八个字。外缘和砖框向后的厚度、石材色泽与总长采用照片推算，立面约宽17.6米、高10米。[建筑档案与照片](reference-review.json) · [独立模型页](../../../tilanqiao-historic-front.html)

上海市房屋管理局第二批优秀历史建筑名录登记号为2F012，列长阳路147号，原文给出“上海监狱”和“提蓝桥监狱”。一张标作1942年前的档案照中，石门额的英文字样清楚可见。2014年和2015年的照片确认门额与凹槽竖柱的基本形制，门额文字已难辨。2024年报道确认整体搬迁，记者的现场图拍的是另一段街墙。历史构件的准确施工年、2015年以后本立面的修缮变化以及左右相邻房屋都另行待核。[房管局原表](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [旧照出处](https://commons.wikimedia.org/wiki/Special:Redirect/page/27174853) · [2015年正面](https://commons.wikimedia.org/wiki/Special:Redirect/page/37791618) · [搬迁报道](https://www.thepaper.cn/newsDetail_forward_27921621)

## 资产与重建

Blender文件含40个可编辑网格，近景及原始GLB各28,296个三角面，远景17,204个。作者按照片构建15种材质。名称直牌的字形来自SIL OFL 1.1许可的思源宋体同源字库Noto Serif CJK SC子集。[清单与四种下载](../../../assets/models/candidates/hongkou-tilanqiao-historic-front/manifest.json) · [字体文件说明](source/fonts/provenance.json) · [原生预览与核验](../../../data/audit/tilanqiao-historic-front-v1/README.md)

在上海项目目录运行以下命令。重建组件使用Python、NumPy、Shapely、fontTools、gltfpack、Blender、ImageMagick以及Open Image Denoise。三个工具参数也可使用本机绝对路径。输出目录中含近景、远景、原始GLB和可编辑Blender文件。作者源将竖槽、砖框、石基、铭牌、门额及素色背面分组，便于按新的公开测绘资料修订。

```sh
python source/precise/hongkou-tilanqiao-historic-front/source/build_model.py \
  --out /tmp/tilanqiao-model --audit /tmp/tilanqiao-audit --decoded /tmp/tilanqiao-decoded \
  --blender blender --gltfpack gltfpack --oidn oidnDenoise
python data/audit/tilanqiao-historic-front-v1/check-relief.py \
  --project . --decoded /tmp/tilanqiao-decoded --manifest /tmp/tilanqiao-model/manifest.json \
  --out /tmp/tilanqiao-audit/relief-checks.json
```
