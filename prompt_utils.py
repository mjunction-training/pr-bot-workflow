class PromptTemplates:
    """
    A class to hold various prompt templates for the AI model.
    """

    # Default template for the conversation chain, acting as a general instruction
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
        Ensure all sections are present, even if empty.
        For 'code_issues' and 'security_vulnerabilities', provide the 'line_number'
        relative to the *new* file content in the diff, if applicable.
        If a comment pertains to a deleted line, include it in the 'overall_review_comments'
        or as a general 'code_issue' without a specific line number, as direct line comments
        on deleted lines are not supported by the GitHub API's 'position' parameter.
        
        ```json
        {{
          "pr_summary": "Summary of the Pull Request.",
          "improvement_suggestions": [
            "Suggestion 1",
            "Suggestion 2"
          ],
          "code_issues": [
            {{
              "file": "path/to/file.py",
              "line_number": 123,
              "comment": "Line-specific comment about an issue.",
              "category": "Bug/Readability/Performance/Maintainability"
            }}
          ],
          "security_vulnerabilities": [
            {{
              "file": "path/to/file.py",
              "line_number": 45,
              "comment": "Security vulnerability description.",
              "severity": "High/Medium/Low",
              "category": "Injection/XSS/Auth/Misconfiguration"
            }}
          ],
          "overall_review_comments": "Overall summary comments for the PR review."
        }}
        ```
        
        Please ensure the JSON is valid and complete. If no issues or suggestions are found for a category,
        provide an empty array or an appropriate message in the string fields.
        """
