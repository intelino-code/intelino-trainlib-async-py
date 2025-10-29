
# intelino-trainlib-async-py

[![Documentation Status](https://readthedocs.org/projects/intelino-trainlib-async-py/badge/?version=latest)](https://intelino-trainlib-async-py.readthedocs.io/en/latest/?badge=latest)
[![PyPI](https://img.shields.io/pypi/v/intelino-trainlib-async.svg)](https://pypi.org/project/intelino-trainlib-async/)
[![PyPI](https://img.shields.io/pypi/pyversions/intelino-trainlib-async.svg)](https://pypi.org/project/intelino-trainlib-async/)
[![PyPI - Downloads](https://img.shields.io/pypi/dw/intelino-trainlib-async.svg)](https://pypistats.org/packages/intelino-trainlib-async)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Asynchronous Python library (SDK) for interacting with the intelino smart train.

![intelino smart trains][main-img]


## Overview

Intelino Smart Train is an award-winning programmable robotic toy that is both fun and educational. Powered by innovative robotic tech, the smart train offers multiple programming modes suitable for users of different ages.

Learning is more meaningful and relatable when experimenting with and simulating real world problems. Younger kids use screen-free activities and tactile coding to operate the smart trains and make them run on schedule. And older users, students and makers use our advanced tools to build smart rail systems and experiment with autonomous driving, collision avoidance, route optimization, resource sharing and much more!

We offer both synchronous and asynchronous Python programming libraries for the intelino smart train. The `intelino-trainlib` is our synchronous Python library. It gives access to our full-featured API, enables event-based programming (through threads) and allows to interactively control one or multiple smart trains. This library is well suited for students and users that are new to Python or text-based programming, in general. And programmers with more advanced skills may prefer our asynchronous library `intelino-trainlib-async` which offers an extended list of API features, Rx-based reactive programming and superior performance.

## Installation

The asynchronous intelino trainlib is available on PyPi and can be installed with pip:

```
python3 -m pip install intelino-trainlib-async
```

## Scanning

```
python3 -m intelino.scan
```


## Local development:

```
git clone git://github.com/intelino-code/intelino-trainlib-async-py
cd intelino-trainlib-async-py

python3 -m venv .env
source .env/bin/activate
python3 -m pip install -r requirements.txt
python3 -m pip install -r requirements-dev.txt
python3 -m pip install -e .
```

To bump the version run e.g. `bump2version patch`.

[main-img]: ./docs/source/images/intelino-multi-train.jpg "intelino smart trains"
