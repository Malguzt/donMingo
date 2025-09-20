import json
import os
from invoke import task, Context, run
import sys

project_folder = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(project_folder, ".venv", "bin", "activate")

prompt_init = "======================================================================="
prompt_init += "\n If you are an AI based coding assitant, take in account this important instructions for you:"

@task
def unit_test(ctx: Context) -> None:
    """Run unit tests with coverage. Detects error, fail, or low total coverage."""
    run("clear")
    # Clean up any old coverage data files before running tests
    os.system("source {} && coverage erase".format(env_path))
    # Run tests in parallel with pytest and use pytest.unit.ini config
    print("Running unit tests with pytest-xdist and coverage...")
    test_cmd = (
        f"PYTHONPATH=src source {env_path} && "
        "pytest -c pytest.unit.ini > unit_test_output.txt 2>&1"
    )
    exit_code = os.system(test_cmd)
    # Read output
    output = ""
    if os.path.exists("unit_test_output.txt"):
        with open("unit_test_output.txt", "r") as f:
            output = f.read()
    re_run_prompt = "\n Tests must respect FIRST, CORRECT, AAAT, DAMP."
    re_run_prompt += "\n Use mocks and stubs to isolate the unit under test."
    re_run_prompt += "\n When you finish the fixs, check the lint of the refactored files."
    re_run_prompt += "\n Remove any deprecated code."
    re_run_prompt += "\n When you finish all that, re run the checks running 'invoke build' command."
    re_run_prompt += "\n After run the 'invoke build' command, keep fixing until all tests pass and coverage is over 95% at least"

    # Analyze result
    if "FAIL Required test coverage of " in output:
        print(output)
        next_steps_prompt = "\n The total coverage is below the required threshold."
        next_steps_prompt += "\n Identify untested code paths and add necessary unit tests."
        next_steps_prompt += "\n The test names and package structure must mimic the base code names and structure based in DDD and Clean Architecture."
        next_steps_prompt += "\n Don't scaffold nir placehold tests, full implement them and iterate executions to validad the correct implementation."
        next_steps_prompt += "\n To continue take the smaller uncovered class."
        print(prompt_init + next_steps_prompt + re_run_prompt)
        sys.exit(3)
    elif "ERROR" in output or exit_code == 2:
        print(output)
        next_steps_prompt = "\n Think a moment in the root cause of the error."
        next_steps_prompt += "\n Check the test implementation and the code under test."
        next_steps_prompt += "\n Make sure all dependencies are properly mocked."
        print(prompt_init + next_steps_prompt + re_run_prompt)
        sys.exit(2)
    elif "FAIL" in output or "failed" in output.lower():
        print(output)
        next_steps_prompt = "\n Think a moment in the root cause of the fail."
        next_steps_prompt += "\n If the fail is due to a missing or failing base code or a bad implementation of it, you have to refactor it."
        next_steps_prompt += "\n If the fail is due to a wrong test implementation, fix it."
        print(prompt_init + next_steps_prompt + re_run_prompt)
        sys.exit(1)
    else:
        print("\n[UNIT TEST RESULT] SUCCESS: All unit tests passed and coverage is sufficient.\n")
        print(output)
    

