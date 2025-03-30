import typer

from stocks.commands import msci_world

app = typer.Typer(help="CLI for job processing.")
app.command()(msci_world)


def main():
    app()
