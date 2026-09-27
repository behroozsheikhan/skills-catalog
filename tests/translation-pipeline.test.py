import importlib.util
from pathlib import Path
import unittest
spec = importlib.util.spec_from_file_location('bulk', Path(__file__).resolve().parents[1]/'scripts/bulk_translate.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
class TranslationPipeline(unittest.TestCase):
    def test_round_trip(self):
        text='Use React and Next.js via CLI (op), "improve this copy", `npm run build` or…'
        masked,tokens=m.protect(text)
        self.assertIn('React',tokens); self.assertIn('Next.js',tokens)
        self.assertIn('CLI',tokens); self.assertIn('"improve this copy"',tokens)
        self.assertIn('`npm run build`',tokens); self.assertIn('…',tokens)
        translated='استفاده از '+ ' '.join(f'[[T{i}]]' for i in range(len(tokens)))
        self.assertTrue(m.restore(translated,tokens,text).endswith('…'))
    def test_persian_word_order_can_move_ellipsis(self):
        self.assertEqual(m.restore('برای [[T0]] استفاده کنید', ['…'], 'Use for…'), 'برای … استفاده کنید')
    def test_provider_bracket_formatting_is_normalized(self):
        self.assertEqual(m.restore('دستور [[T0] جدید', ['IR'], 'New IR instruction'), 'دستور IR جدید')
    def test_single_quoted_commands_are_preserved(self):
        masked,tokens=m.protect("Use when asked 'improve this copy' or 'check my site…")
        self.assertIn("'improve this copy'", tokens)
        self.assertIn("'check my site…", tokens)
    def test_missing_placeholder_rejected(self):
        with self.assertRaises(ValueError):m.restore('استفاده', ['CLI'],'Use the CLI')
    def test_duplicated_placeholder_rejected(self):
        with self.assertRaises(ValueError):m.restore('[[T0]] [[T0]]', ['CLI'],'Use the CLI')
    def test_fallback_changes_invalidate_translation(self):
        a={'what':'','use_when':'When needed','description':'First'}
        b={**a,'description':'Second'}
        self.assertNotEqual(m.source_hash(a),m.source_hash(b))
        a['what']=b['what']='Nonempty';self.assertEqual(m.source_hash(a),m.source_hash(b))
if __name__ == '__main__':unittest.main()
