import typer

from find_job.process import process
from find_job.scrape import scrape

app = typer.Typer(help="CLI for job processing.")
app.command()(scrape)
app.command()(process)


def main():
    app()
