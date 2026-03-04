import sys
import argparse
from dane_publiczne import developer_data_generate

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="create data for developer")
    parser.add_argument("developer_code", type=str, help="developer code")
    args = parser.parse_args()

    code = args.developer_code

    if input(f'create data for "{code}"? Y/N') != 'Y':
        sys.exit()
    developer_data_generate(code)
