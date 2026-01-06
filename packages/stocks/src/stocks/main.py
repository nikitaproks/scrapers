import typer

from stocks.commands import msci_world, traderepublic

app = typer.Typer(help="CLI for job processing.")
app.command("msci_world")(msci_world)
app.command("traderepublic")(traderepublic)


def main():
    app()
