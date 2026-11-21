# 安福路284号花园住宅露木构悬挑窗楼

安福路284号原花园住宅建于1937年，现由上海话剧艺术中心使用。衡复风貌区的历史建筑资料刊有1948年行号图、同期航片和花园内的实景照片。在朝花园的山墙一侧，红褐色木构墙面向外悬出，长面与短端均有立木。托座的下缘从墙脚向外弯起，承接露在梁底的横木。本次制作该悬挑体和紧邻的一列成对小格窗。[上海市第四批优秀历史建筑名录](https://fgj.sh.gov.cn/yxlsjz/20200331/e3b99cf457ae48cab87ad5c02aa0fee3.html) · [号图、航片和多角度建筑照片](https://www.sohu.com/a/420379562_802458)

从斜拍照读取前端转角及两面上中下三道木横带的端点，按两面相交为直角反算比例。以相邻木门扇高约2.10米作估计，长面约2.33米，短面出挑约1.10米，第一层木构墙高约2.87米。门扇无实测值，窗楼与门之间可能存在退进。三张照片中的横木中心约位于下层木构自底部起64%的位置，约高出脚梁1.84米。[横木位置读数](measurements/red-rail-height.json)

较正的照片用于校对下部七格、上下层不同的斜撑位置、上层浅色修补块和相邻窗格。[照片像素、假定与取值范围](measurements/two-face-proportions.json)

较正的细部照片中，上层两根横木分别高出层间木带约1.47米和2.89米。较高的一根跨过木构与石子墙的接缝，继续伸到成对的窗上方。每个窗洞有两扇窗，每扇包含两列小格。以二楼窗框和脚梁对齐两张照片，再比对一楼的13块图像，一楼窗墙与上方基本共面。弧形托木下方的墙则退在脚梁之后。[窗墙前后位置核对](measurements/ground-window-plane-review.json)

右方屋檐超出近照，截取的坡顶尺寸为估计。[上层横木读数](measurements/upper-frame.json) · [成对窗的视差与取值](measurements/adjacent-sashes.json)

屋前一大一小两个山墙、后方浅色住宅和弧形阳台高楼可用于核对老宅的屋顶。原有匿名轮廓比资料所述约320平方米的占地小，树冠遮住悬挑底部。院门、整个屋顶、其余宅翼和现代剧场另外登记。[地块与两套屋顶影像](measurements/parcel-and-roof.json) · [原始文献与许可](reference-review.json)

从仓库根目录生成原始、网页、远景模型及可编辑文件。

```sh
python projects/shanghai/source/precise/xuhui-anfu-284-timber-jetty/source/build_model.py \
  --out out/anfu-jetty/assets --audit out/anfu-jetty/audit
```

[花园方向斜看悬挑木构](study-views/garden-oblique.jpg) · [上层木构](study-views/upper-panel.jpg) · [相邻的成对窗](study-views/paired-sashes.jpg) · [模型许可](SOURCES-LICENSE.md)
