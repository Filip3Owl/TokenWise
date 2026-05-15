#!/usr/bin/env python3
import argparse
import sys

from rich.console import Console, Group
from rich.table import Table
from rich import box
from rich.panel import Panel

from optimizer.core import Optimizer
from optimizer.pricing import format_cost, get_price

console = Console()

_STRATEGY_LABELS = {
    "whitespace_collapse": "Whitespace Collapse",
    "verbose_phrases":     "Verbose Phrases",
    "redundancy_removal":  "Redundancy Removal",
    "stopword_removal":    "Stopword Removal",
}


def _strategy_label(name: str) -> str:
    return _STRATEGY_LABELS.get(name, name.replace("_", " ").title())


def _token_bar(saved: int, max_saved: int, width: int = 16) -> str:
    if max_saved == 0 or saved <= 0:
        return "[dim]" + "░" * width + "[/dim]"
    filled = max(1, round(saved / max_saved * width))
    return "[green]" + "█" * filled + "[/green]" + "[dim]" + "░" * (width - filled) + "[/dim]"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tokenwise",
        description="Optimize prompts to reduce token consumption for LLM APIs.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("prompt", nargs="?", help="Prompt text to optimize")
    source.add_argument("--file", "-f", metavar="PATH", help="Read prompt from file")

    parser.add_argument(
        "--model", "-m",
        default="claude",
        help="Target model (claude, gpt-4, gpt-4o, gpt-3.5, codex). Default: claude",
    )
    parser.add_argument(
        "--conservative", "-c",
        action="store_true",
        help="Use only safe strategies (no stopword removal)",
    )
    parser.add_argument(
        "--output", "-o",
        metavar="PATH",
        help="Write optimized text to file instead of stdout",
    )
    parser.add_argument(
        "--lang", "-l",
        default="auto",
        choices=["auto", "en", "pt"],
        help="Language of the prompt (auto, en, pt). Default: auto",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Print only the optimized text, no report",
    )
    return parser


def print_report(result) -> None:
    price = get_price(result.model)
    savings_color = "green" if result.tokens_saved > 0 else "yellow"
    lang_label = {"en": "English", "pt": "Português"}.get(result.lang, result.lang)

    meta = (
        f"[dim]Model[/dim]     [bold]{result.model}[/bold]   "
        f"[dim]Language[/dim]  [bold]{lang_label}[/bold]   "
        f"[dim]Price[/dim]     [bold]${price.input_per_million:.2f}/M tokens[/bold]"
    )

    stats = Table.grid(padding=(0, 4))
    stats.add_column()
    stats.add_column()
    stats.add_row(
        f"[dim]Tokens[/dim]   {result.original_tokens} [dim]→[/dim] [{savings_color} bold]{result.final_tokens}[/{savings_color} bold]",
        f"[dim]Cost[/dim]     {format_cost(result.original_cost)} [dim]→[/dim] [{savings_color} bold]{format_cost(result.final_cost)}[/{savings_color} bold]",
    )
    stats.add_row(
        f"[dim]Saved[/dim]    [{savings_color}]{result.tokens_saved} ({result.savings_pct:.1f}%)[/{savings_color}]",
        f"[dim]Saved[/dim]    [{savings_color}]{format_cost(result.cost_saved)} ({result.cost_savings_pct:.1f}%)[/{savings_color}]",
    )

    console.print(Panel(
        Group(meta, "", stats),
        title="[bold blue]TokenWise Report[/bold blue]",
        box=box.ROUNDED,
        padding=(1, 2),
    ))

    max_saved = max((sr.tokens_saved for sr in result.strategy_results), default=0)

    table = Table(box=box.SIMPLE_HEAD, show_edge=False, padding=(0, 1))
    table.add_column("Strategy", style="cyan", min_width=22)
    table.add_column("Savings", no_wrap=True)
    table.add_column("Tokens", justify="right", min_width=6)
    table.add_column("Status", justify="center", min_width=10)

    for sr in result.strategy_results:
        bar = _token_bar(sr.tokens_saved, max_saved)
        if sr.tokens_saved > 0:
            table.add_row(_strategy_label(sr.name), bar, f"[green bold]-{sr.tokens_saved}[/green bold]", "[green]applied[/green]")
        else:
            table.add_row(_strategy_label(sr.name), bar, "[dim]—[/dim]", "[dim]no change[/dim]")

    console.print(table)

    console.print(Panel(
        result.optimized_text,
        title="[bold green]Optimized Prompt[/bold green]",
        border_style="green",
        box=box.ROUNDED,
        padding=(1, 2),
    ))


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.file:
        try:
            text = open(args.file).read()
        except OSError as e:
            console.print(f"[red]Error reading file:[/red] {e}")
            sys.exit(1)
    else:
        text = args.prompt

    optimizer = Optimizer(conservative=args.conservative)

    with console.status("Optimizing...", spinner="dots"):
        result = optimizer.optimize(text, model=args.model, lang=args.lang)

    if args.no_report:
        print(result.optimized_text)
    else:
        print_report(result)

    if args.output:
        try:
            open(args.output, "w").write(result.optimized_text)
            console.print(f"[green]Saved to[/green] {args.output}")
        except OSError as e:
            console.print(f"[red]Error writing output:[/red] {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
