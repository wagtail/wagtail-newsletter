# Contributing to Wagtail Newsletter

## Install

To make changes to this project, first clone this repository:

```sh
git clone https://github.com/wagtail/wagtail-newsletter.git
cd wagtail-newsletter
```

With your preferred virtualenv activated, install testing dependencies:

### Using pip

```sh
python -m pip install --upgrade 'pip>=21.3'
python -m pip install -e '.[testing,ci,mailchimp,mrml]' -U
```

### Using flit

```sh
python -m pip install flit
flit install
```

## pre-commit

Note that this project uses [pre-commit](https://github.com/pre-commit/pre-commit).
It is included in the project testing requirements. To set up locally:

```shell
# go to the project directory
$ cd wagtail-newsletter
# initialize pre-commit
$ pre-commit install

# Optional, run all checks once for this, then the checks will run only on the changed files
$ git ls-files --others --cached --exclude-standard | xargs pre-commit run --files
```

## How to run tests

Now you can run tests as shown below:

```sh
tox
```

or, you can run them for a specific environment `tox -e python3.12-django5.0-wagtail6.1` or specific test
`tox -e python3.12-django5.0-wagtail6.1-sqlite wagtail-newsletter.tests.test_file.TestClass.test_method`

To run the test app interactively, use `tox -e interactive`, visit `http://127.0.0.1:8020/admin/` and log in with `admin`/`changeme`.

## How to build the documentation

The documentation source lives under `docs/`. It's built with [Sphinx](https://www.sphinx-doc.org/).
You can start a development server that will auto-build and refresh the page in the browser:

```sh
pip install sphinx-autobuild
sphinx-autobuild docs docs/_build/html
```
