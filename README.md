# **PR Review Bot**

This repository contains a GitHub Action-powered bot that automates Pull Request reviews using a Large Language Model (LLM). The bot provides comprehensive feedback, identifies potential issues, suggests improvements, and highlights security vulnerabilities directly within your GitHub Pull Requests.

## **Description**

The PR Review Bot is designed to streamline the code review process by leveraging AI capabilities. When a pull request is created or a review is requested, the bot analyzes the code changes, generates a detailed review, and posts it as a GitHub PR comment. It integrates with a local knowledge base to provide context-aware suggestions and maintains conversation memory for more cohesive reviews.

## **Features**

* **Automated PR Reviews:** Automatically reviews pull requests upon creation or review request.  
* **Comprehensive Feedback:** Provides summaries, overall comments, file-specific reviews, and line-level comments.  
* **Security Vulnerability Detection:** Identifies potential security risks in the code.  
* **Code Quality & Improvement Suggestions:** Offers recommendations for code quality, readability, performance, and refactoring.  
* **Knowledge Base Integration:** Uses a local FAISS knowledge base to provide contextually relevant suggestions based on your project's sample code.  
* **Conversation Memory:** Maintains a conversation history with the LLM for more coherent and context-aware reviews across multiple code chunks.  
* **Configurable LLM:** Supports using OpenAI completion models with an API key and configurable model name.

## **Setup**

To set up and run the PR Review Bot, follow these steps:

### **1\. Environment Variables**

The bot requires several environment variables to be set in your GitHub Actions workflow secrets or environment.

* GITHUB\_TOKEN: A GitHub Personal Access Token with repo scope (for private repositories) or public\_repo (for public repositories). This token is used to interact with the GitHub API (e.g., fetching PR details, posting comments). GitHub Actions typically provides a default secrets.GITHUB\_TOKEN.  
* OPENAI\_API\_KEY: Your OpenAI API key. This is used for both the LLM calls (if using an OpenAI model) and for generating embeddings for the local knowledge base.  
* LLM\_MODEL\_NAME: (Optional) The name of the OpenAI completion model you wish to use (e.g., text-davinci-003, gpt-3.5-turbo-instruct). If not provided, it defaults to gpt-4o (though OpenAI class is used, ensure the model supports completion if gpt-4o causes issues).  
* REPO: The full repository name (e.g., owner/repo). This is usually provided by GitHub Actions as github.repository.  
* PR\_NUMBER: The Pull Request number. This is usually provided by GitHub Actions as github.event.pull\_request.number.

### **2\. Dependencies**

The Python dependencies are listed in requirements.txt. Install them using pip:

pip install \-r requirements.txt

### **3\. Knowledge Base Samples**

The bot uses a local knowledge base for context. Create a directory named .github/samples in your repository and place relevant code samples (e.g., best practices, common patterns, existing code) as .txt files within it. The bot will build a FAISS index from these files.

.github/  
└── samples/  
    ├── my\_project\_standards.txt  
    └── utility\_functions\_example.txt

### **4\. GitHub Workflow (.github/workflows/pr-review.yml)**

Create a GitHub Actions workflow file (e.g., .github/workflows/pr-review.yml) to trigger the bot.

name: PR Review Bot

on:  
  pull\_request:  
    types: \[review\_requested\] \# Trigger when a review is requested

jobs:  
  review:  
    if: |  
      contains(github.event.requested\_reviewer.login, 'dhp-pr-review-bot') ||  
      contains(github.event.requested\_team.name, 'dhp-pr-review-bot')  
    runs-on: ubuntu-latest

    steps:  
      \- name: Checkout code  
        uses: actions/checkout@v4

      \- name: Set up Python  
        uses: actions/setup-python@v5  
        with:  
          python-version: '3.12' \# Or your preferred Python version

      \- name: Install dependencies  
        run: pip install \-r requirements.txt

      \- name: Create samples directory for KB  
        run: mkdir \-p .github/samples \# Ensure this directory exists for the KB

      \- name: Run PR Review  
        env:  
          GITHUB\_TOKEN: ${{ secrets.GITHUB\_TOKEN }}  
          PR\_NUMBER: ${{ github.event.pull\_request.number }}  
          REPO: ${{ github.repository }}  
          OPENAI\_API\_KEY: ${{ secrets.OPENAI\_API\_KEY }} \# Your OpenAI API Key  
          \# LLM\_MODEL\_NAME: "text-davinci-003" \# Uncomment and set if you want a specific non-chat OpenAI model  
        run: python pr\_review\_bot.py

### **5\. Bot User**

Ensure the BOT\_USER variable in pr\_review\_bot.py matches the GitHub username of your bot account (e.g., dhp-pr-review-bot). This bot user should be added as a requested reviewer to trigger the action.

## **Usage**

1. **Create a Pull Request:** Open a pull request in your repository.  
2. **Request Review:** Request a review from the bot user (e.g., dhp-pr-review-bot).  
3. **Monitor GitHub Actions:** The GitHub Action will run, and the bot will post its review comments directly on the pull request.

## **File Structure**

* pr\_review\_bot.py: The main entry point for the bot. Orchestrates the review process.  
* github\_utils.py: Handles interactions with the GitHub API (fetching PR details, managing files).  
* genai\_utils.py: Manages the LLM interaction, conversation memory, and knowledge base integration.  
* kb\_utils.py: Utility for creating, loading, and querying the local FAISS knowledge base.  
* comment\_utils.py: Contains logic for formatting and posting review comments to GitHub.  
* prompt\_utils.py: Stores various prompt templates used by the LLM.  
* requirements.txt: Lists all Python dependencies.  
* .github/workflows/pr-review.yml: GitHub Actions workflow definition.  
* .github/samples/: Directory for knowledge base sample files.

## **License**

This project is open-sourced under the MIT License.