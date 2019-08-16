# pyramid_deferred_sqla

[![Build Status](https://travis-ci.com/niteoweb/pyramid_deferred_sqla.svg?branch=master)](https://travis-ci.com/niteoweb/pyramid_deferred_sqla)
[![PyPi](https://img.shields.io/pypi/v/pyramid_deferred_sqla.svg)](https://pypi.org/project/pyramid_deferred_sqla/)

Opinionated SQLAlchemy + Pyramid integration with deferred configuration in mind.

## Getting started

To start with, configure db module and configure SQLAlchemy engine and Alembic:

```python
config.include("pyramid_deferred_sqla")
config.sqlalchemy_engine()
config.alembic_config("mypackage:migrations")
```

Both are going to use `database.url` from the registry settings to
configure the URL of the engine.

The configuration also:

a) Sets up `request.db` attribute defaulting to SQLAlchemy Session instance.

b) Sets up Alembic with [recommended naming conventions](http://alembic.zzzcomputing.com/en/latest/naming.html).

c) Exposes `listens_for` pyramid decorator that defers `sqlalchemy.event.listen`

d) Sets up "read only" serialization for request session for GET/OPTIONS/HEAD requests

This behavior can be overridden by passing `read_only` attribute to the @view_config:

```python
@view_config(read_only=True)
def myview(request):
    ...
```

e) SQLA Session is attached to `pyramid_tm` transaction manager and uses `pyramid_retry`.

f) Exposes `Model` that ties abstract class with `id` column as uuid primary key and sane __repr__ implementation

g) Defers automagic Base metaclass logic to take place within pyramid Configurator

```python
from pyramid_deferred_sqla import Base, model_config, Model

@model_config(Base)
class User(Model):
    __tablename__ = 'user'

    ...
```

which is registered by calling `config.scan('.model')`.

## Example implementation

A full-blown example app, with tests, based on this package is available at https://github.com/niteoweb/pyramid-realworld-example-app.

## Running tests

    $ tox

## Related projects

- [websauna](https://github.com/websauna/websauna/tree/master/websauna/system/model)
  has some neat ideas that were incorporated.
- [warehouse](https://github.com/pypa/warehouse/blob/master/warehouse/db.py)
  también
- [pyramid-cookiecutter-alchemy](https://github.com/Pylons/pyramid-cookiecutter-alchemy)