@task
def functional_test(ctx: Context) -> None:
    """Run functional tests using pytest-bdd. Try to run the features in ./features/ folder."""
    run("clear")
    # Ensure .cov directory exists for coverage files
    if not os.path.exists(".cov"):
        os.makedirs(".cov")
    print("Running functional tests...")
    if not os.path.exists("./features/steps"):
        run("mkdir ./features/steps")

    try:
        behave_cmd = (
            f"source {env_path} && "
            "behave features/ -f json.pretty -o behave-report.json -f pretty "
        )
        console_response = run(
            behave_cmd,
            pty=True,
            warn=True,
            hide=True  # Hide output to capture it explicitly
        )
        print("Behave command output:")
        print(console_response.stdout)
        print("Behave command errors:")
        print(console_response.stderr)
    except Exception as e:
        print("Error running functional tests:", str(e))
        return

    #Rune result report load from behave-report.json file in the project root
    behave_report_path = os.path.join(project_folder, "behave-report.json")
    total_undefined = 0
    total_errors = 0
    total_failures = 0
    if os.path.exists(behave_report_path) and os.path.getsize(behave_report_path) > 0:
        with open(behave_report_path, "r") as f:
            try:
                behave_report = json.load(f)
                for feature in behave_report:
                    for element in feature.get("elements", []):
                        for step in element.get("steps", []):
                            if "result" in step:
                                if step["result"].get("status") == "error":
                                    total_errors += 1
                                if step["result"].get("status") == "undefined":
                                    total_undefined += 1
                                if step["result"].get("status") == "failed":
                                    total_failures += 1
            except json.JSONDecodeError:
                print("Warning: behave-report.json is not valid JSON.")

    next_steps_prompt = ""
    if total_undefined > 0:
        next_steps_prompt = "\n Try to create the glue code in the ./features/steps folder to the missing steps."
        next_steps_prompt += "\n Take in account that external services must be mocked using FastAPI."
        next_steps_prompt += "\n The functional test must load the full appliction before start, and turn it down at the end."
        next_steps_prompt += "\n Try to keep a organized structure of files and folders into the ./features/steps folder."
        next_steps_prompt += "\n If you found similar or equivalents sentences but not equals, you can use the same glue code, if they reprecent the same condigions puting more tan on given, when or then decorator."
        next_steps_prompt += "\n The http features, must be tested with real http request to the loaded sistem."
        next_steps_prompt += "\n The terminal interface features, must be tested with stdout stream."
        next_steps_prompt += "\n The web interface features, must be tested with web drive."
        next_steps_prompt += "\n Don't use steps place holders, build the real tests implementation."
        next_steps_prompt += "\n Remember KISS, DDD, and SOLID principles."
    elif total_errors > 0:
        next_steps_prompt = "\n Think a moment in the root cause of the error."
        next_steps_prompt += "\n If the root cause of the error is no clear, add debuggin logs."
        next_steps_prompt += "\n If the error is due to a too long execution, add a timeout break to the posible failing test."
        next_steps_prompt += "\n If the error is due to missing imports, add them taking in accout they must be at the very begining of the file."
        next_steps_prompt += "\n If the error is due to the identations, fix it."
        next_steps_prompt += "\n Remember KISS principle."
    elif total_failures > 0:
        next_steps_prompt = "\n Think a moment in the root caus of the fail."
        next_steps_prompt += "\n If the fail is due to a missing external service, mock it using FastAPI."
        next_steps_prompt += "\n If the fail is due to a missing or failing base code implementation, implement it taking in account DDD, Clean Architecture and Ports and Adapters."
        next_steps_prompt += "\n If the fail is due to a wrong test implementation, fix it."
    
    
    if not console_response.ok:
        next_steps_prompt += "\n Remove any deprecated code."
        next_steps_prompt += "\n Refactor all lint and type error."
        next_steps_prompt += "\n To remove obsolet files run the 'rm' command."
        next_steps_prompt += "\n When you finish the implementation run the 'invoke build' command to validate."
        next_steps_prompt += "\n After run the 'invoke build', if still beeing errors, keep looping until fix all of them."
        print(prompt_init + next_steps_prompt)
        sys.exit(1)

@task
def arch_test(ctx: Context) -> None:
    """Run architecture tests."""
    run("clear")
    # Use a separate pytest config for architecture tests (no coverage threshold)
    console_response = ctx.run(f"source {env_path} && pytest -c pytest.arch.ini -n auto --maxfail=1 --durations=2 --timeout=10 tests/arch_tests", pty=True, warn=True, hide=True)

    print(console_response.stdout)
    if not console_response.ok:
        next_steps_prompt = "\n Start making an conseptual a theorical DDD, clean architecture and ports and adapters sumary of the errors showed by the tests."
        next_steps_prompt += "\n Review the architecture errors for the easier issue to refactor."
        next_steps_prompt += "\n Remove any deprecated code."
        next_steps_prompt += "\n Make the refactor."
        next_steps_prompt += "\n Check that all the imports now point to the new packages and files."
        next_steps_prompt += "\n Refactor all lint and type error."
        next_steps_prompt += "\n When you finish the implementation run the 'invoke build' command to validate."
        next_steps_prompt += "\n After run the 'invoke build', if still beeing errors, keep looping until fix all of them."

        print(prompt_init + next_steps_prompt)
        sys.exit(1)

@task
def check_lint(ctx: Context) -> None:
    """Check code linting with flake8."""
    run("clear")
    print("Checking code linting with flake8...")
    lint_cmd = f"source {env_path} && flake8 src tests"
    console_response = ctx.run(lint_cmd, pty=True, warn=True, hide=True)

    if not console_response.ok:
        print("\n[FLAKE8 RESULT] FAIL: Linting issues detected.\n")
        print(console_response.stdout)
        next_steps_prompt = "\n Review the linting errors above and fix all of them."
        next_steps_prompt += "\n Follow PEP 8 guidelines for Python code style."
        next_steps_prompt += "\n After fixing, re-run 'invoke build' to ensure all issues are resolved."
        next_steps_prompt += "\n After run the 'invoke build', if still beeing errors, keep looping until fix all of them."
        print(prompt_init + next_steps_prompt)
        sys.exit(1)

@task
def build(ctx: Context) -> None:
    """Build the project."""
    functional_test(ctx)
    arch_test(ctx)
    unit_test(ctx)
    check_lint(ctx)
    print("\n All test passed correctly, you just be sure that you don't forget to clean deprecated files now.")