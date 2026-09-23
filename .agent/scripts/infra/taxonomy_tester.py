import unittest
import os
import sys

# Add scripts root to path
scripts_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if scripts_root not in sys.path:
    sys.path.append(scripts_root)

from infra.taxonomy import TaxonomyEngine


class TaxonomyTester(unittest.TestCase):
    def setUp(self):
        self.engine = TaxonomyEngine()

    def test_canonicalize_domain(self):
        # Empty values
        self.assertEqual(self.engine.canonicalize_domain(""), "")
        self.assertEqual(self.engine.canonicalize_domain(None), "")
        self.assertEqual(self.engine.canonicalize_domain("   "), "")

        # Full match
        self.assertEqual(
            self.engine.canonicalize_domain("機器學習 (Machine Learning)"),
            "機器學習 (Machine Learning)"
        )

        # Bare match
        self.assertEqual(
            self.engine.canonicalize_domain("機器學習"),
            "機器學習 (Machine Learning)"
        )
        self.assertEqual(
            self.engine.canonicalize_domain("AI 代理人"),
            "AI 代理人 (AI Agent)"
        )

        # Non-AI Engineering Domains
        self.assertEqual(
            self.engine.canonicalize_domain("軟體工程與規格 (Software Engineering & Specifications)"),
            "軟體工程與規格 (Software Engineering & Specifications)"
        )
        self.assertEqual(
            self.engine.canonicalize_domain("軟體工程與規格"),
            "軟體工程與規格 (Software Engineering & Specifications)"
        )
        self.assertEqual(
            self.engine.canonicalize_domain("軟體工程"),
            "軟體工程與規格 (Software Engineering & Specifications)"
        )
        self.assertEqual(
            self.engine.canonicalize_domain("系統工程與研發治理"),
            "系統工程與研發治理 (Systems Governance & Operations)"
        )
        self.assertEqual(
            self.engine.canonicalize_domain("研發治理"),
            "系統工程與研發治理 (Systems Governance & Operations)"
        )

        # Invalid domain
        self.assertIsNone(self.engine.canonicalize_domain("AI 治理"))
        self.assertIsNone(self.engine.canonicalize_domain("NotACategory"))

    def test_verify_domain_declaration_valid(self):
        ml_text = "本文討論神經網路架構下的損失函數與梯度下降。"
        res = self.engine.verify_domain_declaration("機器學習", ml_text)
        self.assertTrue(res["valid"])
        self.assertEqual(res["canonical"], "機器學習 (Machine Learning)")
        self.assertIsNone(res["error"])
        self.assertIsNone(res["warning"])

        se_text = "本文分析規格驅動開發中的形式規格、差量規格與架構邊界。"
        res_se = self.engine.verify_domain_declaration("軟體工程與規格", se_text)
        self.assertTrue(res_se["valid"])
        self.assertEqual(res_se["canonical"], "軟體工程與規格 (Software Engineering & Specifications)")
        self.assertIsNone(res_se["error"])

        sys_text = "本文以排隊理論與利特爾法則分析研發流程中的在製品與交付週期瓶頸。"
        res_sys = self.engine.verify_domain_declaration("系統工程與研發治理", sys_text)
        self.assertTrue(res_sys["valid"])
        self.assertEqual(res_sys["canonical"], "系統工程與研發治理 (Systems Governance & Operations)")
        self.assertIsNone(res_sys["error"])

    def test_verify_domain_declaration_invalid_category(self):
        res = self.engine.verify_domain_declaration("AI 治理", "隨意內容")
        self.assertFalse(res["valid"])
        self.assertIsNone(res["canonical"])
        self.assertIn("not registered in taxonomy.json", res["error"])

    def test_verify_domain_declaration_suppresses_weak_noise(self):
        # Queuing theory text with single generic keyword "量化"
        queuing_text = "本文討論利用率敏感度，以及在製品流動指標的量化問題。"
        res = self.engine.verify_domain_declaration("", queuing_text)
        self.assertTrue(res["valid"])
        self.assertEqual(res["canonical"], "")
        self.assertIsNone(res["error"])
        # Single hit noise is correctly suppressed, no warning
        self.assertIsNone(res["warning"])

    def test_keyword_obeys_lexicon_boundaries(self):
        # A keyword that is a term follows the term's not_within and the post's
        # term_exclude, the same rule anchoring and tags use.
        lx = self.engine._boundaries()
        kw = next((k for k, v in lx.not_within.items()
                   if any(k in kws for kws in self.engine.data["ai_taxonomy"]["detection_keywords"].values())),
                  None)
        if kw is None:
            self.skipTest("no detection keyword with a not_within boundary")
        shadow = lx.not_within[kw][0]
        self.assertIsNone(self.engine.classify_domain(f"本文只談{shadow}。"))
        self.assertIsNotNone(self.engine.classify_domain(f"本文談{kw}。"))
        self.assertIsNone(self.engine.classify_domain(f"本文談{kw}。", {lx.keys[kw]}))

    def test_verify_domain_declaration_warns_on_omission(self):
        strong_ml_text = "神經網路中的反向傳播與梯度下降決定了經驗風險最小化下的泛化表現。"
        res = self.engine.verify_domain_declaration("", strong_ml_text)
        self.assertTrue(res["valid"])
        self.assertEqual(res["canonical"], "")
        self.assertIsNotNone(res["warning"])
        self.assertIn("strong evidence", res["warning"])


if __name__ == "__main__":
    unittest.main()

