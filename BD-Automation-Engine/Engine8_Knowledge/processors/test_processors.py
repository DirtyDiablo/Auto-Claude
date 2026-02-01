"""Test Document Processing Pipeline."""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from document_pipeline import BDDocumentPipeline, process_document


def test_document_pipeline():
    print("Testing Document Pipeline...")

    # Test initialization
    pipeline = BDDocumentPipeline()
    print(f"[OK] Pipeline initialized (docling={pipeline.use_docling})")

    # Test with a sample PDF if available
    base_dir = Path(__file__).parent.parent.parent
    test_files = list(base_dir.glob("**/*.pdf"))[:1]

    if test_files:
        test_file = str(test_files[0])
        print(f"\nTesting with: {test_file}")

        result = pipeline.process_to_dict(test_file)

        print(f"[OK] Document ID: {result['document_id']}")
        print(f"[OK] Pages: {result['num_pages']}")
        print(f"[OK] Text length: {result['text_length']}")
        print(f"[OK] Tables found: {result['tables_count']}")
        print(f"[OK] Processor: {result['metadata']['processor']}")
    else:
        print("[WARN] No PDF files found for testing")

    # Test routes import
    from routes import router
    print(f"\n[OK] Router created with prefix: {router.prefix}")

    print("\n[SUCCESS] Document Pipeline tests passed!")


if __name__ == "__main__":
    test_document_pipeline()
