import unittest
from click.testing import CliRunner
from aetherdb.cli.main import cli
import os

def test_script_file():
    script = "test_query_script.sql"
    with open(script, "w") as f:
        f.write("SELECT 1;\n-- a comment\n\\help\n\\apm list\n")
    runner = CliRunner()
    r = runner.invoke(cli, ["shell", "-c", f"\\i {script}"])
    os.remove(script)
    assert "1" in r.output
    assert "Meta-Commands" in r.output
    assert "Installed Extensions" in r.output
    assert r.exit_code == 0 or r.exit_code is None

class TestCliShell(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
    def test_help_and_profiles(self):
        result = self.runner.invoke(cli, ['shell', '-c', '\\help'])
        self.assertIn("Meta-Commands", result.output)
        result = self.runner.invoke(cli, ['shell', '-c', '\\profiles'])
        self.assertIn("Available profiles", result.output)
    def test_set_and_saveprofile(self):
        result = self.runner.invoke(cli, ['shell', '-c', '\\set format json'])
        self.assertIn("output format now: json", result.output)
        result = self.runner.invoke(cli, ['shell', '-c', '\\saveprofile TESTCLI'])
        self.assertIn("Profile 'TESTCLI' saved", result.output)
    def test_apm_integration(self):
        result = self.runner.invoke(cli, ['shell', '-c', '\\apm list'])
        self.assertIn("Installed Extensions", result.output)
        result = self.runner.invoke(cli, ['shell', '-c', '\\apm install ext1'])
        self.assertIn("Installed ext1", result.output)
    def test_script(self):
        test_script_file()
if __name__ == "__main__":
    unittest.main()
