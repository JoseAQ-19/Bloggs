import os
import tempfile
import unittest
import shutil
from purge_and_clean import run_purge_and_clean
import audit_v2

class TestPurgeAndClean(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)
        os.makedirs(os.path.join(self.test_dir, 'content', 'en'))
        os.makedirs(os.path.join(self.test_dir, 'content', 'es'))

        # Good Article (No Scripts, Good SEO/EEAT)
        self.good_md = os.path.join(self.test_dir, 'content', 'en', 'good.md')
        with open(self.good_md, 'w', encoding='utf-8') as f:
            f.write("---\nlanguage: 'en'\ntranslationKey: '123'\n---\nValid article with list\n- one\n- two\nAnd solid content.")

        # Article with Script
        self.script_md = os.path.join(self.test_dir, 'content', 'en', 'script.md')
        with open(self.script_md, 'w', encoding='utf-8') as f:
            f.write("---\nlanguage: 'en'\ntranslationKey: '456'\n---\nValid article with list\n- one\n- two\n<script type=\"application/ld+json\">{\"@context\": \"http://schema.org\"}</script>\nAnd solid content.")

        # Bad Article (No TranslationKey, H1 in body, Spanglish)
        self.bad_md = os.path.join(self.test_dir, 'content', 'es', 'bad.md')
        with open(self.bad_md, 'w', encoding='utf-8') as f:
            f.write("---\nlanguage: 'es'\n---\n# Bad Heading\nel articulo the and with for es malisimo y tiene spanglish.\n```json\n")

    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.test_dir)

    def test_purge_and_clean(self):
        run_purge_and_clean()
        
        # Good article should survive
        self.assertTrue(os.path.exists(self.good_md))
        
        # Script article should survive but without scripts
        self.assertTrue(os.path.exists(self.script_md))
        with open(self.script_md, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertNotIn('<script', content)
            
        # Bad article should be deleted
        self.assertFalse(os.path.exists(self.bad_md))

if __name__ == '__main__':
    unittest.main()
