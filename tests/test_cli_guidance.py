import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Guidance(unittest.TestCase):
    def cli(self, *args):
        return subprocess.run([sys.executable, '-m', 'cnlookthrough', *map(str, args)], cwd=ROOT, capture_output=True)

    def test_json_stdout_unchanged_even_with_explicit_human_guidance(self):
        plain = self.cli(ROOT / 'examples/demo.json')
        guided = self.cli(ROOT / 'examples/demo.json', '--human')
        self.assertEqual(plain.returncode, 0)
        self.assertEqual(plain.stdout, guided.stdout)
        self.assertEqual(plain.stderr, b'')
        self.assertAlmostEqual(json.loads(guided.stdout)['unknownExposure'], .16)
        self.assertIn('教学样本', guided.stderr.decode('utf-8'))

    def test_saved_report_and_existing_output_guidance_keep_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / '中文报告.html'
            args = (ROOT / 'examples/demo.json', '--format', 'html', '--out', out)
            first = self.cli(*args)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(first.stdout, b'')
            self.assertIn(str(out.resolve()), first.stderr.decode('utf-8'))
            self.assertIn('打开报告', first.stderr.decode('utf-8'))
            before = hashlib.sha256(out.read_bytes()).hexdigest()
            repeat = self.cli(*args)
            self.assertEqual(repeat.returncode, 2)
            self.assertIn('新的文件名', repeat.stderr.decode('utf-8'))
            self.assertEqual(before, hashlib.sha256(out.read_bytes()).hexdigest())

    def test_invalid_input_and_missing_file_do_not_echo_private_material(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'absent.json'
            source = Path(tmp) / 'private-secret.json'
            source.write_text('{"private-secret":', encoding='utf-8')
            invalid = self.cli(source, '--out', out)
            self.assertEqual(invalid.returncode, 2)
            self.assertIn('核对输入', invalid.stderr.decode('utf-8'))
            self.assertNotIn('private-secret', invalid.stderr.decode('utf-8'))
            self.assertFalse(out.exists())
            missing = self.cli(Path(tmp) / 'private-secret-missing.json')
            self.assertEqual(missing.returncode, 2)
            self.assertNotIn('private-secret', missing.stderr.decode('utf-8'))
            self.assertIn('核对本地文件路径', missing.stderr.decode('utf-8'))

    def test_optional_pdf_missing_has_exact_extra_and_no_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'result.json'
            args = [sys.executable, '-S', '-m', 'cnlookthrough.report_cli', str(Path(tmp) / 'private.pdf'),
                    '--report-date', '2025-12-31', '--published-at', '2026-03-27',
                    '--source-url', 'https://www.foresightfund.com/example.pdf',
                    '--net-assets', '100', '--equity-value', '70', '--out', str(out)]
            result = subprocess.run(args, cwd=ROOT, capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('python -m pip install ".[pdf]"', result.stderr.decode('utf-8'))
            self.assertNotIn('private.pdf', result.stderr.decode('utf-8'))
            self.assertEqual(result.stdout, b'')
            self.assertFalse(out.exists())
