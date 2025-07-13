import boto3
from botocore.exceptions import ClientError


class KnowledgeBaseUtils:
    """
    A utility class for querying an existing AWS Bedrock Knowledge Base.
    """

    def __init__(self, bedrock_kb_id: str, bedrock_region: str, aws_access_key_id: str, aws_secret_access_key: str):
        """
        Initializes the KnowledgeBaseUtils with AWS Bedrock Knowledge Base details.

        Args:
            bedrock_kb_id (str): The ID of your existing AWS Bedrock Knowledge Base.
            bedrock_region (str): The AWS region where your Bedrock KB is deployed (e.g., 'us-east-1').
            aws_access_key_id (str): Your AWS Access Key ID.
            aws_secret_access_key (str): Your AWS Secret Access Key.
        """
        self.bedrock_kb_id = bedrock_kb_id
        self.bedrock_region = bedrock_region
        self.bedrock_agent_runtime_client = None
        self.bedrock_runtime_client = None  # Although not directly used for KB retrieval, often needed for LLM
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key

        self._initialize_bedrock_clients()

    def _initialize_bedrock_clients(self):
        """
        Initializes the boto3 Bedrock Agent Runtime client.
        """
        try:
            self.bedrock_agent_runtime_client = boto3.client(
                service_name='bedrock-agent-runtime',
                region_name=self.bedrock_region,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key
            )
            print(f"Bedrock Agent Runtime client initialized for region {self.bedrock_region}.")

            # Also initialize bedrock-runtime client, often useful for LLM invocation
            self.bedrock_runtime_client = boto3.client(
                service_name='bedrock-runtime',
                region_name=self.bedrock_region,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key
            )
            print(f"Bedrock Runtime client initialized for region {self.bedrock_region}.")

        except ClientError as e:
            print(f"Error initializing Bedrock clients: {e}")
            self.bedrock_agent_runtime_client = None
            self.bedrock_runtime_client = None
            raise

    def query_knowledge_base(self, query: str) -> str:
        """
        Retrieves relevant context from the AWS Bedrock Knowledge Base based on a query.

        Args:
            query (str): The query to search the knowledge base with.

        Returns:
            str: A formatted string of retrieved documents, or an empty string if retrieval fails.
        """
        if not self.bedrock_agent_runtime_client:
            print("Bedrock Agent Runtime client not initialized. Cannot query knowledge base.")
            return ""

        try:
            response = self.bedrock_agent_runtime_client.retrieve(
                knowledgeBaseId=self.bedrock_kb_id,
                retrievalQuery={
                    'text': query
                },
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': 3  # Retrieve top 3 relevant documents
                    }
                }
            )

            retrieved_docs = response.get('retrievalResults', [])
            context_parts = []
            for doc in retrieved_docs:
                content = doc.get('content', {}).get('text')
                if content:
                    context_parts.append(content)

            context = "\n\n".join(context_parts)
            print(f"Retrieved {len(retrieved_docs)} documents from Bedrock KB for query.")
            return context

        except ClientError as e:
            print(f"Error querying Bedrock Knowledge Base: {e}")
            return ""
        except Exception as e:
            print(f"An unexpected error occurred during Bedrock KB query: {e}")
            return ""

