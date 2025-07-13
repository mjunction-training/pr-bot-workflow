import os

from genai_utils import GenAIUtils
from github_utils import GitHubUtils
from kb_utils import KnowledgeBaseUtils

if __name__ == "__main__":

    REPO_NAME = os.getenv("REPO")
    PR_NUMBER = int(os.getenv("PR_NUMBER"))
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    BOT_USER = "dhp-pr-review-bot"  # This should match the bot's GitHub username
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    SAMPLES_DIR = "./.github/samples"

    if not all([REPO_NAME, GITHUB_TOKEN, OPENAI_API_KEY]):
        print("Error: Missing required environment variables (REPO, GITHUB_TOKEN, OPENAI_API_KEY).")
        exit(1)

    if not isinstance(PR_NUMBER, int) or PR_NUMBER <= 0:
        print("Error: PR_NUMBER is not a valid integer.")
        exit(1)

    try:
        github_utils = GitHubUtils(GITHUB_TOKEN, REPO_NAME, PR_NUMBER)
        pr = github_utils.get_pr_details()
    except Exception as e:
        print(f"Failed to initialize GitHubUtils: {e}")
        exit(1)

    if not github_utils.is_bot_requested_reviewer(BOT_USER):
        print("Bot not requested as reviewer. Exiting.")
        exit(0)

    try:
        knowledge_base = KnowledgeBaseUtils(
            samples_dir = SAMPLES_DIR,
            openai_api_key = OPENAI_API_KEY
        )
        if knowledge_base.vector_store:
            print("KnowledgeBaseUtils initialized and vector store created.")
        else:
            print("KnowledgeBaseUtils initialized, but no vector store created (e.g., samples dir not found).")
    except Exception as e:
        print(f"Failed to initialize Knowledge Base: {e}")
        exit(1)

    try:
        genai_reviewer = GenAIUtils(
            knowledge_base=knowledge_base,
            openai_api_key=OPENAI_API_KEY
        )
        print("GenAIUtils initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize GenAIUtils: {e}")
        exit(1)

    print("Processing PR files for review...")
    pr_files = github_utils.get_pr_files()
    if not pr_files or len(pr_files) == 0:
        print("No files found in PR or error retrieving files. Exiting.")
        exit(0)

    for file in pr_files:
        if not file.patch:
            print(f"Skipping file {file.filename} as it has no patch content.")
            continue
        genai_reviewer.process_pr_chunk(
            file_name = file.filename,
            file_content_chunk = file.patch
        )
        print(f"Sent patch for {file.filename} to AI for processing.")

    print("Requesting final comprehensive review from AI...")
    ai_review_json = genai_reviewer.get_final_review()

    if ai_review_json:
        print("AI review received. Posting comments...")
        github_utils.post_pr_review_comments(ai_review_json)
        print("PR review comments posted successfully.")
    else:
        print("No AI review content generated or an error occurred.")

    print("PR review process completed.")

