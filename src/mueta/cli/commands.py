# src/mueta/cli/commands.py
"""Mueta CLI commands."""

from pathlib import Path

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from typing_extensions import Annotated

from mueta.cli.completion import Completer

__version__ = "0.3.0"


def version_callback(value: bool):
    if value:
        rprint(f"[bold cyan]Mueta[/bold cyan] version [green]{__version__}[/green]")
        raise typer.Exit()


app = typer.Typer(rich_markup_mode="rich", help="Mueta CLI Application")
console = Console()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit",
        ),
    ] = False,
):
    """Mueta - Music metadata auto getter"""
    pass


@app.command(rich_help_panel="General Commands")
def init():
    """Initialize mueta and configure basic information (API_KEY, storage paths, etc.)"""
    import httpx

    from mueta.core.config import Settings
    from mueta.utils.system import check_fpcalc

    console.print(
        Panel.fit(
            "[bold cyan]🎵 Welcome to Mueta![/bold cyan]\n"
            "Let's configure your settings.",
            border_style="cyan",
        )
    )

    # Check fpcalc dependency
    fpcalc_installed, install_guide = check_fpcalc()
    if not fpcalc_installed:
        console.print("\n[yellow]⚠️  未检测到 fpcalc[/yellow]")
        console.print(f"[dim]{install_guide}[/dim]")

        continue_anyway = Prompt.ask(
            "\n是否继续配置？(稍后安装 fpcalc 也可以正常使用)",
            choices=["y", "n"],
            default="y",
        )

        if continue_anyway.lower() != "y":
            console.print("[yellow]配置已取消[/yellow]")
            raise typer.Exit(0)

    # Get default paths
    default_audio_dir = str(Path.home() / ".mueta" / "audio")
    default_lyrics_dir = str(Path.home() / ".mueta" / "lyrics")

    # Audio save directory
    console.print("\n[bold]📁 Audio Save Directory[/bold]")
    audio_dir = Prompt.ask(
        "  Enter path (leave empty for default)",
        default=default_audio_dir,
        show_default=True,
    )

    # Lyrics save directory
    console.print("\n[bold]📝 Lyrics Save Directory[/bold]")
    lyrics_dir = Prompt.ask(
        "  Enter path (leave empty for default)",
        default=default_lyrics_dir,
        show_default=True,
    )

    # AcoustID API key
    console.print("\n[bold]🔑 AcoustID API Key[/bold]")
    console.print(
        "  [dim]Get your API key at: [link=https://acoustid.org/new-application]https://acoustid.org/new-application[/link][/dim]"
    )
    acoustid_key = Prompt.ask("  Enter your AcoustID API key")

    if not acoustid_key:
        console.print("[red]❌ AcoustID API key is required![/red]")
        raise typer.Exit(1)

    # Validate AcoustID API key
    console.print("  [dim]Validating API key...[/dim]")
    try:
        # Test API key with a minimal request
        test_url = "https://api.acoustid.org/v2/lookup"
        params = {
            "client": acoustid_key,
            "meta": "recordings",
            "duration": "1",
            "fingerprint": "AQABEUmUaEmoSBGmQ",  # Minimal test fingerprint
        }
        response = httpx.get(test_url, params=params, timeout=10.0)

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok":
                console.print("  [green]✓ API Key 验证成功[/green]")
            else:
                console.print("  [yellow]⚠️  API Key 可能无效，但已保存[/yellow]")
        else:
            console.print("  [yellow]⚠️  验证失败，但已保存 Key[/yellow]")
    except Exception as e:
        console.print(f"  [yellow]⚠️  无法验证 (网络错误)，Key 已保存[/yellow]")

    # Genius API key
    console.print("\n[bold]🔑 Genius API Key (Optional)[/bold]")
    console.print(
        "  [dim]Get your Client Access Token at: [link=https://genius.com/api-clients]https://genius.com/api-clients[/link][/dim]"
    )
    genius_key = Prompt.ask("  Enter your Genius API Token (leave empty to skip)")

    # Save configuration
    config_path = Settings._get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    config_content = f"""[default]
audio_save_dir = "{audio_dir}"
lyrics_save_dir = "{lyrics_dir}"

[acoustid]
acoustid_api_key = "{acoustid_key}"

[genius]
genius_api_key = "{genius_key or ""}"

[retry]
max_retries = 3
base_delay = 1.0
max_delay = 30.0

[processing]
default_workers = 3
"""

    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config_content)

    console.print(
        Panel.fit(
            f"[bold green]✅ Configuration saved![/bold green]\n"
            f"Config file: [cyan]{config_path}[/cyan]\n\n"
            f"[dim]Tip: Use 'mueta config' to view or edit this file anytime.[/dim]",
            border_style="green",
        )
    )


