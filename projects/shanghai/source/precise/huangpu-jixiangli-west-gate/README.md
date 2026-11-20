# 吉祥里山东北路西弄门

上海市第二批优秀历史建筑2A035登记“吉祥里”，门牌印为河南中路531–541号。今住宅的两个东弄口分用河南中路531和541弄，西弄口的绿牌为山东北路22弄。黄浦区委组织部2024年记吉祥里始建于1876年，当年仍有近300户居民。报道中改建的车库在北邻河南中路575弄如意里11号。浦东瑞和路555弄亦有一个名为吉祥里的现代住宅小区。[正式保护表](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [外滩街道及居民近况](https://www.shzhdj.sh.cn/djWeb/djweb/web/djweb/newestindex/newinfo.action?articleid=ff80808190b725300190b90ca648005f) · [保护范围](https://www.openstreetmap.org/way/494958239)

2014年1月27日的里弄照片与2018年唐烨的修缮报道可辨灰砖、成排窗和浅色窗框。黄浦报2018年2月的检索摘要讲到保护范围内A至E幢五栋及约1920–30年代的房屋；该摘要、1876年里弄始建记载与西门本身的建造年分别记录。目前只能给西门外貌确定照片年代。[2014年弄内山墙](https://commons.wikimedia.org/wiki/File:A_Type_of_Shikumen_Gable_in_JixiangLi_Shanghai.JPG) · [2018年入户修缮报道及照片](https://www.shobserver.com/detail/84356.html) · [各项原始取证](reference-review.json)

2013年10月的街照显示左、右两扇铁门向里开启，上层窗下题额有磨蚀，门旁已有绿色22弄牌。2017年10月可直接读到石额的三个字，从右至左为“吉祥里”。2021年1月12日可见灰色墙面、木窗、窗下题额、上部层层收进的山墙和闭合的双扇铁门。模型以这次街面为准，细长的铁条之间透空，门扇在实际放置时封闭。上部比例、铁件细纹及配色根据街照推定，研究照片仅作外部参考。[西门街照的三个年代与拼图原始字节](reference-review.json) · [各站方向、门洞尺寸与屋顶比对](street-registration.json)

从三个街道机位对上弄门两上角，估计宽3.39米，向内约75°。西门位于老弄堂通往山东北路的一端，在城市原近、远景住宅间的实际空位上添加。只建门洞、紧邻的两根门垛、石额、上窗和中央顶饰。两排里弄住宅、东门、相邻商业楼以及有关立信会计教育沿革的18号住宅保留原有状态。[冻结城市数据和相邻房屋](footprint-review.json)

## 重建和核对

可在 `projects/shanghai` 下使用 Blender、Python、Node、gltfpack 和 Open Image Denoise。街门构件按名称保留在原生工程中。题额、弄号和路名使用单独的 Noto 字形子集。[构件参数](source/west_gate.py) · [字体来源及许可](source/fonts/provenance.json)

```sh
python source/precise/huangpu-jixiangli-west-gate/source/build_model.py \
  --out assets/models/candidates/huangpu-jixiangli-west-gate \
  --audit data/audit/jixiangli-west-gate-v1 \
  --decoded /tmp/jixiangli-decoded --blender blender \
  --gltfpack gltfpack --oidn oidnDenoise
python data/audit/jixiangli-west-gate-v1/check-gate.py \
  --project . --manifest assets/models/candidates/huangpu-jixiangli-west-gate/manifest.json \
  --decoded /tmp/jixiangli-decoded --out data/audit/jixiangli-west-gate-v1/gate-checks.json
```

[单体页](../../../jixiangli-west-gate.html) · [可编辑Blender](../../../assets/models/candidates/huangpu-jixiangli-west-gate/huangpu-jixiangli-west-gate.blend) · [原始GLB](../../../assets/models/candidates/huangpu-jixiangli-west-gate/huangpu-jixiangli-west-gate-raw.glb) · [网页近景](../../../assets/models/candidates/huangpu-jixiangli-west-gate/huangpu-jixiangli-west-gate-web.glb) · [网页远景](../../../assets/models/candidates/huangpu-jixiangli-west-gate/huangpu-jixiangli-west-gate-lod.glb)
