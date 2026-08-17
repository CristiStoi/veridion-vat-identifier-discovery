import argparse
import re
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup


HEADERS = {"User-Agent": "Mozilla/5.0"}
PAGE_KEYWORDS = ["terms", "privacy", "legal", "contact", "about"]
VAT_NUMBER_PATTERN = re.compile(
    r"\bVAT\s*(?:(?:registration|reg\.?)\s*)?"
    r"(?:number|no\.?)\s*[:\-]?\s*"
    r"((?:GB\s*)?\d(?:[\s.-]*\d){8}(?:(?:[\s.-]*\d){3})?)\b",
    re.IGNORECASE,
)


def download_page(url, timeout=10):
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
    except requests.RequestException:
        return None, url

    if response.status_code != 200:
        return None, response.url

    return BeautifulSoup(response.text, "html.parser"), response.url


def get_domain(url):
    domain = urlparse(url).netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def find_relevant_links(soup, homepage_url, keywords=None, page_limit=5):
    keywords = keywords or PAGE_KEYWORDS
    homepage_domain = get_domain(homepage_url)
    relevant_links = []

    for link in soup.find_all("a"):
        href = link.get("href")
        if not href:
            continue

        link_text = link.get_text(" ", strip=True).lower()
        href_lower = href.lower()

        if not any(keyword in link_text or keyword in href_lower for keyword in keywords):
            continue

        full_url = urljoin(homepage_url, href)
        if get_domain(full_url) == homepage_domain and full_url not in relevant_links:
            relevant_links.append(full_url)

    return relevant_links[:page_limit]


def normalize_vat_candidate(candidate_raw):
    candidate = re.sub(r"\D", "", candidate_raw or "")
    return candidate if len(candidate) in {9, 12} else None


def extract_candidates_from_text(page_text):
    candidates = []

    for candidate_match in VAT_NUMBER_PATTERN.finditer(page_text):
        vat_candidate = normalize_vat_candidate(candidate_match.group(1))
        if not vat_candidate:
            continue

        context_start = max(0, candidate_match.start() - 100)
        context_end = min(len(page_text), candidate_match.end() + 150)
        context = page_text[context_start:context_end]
        candidates.append((vat_candidate, context))

    return candidates


def extract_from_company_website(company, downloader=download_page):
    homepage_soup, final_homepage_url = downloader(company["website_url"])
    if homepage_soup is None:
        return "FETCH_FAILED", []

    pages = [(final_homepage_url, homepage_soup)]
    for page_url in find_relevant_links(homepage_soup, final_homepage_url):
        page_soup, final_page_url = downloader(page_url)
        if page_soup is not None:
            pages.append((final_page_url, page_soup))

    found = []
    seen_candidates = set()
    vat_keyword_found = False

    for page_url, page_soup in pages:
        page_text = page_soup.get_text(" ", strip=True)

        if re.search(r"\bVAT\b", page_text, re.IGNORECASE):
            vat_keyword_found = True

        for vat_candidate, context in extract_candidates_from_text(page_text):
            if vat_candidate in seen_candidates:
                continue

            seen_candidates.add(vat_candidate)
            found.append(
                {
                    "company_number": company["company_number"],
                    "company_name": company["company_name"],
                    "website_match": company["website_match"],
                    "source_page": page_url,
                    "vat_candidate": vat_candidate,
                    "context": context,
                }
            )

    if found:
        return "VAT_CANDIDATE_FOUND", found
    if vat_keyword_found:
        return "VAT_KEYWORD_ONLY", []
    return "VAT_NOT_FOUND", []


def run_extraction(discovery_log_path="data/discovery_log.csv", output_path="data/vat_candidates.csv"):
    discovery_log = pd.read_csv(discovery_log_path, dtype=str)
    websites = discovery_log[discovery_log["website_url"].notna()].copy()

    vat_candidates = []
    fetch_failed_count = 0
    candidate_company_count = 0
    keyword_only_count = 0
    vat_not_found_count = 0

    for _, company in websites.iterrows():
        status, company_candidates = extract_from_company_website(company)

        if status == "FETCH_FAILED":
            fetch_failed_count += 1
        elif status == "VAT_CANDIDATE_FOUND":
            candidate_company_count += 1
        elif status == "VAT_KEYWORD_ONLY":
            keyword_only_count += 1
        else:
            vat_not_found_count += 1

        vat_candidates.extend(company_candidates)

        print(f"{company['company_name']}: {status} ({len(company_candidates)} candidates)")

    candidate_columns = [
        "company_number",
        "company_name",
        "website_match",
        "source_page",
        "vat_candidate",
        "context",
    ]

    candidates_dataframe = pd.DataFrame(vat_candidates, columns=candidate_columns)
    candidates_dataframe.to_csv(output_path, index=False)

    print("\nExtraction summary:")
    print(f"Websites attempted: {len(websites)}")
    print(f"Fetch failed: {fetch_failed_count}")
    print(f"Companies with candidates: {candidate_company_count}")
    print(f"VAT keyword only: {keyword_only_count}")
    print(f"VAT not found: {vat_not_found_count}")
    print(f"Unique candidates: {len(candidates_dataframe)}")
    print(f"\nSaved {output_path}")


def parse_args():
    parser = argparse.ArgumentParser(description="Extract VAT candidates from discovered company websites.")
    parser.add_argument("--discovery-log", default="data/discovery_log.csv", help="Path to discovery log CSV")
    parser.add_argument("--output", default="data/vat_candidates.csv", help="Path to output CSV")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_extraction(args.discovery_log, args.output)