@app.command(rich_help_panel="General Commands")
def config():
    """View or edit mueta configuration file."""
    import platform
    import subprocess

    from mueta.core.config import Settings

    config_path = Settings._get_config_path()

    if not config_path.exists():
        console.print("[yellow]⚠️  配置文件不存在[/yellow]")
        console.print(f"[dim]请先运行 'mueta init' 创建配置[/dim]")
        raise typer.Exit(1)

    console.print(
        Panel.fit(
            f"[bold cyan]📄 Mueta Configuration[/bold cyan]\n\n"
            f"Config file: [green]{config_path}[/green]",
            border_style="cyan",
        )
    )

    # Ask if user wants to edit
    edit = Prompt.ask("\n是否打开编辑器编辑配置文件？", choices=["y", "n"], default="n")

    if edit.lower() == "y":
        # Detect platform and open editor
        system = platform.system()
        try:
            if system == "Windows":
                subprocess.run(["notepad", str(config_path)])
            elif system == "Darwin":  # macOS
                subprocess.run(["open", "-e", str(config_path)])
            else:  # Linux
                # Try common editors in order
                editors = ["nano", "vi", "vim", "gedit", "kate"]
                editor = None
                for ed in editors:
                    if (
                        subprocess.run(["which", ed], capture_output=True).returncode
                        == 0
                    ):
                        editor = ed
                        break

                if editor:
                    subprocess.run([editor, str(config_path)])
                else:
                    console.print("[yellow]未找到可用的文本编辑器[/yellow]")
                    console.print(f"[dim]请手动编辑: {config_path}[/dim]")
        except Exception as e:
            console.print(f"[red]打开编辑器失败: {e}[/red]")
            console.print(f"[dim]请手动编辑: {config_path}[/dim]")


@app.command(rich_help_panel="General Commands")
def cache_clean():
    """Clear mueta cache database."""
    from pathlib import Path

    cache_db = Path.home() / ".mueta" / "cache.db"

    if not cache_db.exists():
        console.print("[yellow]⚠️  缓存文件不存在[/yellow]")
        raise typer.Exit(0)

    # Show cache size
    cache_size_mb = cache_db.stat().st_size / (1024 * 1024)
    console.print(f"\n[cyan]当前缓存大小: {cache_size_mb:.2f} MB[/cyan]")

    # Confirm deletion
    confirm = Prompt.ask(
        "确认清空缓存？(此操作不可恢复)", choices=["y", "n"], default="n"
    )

    if confirm.lower() == "y":
        try:
            cache_db.unlink()
            console.print("[green]✓ 缓存已清空[/green]")
        except Exception as e:
            console.print(f"[red]清空失败: {e}[/red]")
            raise typer.Exit(1)
    else:
        console.print("[yellow]已取消[/yellow]")


