# 九江路219号原教会学校入口与双山墙

模型涵盖原英童学校朝向九江路的中央五组窗。正中是带双竖牌的石砌尖券，两旁两座红砖山墙各有三排钢窗，首层各开一扇方门和一组低窗。窗间的斩假石棱、菱形四瓣花、盾牌和葡萄藤纹以独立几何表达。屋顶台阶和浅折面只延伸到本段立面的后缘。[独立模型页](../../../cathedral-school-jiujiang-front.html)

## 身份与年代

建筑建于1928年，原为圣三一堂附设的英童学校。1937年同仁医院迁入，战后曾出租作百乐饭店及扬子电气公司办公楼，后曾供黄浦区政府使用。2018年保护修缮涵盖泰山砖、斩假石窗套、钢窗、方形铸铁落水管和宗教纹章。此次模型依据修缮后的街面。主堂和钟塔另有独立模型。[市房管局第四批名录 4A019](https://fgj.sh.gov.cn/yxlsjz/20200331/e3b99cf457ae48cab87ad5c02aa0fee3.html) · [建筑保护修缮图录](https://m.thepaper.cn/baijiahao_7604398) · [2013年修缮前北立面，Livelikerw，CC BY-SA 3.0](https://commons.wikimedia.org/wiki/File:219_Jiujiang_Rd._Shanghai.JPG)

## 尺寸与边界

以北侧街墙西端为原点，X向东，Y向九江路，Z向上。2021年1月12日七个街景机位提供连续覆盖，中央三组窗的54个同名观测用于三机位平差。相对于中央窗套石面，两座山墙的窗套各向前约0.6米和0.5米。西峰约21.25米、东峰约21.60米，东峰在不同机位之间存在约0.8米的高度不确定性。主门前端净券口约3.88米，外围券顶约4.20米，矩形石面板高约5.90米。[摄影配准与估计](source/registration.json) · [可复算的模型尺寸](source/dimensions.json)

中央实体覆盖北墙里程约22.8至52.9米。原城编号1810与OSM建筑292718777第4版的足印相交并集比约98.50%。较低的外翼、完整后屋面、室内和院落仍在制作清单中。部分石雕的图样采用照片可辨的概括轮廓；竖牌的小字未录入。[原物、底图及照片范围](reference-review.json) · [OSM历史建筑轮廓](https://www.openstreetmap.org/way/292718777/history/4)

## 模型文件与核验

几何近景为34,428个三角形，远景为10,392个。编辑源码中的窗洞和门洞贯穿外墙，门扇、窗框与钢窗玻璃各有独立深度。原创建筑纹理以实际米数排布错缝泰山砖，嵌入GLB。独立读取器对原始、网页近景及网页远景分别完成224、224及170条表面检测，并以解码后的近远网格各绘制九个角度。[街面近景](../../../data/audit/cathedral-school-jiujiang-front-v1/preflight/full-views/north-street-front.jpg) · [入口细部](../../../data/audit/cathedral-school-jiujiang-front-v1/preflight/full-views/pointed-entrance.jpg) · [窗套与盾饰](../../../data/audit/cathedral-school-jiujiang-front-v1/preflight/full-views/west-shield-and-window-head.jpg) · [逐项检查结果](../../../data/audit/cathedral-school-jiujiang-front-v1/preflight/geometry-rays.json)

在仓库根目录使用下列命令重建。需要 Python、NumPy、Shapely、Pillow、Blender、gltfpack、Node.js、ImageMagick 和 Open Image Denoise；构造函数会在缺图时生成原始砖纹。

```sh
python -B projects/shanghai/source/precise/huangpu-cathedral-school-jiujiang-front/source/build_model.py \
  --out projects/shanghai/assets/models/candidates/huangpu-cathedral-school-jiujiang-front \
  --audit projects/shanghai/data/audit/cathedral-school-jiujiang-front-v1
```

建模源码、构件和砖纹采用仓库的MIT许可。OSM数据遵循ODbL 1.0。实景照片保留原有权利，模型使用独立绘制的材质。[仓库许可](../../../../../LICENSE)
