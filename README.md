# Socratopia Anki 选择题模板转换工具

把 Socratopia 导出的 `.txt` 卡片文件转换成 Anki 可导入的选择题卡片。转换后的卡片支持在正面点击 A/B/C/D，并立即显示正确或错误，同时展开答案解析。

## 功能

- 将 Socratopia 原始 `.txt` 转换为 Anki 可导入的 `.tsv`
- 正面点击选项后即时判断正确/错误，并显示背面答案解析
- 直接翻到背面时，题目区也会自动高亮正确选项
- 生成适配 `Prettify Unified MCQ Stable` 的字段
- 保留原始 `Front` 作为第 1 列，方便 Anki 匹配已有卡片并保留复习记录
- 提供 Windows 双击启动脚本
- 不依赖第三方 Python 库

## 文件说明

- `prettify-unified-mcq-stable-template.apkg`：Anki 模板包，第一次使用前导入
- `socratopia_txt_to_anki_gui.py`：转换工具本体
- `打开_Socratopia转换工具.bat`：Windows 双击启动入口
- `使用说明.md`：更详细的中文使用说明

## 使用方法

1. 在 Anki 中导入 `prettify-unified-mcq-stable-template.apkg`
2. 双击 `打开_Socratopia转换工具.bat`
3. 选择 Socratopia 导出的原始 `.txt` 文件
4. 点击“转换”，生成 `.tsv`
5. 在 Anki 中导入生成的 `.tsv`

导入 TSV 时确认：

- 笔记类型：`Prettify Unified MCQ Stable`
- 分隔符：Tab
- 允许 HTML：开启
- 第 11 列作为 Tags

## 旧卡复习记录

如果你之前已经导入过同一批卡并复习过，不要删除旧卡。

本工具会把原始 `Front` 保留为第 1 列，用于让 Anki 识别已有笔记。重新导入时选择更新已有笔记，通常可以保留原来的复习记录。

导入前建议先在 Anki 中创建备份。

## 环境要求

- Windows
- Python 3

工具使用 Python 自带的 Tkinter，不需要额外安装依赖。
