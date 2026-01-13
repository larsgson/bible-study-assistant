#!/usr/bin/env python3
"""Upload ChromaDB data to fly.io using flyctl ssh console."""

import subprocess
import sys
from pathlib import Path


def run_ssh_command(command: str) -> tuple[bool, str]:
    """Run a command via flyctl ssh console.

    Returns:
        Tuple of (success, output)
    """
    try:
        result = subprocess.run(
            ["flyctl", "ssh", "console", "-C", command],
            capture_output=True,
            text=True,
            timeout=300,
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)


def upload_file_via_python(local_path: Path, remote_path: str) -> bool:
    """Upload a file by base64 encoding and transferring via Python on remote.

    Args:
        local_path: Local file to upload
        remote_path: Remote path on fly.io machine

    Returns:
        True if successful
    """
    print(f"Reading local file: {local_path}")
    with open(local_path, "rb") as f:
        file_data = f.read()

    import base64

    encoded = base64.b64encode(file_data).decode("ascii")
    file_size_mb = len(file_data) / (1024 * 1024)

    print(f"File size: {file_size_mb:.2f} MB")
    print(f"Encoded size: {len(encoded) / (1024 * 1024):.2f} MB")

    # Split into chunks to avoid command line limits
    chunk_size = 50000
    chunks = [encoded[i : i + chunk_size] for i in range(0, len(encoded), chunk_size)]

    print(f"Split into {len(chunks)} chunks")

    # Clear any existing temp file
    print("Clearing remote temp file...")
    success, output = run_ssh_command(f"rm -f /tmp/upload_temp.b64")

    # Upload chunks
    for i, chunk in enumerate(chunks, 1):
        print(f"Uploading chunk {i}/{len(chunks)}...", end="", flush=True)

        # Escape the chunk for shell
        chunk_escaped = chunk.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$")

        cmd = f'python3 -c "with open(\\"/tmp/upload_temp.b64\\", \\"a\\") as f: f.write(\\"{chunk_escaped}\\")"'

        success, output = run_ssh_command(cmd)
        if not success:
            print(f" FAILED")
            print(f"Error: {output}")
            return False
        print(" OK")

    # Decode the file
    print(f"Decoding file on remote to {remote_path}...")
    decode_cmd = f"""python3 -c "
import base64
with open('/tmp/upload_temp.b64', 'r') as f:
    encoded = f.read()
with open('{remote_path}', 'wb') as f:
    f.write(base64.b64decode(encoded))
print('Decoded successfully')
"
"""

    success, output = run_ssh_command(decode_cmd)
    if not success:
        print(f"Decode failed: {output}")
        return False

    print("Upload complete!")

    # Verify
    print("Verifying remote file...")
    success, output = run_ssh_command(f"ls -lh {remote_path}")
    print(output)

    # Cleanup
    print("Cleaning up temp file...")
    run_ssh_command("rm -f /tmp/upload_temp.b64")

    return True


def main():
    """Upload ChromaDB to fly.io."""

    # Check if local chroma.sqlite3 exists
    local_db = Path("data/chroma.sqlite3")

    if not local_db.exists():
        print(f"ERROR: {local_db} not found")
        print("Make sure you run this script from the project root")
        sys.exit(1)

    print("=" * 60)
    print("ChromaDB Upload to fly.io")
    print("=" * 60)
    print()

    # Compress the database
    import gzip
    import tempfile

    print("Compressing database...")
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".gz", delete=False) as tmp:
        temp_path = Path(tmp.name)

        with open(local_db, "rb") as f_in:
            with gzip.open(tmp, "wb") as f_out:
                f_out.writelines(f_in)

    print(f"Compressed to: {temp_path}")
    print(f"Compressed size: {temp_path.stat().st_size / (1024 * 1024):.2f} MB")
    print()

    # Upload
    if not upload_file_via_python(temp_path, "/tmp/chroma.sqlite3.gz"):
        print("Upload failed!")
        temp_path.unlink()
        sys.exit(1)

    # Clean up local temp file
    temp_path.unlink()

    # Extract on remote
    print()
    print("=" * 60)
    print("Extracting database on fly.io...")
    print("=" * 60)

    extract_cmd = """
    gunzip -f /tmp/chroma.sqlite3.gz && \
    mv /tmp/chroma.sqlite3 /data/chroma.sqlite3.new && \
    ls -lh /data/chroma.sqlite3.new
    """

    success, output = run_ssh_command(extract_cmd)
    print(output)

    if not success:
        print("Extraction failed!")
        sys.exit(1)

    # Stop the app
    print()
    print("=" * 60)
    print("Replacing database...")
    print("=" * 60)
    print()
    print("You need to:")
    print("1. Stop the app: flyctl scale count 0")
    print(
        "2. Replace database: flyctl ssh console -C 'mv /data/chroma.sqlite3.new /data/chroma.sqlite3'"
    )
    print("3. Also copy the UUID directory if needed")
    print("4. Restart app: flyctl scale count 1")
    print()
    print("Or run these commands now:")

    response = input("Stop app and replace database now? (y/N): ")

    if response.lower() == "y":
        print("\nStopping app...")
        subprocess.run(["flyctl", "scale", "count", "0"])

        print("Replacing database...")
        run_ssh_command("mv /data/chroma.sqlite3.new /data/chroma.sqlite3")

        # Check if UUID directory exists locally
        data_dir = Path("data")
        uuid_dirs = [d for d in data_dir.iterdir() if d.is_dir() and len(d.name) == 36]

        if uuid_dirs:
            print(f"\nFound UUID directory: {uuid_dirs[0].name}")
            print("This directory also needs to be uploaded.")
            print("Skipping for now - manual upload needed if collections reference it.")

        print("\nRestarting app...")
        subprocess.run(["flyctl", "scale", "count", "1"])

        print(
            "\nDone! Verify with: flyctl ssh console -C 'python3 -c \"from bt_servant_engine.adapters.chroma import list_chroma_collections; print(list_chroma_collections())\"'"
        )
    else:
        print("\nDatabase file ready at /data/chroma.sqlite3.new on fly.io")
        print("Run the commands above when ready.")


if __name__ == "__main__":
    main()
