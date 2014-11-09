===========
pysyncthing
===========

pysyncthing is a pure python implementation of the syncthing protocol.

It's primary goal is to ensure that third-party implementation implementations
of syncthing are possible, and to help non-go programmers figure out how it
works ;).

It's implemented purely from the documentation and blackbox testing, not by
looking at the (GPL) code. Please don't send pull requests if they are based on
direct porting of the code.


Dev environment
===============

Install dev packages::

    sudo apt-get install libssl-dev libffi-dev

And python packages::

    virtualenv .
    source bin/activate
    pip install -r requirements.txt
