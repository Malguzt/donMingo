import shutil

from invoke.context import Context
from invoke.tasks import task


@task
def build(c: Context) -> None:
    test(c)
    lint(c)
    typecheck(c)


@task
def run(c: Context) -> None:
    c.run("python src/main.py")


@task
def test(c: Context) -> None:
    # Always run coverage: terminal + XML + HTML
    c.run(
        "pytest --cov=src --cov-report=term-missing --cov-report=xml --cov-report=html -n auto --force-sugar"
    )
    # Convert coverage.xml -> lcov.info
    c.run(
        "coverage-lcov --data_file_path .coverage --output_file_path lcov.info --relative_path"
    )

    # Optionally build a colored HTML report with genhtml if available
    if shutil.which("genhtml"):
        c.run("genhtml lcov.info -o lcov-report")


@task
def typecheck(c: Context) -> None:
    c.run("pyright src test")


@task
def lint(c: Context) -> None:
    c.run("ruff check src test --fix")
    c.run("ruff format src test")
    c.run("isort src test")
