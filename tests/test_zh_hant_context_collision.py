import unittest

from scripts.update_news import to_zh_hant


class ZhHantContextCollisionTests(unittest.TestCase):
    """fix/zh-hant-context-collision-0721: five s2twp word-choice bugs found
    by the 2026-07-21 full-corpus substitution audit
    (.claude-reports/2026-07-21-s2twp-substitution-audit.md) - correct in
    software contexts but wrong for this site's actual (non-programming)
    reader-facing content. See
    .claude-reports/2026-07-21-zh-hant-context-collision.md for the fix and
    full-corpus backtest."""

    # --- Group 1: unconditional protection ---------------------------------

    def test_loop_unconditionally_protected(self):
        self.assertIn("循環神經", to_zh_hant("循环神经网络"))

    def test_pullback_unconditionally_protected(self):
        self.assertIn("回調", to_zh_hant("股价回调"))

    def test_image_unconditionally_protected(self):
        out = to_zh_hant("快速图像与视频")
        self.assertIn("圖像", out)
        self.assertNotIn("影象", out)

    # --- Group 2: bare "字节" gate, extended ---------------------------------

    def test_bytedance_with_bat_context_protected(self):
        self.assertIn("字節", to_zh_hant("BAT抱团阻击字节"))

    def test_bytedance_with_announcement_verb_context_protected(self):
        self.assertIn("字節", to_zh_hant("字节发现Agent的Scaling Law"))
        self.assertIn("字節", to_zh_hant("字节跳动发布Seed Audio 1.0"))
        self.assertIn("字節", to_zh_hant("字节旗下产品宣布重大更新"))

    def test_bare_byte_still_converts_normally_without_context(self):
        # Regression guard: genuine byte-quantity usage must not be caught
        # by the new BAT/verb co-occurrence terms.
        self.assertIn("位元組", to_zh_hant("这个文件是16字节"))
        self.assertIn("位元組", to_zh_hant("字节数组"))

    # --- Group 3: reverse-gated "对象" ---------------------------------------

    def test_object_defaults_to_person_sense(self):
        out = to_zh_hant("续约对象")
        self.assertIn("對象", out)
        self.assertNotIn("物件", out)

    def test_object_with_dating_context_still_defaults(self):
        out = to_zh_hant("八村垒并不是湖人的优先续约对象")
        self.assertIn("對象", out)
        self.assertNotIn("物件", out)

    def test_object_with_storage_context_allows_s2twp_result(self):
        out = to_zh_hant("多云对象存储的统一桌面管理器")
        self.assertIn("物件", out)

    def test_object_with_database_context_allows_s2twp_result(self):
        self.assertIn("物件", to_zh_hant("对象数据库的设计与实现"))

    def test_object_with_bucket_context_allows_s2twp_result(self):
        self.assertIn("物件", to_zh_hant("S3 bucket 对象生命周期管理"))


if __name__ == "__main__":
    unittest.main()
