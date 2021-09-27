"""Setup script for intelino-trainlib-async."""

from setuptools import setup, find_namespace_packages


with open("README.md", encoding="utf-8") as f:
    text = f.read()
    # update relative image path to url for pypi
    img_ref = "[main-img]: ./"
    img_url = "[main-img]: https://raw.githubusercontent.com/intelino-code/intelino-trainlib-async-py/master/"
    long_description = text.replace(img_ref, img_url)


REQUIREMENTS = [
    "bleak",
    "Rx",
    "typing-extensions",
]

setup(
    name="intelino-trainlib-async",
    version="1.0.1",
    description="Asynchronous Python library (SDK) for interacting with the intelino smart train.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="intelino",
    author_email="developer@intelino.com",
    license="Intelino Public License",
    url="https://intelino.com",
    project_urls={
        "Documentation": "https://intelino-trainlib-async-py.readthedocs.io/",
        "Source Code": "https://github.com/intelino-code/intelino-trainlib-async-py",
        "Intelino Lab": "https://lab.intelino.com",
    },
    packages=find_namespace_packages(include=["intelino*"]),
    python_requires=">=3.7",
    classifiers=[
        "Framework :: AsyncIO",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "License :: Other/Proprietary License",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3 :: Only",
        "Typing :: Typed",
    ],
    install_requires=REQUIREMENTS,
)
