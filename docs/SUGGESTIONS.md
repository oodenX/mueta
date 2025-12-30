# Mueta 改进建议 (Improvement Suggestions)

基于 Picard 对比和测试观察，以下是一些改进 Mueta 功能和元数据完整性的建议：

## 1. 元数据完整性 (Metadata Completeness)

对比 MusicBrainz Picard 的元数据字段，Mueta 目前的支持状态如下：

### 1.1 基本信息 (Basic Info)

| 字段 | Picard Tag | Mueta 状态 | 说明 |
|------|-----------|-----------|------|
| 标题 | `title` | ✅ 已实现 | |
| 艺术家 | `artist` | ✅ 已实现 | |
| 多艺术家 | `artists` | ✅ 已实现 | 列表格式 |
| 专辑 | `album` | ✅ 已实现 | |
| 专辑艺术家 | `albumartist` | ✅ 已实现 | |
| 流派 | `genre` | ✅ 已实现 | 从 tags 获取 |

### 1.2 排序字段 (Sort Order)

| 字段 | Picard Tag | Mueta 状态 | 说明 |
|------|-----------|-----------|------|
| 艺术家排序 | `artistsort` | ✅ 已实现 | |
| 专辑艺术家排序 | `albumartistsort` | ✅ 已实现 | |
| 标题排序 | `titlesort` | ❌ 缺失 | 用于非拉丁语系排序 |
| 专辑排序 | `albumsort` | ❌ 缺失 | |

### 1.3 曲目/碟片信息 (Track/Disc)

| 字段 | Picard Tag | Mueta 状态 | 说明 |
|------|-----------|-----------|------|
| 曲目号 | `tracknumber` | ✅ 已实现 | |
| 总曲目数 | `totaltracks` | ✅ 已实现 | |
| 碟片号 | `discnumber` | ✅ 已实现 | |
| 总碟片数 | `totaldiscs` | ✅ 已实现 | |
| 碟片副标题 | `discsubtitle` | ❌ 缺失 | |

### 1.4 日期信息 (Date)

| 字段 | Picard Tag | Mueta 状态 | 说明 |
|------|-----------|-----------|------|
| 发布日期 | `date` | ✅ 已实现 | |
| 年份 | `date` (year) | ✅ 已实现 | |
| 原始发布日期 | `originaldate` | ✅ 已实现 | |
| 原始年份 | `originalyear` | ✅ 已实现 | |

### 1.5 发布信息 (Release Info)

| 字段 | Picard Tag | Mueta 状态 | 说明 |
|------|-----------|-----------|------|
| 唱片公司 | `label` | ✅ 已实现 | |
| 目录号 | `catalognumber` | ✅ 已实现 | |
| 条形码 | `barcode` | ✅ 已实现 | |
| ASIN | `asin` | ✅ 已实现 | |
| ISRC | `isrc` | ✅ 已实现 | |
| 介质类型 | `media` | ✅ 已实现 | CD, Digital 等 |
| 发布类型 | `releasetype` | ✅ 已实现 | Album, Single 等 |
| 发布状态 | `releasestatus` | ✅ 已实现 | Official, Bootleg |
| 发布国家 | `releasecountry` | ✅ 已实现 | |
| 文字脚本 | `script` | ✅ 已实现 | Jpan, Latn 等 |

### 1.6 涉及人员 (Credits) — ⚠️ 需增强

| 字段 | Picard Tag | Mueta 状态 | 说明 |
|------|-----------|-----------|------|
| 作曲 | `composer` | ✅ 已实现 | 模型有，但 MusicBrainz 未获取 |
| 作词 | `lyricist` | ⚠️ 模型有 | 模型已定义但未填充数据 |
| 制作人 | `producer` | ⚠️ 模型有 | 模型已定义但未填充数据 |
| 编曲 | `arranger` | ❌ 缺失 | MusicBrainz relations 可获取 |
| 混音 | `mixer` | ❌ 缺失 | |
| 指挥 | `conductor` | ❌ 缺失 | |
| 演奏者 | `performer` | ❌ 缺失 | |
| DJ/混音师 | `djmixer` | ❌ 缺失 | |
| 工程师 | `engineer` | ❌ 缺失 | |
| 录音师 | `writer` | ❌ 缺失 | |

