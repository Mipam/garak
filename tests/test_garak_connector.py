import unittest
from unittest.mock import patch, MagicMock
import queue

from garak_gui import garak_connector

class TestGarakConnector(unittest.TestCase):

    def test_parse_plugin_list_probes(self):
        output = """
probes:
  dan.Dan_11_0          | DAN 11.0
  promptinject.Hijack   | promptmap hijack
"""
        plugins = garak_connector._parse_plugin_list(output, "probes")
        self.assertEqual(plugins, ["dan.Dan_11_0", "promptinject.Hijack"])

    def test_parse_plugin_list_generators(self):
        output = """
generators:
openai
huggingface
"""
        plugins = garak_connector._parse_plugin_list(output, "generators")
        self.assertEqual(plugins, ["openai", "huggingface"])

    @patch("subprocess.check_output")
    def test_get_plugins(self, mock_check_output):
        mock_check_output.return_value = "probes:\n  test.Test"
        plugins = garak_connector.get_plugins("probes")
        mock_check_output.assert_called_with(["python", "-m", "garak", "--list_probes"], text=True)
        self.assertEqual(plugins, ["test.Test"])

    @patch("subprocess.Popen")
    def test_run_garak_command(self, mock_popen):
        q = queue.Queue()
        garak_connector.run_garak_command(["--probes", "all"], q)
        mock_popen.assert_called_with(
            ["python", "-m", "garak", "--probes", "all"],
            stdout=unittest.mock.ANY,
            stderr=unittest.mock.ANY,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

    @patch("subprocess.Popen")
    def test_start_interactive_process(self, mock_popen):
        q = queue.Queue()
        garak_connector.start_interactive_process(q)
        mock_popen.assert_called_with(
            ["python", "-m", "garak", "--interactive"],
            stdin=unittest.mock.ANY,
            stdout=unittest.mock.ANY,
            stderr=unittest.mock.ANY,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

if __name__ == "__main__":
    unittest.main()
