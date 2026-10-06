# gzip-member

解析可能由多个成员拼接而成的 gzip 流：按成员建索引，逐个取成员内容。只用 Python 标准库。

```
python3 -m unittest discover -s tests
python3 -m gzmember --sample=fname
python3 -m gzmember --sample=crc
python3 -m gzmember --sample=isize
python3 -m gzmember --sample=multi
python3 -m gzmember --sample=work
```

## 口径

- **成员**：一个 gzip 流里可以拼接多个成员，成员之间首尾相接，逐个解析。
- **头**：按 `FLG` 跳过额外字段、原始文件名、注释与头校验，文件名解析进成员信息。
- **校验**：每个成员解压后都要核 CRC32 与原始长度；对不上就到此为止，不再收后续成员。
- **定位**：建好索引后按序号取成员，不重新解析整条流。

## 不变量

- 索引里的成员数与流里通过校验的成员数一致。
- 取出的成员内容长度与成员信息里的长度一致。
- `scanned` 不随成员数平方级放大：三百个成员逐个取一遍的 `scanned` 不超过 6000。

## 输出契约

场景打印一行 JSON，键随场景而定。`--sample=work` 打印 `{"members": N, "scanned": N}`。
