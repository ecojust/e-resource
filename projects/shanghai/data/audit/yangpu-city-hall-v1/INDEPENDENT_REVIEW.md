# 独立几何与落位审查

总结果见 [independent-model-review.json](independent-model-review.json)。正式四资产与私有验收版本逐字节相同；[公开绑定证明](independent-publication-binding.json) 明确列出映射文件的路径、状态和清单绑定变化，并验证其余内容深比较相同。本次公开化没有重复执行 177 条射线、原生文件重开或原城市场景矩阵。

三档 GLB 各有 59 条独立实际表面射线。原始版与全量压缩版的严格 FLOAT32 有向面及材质多重集一致；轻量版保留相同外包范围和被测开口，但平面投影存在约 0.582236 平方米细节差异。原生文件经独立只读重开，其建筑三角表面也与原始 GLB 严格一致。7 张最终原生图均实际查看，记录在 [独立审图证明](independent-native-image-review.json)。作者闭合正体积部件检查另行绑定，不声称整栋是单一布尔并集流形。

主源 525 完整替换，显示裁剪仅额外清除有界旧檐。碰撞来自真实三角形精确截取的 0–2 米高度层，加上仅限主源内部的保守实体填充。最终两片碰撞环分别为 58、25 个闭合点，桥下道路中心及肩线保持空；主楼室内、桥面和台阶漫游均未开放。原始城市场景、全部 2323 个其他源和同组 6 个邻体的检查见 [独立落位证明](independent-placement-review.json)。

以下命令从 `projects/shanghai` 运行。Python 依赖与本模型源码相同；Node 使用仓库内 Meshopt 解码器，原生复验使用 Blender 4.3.2。全部重算输出放在仓库外临时目录，历史源由已记录 Git 提交提取并核对 SHA。此流程不启动浏览器，也不修改原生文件。

```sh
audit_dir=data/audit/yangpu-city-hall-v1
asset_dir=assets/models/candidates/yangpu-former-shanghai-city-hall
replay_dir="$(mktemp -d)"

python "$audit_dir/independent-prepare-source-cache.py" "$replay_dir/source"
node "$audit_dir/independent-city-source-check.mjs" "$replay_dir/source" "$replay_dir/city"
python "$audit_dir/independent-check-original-city.py" "$replay_dir/source" "$replay_dir/city" "$replay_dir/original-city.json"

node "$audit_dir/independent-geometry-check.mjs" "$asset_dir" "$audit_dir/independent-probes.json" "$replay_dir/geometry.json" "$replay_dir/projection"
python "$audit_dir/independent-derive-occupancy.py" "$replay_dir/geometry.json" "$replay_dir/projection" "$replay_dir/occupancy"
python "$audit_dir/independent-check-placement.py" "$replay_dir/geometry.json" "$replay_dir/occupancy" "$audit_dir/footprint-review.json" "$replay_dir/placement.json" "$replay_dir/source" "$replay_dir/original-city.json"

blender -b "$asset_dir/yangpu-former-shanghai-city-hall.blend" -t 1 --python-exit-code 1 --python "$audit_dir/independent-check-native.py" -- "$asset_dir/yangpu-former-shanghai-city-hall-raw.glb" "$replay_dir/native.json"
```

独立探针可从已冻结参数重新生成，未调用作者的建模函数或探针：

```sh
python "$audit_dir/independent-make-probes.py" source/precise/yangpu-former-shanghai-city-hall/source/model-parameters.json "$replay_dir/probes.json"
```

`independent-occupancy/` 保存最终实际投影与高度层结果；巨大的中间三角数组不入库，可用上面的命令重建。历史资料阅读记录中的私有照片、文本及早期原型缓存路径仅供追溯，没有复制第三方照片或全文。公开来源说明以本模型的 `source-register.json`、`documentary-review.json` 和 `photo-review.json` 为准。全局网页、灯牌和邻体可见像素由单独浏览器验收证明。
