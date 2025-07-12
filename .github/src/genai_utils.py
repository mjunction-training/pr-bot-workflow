import json

from pydantic import SecretStr
from langchain_openai import OpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferWindowMemory

from kb_utils import KnowledgeBaseUtils
from prompt_utils import PromptTemplates

class GenAIUtils:
    """
    A utility class for interacting with GenAI models for PR reviews.
    It uses Langchain for conversation management, prompt engineering,
    and integrates a local knowledge base for context.
    """

    def __init__(self, samples_dir: str, openai_api_key: str, model_name: str):
        """
        Initializes the GenAIUtils with Langchain components and Knowledge Base.

        Args:
            samples_dir (str): Path to the directory containing sample code for the KB.
            openai_api_key (str): API key for OpenAI (used for embeddings in KB and the main LLM).
            model_name (str): The name of the LLM model to use (e.g., 'text-davinci-003').
        """
        self.llm = None
        self.conversation_chain = None
        self.memory = None
        self.knowledge_base = None
        self.openai_api_key = openai_api_key
        self.model_name = model_name

        self.knowledge_base = KnowledgeBaseUtils(samples_dir, openai_api_key)
        if self.knowledge_base.vector_store:
            print("KnowledgeBaseUtils initialized and vector store created.")
        else:
            print("KnowledgeBaseUtils initialized, but no vector store created (e.g., samples dir not found).")

        self._initialize_langchain(openai_api_key, model_name)


    def _retrieve_context(self, query: str) -> str:
        """
        Retrieves relevant context from the knowledge base based on a query.

        Args:
            query (str): The query to search the knowledge base with.

        Returns:
            str: A formatted string of retrieved documents, or an empty string if no KB.
        """
        if not self.knowledge_base:
            return ""
        return self.knowledge_base.query_knowledge_base(query)

    def _initialize_langchain(self, openai_api_key: str, model_name: str):
        """
        Initializes Langchain components: LLM, memory, and conversation chain.
        """
        try:
            # Initialize OpenAI (for completion models) with the provided model name and API key
            self.llm = OpenAI(
                model=model_name,
                api_key=SecretStr(openai_api_key), # Use api_key for OpenAI
                temperature=0.2,
                max_tokens=2048
            )
            print(f"Langchain OpenAI ({model_name}) initialized.")

            # Using ConversationBufferWindowMemory. It will automatically manage ChatMessageHistory.
            # k=5 means it will keep a window of the last 5 exchanges (input/output pairs)
            self.memory = ConversationBufferWindowMemory(k=5)
            print("ConversationBufferWindowMemory initialized.")

            # Use the prompt template from PromptTemplates, including context placeholder
            self.prompt = PromptTemplate(
                input_variables=["history", "input", "context"],
                template=PromptTemplates.DEFAULT_CONVERSATION_TEMPLATE
            )
            print("PromptTemplate initialized.")

            self.conversation_chain = ConversationChain(
                llm=self.llm,
                memory=self.memory,
                prompt=self.prompt,
                verbose=False
            )
            print("ConversationChain initialized.")

        except Exception as e:
            print(f"Error initializing Langchain components: {e}")
            raise

    def _invoke_llm(self, input_text: str, context: str = "") -> str:
        """
        Invokes the LLM with the given input text and returns the response.
        This method uses the ConversationChain to manage memory and includes KB context.

        Args:
            input_text (str): The text to send to the LLM.
            context (str): Relevant context retrieved from the knowledge base.

        Returns:
            str: The LLM's response.
        """
        try:
            response = self.conversation_chain.predict(input=input_text, context=context)
            return response
        except Exception as e:
            print(f"An unexpected error occurred during LLM invocation: {e}")
            raise

    def process_pr_chunk(self, file_name: str, file_content_chunk: str):
        """
        Processes a chunk of PR content by sending it to the LLM.
        The LLM's response will be stored in the conversation memory.
        Relevant knowledge base context is retrieved and included.

        Args:
            file_name (str): The name of the file being reviewed.
            file_content_chunk (str): A chunk of the file's content (e.g., a diff hunk).
        """

        print(f"Processing chunk for file: {file_name}")
        kb_context = self._retrieve_context(file_content_chunk)
        input_prompt = PromptTemplates.PR_CHUNK_REVIEW_TEMPLATE.format(
            file_name=file_name,
            file_content_chunk=file_content_chunk
        )
        self._invoke_llm(input_prompt, context=kb_context)
        print(f"Chunk for {file_name} processed.")

    def get_final_review(self) -> dict:
        """
        Generates the final comprehensive PR review in JSON format.
        This method sends a final prompt to the LLM, asking it to synthesize
        all previous discussions and format the output as specified.
        It also includes overall knowledge base context.

        Returns:
            dict: A dictionary containing the PR review details in JSON format.
        """
        print("Generating final PR review...")
        response_text = self._invoke_llm(PromptTemplates.FINAL_REVIEW_JSON_TEMPLATE, context="")
        print("Final review generated. Attempting to parse JSON.")

        try:
            json_start = response_text.find("```json")
            json_end = response_text.rfind("```")

            if json_start != -1 and json_end != -1 and json_end > json_start:
                json_string = response_text[json_start + len("```json"):json_end].strip()
            else:
                json_string = response_text.strip()

            review_json = json.loads(json_string)
            print("JSON parsed successfully.")
            return review_json
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {e}")
            print(f"Raw response text: {response_text}")
            return {
                "pr_summary": "Error: Could not parse AI review. Please check logs.",
                "overall_review_comments": f"Failed to parse AI response: {e}. Raw response: {response_text[:500]}...",
                "file_reviews": [],
                "line_comments": []
            }
        except Exception as e:
            print(f"An unexpected error occurred while processing final review: {e}")
            return {
                "pr_summary": "Error: An unexpected error occurred during AI review.",
                "overall_review_comments": f"Unexpected error: {e}",
                "file_reviews": [],
                "line_comments": []
            }

