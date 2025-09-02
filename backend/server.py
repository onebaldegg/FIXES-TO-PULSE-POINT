from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from emergentintegrations.llm.chat import LlmChat, UserMessage


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class SentimentRequest(BaseModel):
    text: str

class SentimentResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    sentiment: str  # positive, negative, neutral
    confidence: float
    analysis: str
    emotions: Optional[dict] = {}  # {"joy": 0.8, "anger": 0.1, etc.}
    dominant_emotion: Optional[str] = ""  # Primary emotion detected
    sarcasm_detected: Optional[bool] = False  # Whether sarcasm is detected
    sarcasm_confidence: Optional[float] = 0.0  # Confidence of sarcasm detection (0-1)
    sarcasm_explanation: Optional[str] = ""  # Explanation of detected sarcasm
    adjusted_sentiment: Optional[str] = ""  # Sentiment after considering sarcasm
    sarcasm_indicators: Optional[List[str]] = []  # Specific phrases suggesting sarcasm
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SentimentAnalysis(BaseModel):
    id: str
    text: str
    sentiment: str
    confidence: float
    analysis: str
    emotions: Optional[dict] = {}
    dominant_emotion: Optional[str] = ""
    sarcasm_detected: Optional[bool] = False
    sarcasm_confidence: Optional[float] = 0.0
    sarcasm_explanation: Optional[str] = ""
    adjusted_sentiment: Optional[str] = ""
    sarcasm_indicators: Optional[List[str]] = []
    timestamp: datetime


# Sentiment Analysis Service
async def analyze_sentiment(text: str) -> dict:
    """Analyze sentiment, emotions, and sarcasm using LLM"""
    try:
        # Initialize LLM chat
        chat = LlmChat(
            api_key=os.environ.get('EMERGENT_LLM_KEY'),
            session_id=f"sentiment_{uuid.uuid4()}",
            system_message="""You are an expert sentiment, emotion, and sarcasm analysis AI specialized in PR and marketing text analysis. 

            Analyze the provided text and return ONLY a valid JSON response with these exact fields:
            {
                "sentiment": "positive" | "negative" | "neutral",
                "confidence": 0.85,
                "analysis": "Brief explanation of the sentiment and key factors",
                "emotions": {
                    "joy": 0.8,
                    "sadness": 0.1,
                    "anger": 0.0,
                    "fear": 0.0,
                    "trust": 0.7,
                    "disgust": 0.0,
                    "surprise": 0.3,
                    "anticipation": 0.5
                },
                "dominant_emotion": "joy",
                "sarcasm_detected": true,
                "sarcasm_confidence": 0.85,
                "sarcasm_explanation": "Text uses ironic language that contradicts surface meaning",
                "adjusted_sentiment": "negative",
                "sarcasm_indicators": ["great", "just what I needed"]
            }
            
            Rules:
            - sentiment must be exactly "positive", "negative", or "neutral" (surface-level sentiment)
            - confidence must be a number between 0 and 1
            - analysis should be 1-2 sentences explaining the sentiment, emotions, and sarcasm if detected
            - emotions: Use Plutchik's 8 basic emotions, each scored 0-1
            - dominant_emotion: The emotion with the highest score
            - sarcasm_detected: true if irony/sarcasm is present, false otherwise
            - sarcasm_confidence: 0-1 confidence in sarcasm detection
            - sarcasm_explanation: Brief explanation of why text is sarcastic (empty if no sarcasm)
            - adjusted_sentiment: The true sentiment after considering sarcasm (same as sentiment if no sarcasm)
            - sarcasm_indicators: Array of specific words/phrases that suggest sarcasm (empty if no sarcasm)
            - Return ONLY the JSON, no other text
            
            Sarcasm Detection Guidelines:
            - Look for phrases like "Oh great", "Just perfect", "Thanks a lot"
            - Identify quotation marks around positive words in negative contexts
            - Detect exaggerated praise that seems insincere
            - Watch for contradictions between tone and context
            - Consider timing phrases like "just what I needed" in frustrating situations"""
        ).with_model("openai", "gpt-4o-mini")
        
        # Create user message
        user_message = UserMessage(text=f"Analyze the sentiment, emotions, and potential sarcasm of this text: {text}")
        
        # Get response
        response = await chat.send_message(user_message)
        
        # Parse JSON response
        import json
        try:
            result = json.loads(response)
            
            # Ensure emotions dictionary exists and has all 8 emotions
            if "emotions" not in result:
                result["emotions"] = {}
            
            # Default emotion values
            default_emotions = {
                "joy": 0.0, "sadness": 0.0, "anger": 0.0, "fear": 0.0,
                "trust": 0.0, "disgust": 0.0, "surprise": 0.0, "anticipation": 0.0
            }
            
            # Merge with detected emotions
            for emotion in default_emotions:
                if emotion not in result["emotions"]:
                    result["emotions"][emotion] = 0.0
            
            # Find dominant emotion
            if result["emotions"]:
                dominant_emotion = max(result["emotions"], key=result["emotions"].get)
                result["dominant_emotion"] = dominant_emotion
            else:
                result["dominant_emotion"] = "neutral"
            
            # Ensure sarcasm fields exist with defaults
            if "sarcasm_detected" not in result:
                result["sarcasm_detected"] = False
            if "sarcasm_confidence" not in result:
                result["sarcasm_confidence"] = 0.0
            if "sarcasm_explanation" not in result:
                result["sarcasm_explanation"] = ""
            if "adjusted_sentiment" not in result:
                result["adjusted_sentiment"] = result["sentiment"]  # Same as sentiment if no sarcasm
            if "sarcasm_indicators" not in result:
                result["sarcasm_indicators"] = []
            
            return result
            
        except json.JSONDecodeError:
            # Fallback parsing if response is not pure JSON
            response_lower = response.lower()
            if "positive" in response_lower:
                sentiment = "positive"
            elif "negative" in response_lower:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            # Basic sarcasm detection from keywords
            sarcasm_keywords = ["oh great", "just perfect", "thanks a lot", "wonderful", "fantastic", "just what i needed"]
            sarcasm_detected = any(keyword in response_lower for keyword in sarcasm_keywords)
            
            # Basic emotion detection from keywords
            emotions = {
                "joy": 0.7 if any(word in response_lower for word in ["joy", "happy", "excited", "pleased"]) else 0.0,
                "sadness": 0.6 if any(word in response_lower for word in ["sad", "disappointed", "sorrow"]) else 0.0,
                "anger": 0.6 if any(word in response_lower for word in ["angry", "frustrated", "annoyed"]) else 0.0,
                "fear": 0.5 if any(word in response_lower for word in ["fear", "worried", "anxious"]) else 0.0,
                "trust": 0.6 if any(word in response_lower for word in ["trust", "confident", "reliable"]) else 0.0,
                "disgust": 0.5 if any(word in response_lower for word in ["disgusted", "revolting"]) else 0.0,
                "surprise": 0.5 if any(word in response_lower for word in ["surprised", "shocked", "amazed"]) else 0.0,
                "anticipation": 0.5 if any(word in response_lower for word in ["excited", "anticipation", "expecting"]) else 0.0,
            }
                
            return {
                "sentiment": sentiment,
                "confidence": 0.75,
                "analysis": "Sentiment, emotion, and sarcasm analysis completed based on text content.",
                "emotions": emotions,
                "dominant_emotion": max(emotions, key=emotions.get) if emotions else "neutral",
                "sarcasm_detected": sarcasm_detected,
                "sarcasm_confidence": 0.7 if sarcasm_detected else 0.0,
                "sarcasm_explanation": "Detected potential sarcastic language patterns" if sarcasm_detected else "",
                "adjusted_sentiment": "negative" if sarcasm_detected and sentiment == "positive" else sentiment,
                "sarcasm_indicators": [kw for kw in sarcasm_keywords if kw in response_lower] if sarcasm_detected else []
            }
            
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        default_emotions = {
            "joy": 0.0, "sadness": 0.0, "anger": 0.0, "fear": 0.0,
            "trust": 0.0, "disgust": 0.0, "surprise": 0.0, "anticipation": 0.0
        }
        return {
            "sentiment": "neutral",
            "confidence": 0.5,
            "analysis": f"Error in analysis: {str(e)}",
            "emotions": default_emotions,
            "dominant_emotion": "neutral",
            "sarcasm_detected": False,
            "sarcasm_confidence": 0.0,
            "sarcasm_explanation": "",
            "adjusted_sentiment": "neutral",
            "sarcasm_indicators": []
        }


