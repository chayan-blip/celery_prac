from producer.decorator import dec

@dec
def add(a,b):
    return a + b

@dec
def mul(a,b):
    return a*b

class TestDecorator:
    def test_add(self):
        # add 2 and 3 check if 5 is recieved
        assert add(2,3) == 5
        # add 5 and 8 check if 13 is recieved
        assert add(5,8) == 13

    def test_mul(self):
        # multiply 2 and 3 check if 6 is recieved
        assert mul(2,3) == 6
        # multiply 5 and 4 check if 20 is recieved
        assert mul(5,8) == 40
