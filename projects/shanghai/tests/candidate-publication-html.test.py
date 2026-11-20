"""Release checks must follow the same module and stylesheet declarations as the HTML page."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from check_candidate_publication import PageAssets


class PublicationHTMLTests(unittest.TestCase):
    def test_reordered_attributes_and_quoted_inline_import(self):
        page = PageAssets("""<LINK href='src/view.css?v=1&amp;theme=dark' media='all' REL='alternate Stylesheet'/>
            <script nonce="a" type='module'>
              import { showViewer } from './src/view.js?v=version';
              showViewer();
            </script>""")
        self.assertEqual(page.styles, ['src/view.css?v=1&theme=dark'])
        self.assertEqual(page.modules, ['src/view.js?v=version'])
        self.assertEqual(page.external_modules, [])

    def test_external_module_and_index_styles(self):
        page = PageAssets("""<link rel="stylesheet" href="./src/historical-view.css?v=one">
            <script src='./src/app.js?v=two' defer TYPE='MODULE'></script>
            <script type="module" src="src/other.js">import './src/ignored.js';</script>""")
        self.assertEqual(page.styles, ['src/historical-view.css?v=one'])
        self.assertEqual(page.modules, ['src/app.js?v=two', 'src/other.js'])
        self.assertEqual(page.external_modules, page.modules)

    def test_skip_non_executable_text_and_nonlocal_assets(self):
        page = PageAssets("""<!-- <link rel='stylesheet' href='src/comment.css'> -->
            <link rel='preload' href='src/unused.css'>
            <link rel='stylesheet' href='https://cdn.example/src/third-party.css'>
            <script type='importmap'>{"imports":{"x":"./src/ignored.js"}}</script>
            <script>import x from './src/classic.js';</script>
            <script type='module' src='//cdn.example/src/vendor.js'></script>
            <script type='module'>
              // import thing from './src/comment.js'
              const title = "from './src/string.js'";
              import x from './src/../outside.js';
            </script>
            <p>from './src/text.js'</p>""")
        self.assertEqual((page.styles, page.modules, page.external_modules), ([], [], []))


if __name__ == '__main__':
    unittest.main()
