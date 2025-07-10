import json
import boto3
from langchain_aws import ChatBedrock
from langchain_core.prompts import PromptTemplate
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferWindowMemory
from botocore.exceptions import ClientError
from prompt_utils import PromptTemplates # New import

class GenAIUtils:
    """
    A utility class for interacting with AWS Bedrock's GenAI models for PR reviews.
    It uses Langchain for conversation management and prompt engineering.
    """

    def __init__(self, knowledge_base_id: str, region_name: str = "us-east-1"):
        """
        Initializes the GenAIUtils with Bedrock client, Langchain components.

        Args:
            knowledge_base_id (str): The ID of the AWS Bedrock Knowledge Base.
            region_name (str): The AWS region where Bedrock is deployed.
        """
        self.knowledge_base_id = knowledge_base_id
        self.region_name = region_name
        self.bedrock_runtime_client = None
        self.llm = None
        self.conversation_chain = None
        self.memory = None

        self._initialize_bedrock_client()
        self._initialize_langchain()

    def _initialize_bedrock_client(self):
        """
        Initializes the boto3 Bedrock runtime client.
        """
        try:
            self.bedrock_runtime_client = boto3.client(
                "bedrock-runtime",
                region_name=self.region_name
            )
            print(f"Bedrock runtime client initialized for region: {self.region_name}")
        except ClientError as e:
            print(f"Error initializing Bedrock client: {e}")
            raise

    def _initialize_langchain(self):
        """
        Initializes Langchain components: LLM, memory, and conversation chain.
        """
        try:
            self.llm = ChatBedrock(
                model="anthropic.claude-3-sonnet-20240229-v1:0", # Use the appropriate model ID
                client=self.bedrock_runtime_client,
                model_kwargs={"temperature": 0.2, "max_tokens": 2048}
            )
            print("Langchain BedrockChat (Claude Sonnet) initialized.")

            self.memory = ConversationBufferWindowMemory(k=5)
            print("ConversationBufferWindowMemory initialized.")

            # Use the prompt template from PromptTemplates
            self.prompt = PromptTemplate(
                input_variables=["history", "input"],
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

    def _invoke_llm(self, input_text: str) -> str:
        """
        Invokes the LLM with the given input text and returns the response.
        This method uses the ConversationChain to manage memory.

        Args:
            input_text (str): The text to send to the LLM.

        Returns:
            str: The LLM's response.
        """
        try:
            response = self.conversation_chain.predict(input=input_text)
            return response
        except ClientError as e:
            print(f"Error invoking LLM: {e}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred during LLM invocation: {e}")
            raise

    def process_pr_chunk(self, file_name: str, file_content_chunk: str):
        """
        Processes a chunk of PR content by sending it to the LLM.
        The LLM's response will be stored in the conversation memory.

        Args:
            file_name (str): The name of the file being reviewed.
            file_content_chunk (str): A chunk of the file's content (e.g., a diff hunk).
        """
        print(f"Processing chunk for file: {file_name}")
        # Use the PR_CHUNK_REVIEW_TEMPLATE
        input_prompt = PromptTemplates.PR_CHUNK_REVIEW_TEMPLATE.format(
            file_name=file_name,
            file_content_chunk=file_content_chunk
        )
        self._invoke_llm(input_prompt)
        print(f"Chunk for {file_name} processed.")

    def get_final_review(self) -> dict:
        """
        Generates the final comprehensive PR review in JSON format.
        This method sends a final prompt to the LLM, asking it to synthesize
        all previous discussions and format the output as specified.

        Returns:
            dict: A dictionary containing the PR review details in JSON format.
        """
        print("Generating final PR review...")
        # Use the FINAL_REVIEW_JSON_TEMPLATE
        response_text = self._invoke_llm(PromptTemplates.FINAL_REVIEW_JSON_TEMPLATE)
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
                "improvement_suggestions": [],
                "code_issues": [],
                "security_vulnerabilities": [],
                "overall_review_comments": f"Failed to parse AI response: {e}. Raw response: {response_text[:500]}..."
            }
        except Exception as e:
            print(f"An unexpected error occurred while processing final review: {e}")
            return {
                "pr_summary": "Error: An unexpected error occurred during AI review.",
                "improvement_suggestions": [],
                "code_issues": [],
                "security_vulnerabilities": [],
                "overall_review_comments": f"Unexpected error: {e}"
            }
