================
class-namespaces
================

.. image:: https://travis-ci.org/mwchase/class-namespaces.svg?branch=master
    :target: https://travis-ci.org/mwchase/class-namespaces

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
