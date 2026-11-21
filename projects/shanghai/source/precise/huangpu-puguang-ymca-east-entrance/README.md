# 浦光大楼 · 四川中路门头与东立面窗墙

四川中路599号的钟门在整段街墙中偏南。历史正面照片中，门南有两道店券，门北有三道。本模型细化钟门、紧邻它的南北两道店券，以及上面两层的六扇窗。街墙的其余开间、晚期加层和后部沿用城市底图。[独立模型](../../../puguang-ymca-east-entrance.html) · [模型范围与资料](reference-review.json)

市房屋管理局第四批优秀历史建筑以4A001登记上海基督教青年会，即浦光大楼、浦光中学，整栋地址为四川中路595–607号。馆藏照片记录了青年会在四川路的原楼。西藏南路的八仙桥青年会和虎丘路的学校校址另有各自的建筑。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20200331/e3b99cf457ae48cab87ad5c02aa0fee3.html) · [明尼苏达大学青年会档案正面原照](https://umedia.lib.umn.edu/item/p16022coll261:2197)

## 街面外观

立面取2023年7月刊出的一组修缮后实照。斩假石门头上有三行英文会名，两侧外柱保留中文会名、会训和小字号纪年。门扇上方的半圆气窗内安有罗马数字圆钟。门北第一道券下为浅灰卷帘，门南一道券下后来填入红砖和横向玻璃窗。两券上方保留深色分格扇窗。楼上的砖柱托住两截断开的斜山花，中间的长窗下探至英文铭额顶端。[修缮后实照与铭文释读](https://news.qq.com/rain/a/20230720A09B2000) · [2022年房管部门的修缮说明](https://www.thepaper.cn/newsDetail_forward_20993211) · [逐幅来源、藏所与许可](photographic-sources.json)

英文三行、两侧中文主刻与年款均切入实体板面，刻槽有底和侧壁。时钟、罗马字盘、两根指针、券肩、石柱卷涡、木门芯板、成组的楔形砖、卷帘和店窗可以独立观察。上层带水平凹槽的砖墩和贴柱从主墙向街面突出。实体模型使用原创线形、砖纹和材质。石柱花叶、门套进深、字形及钟面尺度按照片估计。[门钟和石刻的证据](source/stone-entrance-observations.json)

## 定位与尺度

公开地图的建筑轮廓与冻结城市中2382号楼的平面交并比为0.989。沿街边长37.31米，根据历史正面照片的四个控制点，门轴距南端16.29米。改变控制点后，门轴结果落在15.99至16.59米间。街景车位带有定位误差，模型采用整幅历史正面中门轴相对于街面两端的比例。首层通长线脚按门券净宽与半圆半径估为7.08米。[原城边界与相邻房屋](footprint-review.json) · [馆藏照片像素和投影换算](source/historic-front-measurements.json) · [时间分期的街景位置](source/street-cameras.json)

底层细化宽19.43米，楼上三条窗轴宽15.25米。两段源墙按各自的宽度和高度局部替换。15.04米以上的原楼、未细化街墙与现有街区矢量边界全部保留。模型尺寸依据外部史料估算，室内和隐蔽结构有待补充。[街墙定位参数](source/frontage-registration.json) · [原始三维瓦片复核](../../../data/audit/puguang-ymca-east-entrance-v1/source-cut.json)

## 重建

从上海项目目录运行。需要项目现用的 Python 几何依赖、Blender、gltfpack、Open Image Denoise 和 Node 环境。

```sh
python -B source/precise/huangpu-puguang-ymca-east-entrance/source/build_model.py \
  --out assets/models/candidates/huangpu-puguang-ymca-east-entrance \
  --audit data/audit/puguang-ymca-east-entrance-v1
```

原始网格、近景和远景 GLB 均由同一套几何源码生成。可编辑 Blender 文件保存分组网格、材质、砖墙纹理和街面对景相机，字体子集采用 SIL Open Font License。[字形目录](source/entrance_fonts)
