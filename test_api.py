"""
Test script for Excel Relationship Discovery API

This script demonstrates how to:
1. Upload files and create a job
2. Monitor progress via polling
3. Retrieve results when complete
"""
import requests
import time
import json
from pathlib import Path


# API Configuration
API_BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"


def test_health_check():
    """Test API health check"""
    print("\n1. Testing health check...")
    response = requests.get(f"{API_BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200


def create_job(file_paths):
    """Create a new analysis job"""
    print(f"\n2. Creating job with {len(file_paths)} files...")

    # Prepare files for upload
    files = []
    for file_path in file_paths:
        files.append(
            ('files', (Path(file_path).name, open(file_path, 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))
        )

    # Create job
    response = requests.post(
        f"{API_BASE_URL}{API_PREFIX}/jobs",
        files=files
    )

    # Close file handles
    for _, (_, file_handle, _) in files:
        file_handle.close()

    if response.status_code != 201:
        print(f"Error: {response.status_code}")
        print(response.json())
        return None

    job_data = response.json()
    print(f"Job created: {job_data['job_id']}")
    print(f"Status: {job_data['status']}")
    print(f"Files: {job_data['file_count']}")

    return job_data['job_id']


def poll_job_status(job_id, interval=2, timeout=300):
    """Poll job status until completion"""
    print(f"\n3. Polling job status (checking every {interval}s)...")

    start_time = time.time()

    while True:
        # Check timeout
        if time.time() - start_time > timeout:
            print(f"Timeout after {timeout}s")
            return False

        # Get job status
        response = requests.get(f"{API_BASE_URL}{API_PREFIX}/jobs/{job_id}")

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return False

        job = response.json()

        # Print progress
        print(f"  Progress: {job['progress_percent']}% - {job['status']} - Stage: {job.get('current_stage', 'N/A')}")

        # Check if completed
        if job['status'] == 'completed':
            print(f"\n✓ Job completed!")
            print(f"  Relationships found: {job.get('relationships_found', 0)}")
            print(f"  Duration: {(time.time() - start_time):.1f}s")
            return True

        elif job['status'] == 'failed':
            print(f"\n✗ Job failed!")
            print(f"  Error: {job.get('error', 'Unknown error')}")
            return False

        # Wait before next check
        time.sleep(interval)


def get_job_result(job_id, output_file=None):
    """Get job result"""
    print(f"\n4. Retrieving job result...")

    response = requests.get(f"{API_BASE_URL}{API_PREFIX}/jobs/{job_id}/result")

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return None

    result_data = response.json()

    if 'result' not in result_data:
        print("No result available")
        return None

    result = result_data['result']

    # Print summary
    print(f"\n✓ Result retrieved:")
    print(f"  Files analyzed: {result['report_metadata']['file_count']}")
    print(f"  Relationships found: {result['report_metadata']['total_relationships_found']}")
    print(f"  High confidence: {result['report_metadata']['high_confidence']}")
    print(f"  Medium confidence: {result['report_metadata']['medium_confidence']}")
    print(f"  Low confidence: {result['report_metadata']['low_confidence']}")

    # Save to file
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n  Result saved to: {output_file}")

    return result


def list_jobs():
    """List all jobs"""
    print(f"\n5. Listing all jobs...")

    response = requests.get(f"{API_BASE_URL}{API_PREFIX}/jobs?limit=10")

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return

    data = response.json()

    print(f"  Total jobs: {data['total']}")
    for job in data['jobs']:
        print(f"  - {job['job_id']}: {job['status']} ({job.get('relationships_found', 0)} relationships)")


def delete_job(job_id):
    """Delete a job"""
    print(f"\n6. Deleting job {job_id}...")

    response = requests.delete(f"{API_BASE_URL}{API_PREFIX}/jobs/{job_id}")

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return False

    print(f"✓ Job deleted")
    return True


def main():
    """Main test flow"""
    print("=" * 60)
    print("Excel Relationship Discovery API - Test Script")
    print("=" * 60)

    # Test health check
    if not test_health_check():
        print("\n✗ API is not healthy. Make sure the server is running:")
        print("  python -m api.main")
        return

    # Example files (update these paths to your actual files)
    file_paths = [
        "data/customers.xlsx",
        "data/orders.xlsx",
        "data/products.xlsx"
    ]

    # Check files exist
    for file_path in file_paths:
        if not Path(file_path).exists():
            print(f"\n✗ File not found: {file_path}")
            print("\nUpdate the file paths in this script to point to your Excel files.")
            return

    # Create job
    job_id = create_job(file_paths)
    if not job_id:
        return

    # Poll until completion
    success = poll_job_status(job_id, interval=2)
    if not success:
        return

    # Get result
    result = get_job_result(job_id, output_file=f"test_result_{job_id}.json")

    # List all jobs
    list_jobs()

    # Optional: Delete job
    # delete_job(job_id)

    print("\n" + "=" * 60)
    print("✓ Test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
