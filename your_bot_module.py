import json

def get_cached_reviewed_lines(pr):
    for comment in pr.get_issue_comments():
        if comment.body.startswith("<!-- dhp-pr-review-bot-meta"):
            try:
                meta = json.loads(comment.body.split('\n', 1)[1])
                return meta.get("reviewed", {})
            except Exception:
                continue
    return {}

def post_metadata_comment(pr, reviewed_lines_dict):
    meta = { "reviewed": reviewed_lines_dict }
    body = f"<!-- dhp-pr-review-bot-meta\n{json.dumps(meta, indent=2)}\n-->"
    pr.create_issue_comment(body)

def generate_review_comments(pr, cache):
    comments = []
    new_cache = {}

    for file in pr.get_files():
        if not file.patch or file.status == 'removed':
            continue
        filename = file.filename
        reviewed_positions = set(cache.get(filename, []))
        new_cache[filename] = list(reviewed_positions)
        patch_lines = file.patch.split("\n")
        position = 0

        for line in patch_lines:
            position += 1
            if line.startswith("+") and not line.startswith("++"):
                if position not in reviewed_positions:
                    comments.append({
                        "path": filename,
                        "position": position,
                        "body": f"💡 Review suggestion by dhp-pr-review-bot: Consider reviewing this line."
                    })
                    new_cache[filename].append(position)
    return comments, new_cache
