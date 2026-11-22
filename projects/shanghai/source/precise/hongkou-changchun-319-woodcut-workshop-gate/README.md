# 长春路319号木刻讲习会旧址院门

1931年8月17日至22日，鲁迅在长春路319号三楼举办木刻讲习会，内山嘉吉主讲。这里的模型记录近年街道一侧所见的院门。门口的两座砖柱托起多层浅色压顶，左柱挂有“优秀历史建筑”牌，右柱挂有“木刻讲习所旧址”牌。右扇的五个字在2023年照片中竖排成“木刻講習會”。[虹口区旧址资料](https://www.shhk.gov.cn/zjhk/001003/001003002/20140902/2008bff6-eb22-4afe-a622-42e7e03fb0a3.html)

## 如何辨认同址

高参88的原片摄于2015年4月25日，楼身入口上方的绿色门牌可读为319。街前当时有数座砖柱和透空铁门，柱顶为带浅坡的多层压顶。楼身门牌比街前门柱退后。同组照片中另有余庆坊居委会，其门面独立。[高参88摄影手记](https://blog.sina.cn/dpool/blog/s/blog_5d1bdf480102vtah.html)

上观新闻蒋迪雯摄于2021年9月25日开馆当天的斜照，可见两块铭牌与向院里打开的褐色门扇。上海虹口在2023年3月发布的街前近照中，两扇门闭合，左侧四片长斜页之间露出亮缝，右侧门面刻有五字。两块牌的标题可辨，小字与二维码内容留在来源照片中。[上观开馆报道](https://export.shobserver.com/baijiahao/html/408688.html) · [虹口区街区图集](https://www.shhk.gov.cn/qyfwy/030002/030002002/030002002005/20230308/10447587-89ab-4422-a788-bf19e49a6f77.html)

## 尺寸与两个机位

模型以左右柱之间的净空中心为原点，X轴向街前正照的右方，Y轴朝院内，Z轴向上。柱身顶与浅色基础之间可数28皮砖，计算暂取每皮64毫米。按这一换算，净宽约1.76米，两柱正面各宽约0.74米，压顶高约2.78米。沿街墙向院内的进深依靠两机位中可见的侧边估算。没有现场尺量，重新取得砖皮高后可将整件同比例调整。

两幅照片的砖缝和铭牌提供42个去重纹理对应点；每五点留一，配合四个留出的柱脚和压顶边角检查相机。开馆日的左压顶边角有约13像素偏差。三份正式几何另做原生像素到模型的最近交点检查，每档用2021年29条、2023年64条观察线。后者包含真实穿过门扇缝隙的五条线。[两机位数据](measurements/gate-camera-fit.json) · [逐点检查](measurements/gate-pixel-tests.json) · [成品图板](../../../data/audit/changchun-319-woodcut-workshop-gate-v1/photograph-review/two-gate-views.jpg)

2023年整排街屋照左侧可见带棕色铭牌的前柱，后方门楣另有319号牌。以刊载的街屋机位把院门接回同一局部坐标时，柱点重投约0.3至6.1像素，楼身控制点的第90百分位约9像素。院门以独立构件交付，保留两处门之间的偏移与此项误差。[前后两平面联测](measurements/frontage-registration.json)

## 重建与出处

在本项目目录下执行下列命令，生成三种下载件、独立解码件和其中一张实测图。需要Python、NumPy、SciPy、Pillow、Node、仓库已有的模型工具及Meshoptimizer的gltfpack。

```sh
python source/build_model.py --out build/models --decoded build/decoded --gltfpack gltfpack
python measurements/check_gate.py build/decoded/decoded-full.glb build/review.json
python measurements/render_gate.py build/decoded/decoded-full.glb build/two-gate-views.jpg
```

源码与自行建成的几何按MIT许可。五字与两碑标题用Noto Serif CJK字形另行排制；已保存SIL Open Font License。三维文件、网页与图板均由模型生成，网页只链接照片原出处。[字体许可](source/NOTO-LICENSE.txt) · [原片标识与来源](measurements/photograph-sources.json)
