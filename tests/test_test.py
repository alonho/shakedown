from .utils import (
    TestCase,
    CustomException,
    )
import itertools
import shakedown

class TestTest(TestCase):
    """
    Test the :class:`Test` class, which is the quickest way to create test classes in Shakedown
    """
    def test_test_class(self):
        events = []
        class Test(shakedown.Test):
            def before(self):
                events.append("before")
            def after(self):
                events.append("after")
            def test_1(self):
                events.append("test_1")
            def test_2(self):
                events.append("test_2")
        tests = list(Test.generate_tests())
        for test in tests:
            self.assertIsInstance(test, Test)
        self.assertEquals(len(tests), 2)
        tests.sort(key=lambda test: test._test_method_name)
        for test in tests:
            test.run()
        self.assertEquals(events, ["before", "test_1", "after", "before", "test_2", "after"])
    def test_before_failures(self):
        "Check that exceptions during before() prevent after() from happening"
        events = []
        class Test(shakedown.Test):
            def before(self):
                raise CustomException()
            def test(self):
                events.append("test")
            def after(self):
                events.append("after")
        [test] = Test.generate_tests()
        with self.assertRaises(CustomException):
            test.run()
        self.assertEquals(events, [])
    def test_after_gets_called(self):
        "If before() is successful, after() always gets called"
        events = []
        class Test(shakedown.Test):
            def before(self):
                events.append("before")
            def test_1(self):
                events.append("test")
                raise CustomException(1)
            def after(self):
                events.append("after")
        [test] = Test.generate_tests()
        with self.assertRaises(CustomException):
            test.run()
        self.assertEquals(events, ["before", "test", "after"])

class AbstractTestTest(TestCase):
    def test_abstract_tests(self):
        @shakedown.abstract_test_class
        class Abstract(shakedown.Test):
            def test1(self):
                pass
            def test2(self):
                pass
            def test3(self):
                pass
        self.assertEquals(list(Abstract.generate_tests()), [])
        class Derived(Abstract):
            pass
        self.assertEquals(len(list(Derived.generate_tests())), 3)

class TestParametersTest(TestCase):
    def test_parameters(self):
        variations = []
        a_values = [1, 2]
        b_values = [3, 4]
        c_values = [5, 6]
        d_values = [7, 8]
        class Parameterized(shakedown.Test):
            @shakedown.parameters.iterate(a=a_values)
            def before(self, a):
                variations.append([a])
            @shakedown.parameters.iterate(b=b_values, c=c_values)
            def test(self, b, c):
                variations[-1].extend([b, c])
            @shakedown.parameters.iterate(d=d_values)
            def after(self, d):
                variations[-1].append(d)
        for test in Parameterized.generate_tests():
            test.run()
        self.assertEquals(
            set(tuple(x) for x in variations),
            set(itertools.product(
                a_values,
                b_values,
                c_values,
                d_values
            )))
