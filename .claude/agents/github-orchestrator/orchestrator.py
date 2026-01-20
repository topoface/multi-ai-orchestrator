#!/usr/bin/env python3
"""
GitHub Orchestrator
Manages GitHub Issues, PRs, and Actions for Multi-AI debates
"""
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from github import Github, GithubException

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
# GitHub Actions provides GITHUB_REPOSITORY automatically (e.g., 'owner/repo')
GITHUB_REPO = os.getenv('GITHUB_REPOSITORY') or os.getenv('GITHUB_REPO', 'topoface/multi-ai-orchestrator')


class GitHubOrchestrator:
    def __init__(self):
        if not GITHUB_TOKEN:
            raise ValueError("GITHUB_TOKEN environment variable not set")

        self.github = Github(GITHUB_TOKEN)
        self.repo = self.github.get_repo(GITHUB_REPO)

    def create_debate_issue(self, title: str, body: str, labels: list = None) -> int:
        """Create a new debate issue"""
        if not title.startswith('[Debate]'):
            title = f"[Debate] {title}"

        default_labels = ['ai-debate']
        if labels:
            default_labels.extend(labels)

        try:
            issue = self.repo.create_issue(
                title=title,
                body=body,
                labels=default_labels
            )
            print(f"✓ Created issue #{issue.number}: {title}")
            return issue.number

        except GithubException as e:
            print(f"Error creating issue: {e}", file=sys.stderr)
            raise

    def monitor_debate_progress(self, issue_number: int, timeout: int = 600) -> Optional[Dict]:
        """Monitor GitHub Actions workflow for debate progress"""
        print(f"Monitoring debate progress for issue #{issue_number}...")

        start_time = time.time()
        workflow_name = 'ai-debate-trigger'

        while time.time() - start_time < timeout:
            try:
                # Get workflow runs
                workflows = self.repo.get_workflows()
                target_workflow = None

                for wf in workflows:
                    if workflow_name in wf.name or workflow_name in wf.path:
                        target_workflow = wf
                        break

                if not target_workflow:
                    print(f"Warning: Workflow '{workflow_name}' not found", file=sys.stderr)
                    return None

                # Get recent runs
                runs = target_workflow.get_runs()
                for run in runs[:5]:  # Check last 5 runs
                    if run.status == 'completed':
                        if run.conclusion == 'success':
                            print(f"✓ Workflow completed successfully")
                            return {'status': 'success', 'run_id': run.id}
                        elif run.conclusion == 'failure':
                            print(f"✗ Workflow failed", file=sys.stderr)
                            return {'status': 'failure', 'run_id': run.id}

                # Wait before next check
                time.sleep(10)

            except GithubException as e:
                print(f"Error monitoring workflow: {e}", file=sys.stderr)
                time.sleep(10)

        print(f"⚠ Monitoring timed out after {timeout}s", file=sys.stderr)
        return {'status': 'timeout'}

    def post_debate_results(self, issue_number: int, results_file: Path):
        """Post debate results as Issue comment"""
        try:
            with open(results_file, 'r') as f:
                results = json.load(f)

            # Format comment
            comment = self._format_debate_comment(results)

            # Post comment
            issue = self.repo.get_issue(issue_number)
            issue.create_comment(comment)

            print(f"✓ Posted results to issue #{issue_number}")

            # Close issue if consensus reached
            consensus = results.get('consensus_score', 0)
            threshold = 0.85

            if consensus >= threshold:
                issue.edit(state='closed')
                issue.create_comment(f"🎉 Consensus reached ({consensus:.2%}). Closing issue.")
                print(f"✓ Closed issue #{issue_number} (consensus: {consensus:.2%})")

        except Exception as e:
            print(f"Error posting results: {e}", file=sys.stderr)
            raise

    def _format_debate_comment(self, results: Dict[str, Any]) -> str:
        """Format debate results as GitHub comment"""
        consensus = results.get('consensus_score', 0)
        status = results.get('status', 'unknown')

        comment = f"""## 🤖 AI Debate Results

**Topic**: {results.get('topic', 'Unknown')}
**Consensus**: {consensus:.2%}
**Status**: {status.upper()}
**Rounds**: {results.get('rounds', 0)}

---

### Claude's Position
{results.get('claude_final_position', 'N/A')[:500]}...

### Gemini's Position
{results.get('gemini_final_position', 'N/A')[:500]}...
"""

        if results.get('perplexity_judgment'):
            comment += f"""
### Perplexity Expert Judgment
{results.get('perplexity_judgment', '')[:500]}...
"""

        comment += f"""
---

**Full details**: See `docs/brain/` for complete debate transcript.

*Generated by Multi-AI Orchestrator*
"""

        return comment

    def create_pr_from_decision(self, title: str, branch: str, base: str = 'main', body: str = ""):
        """Create PR from decision implementation"""
        try:
            pr = self.repo.create_pull(
                title=title,
                body=body,
                head=branch,
                base=base
            )
            print(f"✓ Created PR #{pr.number}: {title}")
            return pr.number

        except GithubException as e:
            print(f"Error creating PR: {e}", file=sys.stderr)
            raise

    def trigger_workflow(self, workflow_name: str, inputs: Dict = None):
        """Manually trigger a workflow"""
        try:
            workflows = self.repo.get_workflows()
            target_workflow = None

            for wf in workflows:
                if workflow_name in wf.name or workflow_name in wf.path:
                    target_workflow = wf
                    break

            if not target_workflow:
                print(f"Error: Workflow '{workflow_name}' not found", file=sys.stderr)
                return False

            target_workflow.create_dispatch(
                ref='main',
                inputs=inputs or {}
            )
            print(f"✓ Triggered workflow: {workflow_name}")
            return True

        except GithubException as e:
            print(f"Error triggering workflow: {e}", file=sys.stderr)
            return False


