# 圣约翰大学校政厅（四号楼）南廊与望楼

四号楼原为霍格别墅。华东政法大学校史记1863年始建，次年基本建成，1899年大修。圣约翰大学的建筑名录记1911年改用作校长办公室。市房管局登记地址为万航渡路1175号，校方和现行校园门牌使用1575号。[校方四号楼档案](https://www.ecupl.edu.cn/2022/1101/c13514a199601/page.htm) · [登记分项与图像记录](reference-review.json)

项目选取两层主楼的南廊、红漆木窗和镂空栏板、黑铁皮乘车门廊，以及中央翘檐和小望楼。南廊进深约3米由学校文字给定，宽约26.6米取自登记轮廓，屋脊、栏板、门廊和望楼高度依照片估算。北部房间、未摄侧墙、校内别栋另列。

格致楼原为格致室，1899年落成，在校方资料中另列。几份二级资料亦称其曾作校政厅。其面向河岸的拱廊照片和格致楼铭牌分别存档。42号新科学馆、韬奋楼和草坪旁的四号楼各有独立位置。[格致楼校方档案](https://www.ecupl.edu.cn/2022/1101/c13514a193943/page.htm)

[打开单体模型](../../../st-johns-administration.html) · [四件文件及尺寸](../../../assets/models/candidates/changning-st-johns-administration-building/manifest.json) · [图像和几何验收](../../../data/audit/st-johns-administration-v1/README.md)

## 重建

从上海项目目录运行。需要Python、NumPy、Shapely、Blender、gltfpack、ImageMagick及Open Image Denoise。木格、门廊、卷翘铁皮屋面和望楼内的窗扇均为原创几何，学校照片作为外部参照。

```sh
python source/precise/changning-st-johns-administration-building/source/build_model.py --out /tmp/stjohn-assets --audit /tmp/stjohn-audit --decoded /tmp/stjohn-decoded --blender blender --gltfpack gltfpack --oidn oidnDenoise
python data/audit/st-johns-administration-v1/check-veranda.py --project . --manifest /tmp/stjohn-assets/manifest.json --decoded /tmp/stjohn-decoded --out /tmp/stjohn-audit/veranda-checks.json
python data/audit/st-johns-administration-v1/verify-placement.py --manifest /tmp/stjohn-assets/manifest.json --work /tmp/stjohn-placement --out /tmp/stjohn-audit
```
