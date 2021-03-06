from .utils import TestCase
from .utils import no_op
from .utils import NullFile
from .utils.test_generator import TestGenerator
from shakedown.frontend import shake_run
from shakedown import site
import os

class ShakeRunTest(TestCase):
    def setUp(self):
        super(ShakeRunTest, self).setUp()
        self.generator = TestGenerator()
        make_test = self.generator.generate_test
        self.forge.replace_with(site, "load", no_op)
        self.root_path = self.generator.write_test_directory(
            {
                "test_1.py" : make_test(),
                "dir_1" : {
                    "dir_2" : {
                        "test_2.py" : [make_test(), make_test()],
                    },
                    "test_3.py" : make_test(),
                    "regular_file.txt" : "some content here",
                    "other_regular_file" : "more contents",
                }
            }
        )
    def test_shake_run_directory_success(self):
        result = self._execute_shake_run([self.root_path])
        self.assertEquals(result, 0, "shake run did not return 0 on success")
    def test_shake_run_directory_failure(self):
        self._test__shake_run_directory_unsuccessful(self.generator.make_test_fail)
    def test_shake_run_directory_error(self):
        self._test__shake_run_directory_unsuccessful(self.generator.make_test_raise_exception)
    def _test__shake_run_directory_unsuccessful(self, fault):
        expected = self.generator.get_expected_test_ids()
        fault(expected[2])
        result = self._execute_shake_run([self.root_path])
        self.assertNotEquals(result, 0, "shake run unexpectedly returned 0 for failure")
    def test_shake_run_specific_file(self):
        for path in [
                "test_1.py",
                "dir_1/dir_2/test_2.py",
                "dir_1/test_3.py"
        ]:
            result = self._execute_shake_run([os.path.join(self.root_path, path)])
            self.assertEquals(result, 0, "shake run did not return successfully for {0}".format(path))
    def _execute_shake_run(self, argv):
        return shake_run.shake_run(argv, report_stream=NullFile())
    def tearDown(self):
        self.generator.assert_all_run()
        super(ShakeRunTest, self).tearDown()
