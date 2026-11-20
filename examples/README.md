# 示例：不联网也能验证安装

本目录提供最小样例，让你**不需要 Zoom 链接或课程讲义**就能验证依赖是否装好、脚本能否跑通。

## 烟雾测试（md → pdf）

在**任意目录**执行（不需要 `cd` 进 skill）：

```bash
# 1) Markdown 转 HTML
python3 <skill>/scripts/run.py md_to_html  <skill>/examples/example_lecture_notes.md /tmp/example.html

# 2) HTML 转 PDF（Node + Playwright + Chromium）
python3 <skill>/scripts/run.py html_to_pdf /tmp/example.html /tmp/example.pdf
```

看到 `Wrote ...html` 与 `image requests failed: none`，并在 `/tmp` 得到 `example.pdf`，
即表示 PDF 链路正常。

> 这条样例没有图片。要测"图片真的被嵌进 PDF"，运行
> `python3 <skill>/tests/run_tests.py` —— 它会把带图样例连同 `figures/` 复制到临时目录
> 再走完整链路，并断言 `image requests failed: none`。

## 样例说明

| 文件 | 对应阶段 | 格式要点 |
|---|---|---|
| `example_transcript.md` | Stage A1 转录稿 | `[mm:ss] 文本`，来源为官方转录 |
| `example_lecture_notes.md` | Stage A2 单讲讲义 | 四行块 `EN · 资料 / EN · 录音 / 中 / 📍 Source` |
| `example_review_handbook.md` | Mode B 复习手册 | 五行块 `EN · 资料 / EN · 录音 / 关键词 / 中（一段话） / 📍 Source`，纯文字无图 |

这三份文件只用于格式参考与本地烟雾测试，**不是真实课程资料**。真实产出请按
[`README.md`](../README.md) 的流程，用自己的 Zoom 链接与讲义生成。
