# Mueta 改进建议 (Improvement Suggestions)

基于 Picard 对比和测试观察，以下是一些改进 Mueta 功能和元数据完整性的建议：

## 1. 元数据完整性 (Metadata Completeness)

目前 Mueta 已涵盖核心元数据，但相比 MusicBrainz Picard 仍缺少部分扩展字段：

- **涉及人员 (Credits)**:
  - `lyricist` (作词)
  - `arranger` (编曲)
  - `composer` (作曲) - *部分已有，建议增强*
  - `performer` (演奏者)
  - `mixer` (混音)
  - `producer` (制作人)

- **发布信息 (Release Info)**:
  - `original_date` (原始发布日期) - *已有 original_release_date，需确认标准 tag 映射*
  - `script` (文字脚本) - *例如 Latin, Japanese*
  - `media` (介质) - *CD, Digital Media 等*
  - `release_status` (发布状态) - *Official, Bootleg 等*

- **标签/分类 (Tags/Categorization)**:
  - `grouping` (分组)
  - `mood` (情绪)
  - `language` (语言)

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
