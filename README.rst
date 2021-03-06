================
class-namespaces
================

.. image:: http://unmaintained.tech/badge.svg
  :target: http://unmaintained.tech
  :alt: No Maintenance Intended

.. image:: https://readthedocs.org/projects/class-namespaces/badge/?version=latest
    :target: http://class-namespaces.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
.. image:: https://travis-ci.org/mwchase/class-namespaces.svg?branch=master
    :target: https://travis-ci.org/mwchase/class-namespaces
.. image:: https://coveralls.io/repos/github/mwchase/class-namespaces/badge.svg?branch=master
    :target: https://coveralls.io/github/mwchase/class-namespaces?branch=master
.. image:: https://api.codacy.com/project/badge/Grade/f73ed5e3849c4049b8c9e3f17f6589da
    :target: https://www.codacy.com/app/max-chase/class-namespaces?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=mwchase/class-namespaces&amp;utm_campaign=Badge_Grade
.. image:: https://codecov.io/gh/mwchase/class-namespaces/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/mwchase/class-namespaces
.. image:: https://landscape.io/github/mwchase/class-namespaces/master/landscape.svg?style=flat
    :target: https://landscape.io/github/mwchase/class-namespaces/master
    :alt: Code Health
.. image:: https://scrutinizer-ci.com/g/mwchase/class-namespaces/badges/quality-score.png?b=master
    :target: https://scrutinizer-ci.com/g/mwchase/class-namespaces/?branch=master
    :alt: Scrutinizer Code Quality
.. image:: https://scrutinizer-ci.com/g/mwchase/class-namespaces/badges/coverage.png?b=master
    :target: https://scrutinizer-ci.com/g/mwchase/class-namespaces/?branch=master
    :alt: Code Coverage
.. image:: https://scrutinizer-ci.com/g/mwchase/class-namespaces/badges/build.png?b=master
    :target: https://scrutinizer-ci.com/g/mwchase/class-namespaces/build-status/master
    :alt: Build Status
.. image:: https://codeclimate.com/github/mwchase/class-namespaces/badges/gpa.svg
   :target: https://codeclimate.com/github/mwchase/class-namespaces
   :alt: Code Climate
.. image:: https://codeclimate.com/github/mwchase/class-namespaces/badges/coverage.svg
   :target: https://codeclimate.com/github/mwchase/class-namespaces/coverage
   :alt: Test Coverage
.. image:: https://codeclimate.com/github/mwchase/class-namespaces/badges/issue_count.svg
   :target: https://codeclimate.com/github/mwchase/class-namespaces
   :alt: Issue Count

Well-behaved class namespacing in Python. Inspired by https://erezsh.wordpress.com/2008/06/27/namespaces-lets-do-more-of-those-python-hackery/

Basic Usage
-----------

Example code::

    import class_namespaces as cn
    
    class MyCls(cn.Namespaceable):
    
        var = 1
    
        with cn.Namespace() as my_ns:
            var = 2
    
    assert MyCls.var == 1
    assert MyCls.my_ns.var == 2

Other things that work:

* Descriptors (methods, classmethods, staticmethods, properties, custom descriptors)
* super()
* Prepopulating Namespaces. The constructor takes the same arguments as a dict.
* abstractmethods. See the compat module.

Things that don't work:

* Various ways of putting a Namespace in a Namespace that I didn't see an obvious way to handle. In particular...

  * There is no way to put an established namespace directly into another namespace.
* Some pytest constructs behave weirdly inside the class definitions. Hopefully, this doesn't matter to anyone not writing tests for the package.
* No way to have instance Namespaces on non-hashable types, or subclasses of some built-in types, particularly tuple. Try using data descriptors instead.

Things that might work:

* New namespace features in Python 3.6. Current testing is spotty.
* Combining with other metaclasses. Unfortunately, the current setup is somewhat brittle. It may be necessary to experiment with the ordering of bases.
