import argparse
import json
import jsonlines
import sys


def convert_json_to_jsonl(json_file, jsonl_file):
    with open(json_file, "r") as file:
        json_data = json.load(file)

    with jsonlines.open(jsonl_file, "w") as writer:
        for item in json_data:
            writer.write(item)


def main():
    parser = argparse.ArgumentParser(description="Convert JSON to JSONL")
    parser.add_argument("input_json", help="Input JSON file")
    parser.add_argument("output_jsonl", help="Output JSONL file")
    args = parser.parse_args()

    try:
        convert_json_to_jsonl(args.input_json, args.output_jsonl)
    except FileNotFoundError:
        print("Error: Input JSON file not found.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
