# Mueta

## 介绍
这是一个可以为音频自动获取各种元属性（如艺术家、专辑、歌词、流派等等）的 CLI 程序。

## 安装

### 依赖
- Python >= 3.12
- [fpcalc](https://acoustid.org/chromaprint) (Chromaprint 命令行工具)

### 使用 uv 安装（推荐）
```bash
# 克隆项目
git clone https://github.com/oodenX/mueta.git
cd mueta

# 安装为全局 CLI 工具
uv tool install -e .

# 验证安装
mueta --version
```

### 使用 pip 安装
```bash
# 克隆项目
git clone https://github.com/oodenX/mueta.git
cd mueta

# 安装
pip install -e .

# 验证安装
mueta --version
```

### 安装 fpcalc（必须）
```bash
# Ubuntu/Debian
sudo apt install libchromaprint-tools

# macOS
brew install chromaprint

# Arch Linux
sudo pacman -S chromaprint
```

## 使用
### 初始化程序
用来初始化，并且配置基本的信息（API_KEY），音乐和歌词默认存储位置等等。
```bash
mueta init
```
然后在其中引导用户输入 **AcoustID API key** 和可选的 **Genius API key** 等信息。

> 💡 获取 AcoustID API key: https://acoustid.org/new-application
>
> 💡 获取 Genius API key (可选): https://genius.com/api-clients (创建 API Client 后取 `Client Access Token`)

### 获取一个音频的所有元属性
用来获取这个音频的所有的元属性。
```bash
mueta view-meta FILE
```
**参数**：
- `FILE`: 文件名称，以 mp3、flac、acc等音频格式。

**选项**:
- `-c --show-cover`: 是否显示封面，但是终端的分辨率非常低，不建议加上。

### 获取文件的所有的元属性
获取单个或者多个文件的元属性，文件用空格分开，可以选择是否有歌词，并且选择是否嵌入歌词到元属性中，或者一个 lrc 文件。
```bash
mueta get-meta [OPTIONS] FILES
```
**参数**:
- `FILES`: 文件名称，多个，以 mp3、flac、acc 等音频格式。

**选项**:
- `-l --lyric`: 是否下载 .lrc 歌词，歌词保存到默认的位置。
- `-e --embedded`: 是否嵌入歌词，歌词会嵌入到歌词的元属性中，但是有的播放器可能不会使用。
- `-c --cover`: 是否下载封面嵌入音频，默认打开。
- `-r --reserve`: 保留原文件（复制而不是移动）。
- `-w --workers`: 并行数，默认为3，可以根据自己的需求调整，要求为整数。
- `-i --interactive`: 交互式模式，当有多个匹配结果时手动选择（此模式下 workers 强制为 1）。

### 获取文件夹下所有文件的所有的元属性
获取一个文件夹下面所有的音频的元属性，可以选择是否有歌词，并且选择是否嵌入歌词到元属性中，或者一个 lrc 文件。
```bash
mueta get-meta-from-folder [OPTIONS] FOLDER
```
**参数**:
- `FOLDER`: 文件夹路径。

**选项**:
- `-l --lyric`: 是否下载 .lrc 歌词，歌词保存到默认的位置。
- `-e --embedded`: 是否嵌入歌词，歌词会嵌入到歌词的元属性中，但是有的播放器可能不会使用。
- `-c --cover`: 是否下载封面嵌入音频，默认打开。
- `-r --reserve`: 保留原文件（复制而不是移动）。
- `-w --workers`: 并行数，默认为3，可以根据自己的需求调整，要求为整数。
- `-i --interactive`: 交互式模式，当有多个匹配结果时手动选择（此模式下 workers 强制为 1）。

## 支持的格式
- MP3
- FLAC
- M4A/AAC
- OGG Vorbis
- Opus
- WAV
- WMA

## 贡献者
- **开发者**: oodenX
- **e-mail**: ven3428set@163.com