@app.command(rich_help_panel="General Commands")
def view_meta(
    file: Annotated[
        str,
        typer.Argument(
            help="Audio file path (mp3, flac, aac, etc.)",
            autocompletion=Completer.complete_audio_files,
        ),
    ],
    show_cover: Annotated[
        bool, typer.Option("--show-cover", "-c", help="Display cover art in terminal")
    ] = False,
):
    """View all metadata properties of an audio file."""
    from rich.table import Table

    from mueta.engine.tagger import TaggerService
    from mueta.utils.display import display_cover_art, extract_cover_from_file

    tagger = TaggerService()
    file_path = Path(file)

    if not file_path.exists():
        console.print(f"[red]❌ File not found: {file}[/red]")
        raise typer.Exit(1)

    # Extract and display cover art (only if --show-cover is specified)
    if show_cover:
        cover_data = extract_cover_from_file(file_path)
        if cover_data:
            console.print("\n[bold cyan]Cover Art:[/bold cyan]")
            display_cover_art(cover_data, width=50)
            console.print()  # Add spacing

    meta = tagger.read_metadata(file_path)

    table = Table(title=f"🎵 Metadata: {file_path.name}", show_header=True)
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    # Organize fields in a logical order
    field_order = [
        ("title", "Title"),
        ("artist", "Artist"),
        ("artists", "Artists"),
        ("artist_sort_order", "Artist Sort Order"),
        ("album", "Album"),
        ("album_artist", "Album Artist"),
        ("album_artist_sort_order", "Album Artist Sort Order"),
        ("track_number", "Track Number"),
        ("total_tracks", "Total Tracks"),
        ("disc_number", "Disc Number"),
        ("total_discs", "Total Discs"),
        ("year", "Year"),
        ("date", "Date"),
        ("original_year", "Original Year"),
        ("original_release_date", "Original Release Date"),
        ("genre", "Genre"),
        ("genres", "Genres"),
        ("mood", "Mood"),
        ("moods", "Moods"),
        # Credits
        ("composer", "Composer"),
        ("lyricist", "Lyricist"),
        ("producer", "Producer"),
        ("arranger", "Arranger"),
        ("mixer", "Mixer"),
        ("conductor", "Conductor"),
        ("performer", "Performer"),
        ("writer", "Writer"),
        # Release info
        ("label", "Label"),
        ("catalog_number", "Catalog Number"),
        ("barcode", "Barcode"),
        ("asin", "ASIN"),
        ("isrc", "ISRC"),
        ("media", "Media"),
        ("release_type", "Release Type"),
        ("release_status", "Release Status"),
        ("release_country", "Release Country"),
        ("script", "Script"),
        # Additional
        ("language", "Language"),
        ("copyright", "Copyright"),
        ("duration", "Duration (s)"),
        ("bpm", "BPM"),
        ("key", "Key"),
        # MusicBrainz IDs
        ("mbid", "Recording MBID"),
        ("release_mbid", "Release MBID"),
        ("release_group_mbid", "Release Group MBID"),
        ("artist_mbid", "Artist MBID"),
        ("release_artist_mbids", "Release Artist MBIDs"),
        ("work_mbid", "Work MBID"),
        ("acoustid_id", "AcoustID"),
    ]

    meta_dict = meta.model_dump()
    for field_key, field_label in field_order:
        value = meta_dict.get(field_key)
        if value is not None:
            # Format list values
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            table.add_row(field_label, str(value))

    console.print(table)


