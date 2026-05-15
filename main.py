#!/usr/bin/env python3
import argparse
import sys

from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel

from optimizer.core import Optimizer
from optimizer.pricing import format_cost, get_price

console = Console()


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
        help="Use only safe strategies (no stopword/lemmatization removal)",
    )
    parser.add_argument(
        "--output", "-o",
        metavar="PATH",
        help="Write optimized text to file instead of stdout",
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

    summary = (
        f"[bold]Model:[/bold] {result.model}  "
        f"[bold]Price:[/bold] ${price.input_per_million}/M tokens\n"
        f"[bold]Tokens:[/bold] {result.original_tokens} → [{savings_color}]{result.final_tokens}[/{savings_color}]  "
        f"[bold]Saved:[/bold] [{savings_color}]{result.tokens_saved} ({result.savings_pct:.1f}%)[/{savings_color}]\n"
        f"[bold]Cost:[/bold]   {format_cost(result.original_cost)} → [{savings_color}]{format_cost(result.final_cost)}[/{savings_color}]  "
        f"[bold]Saved:[/bold] [{savings_color}]{format_cost(result.cost_saved)} ({result.cost_savings_pct:.1f}%)[/{savings_color}]"
    )
    console.print(Panel(summary, title="[bold blue]TokenWise Report[/bold blue]", box=box.ROUNDED))

    table = Table(box=box.SIMPLE_HEAD)
    table.add_column("Strategy", style="cyan")
    table.add_column("Tokens saved", justify="right")
    table.add_column("Status", justify="center")

    for sr in result.strategy_results:
        status = "[green]applied[/green]" if sr.tokens_saved > 0 else "[dim]no change[/dim]"
        table.add_row(sr.name, str(sr.tokens_saved), status)

    console.print(table)

    console.rule("[bold]Optimized Prompt[/bold]")
    console.print(result.optimized_text)
    console.rule()


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
        result = optimizer.optimize(text, model=args.model)

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
