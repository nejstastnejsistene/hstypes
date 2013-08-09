import functools
import inspect
import re
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


class Lexer(object):

    upper_id = re.compile(r'([A-Z]\w*)\s*')
    lower_id = re.compile(r'([a-z]\w*)\s*')
    arrow = re.compile(r'(->)\s*')
    l_paren = re.compile(r'(\()\s*')
    r_paren = re.compile(r'(\))\s*')
    ws = re.compile(r'\s*')

    UPPER_ID = 'UPPER_ID'
    LOWER_ID = 'LOWER_ID'
    ARROW = 'ARROW'
    L_PAREN = 'L_PAREN'
    R_PAREN = 'R_PAREN'
    EOF = 'EOF'

    lexemes = [
        (upper_id, UPPER_ID),
        (lower_id, LOWER_ID),
        (arrow, ARROW),
        (l_paren, L_PAREN),
        (r_paren, R_PAREN),
        ]

    def __init__(self, text):
        self.text = text
        self.tok = ''
        self.ttype = None
        m = self.ws.match(self.text)
        if m is not None:
            self.text = self.text[m.end(0):]

    def __iter__(self):
        while self.ttype != self.EOF:
            yield next(self)

    def __next__(self):
        if not self.text:
            self.tok = ''
            self.ttype = self.EOF
            return self.ttype, self.tok
        else:
            for lex in Lexer.lexemes:
                m = lex[0].match(self.text)
                if m is not None:
                    self.tok = m.group(1)
                    self.ttype = lex[1]
                    self.text = self.text[m.end(0):]
                    return self.ttype, self.tok
        raise Exception('invalid text: {!r}'.format(self.text))


class Composition(object):
    def __init__(self, args):
        self.args = args
    def __repr__(self):
        return ' '.join(map(str, self.args))


class Lambda(object):
    def __init__(self, t1, t2):
        self.t1 = t1
        self.t2 = t2
    def __repr__(self, parens=False):
        if isinstance(self.t2, Lambda):
            t2 = self.t2.__repr__(True)
        else:
            t2 = repr(self.t2)
        fmt = '{0} -> {1}'
        if parens:
            fmt = '(' + fmt + ')'
        return fmt.format(self.t1, t2)


def parse(text):
    '''Parse a type annotation.

       expr   := simple | lambda | L_PAREN expr R_PAREN
       simple := id | id simple
       id     := UPPER_ID | LOWER_ID
       lambda := expr ARROW expr
    '''
    return _parse(Lexer(text))


def _parse(tokens):
    result, left = [], []
    for ttype, token in tokens:
        if ttype in (Lexer.UPPER_ID, Lexer.LOWER_ID):
            # Build a simple type
            result.append(token)
        else:
            # Condense result when finished building it.
            if result and left or ttype == Lexer.ARROW:
                if isinstance(result, list):
                    result = Composition(result)
            # Left and right are finish, so make lambda.
            if left and result:
                result, left = Lambda(left, result), []
            # Left is finished, start building right side.
            if result and ttype == Lexer.ARROW:
                left, result = result, []
            # Left paren encountered, parse until right paren.
            elif not result and ttype == Lexer.L_PAREN:
                # Build a list of tokens until the next right paren.
                for tok in tokens:
                    if tok[0] == Lexer.EOF:
                        raise Exception
                    elif tok[0] == Lexer.R_PAREN:
                        # Put an EOF inplace of the right paren and parse.
                        result.append((Lexer.EOF, ''))
                        result = _parse(result)
                        break
                    else:
                        result.append(tok)
            elif ttype != Lexer.EOF:
                raise Exception
    return result
