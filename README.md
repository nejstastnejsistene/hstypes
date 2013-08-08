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

print(square)
# <function square at 0x7f7d9531b160>
print(square(3))
# 9
print(square_twice)
# <function square.square at 0x7f7d9531b0d8>
print(square_twice(3))
# 81
```
