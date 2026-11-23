# 高安路77号花园住宅

市房屋管理局列本宅为第五批优秀历史建筑5D039。南面局部三层，弧形阳台嵌在深色半露木架和折檐红瓦之间。三扇窗旁的饰面红砖、圆拱两侧的斜撑、弧台上九道卷圈和瓦坡上十道近横瓦行均按照片制作。图集原图保留了2012、2013和2018年的拍摄日期。[资料与授权](SOURCES-LICENSE.md)

## 尺度

南面中窗和上层两根木立柱同时出现在多个旧街景机位。中窗在两次交会中宽约1.07至1.09米，高约1.34至1.40米。与三张历史照片配准后，模型取木柱轴距3.13米。横木离路面的展示高度约9.1米，街景位置与俯仰误差使该标高仍有约一米的不确定性。按此尺度换算，南窗间的装饰砖皮约44毫米高。[三维尺度](measurements/relative-street-dimensions.json) · [原片砖皮读数](measurements/south-brick-course-scale.json)

## 重建

在本目录运行 `python measurements/check_mesh.py output` 可生成近景和远景网格并复核逐件封闭性。`source/house_layout.py` 给出可替换的公制标尺。原片投影与同角模型可以用 `measurements/render_registered_views.py` 复算。[配准读数](measurements/south-window-and-gallery-fit.json)
