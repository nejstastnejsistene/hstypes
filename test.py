from hs import *

if __name__ == '__main__':

    @Composable
    def square(x):
        return x * x

    square_twice = square . square

    print(square)
    print(square(3))
    print(square_twice)
    print(square_twice(3))
