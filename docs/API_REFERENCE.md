# Mueta CLI 命令参考

## 全局选项

| 选项 | 简写 | 说明 |
|------|------|------|
| `--version` | `-v` | 显示版本号 |
| `--help` | | 显示帮助信息 |
| `--install-completion` | | 安装 shell 自动补全 |
| `--show-completion` | | 显示自动补全脚本 |

---

## init

初始化 Mueta 并配置基本信息。

```bash
mueta init
```

### 交互式配置

运行后会引导输入：
1. **AcoustID API Key** - 必须，从 https://acoustid.org/new-application 获取
2. **音频保存目录** - 处理后音频的存储位置
3. **歌词保存目录** - 下载歌词的存储位置

### 配置文件

配置保存在 `config.toml`:
```toml
[default]
audio_save_dir = "/path/to/audio"
lyrics_save_dir = "/path/to/lyrics"

[acoustid]
acoustid_api_key = "your-key"
```

---

## view-meta

查看单个音频文件的当前元数据。

```bash
mueta view-meta [OPTIONS] FILE
```

### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `FILE` | 是 | 音频文件路径 |

### 选项

| 选项 | 简写 | 默认 | 说明 |
|------|------|------|------|
| `--show-cover` | `-c` | False | 在终端显示封面图（低分辨率） |

### 示例

```bash
# 查看基本元数据
mueta view-meta song.mp3

# 包含封面显示
mueta view-meta -c song.flac
```

### 输出格式

```
🎵 Metadata: song.mp3
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃ Property     ┃ Value             ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
│ Title        │ Song Title        │
│ Artist       │ Artist Name       │
│ Album        │ Album Name        │
│ Duration (s) │ 180.5             │
└──────────────┴───────────────────┘
```

---

## get-meta

获取单个或多个音频文件的元数据。

```bash
mueta get-meta [OPTIONS] FILES...
```

### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `FILES` | 是 | 一个或多个音频文件路径（空格分隔） |

### 选项

| 选项 | 简写 | 默认 | 说明 |
|------|------|------|------|
| `--lyric` | `-l` | False | 下载 .lrc 歌词文件 |
| `--embedded` | `-e` | False | 嵌入歌词到音频元数据 |
| `--cover` | `-c` | True | 下载并嵌入封面 |
| `--reserve` | `-r` | False | 保留原文件（复制而非移动） |
| `--workers` | `-w` | 3 | 并行处理线程数 |

### 示例

```bash
# 处理单个文件
mueta get-meta song.mp3

# 处理多个文件，保留原文件
mueta get-meta -r song1.mp3 song2.flac song3.m4a

# 下载歌词，使用 5 个并行 worker
mueta get-meta -l -w 5 *.flac

# 完整选项
mueta get-meta -r -l -e -c -w 4 song.mp3
```

### 处理流程

1. 验证文件格式
2. 生成音频指纹
3. 查询 AcoustID
4. 获取 MusicBrainz 元数据
5. 写入标签
6. 可选：下载歌词/封面
7. 移动/复制到目标目录

---

## get-meta-from-folder

批量处理整个文件夹中的音频文件。

```bash
mueta get-meta-from-folder [OPTIONS] FOLDER
```

### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `FOLDER` | 是 | 包含音频文件的文件夹路径 |

### 选项

与 `get-meta` 命令相同：

| 选项 | 简写 | 默认 | 说明 |
|------|------|------|------|
| `--lyric` | `-l` | False | 下载 .lrc 歌词文件 |
| `--embedded` | `-e` | False | 嵌入歌词到音频元数据 |
| `--cover` | `-c` | True | 下载并嵌入封面 |
| `--reserve` | `-r` | False | 保留原文件（复制而非移动） |
| `--workers` | `-w` | 3 | 并行处理线程数 |

### 示例

```bash
# 处理整个音乐文件夹
mueta get-meta-from-folder ~/Music/

# 保留原文件，下载歌词
mueta get-meta-from-folder -r -l ~/Downloads/music/

# 最大并行处理
mueta get-meta-from-folder -w 10 -r /media/music/
```

### 支持的文件类型

文件夹扫描会自动识别以下扩展名：
- `.mp3`
- `.flac`
- `.m4a`, `.aac`
- `.ogg`
- `.opus`
- `.wav`
- `.wma`

---

## 退出码

| 退出码 | 说明 |
|--------|------|
| 0 | 成功完成 |
| 1 | 一般错误 |
| 2 | 命令行参数错误 |

## 日志

日志文件位置：`logs/mueta.log`

可通过环境变量控制日志级别：
```bash
export MUETA_DEBUG=true
mueta get-meta song.mp3
```
