"""
Example script to ask a question.
Run from project root: python scripts/ask_example.py "Your question?" UK [department]
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.rag_service import answer


def main():
    if len(sys.argv) < 3:
        print('Usage: python scripts/ask_example.py "Your question?" <region> [department]')
        print("Regions: US, UK, EU, Caribbean, APAC")
        print("Department: optional, e.g. IT, HR (omit for All)")
        sys.exit(1)

    question = sys.argv[1]
    region = sys.argv[2]
    department = sys.argv[3] if len(sys.argv) > 3 else None

    resp = answer(question, region=region, department=department)
    print("--- Answer ---")
    print(resp.answer)
    print("\n--- Sources ---")
    for s in resp.sources:
        print(f"  - {s.source} ({s.region})")
    print(f"\nConfidence: {resp.confidence}")


if __name__ == "__main__":
    main()
