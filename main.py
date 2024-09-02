import argparse
from ai_code_reviewer import AICodeReviewer
from github_service import GitHubService


def main():
    parser = argparse.ArgumentParser(description="AI-Powered Code Reviewer")
    parser.add_argument('--repo_path', required=True,
                        help='Path to the local git repository')
    parser.add_argument('--repo_owner', required=True,
                        help='Owner of the repository')
    parser.add_argument('--repo_name', required=True,
                        help='Name of the repository')
    parser.add_argument('--github_token', required=True,
                        help='GitHub token for authentication')
    parser.add_argument('--db_path', default='./chroma_db',
                        help='Path to the Chroma database')
    parser.add_argument('--mr_number', type=int,
                        help='Specific MR number to review')
    parser.add_argument('--additional_context',
                        help='Path to additional context (file or directory) for embedding')

    args = parser.parse_args()

    # Initialize GitHub service
    github_service = GitHubService(
        args.repo_owner, args.repo_name, args.github_token)

    # Initialize and run the AI Code Reviewer
    reviewer = AICodeReviewer(
        repo_path=args.repo_path,
        repo_owner=args.repo_owner,
        repo_name=args.repo_name,
        git_service=github_service,
        db_path=args.db_path,
        mr_number=args.mr_number,
        additional_context_for_embedding=args.additional_context
    )
    reviewer.run()


if __name__ == "__main__":
    main()
