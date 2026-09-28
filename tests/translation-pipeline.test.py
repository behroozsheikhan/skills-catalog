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
    def test_fragmentation_does_not_remove_source_content(self):
        text='Use NVIDIA CUDA GPU API SDK CLI tools for CPU and TPU, then run "improve this copy" with React; keep Next.js…'
        rebuilt=''.join(part+separator for part,separator in m.fragments(text))
        self.assertEqual(' '.join(rebuilt.split()), ' '.join(text.split()))
        for part,separator in m.fragments(text):
            self.assertLessEqual(len(m.protect(part)[1]), 6)
    def test_untranslated_chinese_prose_is_rejected(self):
        self.assertFalse(m.valid_cached('创建和编辑文档', '创建和编辑文档'))
        self.assertTrue(m.valid_cached('创建和编辑文档', 'ساخت و ویرایش سند'))
    def test_stored_machine_drafts_preserve_terms_and_translate_prose(self):
        import json
        root=Path(__file__).resolve().parents[1]
        rows={r['author']+'/'+r['name']:r for r in map(json.loads,(root/'skills-catalog/skills-index-flat.jsonl').read_text().splitlines())}
        for key,entry in json.loads((root/'data/fa.json').read_text()).items():
            if entry.get('method') != 'machine':continue
            row=rows[key]
            for field in ('what','use_when','description'):
                if field=='description' and row.get('what'):continue
                self.assertTrue(m.valid_cached(row.get(field,''),entry.get(field,'')), key+'/'+field)
    def test_fallback_changes_invalidate_translation(self):
        a={'what':'','use_when':'When needed','description':'First'}
        b={**a,'description':'Second'}
        self.assertNotEqual(m.source_hash(a),m.source_hash(b))
        a['what']=b['what']='Nonempty';self.assertEqual(m.source_hash(a),m.source_hash(b))
if __name__ == '__main__':unittest.main()
