import os,subprocess,sys,unittest
from pathlib import Path
class Tests(unittest.TestCase):
 def test_ascii_host_console_still_returns_utf8(self):
  root=Path(__file__).resolve().parents[1];env=dict(os.environ,PYTHONIOENCODING='ascii')
  p=subprocess.run([sys.executable,'-m','cnlookthrough',str(root/'examples/demo.json'),'--format','markdown'],capture_output=True,env=env)
  self.assertEqual(p.returncode,0,p.stderr.decode('utf-8'))
  self.assertIn('# ',p.stdout.decode('utf-8'))
if __name__=='__main__':unittest.main()
