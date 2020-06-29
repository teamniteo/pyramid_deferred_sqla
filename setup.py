"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from setuptools import setup, find_packages
from os import path
from io import open

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


version = "0.3.0"

setup(
    name="pyramid_deferred_sqla",
    version=version,
    description="Pyramid integration with SQLAlchemy",
    long_description=long_description,
    license="MIT",
    long_description_content_type="text/markdown",
    url="https://github.com/niteoweb/pyramid_deferred_sqla",
    author="Niteoweb",
    author_email="info@niteo.co",
    classifiers=[  # Optional
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
    keywords="pyramid sqlalchemy",
    packages=find_packages(exclude=["contrib", "docs", "tests"]),
    include_package_data=True,
    install_requires=[
        "pyramid",
        "pyramid_tm",
        "pyramid_retry",
        "sqlalchemy",
        "alembic",
        "venusian",
        "zope.sqlalchemy",
    ],
    extras_require={"dev": ["coverage", "pytest", "tox"], "lint": ["black"]},
)
