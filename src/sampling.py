import argparse

import numpy as np
import pandas as pd


COLUMNS_TO_KEEP = [
    "CompanyName",
    "CompanyNumber",
    "RegAddress.AddressLine1",
    "RegAddress.PostTown",
    "RegAddress.PostCode",
    "CompanyCategory",
    "CompanyStatus",
    "IncorporationDate",
    "Accounts.AccountCategory",
    "SICCode.SicText_1",
    "URI",
]


def sample_companies(
    csv_path="data/raw/BasicCompanyDataAsOneFile-2026-08-01.csv",
    output_path="data/sample_companies.csv",
    sample_size=50,
    random_seed=42,
    chunk_size=100000,
):
    chunks = pd.read_csv(
        csv_path,
        chunksize=chunk_size,
        dtype=str,
        usecols=COLUMNS_TO_KEEP,
        skipinitialspace=True,
    )

    rng = np.random.default_rng(random_seed)
    sample = pd.DataFrame()

    total_companies = 0
    total_eligible_companies = 0
    chunk_number = 0

    for chunk in chunks:
        chunk_number += 1
        total_companies += len(chunk)

        eligible_companies = chunk[
            (chunk["CompanyStatus"] == "Active")
            & (chunk["Accounts.AccountCategory"] != "DORMANT")
            & (chunk["CompanyName"].notna())
            & (chunk["CompanyNumber"].notna())
        ].copy()

        eligible_companies["source_chunk"] = chunk_number
        total_eligible_companies += len(eligible_companies)
        eligible_companies["_random_key"] = rng.random(len(eligible_companies))

        chunk_sample = eligible_companies.nsmallest(sample_size, "_random_key")
        sample = pd.concat([sample, chunk_sample], ignore_index=True)
        sample = sample.nsmallest(sample_size, "_random_key")

        if chunk_number % 10 == 0:
            print(f"Processed {chunk_number} chunks...")

    sample = sample.sort_values("_random_key").reset_index(drop=True)

    print("\nSampling completed.")
    print("Total companies processed:", total_companies)
    print("Total eligible companies:", total_eligible_companies)
    print("Final sample size:", len(sample))

    sample["sample_seed"] = random_seed
    sample = sample.drop(columns="_random_key")
    sample = sample.rename(
        columns={
            "CompanyName": "company_name",
            "CompanyNumber": "company_number",
            "RegAddress.AddressLine1": "address_line_1",
            "RegAddress.PostTown": "post_town",
            "RegAddress.PostCode": "postcode",
            "CompanyCategory": "company_category",
            "CompanyStatus": "company_status",
            "IncorporationDate": "incorporation_date",
            "Accounts.AccountCategory": "accounts_category",
            "SICCode.SicText_1": "sic_code_1",
            "URI": "companies_house_uri",
        }
    )

    sample.to_csv(output_path, index=False)
    print(f"Sample saved to: {output_path}")


def parse_args():
    parser = argparse.ArgumentParser(description="Sample active non-dormant UK companies from Companies House bulk CSV.")
    parser.add_argument("--input", default="data/raw/BasicCompanyDataAsOneFile-2026-08-01.csv", help="Path to raw Companies House CSV")
    parser.add_argument("--output", default="data/sample_companies.csv", help="Path to output sample CSV")
    parser.add_argument("--size", type=int, default=50, help="Sample size")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--chunk-size", type=int, default=100000, help="CSV chunk size")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    sample_companies(args.input, args.output, args.size, args.seed, args.chunk_size)
