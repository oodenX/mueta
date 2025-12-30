# Design Plan
## CLI 命令设计
### 初始化程序
用来初始化，并且配置基本的信息（API_KEY），音乐和歌词默认存储位置等等。
```bash
mueta init
```
然后会引导用户输入 **AcoustID API key** 等等信息。

### 获取一个音频的所有元属性
用来获取这个音频的所有的元属性。
```bash
mueta view-meta FILE
```
**参数**：
- `FILE`: 文件名称，以 mp3、flac、acc等音频格式。

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

### 获取文件夹下所有文件的所有的元属性
获取一个文件夹下面所有的音频的元属性，可以选择是否有歌词，并且选择是否嵌入歌词到元属性中，或者一个 lrc 文件。
```bash
mueta get-meta-from-folder [OPTIONS] FOLDER
```
**参数**:
- `FOLDER`: 文件名称，多个，以 mp3、flac、acc 等音频格式。

**选项**:
- `-l --lyric`: 是否下载 .lrc 歌词，歌词保存到默认的位置。
- `-e --embedded`: 是否嵌入歌词，歌词会嵌入到歌词的元属性中，但是有的播放器可能不会使用。
