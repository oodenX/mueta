Output demo/semantic.gif

Set FontSize 16
Set Width 1200
Set Height 600
Set Padding 20
Set TypingSpeed 50ms

Hide
Type "export MUETA_CONFIG_PATH=$(pwd)/config.toml"
Enter
Type "cd /home/taurus/Projetcs/mueta"
Enter
Show

# Demo: AI Semantic Analysis (Genre/Mood)
Type "# Use --semantic (or -s) to predict genre and mood using AI models"
Enter
Type "uv run mueta analyze '/home/taurus/test/test_audio/17 - 椎名林檎.flac' --semantic -f"
Sleep 500ms
Enter
Sleep 15s

# View the metadata
Type "uv run mueta view-meta '/home/taurus/test/test_audio/17 - 椎名林檎.flac'"
Sleep 500ms
Enter
Sleep 8s
