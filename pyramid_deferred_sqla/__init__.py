import functools

import alembic.config
import sqlalchemy
import venusian
import zope.sqlalchemy

from pyramid.interfaces import PHASE2_CONFIG
try:
    from pyramid.config.util import action_method
except ImportError:
    from pyramid.config.actions import action_method

from sqlalchemy import event, inspect
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative.base import _declarative_constructor
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import DetachedInstanceError

import deferred_sqla


__all__ = ["includeme", "Model", "Base", "listens_for"]

# Recommended naming convention used by Alembic, as various different database
# providers will autogenerate vastly different names making migrations more
# difficult. See: http://alembic.zzzcomputing.com/en/latest/naming.html
NAMING_CONVENTION = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = sqlalchemy.MetaData(naming_convention=NAMING_CONVENTION)
Base = declarative_base(metadata=metadata)


def make_repr(*attrs, _self=None):
    def _repr(self=None):
        if self is None and _self is not None:
            self = _self

        try:
            return "{}({})".format(
                self.__class__.__name__,
                ", ".join("{}={}".format(a, repr(getattr(self, a))) for a in attrs),
            )
        except DetachedInstanceError:
            return "{}(<detached>)".format(self.__class__.__name__)

    return _repr



# Create our session class here, this will stay stateless as we'll bind the
# engine to each new state we create instead of binding it to the session
# class.
Session = sessionmaker()


def listens_for(target, identifier, *args, **kwargs):
    """Deferred listens_for decorator that calls sqlalchemy.event.listen
    """
    def deco(wrapped):
        def callback(scanner, _name, wrapped):
            wrapped = functools.partial(wrapped, scanner.config)
            event.listen(target, identifier, wrapped, *args, **kwargs)

        venusian.attach(wrapped, callback)

        return wrapped

    return deco

@action_method
def register_sqla_models(config, *models):
    def register():
        deferred_sqla.register_sqla_models(config, *models)
    config.action(None, callable=register)
    

@action_method
def attach_sqla_models_to_base(config, base):
    """Dynamically add models registered using ``register_sqla_models`` to
    chosen SQLAlchemy Base class.

    More flexibility is gained by not inheriting from SQLAlchemy declarative
    base and instead plugging in models during the pyramid configuration time.

    Directly inheriting from SQLAlchemy Base class has non-undoable side
    effects.  All models automatically pollute SQLAlchemy namespace and may
    e.g. cause problems with conflicting table names. This also allows
    @declared_attr to access Pyramid registry.

    :param base: SQLAlchemy declarative Base for which model should belong to
    """
    def attach():
        deferred_sqla.attach_sqla_models_to_base(config, base)
        basereg = base._decl_class_registry
        for model in config._deferred_sqla_models:
            modelreg = model.__dict__.get('_decl_class_registry')
            if modelreg == basereg:
                discriminator = ('sqlalchemy-model', base, model)
                intr = config.introspectable(
                    'sqlalchemy models',
                    discriminator,
                    model.__name__,
                    'sqlalchemy model',
                )
                intr['base'] = base
                intr['class'] = model
                config.action(
                    discriminator,
                    callable=None,
                    introspectables=(intr,),
                )
    discriminator = ('attach-sqla-models-to-base', base)
    # make sure this happens after all models are registered
    config.action(discriminator, callable=attach, order=PHASE2_CONFIG)

@deferred_sqla.model_config
class Model(object):
    __abstract__ = True

    __init__ = _declarative_constructor

    def __repr__(self):
        inst = inspect(self)
        self.__repr__ = make_repr(
            *[c_attr.key for c_attr in inst.mapper.column_attrs], _self=self
        )
        return self.__repr__()

    id = sqlalchemy.Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sqlalchemy.text("gen_random_uuid()"),
    )

def _create_session(request):
    """On every request, we create a new session and attach it to
       the transaction (manager).
    """

    # Create a session from our connection
    session = Session(bind=request.registry.settings["sqlalchemy.engine"])

    # Now that we have a connection, we're going to go and set it to the
    # correct isolation level.
    if getattr(request, 'read_only', None):
        session.connection(execution_options={'isolation_level': 'SERIALIZABLE READ ONLY DEFERRABLE'})

    # Register only this particular session with zope.sqlalchemy
    zope.sqlalchemy.register(session, transaction_manager=request.tm)

    # Setup a callback that will ensure that everything is cleaned up at the
    # end of our connection.
    @request.add_finished_callback
    def cleanup(request):
        session.close()

    # Return our session now that it's created and registered
    return session


def readonly_view_deriver(view, info):
    def wrapper_view(context, request):
        if 'read_only' in info.options:
            request.read_only = info.options['read_only']
        else:
            request.read_only = request.method.lower in ("get", "options", "head")
        response = view(context, request)
        return response
    return wrapper_view

readonly_view_deriver.options = ('read_only',)


def _configure_alembic(config, package, db_url_key="sqlalchemy.url"):
    alembic_cfg = alembic.config.Config()
    # TODO: load from cfg
    alembic_cfg.set_main_option("script_location", package)
    alembic_cfg.set_main_option("url", config.registry.settings[db_url_key])
    return alembic_cfg


def _create_engine(config, db_url_key="sqlalchemy.url", **kw):
    engine = sqlalchemy.create_engine(
        config.registry.settings[db_url_key],
        **kw
    )
    Base.metadata.bind = engine
    config.registry.settings['sqlalchemy.engine'] = engine


def includeme(config):
    # Hook request lifecycle to a transaction and retry transient failures
    config.include('pyramid_tm')
    config.include('pyramid_retry')

    # Add a directive to get an alembic configuration.
    config.add_directive("alembic_config", _configure_alembic)

    # Create our SQLAlchemy Engine.
    config.add_directive("sqlalchemy_engine", _create_engine)

    config.add_directive(
        'register_sqla_models',
        register_sqla_models
    )
    config.add_directive(
        'attach_sqla_models_to_base',
        attach_sqla_models_to_base
    )

    # Register our request.db property
    config.add_request_method(_create_session, name="db", reify=True)

    # Add a route predicate to mark a route as read only.
    config.add_view_deriver(readonly_view_deriver)

    config.scan('.')
