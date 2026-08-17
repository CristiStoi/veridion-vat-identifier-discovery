import csv
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.sampling import sample_companies


class SamplingTests(unittest.TestCase):
    def test_sampling_filters_and_output_columns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            input_path = tmp_path / "input.csv"
            output_path = tmp_path / "output.csv"

            rows = [
                {
                    "CompanyName": "A Ltd",
                    "CompanyNumber": "0001",
                    "RegAddress.AddressLine1": "Line 1",
                    "RegAddress.PostTown": "Town",
                    "RegAddress.PostCode": "AA1 1AA",
                    "CompanyCategory": "Private",
                    "CompanyStatus": "Active",
                    "IncorporationDate": "2020-01-01",
                    "Accounts.AccountCategory": "SMALL",
                    "SICCode.SicText_1": "Retail",
                    "URI": "uri-a",
                },
                {
                    "CompanyName": "Dormant Ltd",
                    "CompanyNumber": "0002",
                    "RegAddress.AddressLine1": "Line 2",
                    "RegAddress.PostTown": "Town",
                    "RegAddress.PostCode": "AA1 1AB",
                    "CompanyCategory": "Private",
                    "CompanyStatus": "Active",
                    "IncorporationDate": "2020-01-01",
                    "Accounts.AccountCategory": "DORMANT",
                    "SICCode.SicText_1": "Retail",
                    "URI": "uri-b",
                },
                {
                    "CompanyName": "Inactive Ltd",
                    "CompanyNumber": "0003",
                    "RegAddress.AddressLine1": "Line 3",
                    "RegAddress.PostTown": "Town",
                    "RegAddress.PostCode": "AA1 1AC",
                    "CompanyCategory": "Private",
                    "CompanyStatus": "Dissolved",
                    "IncorporationDate": "2020-01-01",
                    "Accounts.AccountCategory": "SMALL",
                    "SICCode.SicText_1": "Retail",
                    "URI": "uri-c",
                },
            ]

            with input_path.open("w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)

            sample_companies(str(input_path), str(output_path), sample_size=5, random_seed=42, chunk_size=2)

            output = pd.read_csv(output_path, dtype=str)
            self.assertEqual(len(output), 1)
            self.assertEqual(output.loc[0, "company_name"], "A Ltd")
            self.assertEqual(output.loc[0, "sample_seed"], "42")
            self.assertIn("source_chunk", output.columns)


if __name__ == "__main__":
    unittest.main()
