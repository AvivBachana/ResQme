# Shared CLI arguments and common paths.
# Keeps code comments in English only.
import argparse

def base_parser(desc: str):
    p = argparse.ArgumentParser(description=desc)
    p.add_argument("--raw", default="src/resqme/data/raw", help="Path to raw data")
    p.add_argument("--processed", default="src/resqme/data/processed", help="Path to processed data")
    p.add_argument("--outputs", default="outputs", help="Path to outputs root")
    return p
