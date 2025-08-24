import pytest
from unittest.mock import patch, MagicMock
import subprocess

from garak_gui.garak_connector import _parse_plugin_list, get_plugins

def test_parse_plugin_list_probes():
    output = """
probes:
  probe1:
    desc: a test probe
  probe2:
    desc: another test probe
"""
    plugins = _parse_plugin_list(output, "probes")
    assert plugins == ["probe1", "probe2"]

def test_parse_plugin_list_generators():
    output = """
generators:
  generator1
  generator2
"""
    plugins = _parse_plugin_list(output, "generators")
    assert plugins == ["generator1", "generator2"]

def test_parse_plugin_list_empty():
    output = """
probes:
"""
    plugins = _parse_plugin_list(output, "probes")
    assert plugins == []

@patch('subprocess.check_output')
def test_get_plugins_success(mock_check_output):
    mock_check_output.return_value = "probes:\n  probe1:\n"
    plugins, err = get_plugins("probes")
    assert plugins == ["probe1"]
    assert err is None

@patch('subprocess.check_output', side_effect=FileNotFoundError)
def test_get_plugins_file_not_found(mock_check_output):
    plugins, err = get_plugins("probes")
    assert plugins == []
    assert "not found" in err

@patch('subprocess.check_output')
def test_get_plugins_called_process_error(mock_check_output):
    mock_check_output.side_effect = subprocess.CalledProcessError(1, "cmd", output="error message")
    plugins, err = get_plugins("probes")
    assert plugins == []
    assert "error message" in err