# API Routes
@api_router.get("/")
async def root():
    return {"message": "Brand Watch AI Sentiment Analysis API"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

@api_router.post("/analyze-sentiment", response_model=SentimentResponse)
async def analyze_text_sentiment(request: SentimentRequest):
    """Analyze sentiment of provided text"""
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Perform sentiment analysis
        analysis_result = await analyze_sentiment(request.text)
        
        # Create response
        response = SentimentResponse(
            text=request.text,
            sentiment=analysis_result["sentiment"],
            confidence=analysis_result["confidence"],
            analysis=analysis_result["analysis"],
            emotions=analysis_result.get("emotions", {}),
            dominant_emotion=analysis_result.get("dominant_emotion", ""),
            sarcasm_detected=analysis_result.get("sarcasm_detected", False),
            sarcasm_confidence=analysis_result.get("sarcasm_confidence", 0.0),
            sarcasm_explanation=analysis_result.get("sarcasm_explanation", ""),
            adjusted_sentiment=analysis_result.get("adjusted_sentiment", analysis_result["sentiment"]),
            sarcasm_indicators=analysis_result.get("sarcasm_indicators", [])
        )
        
        # Store in database
        response_dict = response.dict()
        response_dict['timestamp'] = response_dict['timestamp'].isoformat()
        await db.sentiment_analyses.insert_one(response_dict)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in sentiment analysis endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.get("/sentiment-history", response_model=List[SentimentAnalysis])
async def get_sentiment_history(limit: int = 20):
    """Get recent sentiment analysis history"""
    try:
        analyses = await db.sentiment_analyses.find().sort("timestamp", -1).limit(limit).to_list(limit)
        return [SentimentAnalysis(**analysis) for analysis in analyses]
    except Exception as e:
        logger.error(f"Error fetching sentiment history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()