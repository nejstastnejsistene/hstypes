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
        self.arg_spec = spec = inspect.getfullargspec(func)
        if spec.varargs or spec.varkw or spec.defaults:
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

class PatternMismatch(Exception):
    pass

class PatternMatched(Curried):

    _functions = {}

    def __init__(self, func):
        Curried.__init__(self, func)
        name = func.__name__
        lst = self._functions.get(name, [])
        if lst and lst[0].nargs != self.nargs:
            raise TypeError('another function with this name already '
                            'exists with a different number or args.')
        self._functions[name] = lst + [self]

    def check_case(self, *args):
        args_dict = dict(zip(self.arg_spec.args, args))
        annotations = self.arg_spec.annotations
        for key in annotations:
            if args_dict[key] != annotations[key]:
                raise PatternMismatch
        return Curried.__call__(self, *args)

    def __call__(self, *args):
        for case in self._functions[self.func.__name__]:
            try:
                return case.check_case(*args)
            except PatternMismatch:
                pass
        raise PatternMismatch('no cases were matched')
