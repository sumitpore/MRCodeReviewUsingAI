# AI-Powered Code Reviewer

## Introduction
The AI-Powered Code Reviewer is a tool that uses natural language processing and machine learning to provide intelligent code reviews for Merge Requests (MRs) in a GitHub repository. It analyzes the code changes, considers the relevant context from the codebase, and generates detailed feedback on potential issues, code quality, and areas for improvement.

## Technologies Used
The project utilizes the following technologies:

1. **Python**: The main programming language used for the project.
2. **Chroma**: A vector database used for storing and querying code embeddings.
3. **Git**: Used for cloning and managing the Git repository.
4. **GitHub API**: Used for fetching Merge Request details and posting review comments.
5. **Ollama**: Ollama is a software required to run LLM locally.
6. **LLMs (Large Language Models)**: Used for generating code embeddings and reviews, operating under their respective licenses.

The code relies on the vector database (Chroma) to store and query relevant context for the code review process.

## Installation and Setup

1. Clone the repository:
   ```
   git clone https://github.com/sumitpore/MRCodeReviewUsingAI.git
   ```

2. Create a new Python virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up the Chroma database:
   ```
   mkdir chroma_db
   ```

## Usage

1. Run the code reviewer:
   ```
   python main.py --repo_path /path/to/git/repo --repo_owner your-github-username --repo_name your-repo-name --github_token your-github-token
   ```

   This will create code embeddings, analyze the latest open Merge Request, and post the review comments to the GitHub MR.

2. To review a specific Merge Request:
   ```
   python main.py --repo_path /path/to/git/repo --repo_owner your-github-username --repo_name your-repo-name --github_token your-github-token --mr_number 123
   ```

   Replace `123` with the actual Merge Request number you want to review.


## Accepted Arguments

Below is the list of all accepted arguments for `main.py`:

| Argument               | Description                                                                                    | Required | Default       |
| ---------------------- | ---------------------------------------------------------------------------------------------- | -------- | ------------- |
| `--repo_path`          | Path to the local Git repository.                                                              | Yes      | N/A           |
| `--repo_owner`         | Owner of the GitHub repository (username or organization).                                     | Yes      | N/A           |
| `--repo_name`          | Name of the GitHub repository.                                                                 | Yes      | N/A           |
| `--github_token`       | GitHub personal access token for authentication.                                               | Yes      | N/A           |
| `--db_path`            | Path to the Chroma database directory.                                                         | No       | `./chroma_db` |
| `--mr_number`          | Specific Merge Request number to review. If not provided, the latest open MR will be reviewed. | No       | None          |
| `--additional_context` | Path to an additional file or directory for embedding context during the review process.       | No       | None          |

To pass these arguments, use the corresponding flags followed by the appropriate values when running `main.py`.

## Features
- Automatically fetches the latest open Merge Request or a specific MR for review.
- Generates code embeddings for the repository using the Llama 3.1 LLM.
- Analyzes the code changes in the context of the relevant parts of the codebase.
- Identifies and reports on various issues, including code quality, potential bugs, performance implications, and integration problems.
- Provides corrective code snippets for each identified issue.
- Posts the review comments directly to the GitHub Merge Request.
- Supports incremental updates to the code embeddings.