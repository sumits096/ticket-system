"""
Example script to ingest a document.
Run from project root: python scripts/ingest_example.py path/to/document.pdf
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.admin_service import AdminService


def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/ingest_example.py <file_path> <region> [department]")
        print("Regions: US, UK, EU, Caribbean, APAC")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    region = sys.argv[2]
    department = sys.argv[3] if len(sys.argv) > 3 else "General"

    if not file_path.exists():
        print(f"File not found: {file_path}")
        sys.exit(1)

    admin = AdminService()
    result = admin.upload_document(file_path, region=region, department=department)
    if result.success:
        print(f"✓ Ingested {result.source}: {result.chunks_created} chunks")
    else:
        print(f"✗ Failed: {result.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
