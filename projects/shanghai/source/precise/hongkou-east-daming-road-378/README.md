# 东大名路378号红砖办公楼街面与塔亭

上海市第二批优秀历史建筑名录2F005列“北方局／远洋运输公司／东大名路378号”。2014年1月27日街照中的红砖楼有面街七开间、两层退台和西侧绿顶塔亭。当地历史条目称耶松船厂旧址并记1908年建造，原始竣工资料仍待核。《二十世纪香港、上海及中国其他商埠印象》中的船坞照片记录船厂业务，街面几何取自2014年可辨建筑照。[原始照片、图版、登记及年代出处](reference-review.json)

模型的街面宽约27.8米，西侧塔顶约26.8米。窗框分格、白色穿孔栏板、屋顶瓦、塔亭和退台依照片透视估算。四期航空底图用于比对轮廓，两转角间的位置与方位可靠度高于塔亭高度。同门牌30层现代总部在另一独立地块。楼后办公区、院内门房和临时脚手架另列。[地块与航片](footprint-review.json)

[打开独立模型](../../../east-daming-378.html) · [下载四件模型文件](../../../assets/models/candidates/hongkou-east-daming-road-378/manifest.json) · [几何与放置检验](../../../data/audit/east-daming-378-v1/README.md)

## 从源文件重建

从上海项目目录运行以下命令。需要Python、NumPy、Shapely、Blender、gltfpack、ImageMagick和Open Image Denoise。Blender文件中的151个网格以部位命名，砖、石饰、窗格、退台、塔身、角部收边和塔顶均可编辑。

```sh
python source/precise/hongkou-east-daming-road-378/source/build_model.py --out /tmp/east-daming-assets --audit /tmp/east-daming-audit --decoded /tmp/east-daming-decoded --blender blender --gltfpack gltfpack --oidn oidnDenoise
python data/audit/east-daming-378-v1/check-street-elevations.py --project . --manifest /tmp/east-daming-assets/manifest.json --decoded /tmp/east-daming-decoded --out /tmp/east-daming-audit/street-checks.json
python data/audit/east-daming-378-v1/verify-placement.py --manifest /tmp/east-daming-assets/manifest.json --work /tmp/east-daming-placement --out /tmp/east-daming-audit
```
