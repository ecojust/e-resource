# 华盛顿公寓衡山路街角与高安路48号入口

从衡山路与高安路交叉口可以看到公寓北端的阶梯冠部、成列三面凸窗和转角店铺。沿高安路向南，白色退台门框标出住宅入口。门框上方的花饰窗间墙夹在两列凸窗之间，门边的绿色门牌为48号。[查看可旋转模型](../../../washington-apartments.html)

上海市房管局将本楼列为2D021，登记原名华盛顿公寓、现名西湖公寓、地址衡山路303号。徐汇区房管材料记载该楼1928年开工、1930年建成，原有地上九层，1982年加建两层。这里依据2016年街角实照、2020年出版的高安路门牌和门框近照，以及可辨识门口位置的街景，表现加层后的外观。[上海市房屋管理局名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [徐汇区住房保障和房屋管理局](https://www.xuhui.gov.cn/zfjg_qzfbm_fgj_bmdt/20260514/573099.html) · [徐汇发布的门框和花饰照片](https://m.thepaper.cn/baijiahao_6909484) · [MNXANL的2016年街角照片](https://commons.wikimedia.org/wiki/File:201604_Washington_Apartment_in_Xuhui,_Shanghai.jpg)

## 制作范围和落位

北端切角约8.2米。高安路原轮廓约50.2米，衡山路一侧沿街角返回约18.2米。屋顶只制作这三段墙体上方的窄带。两段街面后方的原楼、内院和衡山路其余门牌保留地图原有几何。其他店招、住宅内部、背街窗墙、整栋屋顶设施仍待核实。外墙色以照片近似，楼高、层高、窗宽和构件进深均为估计值。

地图实名原楼131的中英文名称与现行OpenStreetMap地块一致。以街角为起点，街景三机位估出的门洞沿街位置为31.60米，独立48号门牌点投影位置为31.11米，模型采用31.35米。影像上的屋顶存在建筑倾斜投影，因此地面墙线使用实名原楼和街道轮廓。[街面与航片配准](site-and-roof.json) · [底图与独立邻楼](footprint-review.json) · [照片原始链接和核对记录](reference-review.json)

## 原生制作和交付

构件可在 Blender 中按高安路、北端街角、衡山路和截面选择编辑。建筑以米为单位。外露的窗洞、前凸的三个窗面、入口退台及门后深度均为立体几何。花纹按照片中的卷曲轮廓重绘。照片仅作参考，项目提供的模型使用原创几何与材质。

从上海项目目录执行下列命令。运行环境需 Python、NumPy、Shapely、Node.js、Blender、gltfpack、Open Image Denoise 和 ImageMagick。

```sh
python source/precise/xuhui-washington-apartments/source/build_model.py \
  --out assets/models/candidates/xuhui-washington-apartments \
  --audit data/audit/washington-apartments-v1 \
  --decoded /tmp/washington-apartments-decoded
```

[完整近景](../../../assets/models/candidates/xuhui-washington-apartments/xuhui-washington-apartments-web.glb) · [简化远景](../../../assets/models/candidates/xuhui-washington-apartments/xuhui-washington-apartments-lod.glb) · [无压缩GLB](../../../assets/models/candidates/xuhui-washington-apartments/xuhui-washington-apartments-raw.glb) · [可编辑Blender文件](../../../assets/models/candidates/xuhui-washington-apartments/xuhui-washington-apartments.blend)
