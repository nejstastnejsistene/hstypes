from hs import *

if __name__ == '__main__':

    @Composable
    def square(x):
        return x * x

    square_twice = square . square

    print(square(3))
    print(square_twice(3))

    @Curried
    def mult(x, y):
        return x * y

    double = mult(2)
    double_and_square_twice = square_twice . double

    print(double(3))
    print(double_and_square_twice(3))
