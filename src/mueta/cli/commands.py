# src/mueta/cli/commands.py
"""Mueta CLI commands."""
import typer
from pathlib import Path
from typing_extensions import Annotated
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich import print as rprint
from mueta.cli.completion import Completer

app = typer.Typer(rich_markup_mode="rich", help="Mueta CLI Application")
console = Console()


@app.command(rich_help_panel="General Commands")
def init():
    """Initialize mueta and configure basic information (API_KEY, storage paths, etc.)"""
    from mueta.core.config import Settings

    console.print(
        Panel.fit(
            "[bold cyan]🎵 Welcome to Mueta![/bold cyan]\n"
            "Let's configure your settings.",
            border_style="cyan",
        )
    )

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

    # Save configuration
    config_path = Settings._get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    config_content = f"""[default]
audio_save_dir = "{audio_dir}"
lyrics_save_dir = "{lyrics_dir}"

[acoustid]
acoustid_api_key = "{acoustid_key}"
"""

    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config_content)

    console.print(
        Panel.fit(
            f"[bold green]✅ Configuration saved![/bold green]\n"
            f"Config file: [cyan]{config_path}[/cyan]",
            border_style="green",
        )
    )


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
    from mueta.engine.tagger import TaggerService
    from mueta.utils.display import extract_cover_from_file, display_cover_art
    from rich.table import Table

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
        ("track_number", "Track #"),
        ("total_tracks", "Total Tracks"),
        ("disc_number", "Disc #"),
        ("total_discs", "Total Discs"),
        ("year", "Year"),
        ("date", "Date"),
        ("original_year", "Original Year"),
        ("original_release_date", "Original Release Date"),
        ("genre", "Genre"),
        ("composer", "Composer"),
        ("label", "Label"),
        ("catalog_number", "Catalog #"),
        ("barcode", "Barcode"),
        ("asin", "ASIN"),
        ("isrc", "ISRC"),
        ("media", "Media"),
        ("release_type", "Release Type"),
        ("release_status", "Status"),
        ("release_country", "Country"),
        ("script", "Script"),
        ("duration", "Duration (s)"),
        ("bpm", "BPM"),
        ("mbid", "Recording MBID"),
        ("release_mbid", "Release MBID"),
        ("release_group_mbid", "Release Group MBID"),
        ("artist_mbid", "Artist MBID"),
        ("release_artist_mbids", "Release Artist MBIDs"),
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


@app.command(rich_help_panel="General Commands")
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
        bool, typer.Option("--reserve", "-r", help="Keep original file (copy instead of move)")
    ] = False,
    workers: Annotated[
        int, typer.Option("--workers", "-w", help="Number of parallel workers")
    ] = 3,
):
    """Get metadata for one or multiple audio files with optional lyrics."""
    from mueta.engine.pipeline import MetaPipeline, ProcessOptions
    from rich.progress import Progress, BarColumn, TaskProgressColumn, TimeRemainingColumn, TextColumn, SpinnerColumn
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from threading import Lock

    options = ProcessOptions(
        download_lyrics=lyric,
        embed_lyrics=embedded,
        embed_cover=cover,
        reserve_original=reserve,
    )

    # Filter out non-existent files
    valid_files = []
    for file in files:
        file_path = Path(file)
        if file_path.exists():
            valid_files.append(file_path)
        else:
            console.print(f"[yellow]⚠️ Skipping (not found): {file}[/yellow]")

    if not valid_files:
        console.print("[red]❌ No valid files to process[/red]")
        raise typer.Exit(1)

    console.print(f"[cyan]📁 Processing {len(valid_files)} audio files with {workers} workers[/cyan]\n")

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
            progress.update(task_id, description=f"[cyan]🎵 {file_path.name}[/cyan]", started=True)

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
                progress.update(overall_task, completed=completed, description=f"[bold]Overall Progress[/bold] ({completed}/{len(valid_files)})")
                progress.update(task_id, description=status_text, completed=1)

            return result.success, status_text

        except Exception as e:
            with lock:
                completed += 1
                failed_count += 1
                status_text = f"[red]❌ {file_path.name}[/red]: {str(e)}"
                progress.update(overall_task, completed=completed, description=f"[bold]Overall Progress[/bold] ({completed}/{len(valid_files)})")
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
            total=len(valid_files)
        )

        # Create individual tasks for each file
        file_tasks = {}
        for file_path in valid_files:
            task_id = progress.add_task(
                f"[dim]⏳ Waiting: {file_path.name}[/dim]",
                total=1,
                start=False
            )
            file_tasks[file_path] = task_id

        # Process files with thread pool
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(process_single_file, file_path, file_tasks[file_path]): file_path
                for file_path in valid_files
            }

            # Wait for all tasks to complete
            for future in as_completed(futures):
                future.result()  # This will raise exceptions if any occurred

    # Summary
    console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
    console.print(f"[bold]📊 Summary:[/bold]")
    console.print(f"  [green]✅ Successful:[/green] {success_count}")
    console.print(f"  [yellow]⚠️ Failed:[/yellow] {failed_count}")
    console.print(f"  [cyan]📁 Total:[/cyan] {len(valid_files)}")
    console.print(f"[bold cyan]{'='*60}[/bold cyan]")


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
        bool, typer.Option("--reserve", "-r", help="Keep original files (copy instead of move)")
    ] = False,
    workers: Annotated[
        int, typer.Option("--workers", "-w", help="Number of parallel workers")
    ] = 3,
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

    console.print(f"[bold cyan]📁 Found {len(audio_files)} audio files in folder[/bold cyan]\n")

    # Reuse get_meta logic with same worker count
    get_meta(files=audio_files, lyric=lyric, embedded=embedded, cover=cover, reserve=reserve, workers=workers)
