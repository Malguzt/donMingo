def print_next_steps_header():
    print("\n================ NEXT STEPS ================\n")


def print_next_steps_footer():
    print(" When you finish the fixs, check the lint of the refactored files.")
    print(" Remove any deprecated code.")
    print(" When you finish all that, re run the checks running 'invoke build' command.")
    print(" After run the 'invoke build' command, keep fixing until all tests and checks pass.\n")


def print_testing_footer():
    print(" Tests must respect FIRST, CORRECT, AAAT, DAMP.")
    print(" Use mocks and stubs to isolate the unit under test.")
    print_next_steps_footer()


def print_next_steps_prompt(prompt: str):
    print_next_steps_header()
    print(prompt)
    print_next_steps_footer()


def print_troubleshooting(tool_name: str):
    print("Troubleshooting suggestions:")
    print("- Check Python version compatibility.")
    print(f"- Verify {tool_name} and its dependencies are installed in the environment.")
    print("- Inspect config files for errors.")
    print("- Run the command manually for more detailed output.")
    print("- Check file permissions and access rights.")
    print_next_steps_footer()
