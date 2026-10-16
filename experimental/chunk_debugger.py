"""
Chunk Processing Debugger - Helps identify where chunks are lost in the pipeline
"""


def debug_chunk_processing(
    chunks_initial, chunks_after_split, chunks_to_process, processed_chunks
):
    """
    Debug function to track chunk counts through the processing pipeline
    """
    print("\n" + "=" * 60)
    print("🔍 CHUNK PROCESSING DEBUG REPORT")
    print("=" * 60)

    print(
        f"📊 Initial documents loaded: {len(chunks_initial) if chunks_initial else 0}"
    )
    print(
        f"📊 After text splitting: {len(chunks_after_split) if chunks_after_split else 0}"
    )
    print(
        f"📊 After duplicate removal: {len(chunks_to_process) if chunks_to_process else 0}"
    )
    print(
        f"📊 Previously processed: {len(processed_chunks) if processed_chunks else 0}"
    )

    if chunks_after_split and chunks_to_process:
        duplicates_removed = len(chunks_after_split) - len(chunks_to_process)
        print(f"📊 Duplicates removed: {duplicates_removed}")

        if duplicates_removed > 0:
            print(f"⚠️  WARNING: {duplicates_removed} duplicate chunks were removed!")
            print("   This might reduce knowledge graph completeness.")
            print("   Consider keeping duplicates for better coverage.")

    print("=" * 60)
    return True


def analyze_chunk_content(chunks, sample_size=3):
    """
    Analyze chunk content to identify potential issues
    """
    print(
        f"\n🔍 CHUNK CONTENT ANALYSIS (Sample of {min(sample_size, len(chunks))} chunks):"
    )
    print("-" * 50)

    for i, chunk in enumerate(chunks[:sample_size]):
        print(f"\nChunk {i + 1}:")
        print(f"  Length: {len(chunk.page_content)} characters")
        print(f"  Preview: {chunk.page_content[:100]}...")

        # Check for empty or very short chunks
        if len(chunk.page_content.strip()) < 50:
            print(f"  ⚠️  WARNING: Very short chunk detected!")

        # Check for metadata
        if hasattr(chunk, "metadata") and chunk.metadata:
            print(f"  Metadata: {chunk.metadata}")

    return True


def find_duplicate_chunks(chunks):
    """
    Find and report duplicate chunks
    """
    content_counts = {}
    duplicates = []

    for i, chunk in enumerate(chunks):
        content = chunk.page_content.strip()
        if content in content_counts:
            content_counts[content].append(i)
            if len(content_counts[content]) == 2:  # First duplicate found
                duplicates.append(content)
        else:
            content_counts[content] = [i]

    if duplicates:
        print(f"\n🔍 DUPLICATE CHUNKS FOUND: {len(duplicates)}")
        print("-" * 50)
        for i, dup_content in enumerate(duplicates[:3]):  # Show first 3
            indices = content_counts[dup_content]
            print(f"\nDuplicate {i + 1} (appears {len(indices)} times):")
            print(f"  Chunk indices: {indices}")
            print(f"  Content preview: {dup_content[:100]}...")
    else:
        print("\n✅ No duplicate chunks found")

    return duplicates
