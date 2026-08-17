import unittest

from bs4 import BeautifulSoup

from src.extraction import (
    extract_candidates_from_text,
    find_relevant_links,
    normalize_vat_candidate,
)


class ExtractionTests(unittest.TestCase):
    def test_normalize_vat_candidate(self):
        self.assertEqual(normalize_vat_candidate("GB 123 456 789"), "123456789")
        self.assertEqual(normalize_vat_candidate("123 456 789 000"), "123456789000")
        self.assertIsNone(normalize_vat_candidate("12345"))

    def test_extract_candidates_requires_vat_label(self):
        text = "VAT number: GB 123 456 789 and ref 123456789"
        candidates = extract_candidates_from_text(text)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0][0], "123456789")

    def test_find_relevant_links_internal_and_deduplicated(self):
        html = """
        <a href='/privacy'>Privacy</a>
        <a href='https://example.com/contact'>Contact</a>
        <a href='https://other.com/privacy'>Other Privacy</a>
        <a href='/privacy'>Privacy Duplicate</a>
        """
        soup = BeautifulSoup(html, "html.parser")
        links = find_relevant_links(soup, "https://example.com")
        self.assertEqual(links, ["https://example.com/privacy", "https://example.com/contact"])


if __name__ == "__main__":
    unittest.main()
