import os
import json
from github_utils import GitHubUtils # New import
from genai_utils import GenAIUtils
# prompt_utils is used by genai_utils, so no direct import needed here

def main():
    """
    Main function to orchestrate the PR review bot's operations.
    """
    # --- Environment Variables ---
    REPO_NAME = os.getenv("REPO")
    PR_NUMBER = int(os.getenv("PR_NUMBER"))
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    BOT_USER = "dhp-pr-review-bot" # This should match the bot's GitHub username
    AWS_BEDROCK_KB_ID = os.getenv("AWS_BEDROCK_KB_ID")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

    # --- Input Validation ---
    if not all([REPO_NAME, GITHUB_TOKEN, AWS_BEDROCK_KB_ID]):
        print("Error: Missing required environment variables (REPO, GITHUB_TOKEN, AWS_BEDROCK_KB_ID).")
        exit(1)
    if not isinstance(PR_NUMBER, int) or PR_NUMBER <= 0:
        print("Error: PR_NUMBER is not a valid integer.")
        exit(1)

    # --- Initialize GitHubUtils ---
    try:
        github_utils = GitHubUtils(GITHUB_TOKEN, REPO_NAME, PR_NUMBER)
        pr = github_utils.get_pr_details()
    except Exception as e:
        print(f"Failed to initialize GitHubUtils: {e}")
        exit(1)

    # --- Skip if bot is not the requested reviewer ---
    if not github_utils.is_bot_requested_reviewer(BOT_USER):
        print("Bot not requested as reviewer. Exiting.")
        exit(0)

    # --- Initialize GenAIUtils ---
    try:
        genai_reviewer = GenAIUtils(knowledge_base_id=AWS_BEDROCK_KB_ID, region_name=AWS_REGION)
        print("GenAIUtils initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize GenAIUtils: {e}")
        exit(1)

    # --- Process PR content in chunks ---
    print("Processing PR files for review...")
    pr_files = github_utils.get_pr_files()
    if not pr_files:
        print("No files found in PR or error retrieving files. Exiting.")
        exit(0)

    for file in pr_files:
        # Only process added or modified files with content.
        # Deleted files might have a patch, but their content is removed.
        # The AI's prompt in prompt_utils.py handles deleted file context.
        if not file.patch: # Skip files without patch content (e.g., renames without changes)
            print(f"Skipping file {file.filename} as it has no patch content.")
            continue

        filename = file.filename
        patch_content = file.patch

        # For large patches, consider splitting `patch_content` into smaller chunks
        # before sending to `process_pr_chunk` to stay within LLM context limits.
        # Example: Split by lines, or by a character count.
        # For this example, we send the entire patch as one chunk.
        genai_reviewer.process_pr_chunk(filename, patch_content)
        print(f"Sent patch for {filename} to AI for processing.")

    # --- Get the final comprehensive review from the AI ---
    print("Requesting final comprehensive review from AI...")
    ai_review_json = genai_reviewer.get_final_review()

    if ai_review_json:
        print("AI review received. Posting comments...")
        github_utils.post_pr_review_comments(ai_review_json)
        print("PR review comments posted successfully.")
    else:
        print("No AI review content generated or an error occurred.")

    print("PR review process completed.")

if __name__ == "__main__":
    main()

