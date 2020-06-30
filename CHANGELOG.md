## Changelog

0.3.0 (2020-06-29)
------------------

* Remove deprecated pytest_runner.
  [am-on]

* Change license to MIT.
  [am-on]

* Add circleci config.
  [suryasr007]

* Export type annotations for users.
  [mandarvaze]

* Use py3.7 as default, drop support for py34 and py35.
  [zupo]
  
* Check that DB is upgraded to latest Alembic version.
  [zupo]
  
* Format code with black.
  [zupo]
  
* Connection reuse.
  [dz0ny]
  
* Close the connection and return it to the pool.
  [dz0ny]
  
* Properly handle returning connection to the pool.
  [domenkozar]
  
* Properly handle read only mode.
  [domenkozar]
  
* Support pshell scripts.
  [zupo]
  
* Model.__init__ = _declarative_constructor.
  [domenkozar]


0.2.0 (2018-07-13)
------------------

* Fix discovery of Model.
  [domenkozar]

* Store engine in settings
  [domenkozar]


0.1.0 (2018-07-12)
------------------

* Initial release. 
  [zupo, domenkozar]
