# 松江方塔：构建与验证

本模型源身份为 OSM `w461743815@7`、GERS `22db76bc-02c7-4592-9d78-9b3868ec80ff`，位于松江区。原 owner 四边形和原点不变；独立可见建筑采用官方记载的底层 6m 方形砖身、九级四面与正间壸门。外形控制、底层围廊、材料年代和尺寸口径见 DESIGN.md、calibration.json 及 references。42.65m 是官方名义总高，7.85m 塔刹来自另一口径，34.80m 分界为建模推定，不是测绘。隐藏面及各层细分尺寸保留估计说明。

源代码需要 Python、NumPy、Shapely 2.1+。原生编辑文件与三张预览使用 Blender；web/LOD 包装复用项目已有通用工具和 gltfpack。所有运行输出必须选新目录，不覆盖冻结版本。每个文件严格小于 100,000,000 字节。

以下命令在本目录运行。先输出 raw，再根据独立实际 Float32 几何检查决定是否渲染：

```bash
python run_root.py --output run-v1 --raw-only --execute
```

外部检查须读取实际 GLB 三角形，核对闭合、法向/正体积、36 个中央通洞、层间承托、顶墙与屋面收口、瓦排搭接、36 条屋脊座、12 个围廊柱及九道真实中空相轮。构建器的数值报告和 source-preflight-v2.json 不能代替这项复核；后者只检查了 45 个有限构件。

独立几何检查通过后，由 root 独占运行：

```bash
/usr/bin/blender -b -t 2 --python-exit-code 1 --python render_previews.py -- --glb run-v1/raw/songjiang-fangta-pagoda-raw.glb --output run-v1/native --samples 48 --threads 2 --only all
```

三个镜头是全塔 1000×1400、中层 1200×900 和眼高 1.65m 的仰视 1200×900。渲染器按实际 Blender 构建能力决定是否启用 OpenImageDenoise，并保留可编辑压缩 blend。镜头用于检查构件，不是照片摄影测量配准。root 必须实际查看三张新图，并将独立视觉评审绑定到对应 raw/native SHA。

原生复核通过后生成独立 package，不安装到主项目：

```bash
python /workspace/shanghai_project/source/precise/tooling/package_precise_building.py --spec packaging-input.json --raw run-v1/raw/songjiang-fangta-pagoda-raw.glb --native run-v1/native/songjiang-fangta-pagoda.blend --project /workspace/shanghai_project --output run-v1/package --gltfpack /workspace/shanghai_tools/node_modules/.bin/gltfpack --shared-helper /workspace/shanghai_project/source/bund/photo-rebuild-v6/common/package_building.py
node check_decoded_package.mjs /workspace/shanghai_project run-v1 .
```

解码检查使用实际项目 GLTFLoader 与 MeshoptDecoder。web 的有向位置/材质三角形多重集须与 raw 一致，法向变化采用项目既有 0.05° 上限；raw/web/LOD 分别测试 36 个通洞、墙体反例，以及九相轮每轮四组空洞/铁环射线。模型明确无图像或纹理；LOD 只通过有限测试，不宣称全表面等距。

实际独立记录放在 `independent-review/actual-raw-structure.json` 与 `actual-raw-roof-pairs.json`。完成真实 package、解码检查及 root 原生评审后，才可生成九项预浏览器证明和待验证浏览器条目：

```bash
python prepare_registration.py --run run-v1 --native-review run-v1/native/root-native-visual-review.json --contact-review run-v1/root-finite-contact-review.json --navigation navigation-proposal.json
```

`independent-review/actual-roles-contacts.json` 单列门洞、围廊柱、相轮和屋脊接触结果。登记还要求 root 的 `fangta-root-finite-contact-review-v1` 记录：实际审查标记、raw SHA、原接触报告 SHA、采用的承托准则、理由和局限。原报告中不满足其他准则的采样仍保持原值，不能用通过的中心线样本抹去边缘间隙。

独立源码交付工具随后按明确白名单组装四个资产、五张参考照片、源文件和真实证据，提供 install-manifest；不递归收集研究历史。冻结大文件可用硬链接节省磁盘。后续安装前必须再次核验哈希；不要原位修改硬链接文件。公开交付由独立 source-release 流程准备，源码目录中的临时组装脚本不属于本冻结构建白名单。

公开源码仅保留五张分别获许可的照片、短引文/事实/官方链接，不附官方全文 HTML。程序 MIT，新几何 CC BY-SA 4.0，源 owner ODbL-1.0，原照片各自 BY-SA 3.0/4.0。原始分辨率与是否预览逐文件记录，不一概称作 960px。

导航只是塔南侧的几何观察位置，不表示核实过入口、公共通行、地面铺装或现实路径。来源去重、owner 替换、浏览器全景及第三人称低机位须在后续集成中独立验证；本源码和原生模型交付不提前宣称这些步骤通过。
