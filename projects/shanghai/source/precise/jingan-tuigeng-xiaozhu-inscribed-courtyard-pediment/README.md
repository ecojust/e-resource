# 退耕小筑二进院墙半弧题额与回纹框

上海市第五批优秀历史建筑名录将吴镜渊旧居登记在长乐路662弄。两次实地报道将门牌记作662号。施泳峰在2023年指出，浅拱题额在第二进院墙，嵌入的矩形石额以阳文从右向左书写“退耕小筑”。院内住宅的屋顶出现在独立远照中，题刻近照可供逐字比对。项目按院墙局部独立展示。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html) · [中国青年报走访](https://www.sohu.com/a/460419965_119038) · [施泳峰，人民政协报](https://www.icppcc.cn/newsDetail_1128236)

四字共描出48段可见笔画，以石面可见的提按、转折和侧影留出阳文厚度。“小”字右端较淡，照片上的暗影与笔锋外缘在这里相差最大。上边回纹在矫正图中约每55像素重复一次。上部弧檐的圆凸、凹线和下缘珠饰可从正面分辨，后部进深和墙厚按构造估计。模型以题面宽1.80米定比例，原物缺少公开实测尺寸。[市文化旅游局长乐路图文](https://www.sohu.com/a/578713884_121106832)

## 复算

在本目录下运行下列命令。Python需要NumPy、SciPy、Shapely 2和Pillow，打包需要gltfpack及项目共享的网格解码工具。文章原图的取得地址和SHA-256列在measurements/exterior-sources.json。将该原图保存为photo.png即可核验刻字和檐部，普通模型生成可直接读取已记录的手工描线。

```sh
python -B source/package_model.py build --gltfpack gltfpack
python -B measurements/check_pediment.py photo.png build/raw.glb build/decoded-full.glb build/decoded-lod.glb --output build/inscription-and-curve-check.json
python -B measurements/render_pediment.py build/decoded-full.glb build/decoded-lod.glb build/inscription-and-coping.jpg
python -B measurements/coping_section.py build/raw.glb build/decoded-full.glb build/decoded-lod.glb --board build/coping-section.png
```

照片原生坐标以左上角为原点。75个检查点包括刻字和露出的素底，13个另外选取的列采样记录模型弧檐下边与照片的垂直残差。剖面直接与三档成品的三角面相交，图中标尺为模型尺寸。原图及文字作品的著作权归各自权利人，可编辑几何、手工测量和程序材质按MIT许可。公开图板由模型生成。
