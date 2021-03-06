import shakedown
from shakedown.exceptions import (
    SkipTest,
    TestFailed,
    )
from tempfile import mkdtemp
import itertools
import os
import six # pylint: disable=F0401
import uuid

_current_test_generator = None

class TestGenerator(object):
    """
    A utility for generating test classes and making sure they actually
    run
    """
    __test__ = False # for nose

    def __init__(self):
        super(TestGenerator, self).__init__()
        self._expected = set()
        self._uuid_base = str(uuid.uuid1())
        self._uuid_generator = ("{0}/{1}".format(self._uuid_base, i) for i in itertools.count(1))
        self._run_callbacks = {}
        global _current_test_generator
        _current_test_generator = self
    def get_expected_test_ids(self):
        return list(self._expected)
    def generate_tests(self, num_tests=3):
        return [self.generate_test() for _ in six.moves.xrange(num_tests)]
    def generate_test(self):
        test_id = next(self._uuid_generator)
        self._expected.add(test_id)
        return TestPromise(test_id)
    def write_test_directory(self, structure, root=None):
        if root is None:
            root = mkdtemp()
        if not os.path.isdir(root):
            os.makedirs(root)
        for filename, item in six.iteritems(structure):
            path = os.path.join(root, filename)
            if isinstance(item, dict):
                self.write_test_directory(item, path)
            else:
                contents = self._get_test_item_contents(item)
                with open(path, "w") as f:
                    f.write(contents)
        return root

    def _get_test_item_contents(self, items):
        if isinstance(items, str):
            return items
        if not isinstance(items, list):
            items = [items]
        return "\n".join(itertools.chain(
            [_TESTFILE_HEADER],
            (item.generate_test_factory_source() for item in items)
        ))

    def notify_run(self, test_id, test):
        self._expected.remove(test_id)
        callback_list = self._run_callbacks.get(test_id, [])
        while callback_list:
            callback_list.pop(0)(test)
    def assert_all_run(self):
        assert not self._expected, "These tests have not run: {0}".format(", ".join(self._expected))
    ### Functions to manage test execution
    def make_test_raise_exception(self, testpromise):
        self.add_test_run_callback(testpromise, self.do_raise_exception)
    def make_test_fail(self, testpromise):
        self.add_test_run_callback(testpromise, self.do_fail)
    def make_test_skip(self, testpromise):
        self.add_test_run_callback(testpromise, self.do_skip)
    def add_test_run_callback(self, testpromise, handler):
        self._run_callbacks.setdefault(self._get_test_promise_id(testpromise), []).append(handler)
    def _get_test_promise_id(self, p):
        if isinstance(p, shakedown.RunnableTest):
            p = p.__test_generator_promise__
        if isinstance(p, str):
            return p # test id
        return p.id
    ### handlers
    def do_raise_exception(self, _):
        raise OSError("Sample exception")
    def do_fail(self, _):
        raise TestFailed("Test failed")
    def do_skip(self, _):
        raise SkipTest("Reason here")

class TestPromise(object):
    __test__ = False # for nose
    def __init__(self, test_promise_id):
        super(TestPromise, self).__init__()
        self.id = test_promise_id
        self._test_class_name = "T" + self.id.replace("-", "_").replace("/", "_")
    def generate_test_factory_source(self):
        return _TEST_FACTORY_SOURCE_TEMPLATE.format(**self._get_template_context())
    def generate_test_source(self):
        return _TEST_SOURCE_TEMPLATE.format(**self._get_template_context())
    def _get_template_context(self):
        return {
            "test_generator_module_name" : __name__,
            "bucket_test_id" : self.id,
            "test_class_name" : self._test_class_name,
        }
    def generate_test(self):
        d = {"RunnableTest" : shakedown.RunnableTest}
        exec(self.generate_test_source(), d)
        returned = d[self._test_class_name]()
        returned.__test_generator_promise__ = self
        return returned

_TESTFILE_HEADER = """
from shakedown import RunnableTest, RunnableTestFactory
"""

_TEST_SOURCE_TEMPLATE = r"""
class {test_class_name}(RunnableTest):
    def run(self):
        from {test_generator_module_name} import _current_test_generator
        _current_test_generator.notify_run({bucket_test_id!r}, self)
"""

_TEST_FACTORY_SOURCE_TEMPLATE = """
class F{{test_class_name}}(RunnableTestFactory):
    @classmethod
    def generate_tests(cls):
{0}
        return [{{test_class_name}}()]
""".format("\n".join((" " * 8 + line) for line in _TEST_SOURCE_TEMPLATE.splitlines()))
