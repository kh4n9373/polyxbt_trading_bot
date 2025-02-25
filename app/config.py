import os
from dotenv import load_dotenv

load_dotenv(override=True)

                
class Settings:
    def __init__(self):
        self.mongo_distilled_connection = os.getenv("MONGO_CONNECTION")
        self.DISTILLED_SIGN_URL_S3_KEY = os.getenv("DISTILLED_SIGN_URL_S3_KEY")

        self.kafka_server = os.getenv("kafka_server")
        self.kafka_password = os.getenv("kafka_password")

        self.encoder_inference_url = os.getenv("encoder_endpoint")
        self.encoder_model = "distilled_encoder"

        self.chroma_endpoint = os.getenv("chroma_client_url")
        self.together_api_key = os.getenv("TOGETHER_AI_API_KEY")
        self.split_sys_prompt = """Given the article title and its content, break it down into smaller, engaging paragraphs. Each paragraph should represent a distinct event.
Use specific details from the article to craft each event along with its description, ensuring the insights are thought-provoking.

Structure the response as a json list of dictionaries like below template, say nothing else: 
[
    {
        "event_name": "<name of the event>",
        "event_description": "<detailed description of the event>"
    }
]
Ensure each event is clearly introduced and offers an angle for readers to consider."""

        self.entities_sys_prompt = """
You are an entity extractor from a piece of information about cryptocurrency.
You will be given a dictionaries containing the name of events ("event_name" field) and their description ("description" field), your task is to extract the mentioned entities in that information.
The entities mentioned should be economic entities like coin names, government agencies, companies.
Structure the response as a json list of dictionaries like below template, say nothing else: 
[
    {
        "entities": "<list of entities, each is string, extracted from the provided information>"
    }
]
Ensure each event is clearly introduced and offers an angle for readers to consider."""

        self.topic_sys_prompt = """
You are an topic extractor from a piece of information about cryptocurrency.
You will be given a dictionaries containing the name of event ("event_name" field) and their description ("description" field)  your task is to extract the topics of that information. A topic only have one word or a concept.
Structure the response as a json list of dictionaries like below template, say nothing else: 
[
    {
        "topics": "<list of topics, each is string, extracted from the provided information>"
    }
]
Ensure each event is clearly introduced and offers an angle for readers to consider."""
        self.sentiment_sys_prompt = """
You are an sentiment extractor from a piece of information about cryptocurrency.
You will be given a dictionaries containing the name of event ("event_name" field) and their description ("description" field), and their entities ("entities" field) your task is to extract the main sentiment of that information for each entities (positive, neutral or negative).
Structure the response as a json list of dictionaries like below template, say nothing else: 
[
    {
        "sentiment": "<dictionary with key is entities, values for each entities are the sentiment extracted for that entitiy. Three sentiment values are allowed : (positive, neutral, negative)>"
    }
]
Ensure each event is clearly introduced and offers an angle for readers to consider."""
        self.is_ai_split = os.getenv("AI_SPLIT", True)
        self.sumup_model = os.getenv("SUMUP_MODEL")
        self.extract_prediction_model = os.getenv("EXTRACT_PREDICTION_MODEL")
        self.google_search_url = os.getenv("GOOGLE_SEARCH_URL")
        self.agent_base_url = os.getenv("AGENT_BASE_URL")
        self.agent_api_key = os.getenv("AGENT_API_KEY")

        self.poly_predictions_collection_name = "polymarket_predictions"
        self.poly_predictions_test_collection_name = "test_polymarket_predictions"
        self.poly_events_collection_name = "polymarket_events"
        self.test_db_name = "test"
        self.test_collection_name = "test-polymarket-predictions"
        self.poly_risk_threshold = os.getenv("POLY_RISK_THRESHOLD")

        self.discord_url = os.getenv("DISCORD_WEBHOOK_URL")
        self.discord_errors_url = os.getenv("DISCORD_WEBHOOK_ERRORS_URL")
        self.poly_content_discord_webhook_url = os.getenv("POLY_CONTENT_DISCORD_WEBHOOK_URL")
        self.volume_threshold_to_send_noti = float(os.getenv("VOLUME_THRESHOLD_TO_SEND_NOTI"))
        self.poly_win_loss_discord_webhook_url = os.getenv("POLY_WIN_LOSS_DISCORD_WEBHOOK_URL")

settings = Settings()