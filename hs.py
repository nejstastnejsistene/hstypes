import functools
import inspect
import sys


def compose(f, g):
    '''The composition of two functions.
    
       The resulting class is the same as that of f.
    '''
    func = lambda *args, **kwargs: f(g(*args, **kwargs))
    func.__name__ = '{0.__name__}.{1.__name__}'.format(f, g)
    return f.__class__(func)


class Composable(object):
    '''A wrapper around functions to make them composable with dot syntax.
    
       This primarily overloads the dot operator to perform function
       composition by looking up the name in the calling frame's globals
       and composing it with this object.
    '''

    def __init__(self, func):
        self.func = func
        functools.update_wrapper(self, func)

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __getattr__(self, name):
        if hasattr(self.func, name):
            return getattr(self.func, name)
        global_vars = inspect.currentframe().f_back.f_globals
        return compose(self, global_vars[name])

    def __repr__(self):
        return repr(self.func)


class Curried(Composable):
    '''A function wrapper to make functions curried.

       This does not work with variable, keyword, or default arguments,
       nor with functions which are uninspectable, such as some built-in
       functions. Curried is a superclass of Composable, so all curried
       functions are also composable.
    '''

    def __init__(self, func, *args):
        self.func = func
        self.args = list(args)
        spec = inspect.getargspec(func)
        if spec.varargs or spec.keywords or spec.defaults:
            raise TypeError('currying only works with vanilla args')
        self.nargs = len(spec.args)

    def __call__(self, *args):
        args = self.args + list(args)
        if len(args) == self.nargs:
            return self.func(*args)
        if len(args) > self.nargs:
            mesg = 'expecting {0} args, got {1}'
            mesg = mesg.format(self.nargs, len(args))
            raise TypeError(mesg)
        else:
            # Return a curried function.
            return self.__class__(self.func, *args)

    def __repr__(self):
        # Rename the function temporarily to give a better
        # representation of a curried function.
        name = self.func.__name__
        self.func.__name__ += repr(tuple(self.args))
        ret = repr(self.func)
        self.func.__name__ = name
        return ret
