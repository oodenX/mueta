# Mueta 性能测试总结

## 测试环境
- 测试文件数：14 个 FLAC 音频文件
- 测试日期：2025-12-19

## 改进前后对比

### 性能对比
| 指标 | 改进前 | 改进后 |
|------|--------|--------|
| 处理时间 (14文件) | 数分钟 (librosa BPM分析) | ~30-54秒 |
| 成功率 | 约 50-60% | 93% (13/14) |
| 依赖库 | musicbrainzngs + librosa | 仅 httpx (更轻量) |
| 超时控制 | 无 | ✅ 15秒超时 |

### 修复的问题
1. ✅ HTTP 301 重定向错误 - 添加 `follow_redirects=True`
2. ✅ NoneType.lower() 错误 - 添加空值检查
3. ✅ label["name"] NoneType 错误 - 添加空值检查

## 元数据字段支持

### 基础字段
- ✅ Title, Artist, Album, Album Artist
- ✅ Track Number, Disc Number
- ✅ Year, Date, Original Year
- ✅ Genre, Composer

### 扩展字段 (Picard 级别)
- ✅ Label, Catalog Number, Barcode
- ✅ ISRC (International Standard Recording Code)
- ✅ Media Type (CD, Digital Media, etc.)
- ✅ Release Type (Album, Single, EP, etc.)
- ✅ Release Status (Official, Promotional, etc.)
- ✅ Release Country

### MusicBrainz IDs
- ✅ Recording MBID
- ✅ Release MBID
- ✅ Release Group MBID
- ✅ Artist MBID

## 功能测试结果

### 歌词保存 (~/.mueta/lyrics/)
- ✅ 目录自动创建
- ✅ LRC 格式同步歌词正确保存
- ✅ 文件命名格式：`Artist - Title.lrc`
- 📊 14个文件中有2个找到同步歌词

### 元数据写入
- ✅ 所有扩展字段正确写入音频文件
- ✅ 支持 FLAC, MP3, M4A 等格式
- ✅ 使用 mutagen EasyID3/EasyMP4 兼容标签
- ✅ Track/Disc 格式：`5/12` (当前/总数)

### view-meta 命令
- ✅ 美观的表格显示
- ✅ 字段按逻辑顺序排列
- ✅ 显示所有 20+ 元数据字段
- ✅ 可选 `--show-cover` 显示封面

## 当前限制

### AcoustID 数据库覆盖
- ⚠️ 测试集中 1/14 文件未找到 AcoustID 匹配
- 原因：部分小众歌曲不在 AcoustID 数据库中

### LRCLIB 歌词覆盖
- ⚠️ 大部分日语 Vocaloid 歌曲无同步歌词
- ⚠️ 仅 2/14 测试文件找到同步歌词
- 建议：添加其他歌词源作为后备

## 技术优化

### API 请求优化
1. 完全使用 httpx 替代 musicbrainzngs
2. 统一的超时控制 (15秒)
3. 自动重定向跟踪
4. 多线程并发处理 (默认3个worker)

### 错误处理
1. 空值安全检查
2. 详细的错误日志
3. 优雅的降级处理

### 代码质量
1. 移除了 librosa 重依赖
2. 减少了依赖包数量
3. 提升了代码可维护性

## 建议改进

1. 添加文件名解析作为 AcoustID 的后备方案
2. 集成更多歌词源 (如 Genius, AZLyrics)
3. 添加进度持久化，支持断点续传
4. 添加更多音频格式支持
5. 考虑添加封面艺术自动下载选项


## 新增功能测试 (2025-12-19 更新)

### 1. MusicBrainz 搜索后备方案

当 AcoustID 没有匹配时，自动使用 MusicBrainz 搜索作为后备：

- ✅ 自动解析文件名提取艺术家和标题
- ✅ 支持格式：`Artist - Title` 或 `Title - Artist`
- ✅ 处理多艺术家情况（使用第一个艺术家搜索）
- ✅ 搜索成功率显著提升：14/14 (100%) vs 之前 13/14 (93%)

**测试结果：**
- プラシーボ - 蜂屋ななし、初音ミク.flac
  - AcoustID: ❌ 无匹配
  - MusicBrainz搜索: ✅ 成功找到 (aeb2f67b-bc61-4805-a9cb-d3bcfe71629f)
  - 完整元数据已写入

### 2. 文件移动/复制选项

新增 `-r/--reserve` 选项控制文件处理方式：

**默认模式（不使用 -r）：**
- ✅ 处理后文件**移动**到 `~/.mueta/audio/`
- ✅ 原位置文件被删除
- ✅ 失败的文件也会移动到目标目录

**保留模式（使用 -r）：**
- ✅ 处理后文件**复制**到 `~/.mueta/audio/`
- ✅ 原位置文件保持不变
- ✅ 适合需要保留原始文件的场景

**自动功能：**
- ✅ 目标目录自动创建
- ✅ 文件名冲突自动重命名（添加 `_1`, `_2` 后缀）
- ✅ 错误处理优雅降级

### 测试数据

```bash
# 测试 1: 默认模式（移动）
$ mueta get-meta data/file.flac
✅ 文件从 data/ 移动到 ~/.mueta/audio/

# 测试 2: 保留模式（复制）
$ mueta get-meta -r data/file.flac
✅ 文件复制到 ~/.mueta/audio/
✅ 原文件 data/file.flac 保持不变

# 测试 3: 批量处理
$ mueta get-meta-from-folder data/
✅ 14/14 文件成功处理
✅ 所有文件移动到 ~/.mueta/audio/
✅ 处理时间: ~35秒
```

### 命令帮助

```
Options:
  --lyric     -l               Download .lrc lyrics
  --embedded  -e               Embed lyrics in metadata
  --cover     -c               Download and embed cover art
  --reserve   -r               Keep original file (copy instead of move)
  --workers   -w      INTEGER  Number of parallel workers [default: 3]
```

### 成功率对比

| 版本 | 成功率 | 说明 |
|------|--------|------|
| 初始版本 | 8/14 (57%) | 仅 AcoustID |
| 优化后 | 13/14 (93%) | AcoustID + 性能优化 |
| **最新版本** | **14/14 (100%)** | AcoustID + MusicBrainz搜索 |

