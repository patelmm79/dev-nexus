"""
Script to run documentation standards checker on the current repository
"""

import os
import sys
import json
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from github import Github
from core.documentation_standards_checker import DocumentationStandardsChecker


def main():
    # Try to load .env file if it exists
    env_file = project_root / ".env"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)

    # Get GitHub token
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("ERROR: GITHUB_TOKEN environment variable not set")
        print("Please set GITHUB_TOKEN or create a .env file with GITHUB_TOKEN=your_token")
        sys.exit(1)

    # Repository to check
    repository = "patelmm79/dev-nexus"

    # Load standards content
    standards_path = project_root / "docs" / "DOCUMENTATION_STANDARDS.md"
    try:
        with open(standards_path, 'r', encoding='utf-8') as f:
            standards_content = f.read()
    except Exception as e:
        print(f"⚠️ Warning: Could not load standards file: {e}")
        standards_content = None

    # Initialize GitHub client
    from github import Auth
    auth = Auth.Token(github_token)
    github_client = Github(auth=auth)

    # Initialize checker
    checker = DocumentationStandardsChecker(
        github_client=github_client,
        standards_content=standards_content
    )

    print(f"🔍 Checking documentation standards for {repository}...")
    print("📋 Checking priority documentation files only...\n")

    # Check repository (priority files only)
    result = checker.check_repository(
        repository=repository,
        check_all_docs=False
    )

    # Display results
    if not result.get("success"):
        print(f"❌ Error: {result.get('error')}")
        if 'traceback' in result:
            print(f"\nTraceback:\n{result['traceback']}")
        sys.exit(1)

    # Display summary
    print(f"\n{'='*80}")
    print(f"  Documentation Standards Check Results")
    print(f"{'='*80}\n")

    print(f"Repository: {result['repository']}")
    print(f"Status: {result['status_emoji']} {result['status'].replace('_', ' ').title()}")
    print(f"Compliance Score: {result['compliance_score']*100:.0f}%\n")

    summary = result['summary']
    print(f"📊 Summary:")
    print(f"  - Files Checked: {summary['total_files_checked']}")
    print(f"  - Total Violations: {summary['total_violations']}")
    print(f"  - Critical: {summary['critical_violations']}")
    print(f"  - High Priority: {summary['high_violations']}")
    print(f"  - Medium Priority: {summary['medium_violations']}\n")

    # Display critical violations
    if result.get('critical_violations'):
        print(f"🔴 Critical Violations:\n")
        for i, violation in enumerate(result['critical_violations'][:10], 1):
            print(f"{i}. {violation['message']}")
            print(f"   File: {violation['file']}")
            if 'recommendation' in violation:
                print(f"   💡 {violation['recommendation']}")
            print()

    # Display recommendations
    if result.get('recommendations'):
        print(f"💡 Recommendations:\n")
        for rec in result['recommendations']:
            print(f"  • {rec}")
        print()

    # Display per-file results
    print(f"\n{'='*80}")
    print(f"  Per-File Results")
    print(f"{'='*80}\n")

    for file_result in result['file_results']:
        file_path = file_result['file']
        priority = file_result['priority']
        violation_count = file_result.get('violation_count', len(file_result.get('violations', [])))

        if violation_count == 0:
            status = "✅"
        elif file_result.get('violations', [{}])[0].get('type') == 'missing_file':
            status = "❌"
        elif violation_count > 3:
            status = "⚠️"
        else:
            status = "⚠️"

        print(f"{status} {file_path} ({priority} priority)")

        if violation_count > 0:
            for violation in file_result['violations']:
                print(f"   • [{violation['severity'].upper()}] {violation['message']}")
                if 'recommendation' in violation:
                    print(f"     💡 {violation['recommendation']}")
        print()

    # Save detailed results to file
    output_file = project_root / "documentation_check_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    print(f"\n💾 Detailed results saved to: {output_file}")

    # Exit code based on status
    if result['status'] == 'non_compliant':
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
