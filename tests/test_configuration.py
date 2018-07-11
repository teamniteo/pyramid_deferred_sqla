from pyramid.testing import testConfig

def test_imports():
    import pyramid_deferred_sqla

def test_stock_config():
    with testConfig() as config:
        config.include('pyramid_deferred_sqla')
