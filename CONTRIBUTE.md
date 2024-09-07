# How can I contribute?

You may contribute to the project by opening issues or pull requests in the project's repository.

## Opening an issue

Please always search for similar issues before opening one.

### Ask for a fix

When opening an issue for a fix, make sure to describe the problem with as much detail as possible. Indicate:

* What `rzip` version you are using
* What OS (Windows/Linux/Mac) you are using
* What error message you are seeing (if there is none, explicitely say so)
* How the problem occured:
  * What command was used
  * What files you were trying to use

### Ask for a feature/change

When opening an issue to ask for a fix/change, consider the following first:

* Motivate your change request:
  * Why is this change needed?
  * Why is this change relevant to the project?
* Be as specific as possible:
  * What value/result do you expect once the change is implemented?
  * What should trigger the use of the change (new command-line parameter, environment variables, ...)
  * How could the change be implemented (if you have an idea)? Do other projects already implement this?
* Changes/features should not affect defaults: archives must remain reproducible even after updating `rzip` to patch versions. Not doing so is a major change and such changes will be heavily scrutinized.

## Opening a pull request

When opening a pull request, please consider the following:

* Changes that break compatibility with existing python versions WILL NOT be merged. We aim to support all 3.X releases.
* Changes that add runtime dependencies that are not part of the standard library WILL NOT be merged.
* Indicate what your pull request implements (reference an existing issue if possible, else add the detailed information that an issue would have).
* Test your change locally (at least run `pylint` & `pytest`, even better if you run `act`) and indicate how you tested your changes in the description.
* Make sure that any relevant project documentation is up-to-date.

## Making changes to the codebase

We recomment the use of a virtual environment for development, as well as the use of [`act`](https://github.com/nektos/act) to run locally the tests that will be used as a baseline to validate your pull request.

### Create and use a venv

When first checking out the project, you may create a venv with the following command. You should only need to run this once:

```bash
python3 -m venv .venv
```

Once this is done, most IDEs will detect the venv and automatically work within it. If they do not, you may explicitely load it by running the `activate script` in the venv in your current shell:

```bash
. ./.venv/bin/activate
```

### Install dev dependencies

To install the project's dev dependencies, run pip from the project's directory:

```bash
pip install -r dev-requirements.txt
```

### Test changes

To test your changes, run `pylint` to check the formatting and `pytest` to ensure that all tests pass:

```
pylint src/rzip
pytest
```

### Install and use Act

Act allows you to run github workflows locally. It is not required but recommended if you intend to open a pull request.

To install Act, you will need to have a working installation of Docker/Podman and follow the [installation instructions](https://nektosact.com/installation/index.html) on their website. Downloading a prebuilt executable and adding it to the PATH is usually enough.

Once Act is installed, run the `build` job to test your changes:

```bash
act -j run_build
```

Note that Act runners will not test all OS, so there may still be lingering issues that will only be noticed once your code changes run on said environments
