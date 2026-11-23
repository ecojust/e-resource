# 高安路77号花园住宅

上海市房屋管理局第五批优秀历史建筑名录将此宅列为5D039。建筑建于1920年代。南侧可以辨认上层弧阳台、半露木拱、折檐筒瓦和圆柱廊，西侧可见带六只木托的长檐、两樘门券以及三管烟囱。院门旁的独立小楼另属一座建筑。[市级名录](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html) · [来源与许可](SOURCES-LICENSE.md)

南面弧台有九枚铁艺卷圈和十根竖杆，弧台脚下的三樘窗分别设两、四、两列窗格。高处折檐按原图可见瓦行制作。东侧小阳台的长栏有十三组竖孔，短栏有四组。西面小老虎窗用四格木窗和叠层平顶，南面老虎窗用三联木窗和双坡屋顶，东坡另有一处低矮的平顶采光窗。[外观记录](measurements/original-image-metadata.json) · [东侧量测](measurements/east-return-photo-control.json) · [西老虎窗量测](measurements/west-dormer-control.json) · [东坡采光窗](measurements/east-roof-light-photo-control.json)

## 建筑尺度和可见范围

南面中窗在不同历史街景机位的交会结果约为宽1.07至1.09米、高1.34至1.40米。结合三个摄影方向，模型采用3.13米木柱轴距。木横梁离路面约9.10米，估计误差约0.7米。按同一比例换算，两窗之间的饰面每皮约44毫米。透视配准用到的照片年代和镜头不同，两套南向相机分别保存在量测目录。[街景估算](measurements/independent-street-scale.json) · [南面窗组](measurements/south-window-and-gallery-fit.json) · [西面与南面相机](measurements/metric-exterior-photo-frames.json)

圆柱帽的位置由两个独立方向标定。西侧天沟下六处石托的承口，比南面木横梁约高0.22米。西侧烟囱帽线约13.28米，三根管口约14.10米。原图可以判读东侧檐线向后转折和下降的位置。北面门窗、室内布局和树木遮挡的部分缺少足够资料，背面采用素面收口。[圆柱帽观测](measurements/loggia-capital-photo-control.json) · [西墙窗和檐托](measurements/west-eave-photo-control.json) · [烟囱跨视角读数](measurements/west-seat-and-chimney-cross-photo.json) · [门廊檐线配准](measurements/portico-fascia-fit.json)

## 重建

从仓库内本目录运行 `python measurements/check_mesh.py output`。脚本输出原始近景、远景和逐构件的封闭性检查。`source/house_layout.py` 载入统一尺度，`source/cameras.json` 给出九个观察方向。独立查看页的下载区提供原始GLB、网页GLB、远景LOD和可编辑Blender文件。[模型查看页](../../../gaoan-77-curved-veranda.html)
