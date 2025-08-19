from invoke import task
import shutil

@task
def run(c):
    c.run("python src/main.py")

@task
def test(c):
    # Always run coverage: terminal + XML + HTML
    c.run("pytest --cov=src --cov-report=term-missing --cov-report=xml --cov-report=html")
    # Convert coverage.xml -> lcov.info
    c.run("coverage-lcov --data_file_path .coverage --output_file_path lcov.info --relative_path")
    # Optionally build a colored HTML report with genhtml if available
    if shutil.which("genhtml"):
        c.run("genhtml lcov.info -o lcov-report")