@app.command(rich_help_panel="Analysis Commands")
def analyze(
    path: Annotated[
        Path,
        typer.Argument(
            exists=True,
            help="Path to audio file or directory",
            resolve_path=True,
        ),
    ],
    recursive: Annotated[
        bool,
        typer.Option("--recursive", "-r", help="Recursively process directories"),
    ] = False,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Force re-analysis even if tags exist"),
    ] = False,
    semantic: Annotated[
        bool,
        typer.Option("--semantic", "-s", help="Include AI-powered genre and mood detection"),
    ] = True,
):
    """
    Analyze audio files for BPM, Key, and AI-powered Genre/Mood.
    """
    from mueta.engine.analysis import AudioAnalyzer
    from mueta.engine.tagger import TaggerService
    from mueta.engine.semantic import SemanticAnalyzer

    console.print(f"[bold cyan]Analyzing audio in:[/bold cyan] {path}")

    tagger = TaggerService()
    analyzer = AudioAnalyzer()
    semantic_analyzer = SemanticAnalyzer()

    files_to_process = []
    if path.is_file():
        files_to_process.append(path)
    elif path.is_dir():
        pattern = "**/*" if recursive else "*"
        for p in path.glob(pattern):
            if p.is_file():
                files_to_process.append(p)

    processed_count = 0
    skipped_count = 0
    error_count = 0

    with console.status("[bold green]Analyzing files...[/bold green]") as status:
        for file_path in files_to_process:
            is_valid, _ = tagger.validate_audio_file(file_path)
            if not is_valid:
                continue

            status.update(f"Processing {file_path.name}...")

            try:
                # Check if already analyzed
                if not force:
                    current_meta = tagger.read_metadata(file_path)
                    if current_meta.bpm and current_meta.key:
                        console.print(
                            f"[dim]Skipping {file_path.name} (already analyzed)[/dim]"
                        )
                        skipped_count += 1
                        continue

                # Analyze acoustic features
                analysis_meta = analyzer.analyze(file_path)

                # Analyze semantic features (Genre/Mood)
                if semantic:
                    status.update(f"AI detecting genre/mood for {file_path.name}...")
                    # We need artist/title for Last.fm fallback, but ML only needs file
                    current_tags = tagger.read_metadata(file_path)
                    semantic_data = semantic_analyzer.analyze(
                        current_tags.artist or "",
                        current_tags.title or file_path.stem,
                        audio_file=file_path
                    )
                    if semantic_data["genres"]:
                        analysis_meta.genres = semantic_data["genres"]
                        analysis_meta.genre = semantic_data["genres"][0]
                    if semantic_data["moods"]:
                        analysis_meta.moods = semantic_data["moods"]
                        analysis_meta.mood = semantic_data["moods"][0]

                if not analysis_meta.bpm and not analysis_meta.key and not analysis_meta.genres:
                    console.print(
                        f"[yellow]No features extracted for {file_path.name}[/yellow]"
                    )
                    error_count += 1
                    continue

                # Write tags
                tagger.write_metadata(file_path, analysis_meta)

                console.print(
                    f"[green]Analyzed {file_path.name}:[/green] "
                    f"BPM={analysis_meta.bpm}, Key={analysis_meta.key} {analysis_meta.scale or ''} "
                    f"Genre={analysis_meta.genre or 'N/A'}"
                )
                processed_count += 1

            except Exception as e:
                console.print(f"[red]Error analyzing {file_path.name}: {e}[/red]")
                error_count += 1

    console.print(
        Panel(
            f"Processed: {processed_count}\nSkipped: {skipped_count}\nErrors: {error_count}",
            title="Analysis Complete",
            border_style="green",
        )
    )


