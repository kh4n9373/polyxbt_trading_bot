# Kafka topic
KAORI_NEW_TOPIC = "trading-view-news-kaori"
KAORI_IDEA_TOPIC = "trading-view-ideas-kaori"
KAORI_CMC_NEWS_TOPIC = "coinmarketcap-gaming-news-kaori"

ECONOMY_NEW_TOPIC = "trading-view-news-economy"
REDDIT_MEME_TOPIC = "reddit-post-for-agent-memes"

POLYMARKET_EVENTS_TOPIC = "polymarket-all-events"

POLYMARKET_END_EVENTS_TOPIC = "polymarket-end-events"

DEGENERATOR_MENTION_TOPIC = "degenerator_mentions"

COMMON_SUBSCRIBE_TOPICS = [
    KAORI_NEW_TOPIC,
    KAORI_IDEA_TOPIC,
    KAORI_CMC_NEWS_TOPIC,
    ECONOMY_NEW_TOPIC,
]

MEME_SUBSCRIBE_TOPICS = [REDDIT_MEME_TOPIC]

POLYMARKET_SUBSCRIBE_TOPICS = [POLYMARKET_EVENTS_TOPIC, POLYMARKET_END_EVENTS_TOPIC]

DEGENERATOR_SUBSCRIBE_TOPICS = [DEGENERATOR_MENTION_TOPIC]

# Mapping kafka topic to database collection
TOPIC_TABLE_MAPPING = {
    # Common agents topic
    KAORI_NEW_TOPIC: "trading_view_news",
    KAORI_IDEA_TOPIC: "trading_view_ideas",
    KAORI_CMC_NEWS_TOPIC: "cmc_news",
    ECONOMY_NEW_TOPIC: "trading_view_news",

    # Meme topic
    REDDIT_MEME_TOPIC: "reddit_post_for_agents",

    # Polymarket topic
    POLYMARKET_EVENTS_TOPIC: "polymarket_events",
    
    # Degenerator topic
    DEGENERATOR_MENTION_TOPIC: "distilled_twitter_mentions"
}

# Consummed polymarket events
CONSUMMED_POLYMARKET_EVENTS = "consummed_polymarket_events"

# Mongo distilled database
DISTILLED_DATABASE_NAME = "distilled"
DISTILLED_TEST_DATABASE_NAME = "test"

# Mongo distilled collection
DISTILLED_GENERATE_MEME_IDEAS_COLLECTION = "generated_meme_ideas"
DISTILLED_POLYMARKET_EVENTS_COLLECTION = "polymarket-events"
DISTILLED_TWITTER_MENTION_COLLECTION = "distilled_twitter_mentions"

# Chromadb collection name
CHROMADB_POLYMARKET_COLLECTION = "Polymarket"
CHROMADB_NEWS_COLLECTION = "News"
