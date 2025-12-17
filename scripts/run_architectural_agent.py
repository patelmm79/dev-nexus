"""CLI wrapper to run the ArchitecturalAgent from the repository root."""

from agents.architectural_agent.agent import ArchitecturalAgent
import logging
import sys


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print("Usage: run_architectural_agent.py <repo-path-or-git-url> [output.json]")
        sys.exit(2)

    repo = argv[0]
    out = argv[1] if len(argv) > 1 else 'architectural_report.json'

    logging.basicConfig(level=logging.INFO)
    agent = ArchitecturalAgent()
    report = agent.analyze_repo(repo)
    agent.save_json(out, report)
    print('Saved report to', out)


if __name__ == '__main__':
    main()
