================
class-namespaces
================

.. image:: https://travis-ci.org/mwchase/class-namespaces.svg?branch=master
    :target: https://travis-ci.org/mwchase/class-namespaces
.. image:: https://coveralls.io/repos/github/mwchase/class-namespaces/badge.svg?branch=master
    :target: https://coveralls.io/github/mwchase/class-namespaces?branch=master
.. image:: https://api.codacy.com/project/badge/Grade/f73ed5e3849c4049b8c9e3f17f6589da
    :target: https://www.codacy.com/app/max-chase/class-namespaces?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=mwchase/class-namespaces&amp;utm_campaign=Badge_Grade
.. image:: https://ci.appveyor.com/api/projects/status/ik5ci1icjmib9fi7?svg=true
    :target: https://ci.appveyor.com/project/mwchase/class-namespaces


Well-behaved class namespacing in Python. Inspired by https://erezsh.wordpress.com/2008/06/27/namespaces-lets-do-more-of-those-python-hackery/

Basic Usage
-----------

Example code::

    import class_namespaces as cn
    
    class MyCls(metaclass=cn.Namespaceable):
    
        var = 1
    
        with cn.Namespace() as my_ns:
            var = 2
    
    assert MyCls.var == 1
    assert MyCls.my_ns.var == 2

Other things that work:

* Descriptors (methods, classmethods, staticmethods, properties, custom descriptors)
* super()
* Prepopulating Namespaces. The constructor takes the same arguments as a dict.

Things that don't work:

* Combining with nearly any other metaclass.
* Various ways of putting a Namespace in a Namespace that I didn't see an obvious way to handle. In particular...

  * There is no way to put an established namespace directly into another namespace.

Things that might work:

* New namespace features in Python 3.6. Current testing is spotty.
