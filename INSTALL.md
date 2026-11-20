# 安装与排障

面向第一次使用本 skill 的同学。按顺序做，遇到问题对照"排障"。

---

## 一、装之前必须知道的三件事

1. **这是 Agent Skill，不是独立程序。** 把它放进宿主的 skill 目录，由宿主 AI 按
   `SKILL.md` 驱动。脚本可以单独调用，但完整流程靠对话推进。
2. **依赖不会自动安装。** `requirements.txt` / `package.json` 只是版本清单。
3. **本 skill 不做语音转写。** 只读 Zoom 录制自带的官方转录；没有就只下载音频并停止。

---

## 二、安装

### 步骤 1：放到 skill 目录

要求：目录顶层直接能看到 `SKILL.md`。

| 宿主 | 位置 |
|---|---|
| Claude Code | `~/.claude/skills/lecture-to-exam/` 或 `<repo>/.claude/skills/` |
| DSH | 当前 profile 的 skills 目录 |
| WorkBuddy | `~/.workbuddy/skills/lecture-to-exam/` |
| 其它 | 你的框架读取 SKILL.md 的目录 |

```bash
git clone <repo-url> lecture-to-exam
cp -r lecture-to-exam ~/.claude/skills/
```

重载宿主后，在任意工作区都能触发。**不需要**把 skill 目录当成工作目录。

### 步骤 2：Python 依赖

```bash
cd <skill>                              # 只是安装时进来一次
python3 -m pip install -r requirements.txt
```

锁定：Markdown、PyMuPDF、yt-dlp。若系统有多个 Python，用**同一个解释器**装依赖和运行；
自检会自动探测，也可 `PYTHON_BIN=/path/to/python` 指定。更干净的做法是在 skill 目录下建
`.venv`——`run.py` 会优先使用它：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt      # Windows: .venv\Scripts\python.exe
```

### 步骤 3：Node / PDF

```bash
cd <skill>
npm install
npx playwright install chromium
```

Playwright 版本必须与缓存的 Chromium revision 对应。Chromium 缓存默认在
`~/Library/Caches/ms-playwright`（macOS）、`~/.cache/ms-playwright`（Linux）、
`%LOCALAPPDATA%\ms-playwright`（Windows）；可用 `PLAYWRIGHT_BROWSERS_PATH` 覆盖。

### 步骤 4：系统工具

| 工具 | 必需性 | macOS | Linux | Windows |
|---|---|---|---|---|
| curl | 必需 | 自带 | `sudo apt install curl` | 自带（Git Bash） |
| node | 必需 | `brew install node` | `sudo apt install nodejs npm` | 官网安装包 |
| ffmpeg | 条件 | `brew install ffmpeg` | `sudo apt install ffmpeg` | `winget install ffmpeg` |
| LibreOffice | 条件（PPTX 出图） | `brew install --cask libreoffice` | `sudo apt install libreoffice` | 官网安装包 |

`ffmpeg` 只在"无官方转录、要下音频"时用；LibreOffice 只在"PPTX 出原图"时用。

### 步骤 5：自检

```bash
python3 <skill>/scripts/run.py check_env          # 或 --json
```

输出按**阶段**分组：

- `transcript (A1)` —— 转录
- `lecture notes (A2)` —— 出讲义（含出图）
- `pdf export (A3/B)` —— 转 PDF
- `audio fallback` —— 无官方转录时下音频

只为你要用的阶段装依赖。`MISS` 会让脚本以退出码 1 结束并打印可直接复制的安装命令。

### 步骤 6：烟雾测试（不联网）

```bash
python3 <skill>/scripts/run.py md_to_html  examples/example_lecture_notes.md /tmp/demo.html
python3 <skill>/scripts/run.py html_to_pdf /tmp/demo.html /tmp/demo.pdf
```

输出 `image requests failed: none` 即链路正常。

> 所有命令都可以在任意目录执行：`run.py` 按自身位置定位 skill 根目录，并在候选
> Python 中挑一个真正能 `import markdown / pymupdf` 的解释器。

---

## 三、环境变量

| 变量 | 作用 |
|---|---|
| `PYTHON_BIN` | 指定装了依赖的 Python 解释器（优先级最高） |
| `NODE_BIN` | 指定 node |
| `NODE_PATH` | 额外 node_modules 搜索路径 |
| `PLAYWRIGHT_BROWSERS_PATH` | Chromium 缓存目录 |
| `YTDLP_BIN` / `FFMPEG_BIN` | 指定 yt-dlp / ffmpeg |
| `SOFFICE_BIN` | 指定 LibreOffice 的 soffice |

---

## 四、排障

### 1. `NO_TRANSCRIPT`

讲师未开启"音频文字记录"（退出码 3）。脚本只下载音频并停止；请自行转录成
`[mm:ss] 文本`（见 `references/transcript-spec.md`）再交回。

> 若报 `ERROR: ...`（退出码 1），那是**访问问题**，不是没有转录。先在浏览器打开确认。

### 2. 非通用 Zoom 租户跑不通

域名已从链接自动推导。仍失败：

```bash
python3 <skill>/scripts/run.py zoom_transcript "<链接>" -o "_转录稿.md" \
  --domain <你的租户> --referer https://<你的租户>/
