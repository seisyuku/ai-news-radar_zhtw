import unittest

from scripts.update_news import to_zh_hant


class ZhHantTermProtectionTests(unittest.TestCase):
    """fix/zh-hant-term-protection-0721: to_zh_hant()'s s2twp phrase
    conversion mangled specific proper nouns/technical terms whose
    characters overlap with unrelated CS-terminology phrase substitutions
    (线程->執行緒, 字节->位元組, 参数->引數). See
    .claude-reports/2026-07-21-oos-triage-diagnosis.md section D for the
    original diagnosis."""

    def test_moore_threads_protected(self):
        self.assertEqual(to_zh_hant("摩尔线程"), "摩爾線程")

    def test_bytedance_full_name_protected_unconditionally(self):
        self.assertEqual(to_zh_hant("字节跳动"), "字節跳動")

    def test_model_parameter_count_protected_unconditionally(self):
        self.assertEqual(to_zh_hant("参数"), "參數")
        self.assertIn("110 億參數", to_zh_hant("110 亿参数塞进模型"))

    def test_bare_byte_without_context_stays_generic_cs_term(self):
        # Genuine "byte" (data unit) usage, no ByteDance/peer co-occurrence.
        self.assertEqual(to_zh_hant("这个文件是16字节"), "這個檔案是16位元組")
        self.assertEqual(to_zh_hant("字节收购某AI公司"), "位元組收購某AI公司")

    def test_bare_byte_with_product_context_protected(self):
        self.assertIn("字節", to_zh_hant("字节旗下Seedance模型发布"))
        self.assertIn("字節", to_zh_hant("豆包和字节的关系"))

    def test_bare_byte_with_peer_company_context_protected(self):
        for peer in ("腾讯", "阿里", "百度", "美团", "快手"):
            with self.subTest(peer=peer):
                self.assertIn("字節", to_zh_hant(f"{peer}和字节都在做AI"))

    def test_mixed_script_boundary_does_not_suppress_latin_context_match(self):
        # Regression guard: an ASCII context term (Seedance/Doubao) directly
        # adjacent to CJK characters (no space) must still be detected -
        # \w/\b boundaries would incorrectly fail here since Python's
        # Unicode regex treats CJK ideographs as word characters too.
        self.assertIn("字節", to_zh_hant("字节旗下Seedance模型發布"))

    def test_unrelated_thread_and_parameter_usage_still_converts_normally(self):
        # Bare CS terms with no proper-noun collision still get the normal
        # Taiwan-idiom conversion.
        self.assertEqual(to_zh_hant("线程"), "執行緒")

    def test_existing_idempotency_and_overrides_unaffected(self):
        self.assertEqual(to_zh_hant("质量很好"), "品質很好")
        self.assertEqual(to_zh_hant("类型错误"), "類型錯誤")
        self.assertEqual(to_zh_hant("演算法"), "演算法")

    def test_unrelated_brand_names_unaffected(self):
        self.assertEqual(to_zh_hant("智谱"), "智譜")
        self.assertEqual(to_zh_hant("华为"), "華為")
        self.assertEqual(to_zh_hant("英伟达"), "英偉達")
        self.assertEqual(to_zh_hant("寒武纪"), "寒武紀")
        self.assertEqual(to_zh_hant("中芯国际"), "中芯國際")


if __name__ == "__main__":
    unittest.main()