@app.command(rich_help_panel="Metadata Commands")
def get_meta(
    files: Annotated[
        list[str],
        typer.Argument(
            help="Audio file paths (mp3, flac, aac, etc.)",
            autocompletion=Completer.complete_audio_files,
        ),
    ],
    lyric: Annotated[
        bool, typer.Option("--lyric", "-l", help="Download .lrc lyrics")
    ] = False,
    embedded: Annotated[
        bool, typer.Option("--embedded", "-e", help="Embed lyrics in metadata")
    ] = False,
    cover: Annotated[
        bool, typer.Option("--cover", "-c", help="Download and embed cover art")
    ] = True,
    reserve: Annotated[
        bool,
        typer.Option(
            "--reserve", "-r", help="Keep original file (copy instead of move)"
        ),
    ] = False,
    workers: Annotated[
        int, typer.Option("--workers", "-w", help="Number of parallel workers")
    ] = 3,
    interactive: Annotated[
        bool,
        typer.Option(
            "--interactive", "-i", help="Interactive mode (ask user when unsure)"
        ),
    ] = False,
    skip_existing: Annotated[
        bool,
        typer.Option(
            "--skip-existing",
            "-s",
            help="Skip files that already have complete metadata",
        ),
    ] = False,
    analyze: Annotated[
        bool,
        typer.Option(
            "--analyze",
            "-a",
            help="Analyze audio features (BPM, Key, etc.)",
        ),
    ] = False,
    semantic: Annotated[
        bool,
        typer.Option(
            "--semantic",
            "-S",
            help="Include AI-powered genre and mood detection",
        ),
    ] = True,
):
    """Get metadata for one or multiple audio files with optional lyrics."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from threading import Lock

    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TaskProgressColumn,
        TextColumn,
        TimeRemainingColumn,
    )

    from mueta.engine.pipeline import MetaPipeline, ProcessOptions
    from mueta.engine.tagger import TaggerService

    if interactive:
        if workers > 1:
            console.print(
                "[yellow]⚠️ Interactive mode enabled: Forcing workers=1 to prevent console conflicts[/yellow]"
            )
            workers = 1

    options = ProcessOptions(
        download_lyrics=lyric,
        embed_lyrics=embedded,
        embed_cover=cover,
        reserve_original=reserve,
        interactive=interactive,
        analyze=analyze,
        get_genre=semantic,
    )

    # Filter out non-existent files
    valid_files = []
    tagger = TaggerService()

    console.print("[cyan]🔍 Validating audio files...[/cyan]")
    for file in files:
        file_path = Path(file)
        if not file_path.exists():
            console.print(f"[yellow]⚠️ Skipping (not found): {file}[/yellow]")
            continue

        # Quick validation before processing
        is_valid, error = tagger.validate_audio_file(file_path)
        if is_valid:
            # Skip if already has complete metadata
            if skip_existing:
                existing_meta = tagger.read_metadata(file_path)
                if existing_meta and existing_meta.title and existing_meta.artist:
                    console.print(
                        f"[dim]⏭️  Skipping (has metadata): {file_path.name}[/dim]"
                    )
                    continue

            valid_files.append(file_path)
        else:
            console.print(f"[yellow]⚠️ Skipping ({error}): {file_path.name}[/yellow]")

    if not valid_files:
        console.print("[red]❌ No valid audio files to process[/red]")
        raise typer.Exit(1)

    console.print(
        f"[cyan]📁 Processing {len(valid_files)} audio files with {workers} workers[/cyan]\n"
    )

    # Thread-safe counters
    lock = Lock()
    completed = 0
    success_count = 0
    failed_count = 0

    def process_single_file(file_path: Path, task_id):
        """Process a single audio file and return the result."""
        nonlocal completed, success_count, failed_count

        pipeline = MetaPipeline()

        try:
            # Update progress for this task
            progress.update(
                task_id, description=f"[cyan]🎵 {file_path.name}[/cyan]", started=True
            )

            result = pipeline.process_file(file_path, options)

            with lock:
                completed += 1
                if result.success:
                    success_count += 1
                    status_text = f"[green]✅ {file_path.name}[/green]: {result.title} - {result.artist}"
                else:
                    failed_count += 1
                    status_text = f"[yellow]⚠️ {file_path.name}[/yellow]: {result.error}"

                # Update overall progress
                progress.update(
                    overall_task,
                    completed=completed,
                    description=f"[bold]Overall Progress[/bold] ({completed}/{len(valid_files)})",
                )
                progress.update(task_id, description=status_text, completed=1)

            return result.success, status_text

        except Exception as e:
            with lock:
                completed += 1
                failed_count += 1
                status_text = f"[red]❌ {file_path.name}[/red]: {str(e)}"
                progress.update(
                    overall_task,
                    completed=completed,
                    description=f"[bold]Overall Progress[/bold] ({completed}/{len(valid_files)})",
                )
                progress.update(task_id, description=status_text, completed=1)
            return False, status_text

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
        expand=True,
    ) as progress:
        # Overall progress task
        overall_task = progress.add_task(
            f"[bold]Overall Progress[/bold] (0/{len(valid_files)})",
            total=len(valid_files),
        )

        # Create individual tasks for each file
        file_tasks = {}
        for file_path in valid_files:
            task_id = progress.add_task(
                f"[dim]⏳ Waiting: {file_path.name}[/dim]", total=1, start=False
            )
            file_tasks[file_path] = task_id

        # Process files with thread pool
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(
                    process_single_file, file_path, file_tasks[file_path]
                ): file_path
                for file_path in valid_files
            }

            # Wait for all tasks to complete
            for future in as_completed(futures):
                future.result()  # This will raise exceptions if any occurred

    # Summary
    console.print(f"\n[bold cyan]{'=' * 60}[/bold cyan]")
    console.print(f"[bold]📊 Summary:[/bold]")
    console.print(f"  [green]✅ Successful:[/green] {success_count}")
    console.print(f"  [yellow]⚠️ Failed:[/yellow] {failed_count}")
    console.print(f"  [cyan]📁 Total:[/cyan] {len(valid_files)}")
    console.print(f"[bold cyan]{'=' * 60}[/bold cyan]")


@app.command(rich_help_panel="General Commands")
def get_meta_from_folder(
    folder: Annotated[
        str,
        typer.Argument(
            help="Folder path containing audio files",
            autocompletion=Completer.complete_folders,
        ),
    ],
    lyric: Annotated[
        bool, typer.Option("--lyric", "-l", help="Download .lrc lyrics")
    ] = False,
    embedded: Annotated[
        bool, typer.Option("--embedded", "-e", help="Embed lyrics in metadata")
    ] = False,
    cover: Annotated[
        bool, typer.Option("--cover", "-c", help="Download and embed cover art")
    ] = True,
    reserve: Annotated[
        bool,
        typer.Option(
            "--reserve", "-r", help="Keep original files (copy instead of move)"
        ),
    ] = False,
    workers: Annotated[
        int, typer.Option("--workers", "-w", help="Number of parallel workers")
    ] = 3,
    interactive: Annotated[
        bool,
        typer.Option(
            "--interactive", "-i", help="Interactive mode (ask user when unsure)"
        ),
    ] = False,
    skip_existing: Annotated[
        bool,
        typer.Option(
            "--skip-existing",
            "-s",
            help="Skip files that already have complete metadata",
        ),
    ] = False,
    analyze: Annotated[
        bool,
        typer.Option(
            "--analyze",
            "-a",
            help="Analyze audio features (BPM, Key, etc.)",
        ),
    ] = False,
    semantic: Annotated[
        bool,
        typer.Option(
            "--semantic",
            "-S",
            help="Include AI-powered genre and mood detection",
        ),
    ] = True,
):
    """Get metadata for all audio files in a folder with optional lyrics."""
    folder_path = Path(folder)

    if not folder_path.is_dir():
        console.print(f"[red]❌ Folder not found: {folder}[/red]")
        raise typer.Exit(1)

    # Find all audio files
    audio_extensions = {".mp3", ".flac", ".aac", ".wav", ".ogg", ".m4a"}
    audio_files = [
        str(f) for f in folder_path.iterdir() if f.suffix.lower() in audio_extensions
    ]

    if not audio_files:
        console.print(f"[yellow]⚠️ No audio files found in: {folder}[/yellow]")
        raise typer.Exit(0)

    console.print(
        f"[bold cyan]📁 Found {len(audio_files)} audio files in folder[/bold cyan]\n"
    )

    # Reuse get_meta logic with same worker count
    get_meta(
        files=audio_files,
        lyric=lyric,
        embedded=embedded,
        cover=cover,
        reserve=reserve,
        workers=workers,
        interactive=interactive,
        skip_existing=skip_existing,
        analyze=analyze,
        semantic=semantic,
    )
