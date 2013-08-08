import functools
import inspect
import sys


def compose(f, g):
    '''The composition of two functions.'''
    func = lambda *args, **kwargs: f(g(*args, **kwargs))
    func.__name__ = '{0.__name__}.{1.__name__}'.format(f, g)
    return func


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
