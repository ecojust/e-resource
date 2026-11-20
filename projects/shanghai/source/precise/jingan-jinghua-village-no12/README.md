# 景华新邨12号弄内门面

巨鹿路820弄12号是画家朱屺瞻的旧居。1959年他迁入三楼，后来将“梅花草堂”画室移至二楼。2020年陆玲拍摄的门面照片上，绿色门牌清楚写着12。2026年《新民周刊》记者重访时，记录了底层长窗与花坛、内退木门上方的横板，以及二楼居中的大窗。[章正元、陆玲《景华新邨的门牌号里，记录着时代的密码》](https://m.thepaper.cn/baijiahao_9362959) · [12号原图](https://imagepphcloud.thepaper.cn/pph/image/90/956/81.jpg) · [喻军《二度“景华村”》](https://paper.xinmin.cn/html/xmzk/2026-06-22/78/65940.html)

房管局第二批名录2B021采用“景华新邨”，地址列巨鹿路820弄1–51号，以及800–818号、822–836号双号。1937年周湘云划出花园土地开发住宅，建筑资料常记1938年竣工；1939年已有22号的实际承租记载。2021年静安区登记的中共江苏省委机关旧址为22号。另一组走访照片中，门牌分别可读为11和43，均保留为街区旁证。[房管局保护名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [静安区文物记录](https://www.jingan.gov.cn/main/ee321d1e-c44f-43c8-be82-4c83427bc68e/ad355c59-5dec-44ae-8b2c-0d8d80592fe4/%E9%9D%99%E5%BA%9C%E5%8F%91%5B2021%5D6%E5%8F%B7.pdf) · [街区摄影及归属](reference-review.json)

模型呈现12号的三层南向立面和约一米墙体截面。木门的嵌板、上亮、门框、绿牌和双灯来自本户照片。二、三层钢窗参考2016年实拍与同排2020年照片，竖墙与平板檐口划分单元。外门照片未显示全部上层窗格，各层高度、花坛深度和材料颜色均为估计。22号、其他住户、巨鹿路沿街商铺，以及画室室内留待各自的图证。[2016年建筑外观](https://commons.wikimedia.org/wiki/File:Jinghua_Xincun_Shanghai.JPG) · [2020年排屋照片](https://imagepphcloud.thepaper.cn/pph/image/85/370/965.jpg)

沿东西向支弄，从主弄西侧这排的东端数，12号位于第四户。2022、2024、2026三个Esri底图版本均可辨八户连续屋顶。剔除偏离本排的13号地址点后，其余七户的间距拟合为5.78米。模型采用约5.78米宽、9.71米高，正面朝南偏东。户界和前墙的绝对位置估计误差约2.5米。冻结城市底图与现行OSM均未画出该排住房。实际检查附近五组近景和远景后，地图采用新增局部门面，原有楼体与遮挡全部保留。[落位图证及可复查影像](footprint-review.json) · [几何与浏览核验](../../../data/audit/jinghua-village-no12-v1/README.md)

[独立模型预览](../../../jinghua-village-no12.html) · [原始GLB、近远景与Blender工程](../../../assets/models/candidates/jingan-jinghua-village-no12/manifest.json) · [地图入口](../../../index.html#landmark=jingan-jinghua-village-no12&mode=overview)

使用Python、NumPy、Shapely、fontTools、Node.js、Blender、gltfpack、ImageMagick 7及Open Image Denoise重建，在项目目录运行下列命令。模型、碰撞与照片均可分别检查。[制作脚本](source/build_model.py)

```sh
python source/precise/jingan-jinghua-village-no12/source/build_model.py --out /tmp/jinghua-build --audit /tmp/jinghua-audit
python source/precise/jingan-jinghua-village-no12/source/check_surfaces.py --manifest /tmp/jinghua-build/manifest.json --out /tmp/jinghua-surfaces.json
```

模型网格采用仓库MIT许可。照片与航片用于独立查核，权利归各来源，未嵌入模型。门牌字形为按SIL OFL 1.1授权、重新命名的Noto Serif CJK子集。[字形来源](source/fonts/provenance.json)
