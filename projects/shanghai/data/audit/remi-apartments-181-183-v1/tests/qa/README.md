# 分开核对181与183号两户

2268与2598分属两个近景分组。「添加模型后全城增加四个裁剪三角」只能证明总数。两个分组各应只增加两个三角，分别绑定自己的那一户。下列程序在正式父版与本版抽查两个组的原始成员、源编号、裁剪三角数和下载文件。原有单组检查继续使用原来的输入描述。

在本项首次登记或已包含本项的版本中，以下命令对安装前后的文件逐一检验SHA-256。检测到未登记的文件版本会终止。对原始、剩余源体探针版以及按建筑物编号分页的城市版本，安装程序分别选择相应变更。已安装版本重复执行时保留原字节。

```bash
python data/audit/remi-apartments-181-183-v1/tests/qa/install-groups.py . --check
python data/audit/remi-apartments-181-183-v1/tests/qa/install-groups.py .
node tools/check-sourced-candidate-runtime.mjs data/audit/remi-apartments-181-183-v1/map-case.json
node data/audit/remi-apartments-181-183-v1/tests/qa/test-groups.cjs \
  source/precise/xuhui-remi-apartments-181-183/footprint-review.json \
  data/audit/remi-apartments-181-183-v1/final-placement-contract.json \
  data/audit/remi-apartments-181-183-v1/map-case.json \
  data/audit/remi-apartments-181-183-v1/runtime-placement.json
```

测试对照两期实际分组状态，另覆盖漏掉第二组、调换分户、重复分组、原版已裁、裁片数异常以及未绘制第二组。[各版本逐行补丁与SHA-256](patches.json)
