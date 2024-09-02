import requests


class GitHubService:
    def __init__(self, repo_owner, repo_name, github_token):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_token = github_token

    def get_latest_mr(self):
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        url = f'https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/pulls?state=open&sort=created&direction=desc'
        response = requests.get(url, headers=headers)
        pulls = response.json()
        return pulls[0] if pulls else None

    def get_mr_details(self, mr_number):
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        url = f'https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/pulls/{mr_number}'
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(
                f"Failed to get MR #{mr_number} details: {response.status_code}")
            return None

    def get_mr_changes(self, mr_number):
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        url = f'https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/pulls/{mr_number}/files'
        response = requests.get(url, headers=headers)
        return response.json()

    def post_comment(self, mr_number, comment):
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        url = f'https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/issues/{mr_number}/comments'
        data = {'body': comment}
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            print(f"Comment posted to MR #{mr_number}.")
        else:
            print(
                f"Failed to post comment: {response.status_code} - {response.text}")
