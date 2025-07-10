import os
import json
from github import Github
from your_bot_module import generate_review_comments, get_cached_reviewed_lines, post_metadata_comment

REPO = os.getenv("REPO")
PR_NUMBER = int(os.getenv("PR_NUMBER"))
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
BOT_USER = "dhp-pr-review-bot"

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO)
pr = repo.get_pull(PR_NUMBER)

# Skip if bot is not the requested reviewer
reviewers = [r.login for r in pr.get_review_requests()[0]]
if BOT_USER not in reviewers:
    print("Bot not requested as reviewer. Skipping.")
    exit(0)

# Load previously reviewed lines
reviewed_cache = get_cached_reviewed_lines(pr)

# Generate review comments (only for new lines)
comments, new_cache = generate_review_comments(pr, reviewed_cache)

# Post review
if comments:
    pr.create_review(
        body="🤖 dhp-pr-review-bot reviewed this PR.",
        event="COMMENT",
        comments=comments
    )
    post_metadata_comment(pr, new_cache)
else:
    print("No new comments to post.")
