# 外滩7号，临江底层两枚镂空莲花标志

上海市房屋管理局第二批2A004把中山东一路7号列作“大北电报局”，所列使用单位为盘谷银行上海分行。Ferox Seneca在2012年8月31日拍摄的正面照片里，两枚金色标志位于扁拱窗和五开间中部之间。Suicasmo在2025年5月1日拍摄的斜照还能看清尖头、菱形孔、左右叶形孔和金属侧边。中央嘉鲁达和三语门额位于另一处。两张照片的作者、许可、原始文件签名和两侧遮挡均有记录。[名录与原照](reference-review.json)

采用既有外滩7号四档原件与原临江立面坐标。先从既有近景GLB提取嵌入的2025年原照片，其5184×3456像素、6,600,834字节与原照片签名一致。在已标定照片上，标志约宽1.11米、高1.43米，底约高1.81米。将2012年正面照的标志中心分别按两边相邻窗洞插值，使它们落在原模型的实际石壁柱处。这两次定位在原局部横轴上相差约0.50米和0.89米，制作选用逐窗拟合的轴距。离墙厚度和隐藏支脚按施工形状估计。[坐标与像素](geometry-input.json) · [原四件签名](baseline.json)

标志使用有厚度的金色金属片。外廓、菱形孔与两处叶形孔分别收边，正面带窄倒角，侧面和孔内可见颜色较深的金属。每件由背后两个小支脚连接石墙。模型沿用全部原有门窗、底层拱窗框和上层窗的图像纹理，两个新增构件可在Blender分别选取。[制作代码](build_emblems.py) · [Blender制作](native_emblems.py)

从上海项目根目录构建。Python环境需NumPy及带约束三角剖分的Shapely 2.1或以上。原生脚本从同一轮原始GLB读取已生成的两个网格。

    SOURCE=source/precise/bund07/revisions/front-pier-emblems
    python -B "$SOURCE/fetch_baseline.py" /tmp/bund07-prior
    python -B "$SOURCE/build_emblems.py" /tmp/bund07-prior /tmp/bund07-revised
    blender -b --python-exit-code 1 -P "$SOURCE/native_emblems.py" -- \
      /tmp/bund07-prior/native.blend /tmp/bund07-revised/raw.glb \
      /tmp/bund07-revised/native.blend /tmp/bund07-native-reopen.json

逐档检查原几何、原材质、嵌入图像和两件新增浮雕。

    DECODER=source/precise/bund17/revisions/street-wing-doors/decode_views.mjs
    mkdir -p /tmp/bund07-decoded/{prior,output}
    for role in web lod; do
      node "$DECODER" vendor/meshopt_decoder.module.js "/tmp/bund07-prior/$role.glb" "/tmp/bund07-decoded/prior/$role.glb"
      node "$DECODER" vendor/meshopt_decoder.module.js "/tmp/bund07-revised/$role.glb" "/tmp/bund07-decoded/output/$role.glb"
    done
    python -B "$SOURCE/check_revision.py" /tmp/bund07-prior /tmp/bund07-revised /tmp/bund07-decoded \
      data/audit/postal-office-v1/independent-glb-review-helpers.py /tmp/bund07-geometry.json