```

### 3. 需要登录 / SSO / 密码

- 登录：先在 Chrome 登录，再给 `zoom_fetch` 加 `--cookies-from-browser chrome`。
- 密码：在浏览器输入后确认可播放，再交给 skill。
- 旧版 `/rec/play/` 用 `zoom_fetch`；新版 `/rec/share/` 用 `zoom_fetch_share`。

### 4. LibreOffice 装了却启动就崩

**现象**：`soffice --version` 报 `DeploymentException`，或转换返回非零。
`check_env` 会把它标成 WARN（它会真的启动一次，不会给你假 OK）。

处理顺序：

1. `render_pptx_pages` 已内置独立临时 profile，多数情况直接可用。
2. `--lo-app "/path/to/LibreOffice.app"` 指向健康副本（macOS）。
3. `--dmg "/path/to/LibreOffice.dmg"` 挂载干净副本（**仅 macOS**）——注意这条会用
   `hdiutil` 挂载并去掉隔离标记后**执行**其中的 LibreOffice，**只挂载你信任的 DMG**。
4. 最省事：自己把 PPTX 导出成 PDF，交给 `extract_pdf`。

### 5. Playwright 浏览器版本不匹配

```bash
npm install && npx playwright install chromium
```

`html_to_pdf` 会逐个候选路径**实际启动**浏览器验证，全部失败才报错。

### 6. PPTX 和录音对不上

讲义按模块命名、录音按日期命名。脚本不猜对应关系；关键词不匹配时会停下来请你确认。

### 7. 复习模式报"少于 2 讲"

```bash
python3 <skill>/scripts/run.py validate_review_input <讲义1.md> <讲义2.md> --exam <真题.md>
```

少于两份退出码 2；文件缺失退出码 3。

### 8. PDF 没有图片

- 单讲讲义 PDF 应有图：检查 `.md` 里的 `figures/xxx.png` 是否存在、是否与 md 同层级。
- 复习手册本来就无图，正常。
- `html_to_pdf` 若有图片加载失败会**删掉半成品 PDF** 并以退出码 2 结束。

### 9. 自检总是报某个 Python 模块 MISS

装依赖的解释器和运行脚本的不是同一个。用 `PYTHON_BIN` 指定，或建 skill 内 `.venv`：

```bash
$PYTHON_BIN -c "import markdown, pymupdf; print('ok')"
```

### 10. `verify_output` 报不合格

那是格式闸门在工作，不是 bug。它会指出具体条目（缺图注、五行块缺行、中文字数不足、
Mode B 混入图片……）。按提示改草稿，不要改闸门。

---

## 五、仍然失败时

收集以下信息再提问：

1. `run.py check_env --json` 的完整输出。
2. 操作系统与版本、Python / Node 版本。
3. 出错时的完整命令与报错原文。
4. Zoom 链接类型（`/rec/play/` 还是 `/rec/share/`）、是否设密码、是否需要登录。

不要改 `SKILL.md`、`references/` 来绕过报错——那会破坏格式契约与审批关卡。