> **实现建议**: 需要扩展 MusicBrainz API 调用，使用 `inc=artist-rels+recording-rels` 获取 relations 数据，从中提取 credits 信息。

### 1.7 MusicBrainz IDs

| 字段 | Picard Tag | Mueta 状态 | 说明 |
|------|-----------|-----------|------|
| Recording ID | `musicbrainz_recordingid` | ✅ 已实现 | |
| Release ID | `musicbrainz_albumid` | ✅ 已实现 | |
| Release Group ID | `musicbrainz_releasegroupid` | ✅ 已实现 | |
| Artist ID | `musicbrainz_artistid` | ✅ 已实现 | 首位艺术家 |
| Album Artist IDs | `musicbrainz_albumartistid` | ✅ 已实现 | 多值 |
| Track ID | `musicbrainz_trackid` | ❌ 缺失 | 与 Recording ID 不同 |
| Work ID | `musicbrainz_workid` | ❌ 缺失 | 作品ID (用于古典/翻唱关联) |

### 1.8 其他 Picard 字段 — ❌ 缺失

| 字段 | Picard Tag | 说明 | 实现难度 |
|------|-----------|------|---------|
| 语言 | `language` | 歌词/标题语言 | 中 |
| 分组 | `grouping` | 自定义分组 | 低 (用户输入) |
| BPM | `bpm` | 节拍速率 | 高 (需音频分析) |
| 版权 | `copyright` | 版权信息 | 中 |
| 许可证 | `license` | 许可信息 | 低 |
| 编码 | `encodedby` | 编码者 | 低 |
| 评论 | `comment` | 注释 | 低 |
| 情绪 | `mood` | AcousticBrainz (已停用) | N/A |
| 键 | `key` | 音调键 | 高 (需音频分析) |
| AcoustID | `acoustid_id` | 音频指纹 ID | 低 |
| AcoustID Fingerprint | `acoustid_fingerprint` | 原始指纹 | 低 |

### 1.9 总结

| 类别 | 已实现 | 部分实现 | 缺失 |
|------|--------|---------|------|
| 基本信息 | 6/6 | 0 | 0 |
| 排序字段 | 2/4 | 0 | 2 |
| 曲目信息 | 4/5 | 0 | 1 |
| 日期信息 | 4/4 | 0 | 0 |
| 发布信息 | 10/10 | 0 | 0 |
| 涉及人员 | 1/10 | 2 | 7 |
| MusicBrainz IDs | 5/7 | 0 | 2 |
| 其他 | 1/12 | 0 | 11 |

**整体覆盖率**: ~60% (33/58 字段)

> **优先级建议**:
> 1. **高优先级**: `lyricist`, `producer` (模型已有，仅需从 MusicBrainz relations 获取)
> 2. **中优先级**: `arranger`, `language`, `acoustid_id`
> 3. **低优先级**: 排序字段, 其他扩展字段

## 2. 功能增强 (Feature Enhancements)

- **手动匹配/交互模式**:
  对于 AcoustID 无法识别的曲目 (例如 "不在者着信", "花隈の歌..."), 建议增加交互式搜索模式，允许用户输入关键词搜索 MusicBrainz 数据库。

- **多源数据整合**:
  - 如果 MusicBrainz 缺少数据，可以考虑 fallback 到 Discogs 或 Spotify API (需权衡复杂度)。

- **歌词源扩展**:
  - 目前歌词覆盖率约 34%。建议增加更多歌词源 (如 NetEase, QQ Music, Genius) 以提高覆盖率，特别是针对 VOCALOID/中文/日文歌曲。

- **自定义 Tag 映射**:
  - 允许用户在 `config.toml` 中配置自定义的 tag 映射规则，以适应不同的播放器需求。

## 3. 性能与体验

- **日志文件**:
  建议将批量处理的详细日志 (成功/失败列表) 输出到文件中 (`process_log.txt`)，方便用户事后查看失败文件。

- **断点续传**:
  对于超大文件夹，增加跳过已包含完整元数据文件的选项 (`--skip-existing`)。