def main():
    if len(sys.argv) < 2:
        print("Usage: orchestrator.py <command> [options]", file=sys.stderr)
        print("\nCommands:", file=sys.stderr)
        print("  create-issue --title <title> --body <body> [--labels <labels>]", file=sys.stderr)
        print("  monitor --issue <number>", file=sys.stderr)
        print("  post-results --issue <number> --results-file <path>", file=sys.stderr)
        print("  create-pr --title <title> --branch <branch> --body <body>", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    orchestrator = GitHubOrchestrator()

    try:
        if command == 'create-issue':
            # Parse arguments
            title = ""
            body = ""
            labels = []

            i = 2
            while i < len(sys.argv):
                if sys.argv[i] == '--title' and i + 1 < len(sys.argv):
                    title = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] == '--body' and i + 1 < len(sys.argv):
                    body = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] == '--labels' and i + 1 < len(sys.argv):
                    labels = sys.argv[i + 1].split(',')
                    i += 2
                else:
                    i += 1

            issue_num = orchestrator.create_debate_issue(title, body, labels)
            print(f"Issue number: {issue_num}")

        elif command == 'monitor':
            issue_num = None
            i = 2
            while i < len(sys.argv):
                if sys.argv[i] == '--issue' and i + 1 < len(sys.argv):
                    issue_num = int(sys.argv[i + 1])
                    i += 2
                else:
                    i += 1

            if issue_num:
                result = orchestrator.monitor_debate_progress(issue_num)
                print(json.dumps(result, indent=2))

        elif command == 'post-results':
            issue_num = None
            results_file = None

            i = 2
            while i < len(sys.argv):
                if sys.argv[i] == '--issue' and i + 1 < len(sys.argv):
                    issue_num = int(sys.argv[i + 1])
                    i += 2
                elif sys.argv[i] == '--results-file' and i + 1 < len(sys.argv):
                    results_file = Path(sys.argv[i + 1])
                    i += 2
                else:
                    i += 1

            if issue_num and results_file:
                orchestrator.post_debate_results(issue_num, results_file)

        elif command == 'create-pr':
            title = ""
            branch = ""
            body = ""
            base = "main"

            i = 2
            while i < len(sys.argv):
                if sys.argv[i] == '--title' and i + 1 < len(sys.argv):
                    title = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] == '--branch' and i + 1 < len(sys.argv):
                    branch = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] == '--body' and i + 1 < len(sys.argv):
                    body = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] == '--base' and i + 1 < len(sys.argv):
                    base = sys.argv[i + 1]
                    i += 2
                else:
                    i += 1

            orchestrator.create_pr_from_decision(title, branch, base, body)

        else:
            print(f"Unknown command: {command}", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
