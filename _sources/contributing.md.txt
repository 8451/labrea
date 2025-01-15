# Contributing

If you would like to add new functionality or fix a bug, we welcome contributions. All change requests should start with
an [issue on the repo](https://github.com/8451/labrea/issues/new/choose). If you would like to develop the
solution yourself, us the following flow:

1. Read the [style guide](#style-guide) below
2. Tag @8451/cobra-owners in the issue and request to be assigned the issue
   - If this is your first time contributing, ask to be granted write access to the repo
3. Create a new branch based off of [develop](https://github.com/8451/labrea/tree/develop)
   - Give your branch a name starting with `feature/`, `bug/` or `misc/`
4. Clone the repo in your favorite IDE, check out your new branch, and add your changes
5. Run the tests to ensure nothing breaks
   - `pip install -e .[test]`
   - `pytest`
6. Push the changes on your branch to the repo, and open a Pull Request where the base branch is `develop`
   - Request a review from @8451/cobra-owners

## Style Guide

### Pre-Commit
The repo has [pre-commit](https://pre-commit.com/) configured to enforce much (but not all) of the style guide 
automatically. When developing locally, please perform the one-time setup using `pip install pre-commit` followed by 
`pre-commit install` before making any commits.

### PEP 8
We try to follow [PEP 8](https://peps.python.org/pep-0008/) wherever possible. Feel free to familiarize yourself
with it, but most IDEs will automatically help you. Alternatively, you can use a code formatter like
[black](https://pypi.org/project/black/) to format your code for you.

### Imports
Imports should take place at the top of the file and be broken into 4 sections, each section with a single empty line between
them. The sections are:
1. Standard library imports (i.e. typing, regex, math)
2. 3rd-party library imports (i.e. numpy, pandas)
3. Relative imports (importing other modules from the `labrea` package)

For sections 1-3, prefer using the fully-qualified namespace over an unqualified import (`import json` over
`from json import load`). An exception to this rule is imports from the typing library (`from typing import List`).

When importing another module from `labrea`, write it like `from . import core`.

Under no circumstances should `from module import *` be used.

### Typing
All function definitions should be fully type-hinted (arguments and return value). Where applicable, use
generic types from the `typing` library like `List[str]` vs `list`. If a function does not return anything, mark the
return type as `None`.

### Naming
Prefer long, descriptive function names over short abbreviated names. For example, `load_config` is preferred over
`ld_cfg`.

Function and variable names should be lowercase with underscores separating words (`my_function`). Class names should be
camel case (`MyClass`). Constants should be all uppercase with underscores separating words (`MY_CONSTANT`).

Any function, variable, or constant that is not intended to be used outside of the module it is defined in should be
prefixed with an underscore (`_my_private_function`).

### Documentation
All public-facing functions should be documented using docstrings in the
[Numpy Style](https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard).

### Functional Programming
We strongly prefer Functional Programming over Object-Oriented programming. OOP is used specifically to store
configuration data in an object for later use. Regardless of paradigm, there is a preference for stateless programming
and avoiding in-place data mutation where possible. For example, when combining two lists, prefer `list_a + list_b`
over `list_a.extend(list_b)`.
