class PromptTemplates:
    """
    A class to hold various prompt templates for the AI model.
    """

    # Default template for the conversation chain, acting as a general instruction
    # Removed {context} from here; it will be prepended to input in genai_utils.py
    DEFAULT_CONVERSATION_TEMPLATE = """The following is a conversation between a human and an AI assistant.
        The AI assistant is an expert code reviewer and security analyst. It provides constructive feedback,
        identifies potential issues, suggests improvements, and points out security vulnerabilities.

        Current conversation:
        {history}
        Human: {input}
        AI:"""

            # Template for processing individual PR file chunks
    PR_CHUNK_REVIEW_TEMPLATE = """Review the following code chunk from file '{file_name}'.
        This chunk is part of a larger Pull Request. Focus on immediate observations,
        potential issues, or areas for improvement related to this specific chunk.
        Identify any security vulnerabilities, code quality issues, or suggestions for refactoring.
        If lines are added, comment on the new code. If lines are deleted, consider if the deletion
        introduces new issues or if the old code had issues that are now removed (and if that's good/bad).

        Code Chunk:
        ```
        {file_content_chunk}
        ```
        Provide your observations for this chunk. Do not provide a final summary yet."""

    # Template for generating the final comprehensive PR review in JSON format
    FINAL_REVIEW_JSON_TEMPLATE = """Based on our conversation about the Pull Request content,
        please provide a comprehensive review in the following JSON format.
        Ensure all sections are present, even if empty arrays or empty strings.

        For 'line_comments':
        - 'diff_line_number': This MUST be the line number within the *diff hunk* itself,
          relative to the start of the hunk. For example, if a hunk starts at line 100 in the file,
          and the change is on the 5th line of the hunk, 'diff_line_number' would be 5.
          This corresponds to GitHub's 'position' parameter.
        - 'side': This MUST be 'LEFT' for lines that were deleted (prefixed with '-') or 'RIGHT' for lines
          that were added (prefixed with '+') or modified (context lines in a diff, or lines that appear
          in the new file).

        ```json
        {{
          "pr_summary": "Overall summary of the Pull Request.",
          "overall_review_comments": "General comments about the PR as a whole.",
          "file_reviews": [
            {{
              "file_path": "path/to/file1.py",
              "file_summary": "Consolidated summary comment for file1.py. This should include a high-level overview of changes in this file and overall quality.",
              "security_vulnerabilities": {{
                "high": [
                  {{"description": "Description of high severity vulnerability.", "example": "```python\\nproblematic_code()\\n```", "recommendation": "```python\\nfixed_code()\\n```"}}
                ],
                "medium": [
                  {{"description": "Description of medium severity vulnerability.", "example": "```javascript\\nproblematic_code();\\n```", "recommendation": "```javascript\\nfixed_code();\\n```"}}
                ],
                "low": [
                  {{"description": "Description of low severity vulnerability.", "example": "```sql\\nproblematic_query;\\n```", "recommendation": "```sql\\nfixed_query;\\n```"}}
                ]
              }},
              "other_code_issues": [
                {{"description": "Description of a code quality issue (e.g., readability, performance, maintainability).", "example": "```python\\nold_code\\n```", "recommendation": "```python\\nnew_code\\n```"}}
              ],
              "improvement_suggestions": [
                {{"description": "Description of a suggested improvement (e.g., refactoring, better pattern).", "example": "```python\\ncurrent_approach\\n```", "recommendation": "```python\\nimproved_approach\\n```"}}
              ]
            }}
          ],
          "line_comments": [
            {{
              "file_path": "path/to/file1.py",
              "diff_line_number": 15,
              "side": "RIGHT",
              "comment": "Specific comment for this added/modified line.",
              "category": "Code Issue"
            }},
            {{
              "file_path": "path/to/file2.js",
              "diff_line_number": 8,
              "side": "LEFT",
              "comment": "Specific comment for this deleted line.",
              "category": "Security Vulnerability"
            }}
          ]
        }}
        ```

        Please ensure the JSON is valid and complete. If no issues or suggestions are found for a category,
        provide an empty array or an appropriate message in the string fields.
        """

