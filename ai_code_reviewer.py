import os
from git import Repo
from chromadb import PersistentClient
import requests


class AICodeReviewer:
    def __init__(self, repo_path, repo_owner, repo_name, git_service, db_path='./chroma_db', mr_number=None, additional_context_for_embedding=None):
        self.repo_path = repo_path
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.git_service = git_service
        self.repo = Repo(repo_path)
        self.db_path = db_path
        self.mr_number = mr_number
        self.additional_context_for_embedding = additional_context_for_embedding
        self.setup_database()

    def setup_database(self):
        self.chroma_client = PersistentClient(path=self.db_path)
        self.collection = self.chroma_client.get_or_create_collection(
            name="code_embeddings",
            metadata={
                "description": "Embeddings of code files for the repository"}
        )

    def switch_to_source_branch(self, source_branch):
        print(f"Switching to source branch: {source_branch}")
        self.repo.git.checkout(source_branch)
        self.repo.git.pull()

    def ollama_embed(self, texts):
        url = "http://localhost:11434/api/embeddings"
        embeddings = []
        for text in texts:
            if not text.strip():
                print("Skipping empty or invalid text input.")
                embeddings.append([])
                continue

            data = {
                "model": "chroma/all-minilm-l6-v2-f32",
                "prompt": text
            }
            try:
                response = requests.post(url, json=data)
                response_data = response.json()
                embedding = response_data.get('embedding', [])
                if not embedding:
                    print(f"Empty embedding received for text: {text[:30]}...")
                embeddings.append(embedding)
            except Exception as e:
                print(f"Error during embedding generation: {e}")
                embeddings.append([])

        valid_embeddings = [emb for emb in embeddings if emb]
        if len(valid_embeddings) < len(texts):
            print(
                f"Warning: Some embeddings were empty. Processed {len(valid_embeddings)}/{len(texts)} successfully.")

        return embeddings

    def create_embeddings(self):
        print("Creating embeddings for the project...")
        files = [item.path for item in self.repo.tree().traverse()
                 if item.type == 'blob']

        # Include additional context files or directories
        if self.additional_context_for_embedding:
            additional_files = self.collect_additional_files(
                self.additional_context_for_embedding)
            files.extend(additional_files)

        for i in range(0, len(files), 10):
            batch_files = files[i:i+10]
            contents = []
            for file in batch_files:
                try:
                    with open(os.path.join(self.repo_path, file), 'r') as f:
                        contents.append(f.read())
                except Exception as e:
                    print(f"Error reading file {file}: {str(e)}")
                    contents.append("")

            embeddings = self.ollama_embed(contents)
            valid_embeddings = [emb for emb in embeddings if emb]
            valid_files = [file for emb, file in zip(
                embeddings, batch_files) if emb]
            valid_contents = [content for emb,
                              content in zip(embeddings, contents) if emb]

            if valid_embeddings:
                try:
                    self.collection.upsert(
                        ids=valid_files,
                        embeddings=embeddings,
                        metadatas=[{"file_path": file}
                                   for file in valid_files],
                        documents=valid_contents
                    )
                except ValueError as ve:
                    print(f"Error during upsert operation: {ve}")
            else:
                print("No valid embeddings generated for this batch. Skipping upsert.")

        print("Embeddings created and stored in Chroma DB.")

    def collect_additional_files(self, path):
        """
        Collects files from the given directory or single file path for additional context embedding.
        """
        additional_files = []
        if os.path.isfile(path):
            additional_files.append(path)
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    additional_files.append(os.path.join(root, file))
        else:
            print(f"Invalid additional context path: {path}")

        # Convert paths relative to the repository if they are absolute paths
        additional_files = [os.path.relpath(
            file, self.repo_path) for file in additional_files]
        return additional_files

    def get_relevant_context(self, query, k=5):
        query_embedding = self.ollama_embed([query])[0]
        if not query_embedding:
            print("Empty query embedding; skipping context retrieval.")
            return []
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["metadatas", "documents"]
        )
        return list(zip(results['metadatas'][0], results['documents'][0]))

    def analyze_mr(self, mr_data, mr_changes):
        reviews = []
        for change in mr_changes:
            filename = change['filename']

            # Skip files in ignored directories
            if any(skip_dir in filename for skip_dir in ['vendor', 'lib', 'library', 'libraries', 'node-modules']):
                continue

            # Skip minified files by checking for '.min' in filename or extremely long lines
            if '.min.' in filename:
                print(f"Skipping minified file: {filename}")
                continue

            # Skip documentation files based on common extensions
            if filename.lower().endswith(('.md', '.rst', '.txt', '.json', '.xml', '.yml', '.yaml', '.doc', '.docx', '.pdf')):
                print(f"Skipping documentation file: {filename}")
                continue

            patch = change.get('patch', '')

            # Additional check for minification by line length
            if self.is_minified(patch):
                print(f"Skipping minified content in file: {filename}")
                continue

            relevant_context = self.get_relevant_context(patch)
            context_files = [metadata['file_path']
                             for metadata, _ in relevant_context]
            context_str = "\n".join(
                [f"File: {metadata['file_path']}\n\n{content}" for metadata, content in relevant_context])

            prompt = f"""
            Relevant Project Context:
            {context_str}

            Analyze the following code change in the context of the relevant parts of the project:
            File: {filename}
            Patch:
            {patch}

            Identify and list only the issues found in the code, including:
            1. Code quality problems
            2. Potential bugs or issues
            3. Performance implications
            4. Integration issues with existing project architecture
            5. Areas needing improvement

            For each issue, include the line number(s). Add relevant hashtags such as at the end of each review point:
            #bug, #vulnerability, #code-smell, #high-priority, #medium-priority, #low-priority.

            For each identified issue, provide a correct code snippet that can solve the problem.

            Additionally, list the files that were considered as context for this review:
            {', '.join(context_files)}

            Only list the issues and provide corrections; do not include details about what is done correctly.

            If the code is correct as per all the above criteria, skip the file and do not return any review.

            Skip any documentation files.
            """

            review = self.ollama_generate(prompt)

            reviews.append({
                'filename': filename,
                'review': review
            })

        return reviews

    def ollama_generate(self, prompt):
        url = "http://localhost:11434/api/generate"
        data = {
            "model": "llama3:latest",
            "prompt": prompt,
            "stream": False
        }
        response = requests.post(url, json=data)
        return response.json().get('response', 'Error: Failed to generate response.')

    def is_minified(self, content):
        lines = content.split('\n')
        long_lines = [line for line in lines if len(line) > 500]
        if len(long_lines) / len(lines) > 0.3:
            return True
        return False

    def format_review(self, reviews):
        formatted_reviews = []
        for review in reviews:
            formatted_review = f"""
    ## {review['filename']}

{review['review']}
    """
            formatted_reviews.append(formatted_review.strip())
        return "\n\n".join(formatted_reviews)

    def save_reviews_to_file(self, formatted_review, output_path='review_output.md'):
        with open(output_path, 'w') as f:
            f.write(formatted_review)
        print(f"Reviews saved to {output_path}")

    def update_embeddings(self):
        print("Updating embeddings...")
        self.create_embeddings()

    def run(self):
        if self.mr_number:
            mr_number = self.mr_number
            mr_changes = self.git_service.get_mr_changes(mr_number)
            if not mr_changes:
                print(f"MR #{mr_number} not found.")
                return
            latest_mr = self.git_service.get_mr_details(mr_number)
            if latest_mr:
                source_branch = latest_mr['head']['ref']
            else:
                print(f"Could not fetch details for MR #{mr_number}.")
                return
        else:
            latest_mr = self.git_service.get_latest_mr()
            if latest_mr:
                mr_number = latest_mr['number']
                source_branch = latest_mr['head']['ref']
            else:
                print("No open MRs found.")
                return

        print(f"Reviewing MR #{mr_number} from branch {source_branch}")

        self.switch_to_source_branch(source_branch)

        self.update_embeddings()
        reviews = self.analyze_mr(latest_mr, mr_changes)
        formatted_review = self.format_review(reviews)
        self.save_reviews_to_file(formatted_review)

        # Post review as comment to GitHub MR
        self.git_service.post_comment(mr_number, formatted_review)
