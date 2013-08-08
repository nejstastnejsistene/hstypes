hstypes
=======

Haskell types for Python.

## Function Composition

```python
from hs import *

@Composable
def square(x):
    return x * x

square_twice = square . square

print(square(3))
# 9
print(square_twice(3))
# 81
```

## Curried Functions

```python
@Curried
def mult(x, y):
    return x * y

double = mult(2)
double_and_square_twice = square_twice . double

print(double(3))
# 6
print(double_and_square_twice(3))
# 1296
```

## Pattern Matching

For function definitions using argument annotations.

This still needs some improvement, but it works for now.

```python
@PatternMatched
def fact(n:0): return 1
@PatternMatched
def fact(n:1): return 1
@PatternMatched
def fact(n): return n * fact(n - 1)

print(fact(0))
# 1
print(fact(1))
# 1
print(fact(5))
# 120
```
