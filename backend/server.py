from fastapi import FastAPI, APIRouter, HTTPException, File, UploadFile
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
import pandas as pd
import PyPDF2
import io
import tempfile
import json


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
    topics_detected: Optional[List[dict]] = []  # Array of detected topics with confidence
    primary_topic: Optional[str] = ""  # Topic with highest confidence
    topic_summary: Optional[str] = ""  # AI explanation of detected topics
    aspects_analysis: Optional[List[dict]] = []  # Array of aspect-sentiment pairs
    aspects_summary: Optional[str] = ""  # Summary of aspect-based insights
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
    topics_detected: Optional[List[dict]] = []
    primary_topic: Optional[str] = ""
    topic_summary: Optional[str] = ""
    aspects_analysis: Optional[List[dict]] = []
    aspects_summary: Optional[str] = ""
    timestamp: datetime

class FileUploadResponse(BaseModel):
    file_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    file_type: str
    total_entries: int
    extracted_texts: List[dict]  # [{text: str, row_number: int, metadata: dict}]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BatchAnalysisRequest(BaseModel):
    file_id: str
    texts: List[dict]  # [{text: str, row_number: int, metadata: dict}]

class BatchAnalysisResponse(BaseModel):
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file_id: str
    filename: str
    total_processed: int
    results: List[dict]  # List of sentiment analysis results with metadata
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# File Processing Utilities
async def extract_text_from_file(file: UploadFile) -> List[dict]:
    """Extract text from uploaded files based on file type"""
    file_extension = file.filename.split('.')[-1].lower()
    extracted_texts = []
    
    try:
        if file_extension == 'txt':
            # Process TXT files
            content = await file.read()
            text_content = content.decode('utf-8')
            lines = text_content.split('\n')
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if line:  # Skip empty lines
                    extracted_texts.append({
                        "text": line,
                        "row_number": i,
                        "metadata": {"source": "txt_line"}
                    })
                    
        elif file_extension == 'csv':
            # Process CSV files
            content = await file.read()
            df = pd.read_csv(io.BytesIO(content))
            
            # Try to find text columns (columns with string data)
            text_columns = []
            for col in df.columns:
                if df[col].dtype == 'object':  # String columns
                    text_columns.append(col)
            
            # Use first text column or all columns if no clear text column
            if text_columns:
                primary_text_col = text_columns[0]
            else:
                primary_text_col = df.columns[0]
            
            for index, row in df.iterrows():
                text_content = str(row[primary_text_col])
                if text_content and text_content != 'nan':
                    metadata = {col: str(row[col]) for col in df.columns if col != primary_text_col}
                    extracted_texts.append({
                        "text": text_content,
                        "row_number": index + 2,  # +2 because pandas starts at 0 and we account for header
                        "metadata": metadata
                    })
                    
        elif file_extension in ['xlsx', 'xls']:
            # Process Excel files
            content = await file.read()
            df = pd.read_excel(io.BytesIO(content))
            
            # Similar logic to CSV
            text_columns = []
            for col in df.columns:
                if df[col].dtype == 'object':
                    text_columns.append(col)
            
            if text_columns:
                primary_text_col = text_columns[0]
            else:
                primary_text_col = df.columns[0]
            
            for index, row in df.iterrows():
                text_content = str(row[primary_text_col])
                if text_content and text_content != 'nan':
                    metadata = {col: str(row[col]) for col in df.columns if col != primary_text_col}
                    extracted_texts.append({
                        "text": text_content,
                        "row_number": index + 2,
                        "metadata": metadata
                    })
                    
        elif file_extension == 'pdf':
            # Process PDF files
            content = await file.read()
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                text_content = page.extract_text().strip()
                if text_content:
                    # Split into paragraphs for better analysis
                    paragraphs = [p.strip() for p in text_content.split('\n\n') if p.strip()]
                    for para_num, paragraph in enumerate(paragraphs, 1):
                        if len(paragraph) > 10:  # Only process substantial text
                            extracted_texts.append({
                                "text": paragraph,
                                "row_number": f"page_{page_num}_para_{para_num}",
                                "metadata": {"source": f"PDF page {page_num}"}
                            })
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_extension}")
            
        return extracted_texts
        
    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

# Sentiment Analysis Service
async def analyze_sentiment(text: str) -> dict:
    """Analyze sentiment, emotions, sarcasm, and topics using LLM"""
    try:
        # Initialize LLM chat
        chat = LlmChat(
            api_key=os.environ.get('EMERGENT_LLM_KEY'),
            session_id=f"sentiment_{uuid.uuid4()}",
            system_message="""You are an expert sentiment, emotion, sarcasm, topic, and aspect-based analysis AI specialized in PR and marketing text analysis. 

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
                "sarcasm_indicators": ["great", "just what I needed"],
                "topics_detected": [
                    {
                        "topic": "customer_service",
                        "display_name": "Customer Service",
                        "confidence": 0.90,
                        "keywords": ["support", "help", "service"]
                    },
                    {
                        "topic": "product_quality", 
                        "display_name": "Product Quality",
                        "confidence": 0.75,
                        "keywords": ["quality", "build", "materials"]
                    }
                ],
                "primary_topic": "customer_service",
                "topic_summary": "Discussion focuses on customer service experience with secondary mentions of product quality",
                "aspects_analysis": [
                    {
                        "aspect": "Food Quality",
                        "sentiment": "positive",
                        "confidence": 0.90,
                        "keywords": ["delicious", "amazing", "great taste"],
                        "explanation": "Customer praised the taste and quality of food"
                    },
                    {
                        "aspect": "Service Speed",
                        "sentiment": "negative", 
                        "confidence": 0.85,
                        "keywords": ["slow", "waited", "took forever"],
                        "explanation": "Customer complained about long wait times"
                    }
                ],
                "aspects_summary": "Mixed experience with excellent food quality but poor service speed"
            }
            
            Rules:
            - sentiment must be exactly "positive", "negative", or "neutral" (overall surface-level sentiment)
            - confidence must be a number between 0 and 1
            - analysis should be 1-2 sentences explaining the sentiment, emotions, sarcasm, topics, and aspects
            - emotions: Use Plutchik's 8 basic emotions, each scored 0-1
            - dominant_emotion: The emotion with the highest score
            - sarcasm_detected: true if irony/sarcasm is present, false otherwise
            - sarcasm_confidence: 0-1 confidence in sarcasm detection
            - sarcasm_explanation: Brief explanation of why text is sarcastic (empty if no sarcasm)
            - adjusted_sentiment: The true sentiment after considering sarcasm (same as sentiment if no sarcasm)
            - sarcasm_indicators: Array of specific words/phrases that suggest sarcasm (empty if no sarcasm)
            - topics_detected: Array of topic objects with topic, display_name, confidence, and keywords
            - primary_topic: The topic with the highest confidence score
            - topic_summary: Brief explanation of what topics the text discusses
            - aspects_analysis: Array of specific aspects mentioned in text with individual sentiments
            - aspects_summary: Brief summary of how different aspects contribute to overall experience
            - Return ONLY the JSON, no other text
            
            Topic Categories (use these exact topic values):
            - customer_service: Customer support, help desk, service experience
            - product_quality: Build quality, materials, durability, craftsmanship
            - pricing: Cost, value, expensive, cheap, pricing strategy
            - delivery_shipping: Shipping, delivery, logistics, arrival time
            - user_experience: Usability, interface, ease of use, design
            - technical_issues: Bugs, crashes, performance problems, errors
            - marketing_advertising: Ads, promotions, campaigns, marketing messages
            - company_policies: Terms, conditions, policies, procedures
            - competitor_comparison: Mentions of other companies/brands
            - feature_requests: New features, improvements, suggestions
            - security_privacy: Data protection, privacy, security concerns  
            - performance_speed: Speed, performance, responsiveness, loading times
            
            Topic Detection Guidelines:
            - Text can have multiple topics with different confidence levels
            - Only include topics with confidence > 0.3
            - Primary topic should have highest confidence
            - Keywords should reflect actual words from the text that indicate the topic
            - Topic summary should explain the main discussion focus
            
            Aspect-Based Sentiment Analysis Guidelines:
            - Identify specific aspects/features/components mentioned in the text
            - Analyze sentiment for each aspect individually (may differ from overall sentiment)
            - Common aspects include: Food Quality, Service Quality, Price/Value, Delivery Speed, Product Features, User Interface, Build Quality, Customer Support, Location/Ambiance, Staff Behavior, etc.
            - Only include aspects with confidence > 0.4
            - Aspect names should be clear and business-relevant (e.g., "Food Quality" not just "Food")
            - Keywords should be actual words from text that relate to that aspect
            - Explanation should be brief (1 sentence) about why that sentiment was assigned
            - Each aspect can have different sentiments (e.g., positive food, negative service)
            - Aspects summary should synthesize how different aspects contribute to overall experience
            - If no clear aspects are detected, return empty array for aspects_analysis"""
        ).with_model("openai", "gpt-4o-mini")
        
        # Create user message
        user_message = UserMessage(text=f"Analyze the sentiment, emotions, sarcasm, and topics of this text: {text}")
        
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
            
            # Ensure topic fields exist with defaults
            if "topics_detected" not in result:
                result["topics_detected"] = []
            if "primary_topic" not in result:
                result["primary_topic"] = ""
            if "topic_summary" not in result:
                result["topic_summary"] = ""
            
            # Find primary topic if topics exist
            if result["topics_detected"] and len(result["topics_detected"]) > 0:
                primary_topic = max(result["topics_detected"], key=lambda x: x.get("confidence", 0))
                result["primary_topic"] = primary_topic.get("topic", "")
            
            # Ensure aspect analysis fields exist with defaults
            if "aspects_analysis" not in result:
                result["aspects_analysis"] = []
            if "aspects_summary" not in result:
                result["aspects_summary"] = ""
            
            # Validate aspect analysis structure
            if result["aspects_analysis"]:
                validated_aspects = []
                for aspect in result["aspects_analysis"]:
                    if isinstance(aspect, dict) and all(key in aspect for key in ["aspect", "sentiment", "confidence"]):
                        # Ensure required fields exist
                        if "keywords" not in aspect:
                            aspect["keywords"] = []
                        if "explanation" not in aspect:
                            aspect["explanation"] = ""
                        validated_aspects.append(aspect)
                result["aspects_analysis"] = validated_aspects
            
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
            
            # Basic topic detection from keywords
            topics_detected = []
            topic_keywords = {
                "customer_service": ["support", "service", "help", "customer", "staff"],
                "product_quality": ["quality", "product", "build", "material", "construction"],
                "pricing": ["price", "cost", "expensive", "cheap", "money", "value"],
                "technical_issues": ["bug", "crash", "error", "problem", "issue", "broken"],
                "delivery_shipping": ["delivery", "shipping", "package", "arrived", "sent"],
                "user_experience": ["interface", "design", "usability", "experience", "navigation"]
            }
            
            for topic, keywords in topic_keywords.items():
                if any(keyword in response_lower for keyword in keywords):
                    display_names = {
                        "customer_service": "Customer Service",
                        "product_quality": "Product Quality", 
                        "pricing": "Pricing",
                        "technical_issues": "Technical Issues",
                        "delivery_shipping": "Delivery & Shipping",
                        "user_experience": "User Experience"
                    }
                    topics_detected.append({
                        "topic": topic,
                        "display_name": display_names.get(topic, topic.replace("_", " ").title()),
                        "confidence": 0.7,
                        "keywords": [kw for kw in keywords if kw in response_lower]
                    })

            # Basic aspect detection from common patterns
            aspects_analysis = []
            aspect_patterns = {
                "Food Quality": ["food", "taste", "delicious", "bland", "fresh", "stale", "meal", "dish"],
                "Service Quality": ["service", "staff", "waiter", "waitress", "server", "friendly", "rude", "attentive"],
                "Price/Value": ["price", "cost", "expensive", "cheap", "worth", "value", "money", "affordable"],
                "Delivery Speed": ["delivery", "shipping", "fast", "slow", "quick", "delayed", "on time"],
                "Build Quality": ["build", "construction", "material", "sturdy", "flimsy", "durable", "quality"],
                "User Interface": ["interface", "UI", "design", "layout", "navigation", "easy", "confusing"],
                "Customer Support": ["support", "help", "helpful", "unhelpful", "response", "assistance"]
            }
            
            for aspect_name, keywords in aspect_patterns.items():
                aspect_keywords_found = [kw for kw in keywords if kw in response_lower]
                if aspect_keywords_found:
                    # Determine sentiment for this aspect based on surrounding context
                    aspect_sentiment = sentiment  # Default to overall sentiment
                    confidence = 0.6
                    
                    # Try to determine more specific aspect sentiment
                    positive_words = ["good", "great", "excellent", "amazing", "wonderful", "fantastic", "love", "perfect"]
                    negative_words = ["bad", "terrible", "awful", "horrible", "hate", "worst", "disappointing", "poor"]
                    
                    # Look for sentiment words near aspect keywords
                    aspect_context = " ".join([word for word in response_lower.split() 
                                               if any(kw in word for kw in aspect_keywords_found)])
                    
                    if any(pos in aspect_context for pos in positive_words):
                        aspect_sentiment = "positive"
                        confidence = 0.7
                    elif any(neg in aspect_context for neg in negative_words):
                        aspect_sentiment = "negative"  
                        confidence = 0.7
                    
                    aspects_analysis.append({
                        "aspect": aspect_name,
                        "sentiment": aspect_sentiment,
                        "confidence": confidence,
                        "keywords": aspect_keywords_found[:3],  # Limit to top 3 keywords
                        "explanation": f"Detected {aspect_sentiment} sentiment for {aspect_name.lower()} based on keywords: {', '.join(aspect_keywords_found[:2])}"
                    })
            
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
                "analysis": "Sentiment, emotion, sarcasm, topic, and aspect analysis completed based on text content.",
                "emotions": emotions,
                "dominant_emotion": max(emotions, key=emotions.get) if emotions else "neutral",
                "sarcasm_detected": sarcasm_detected,
                "sarcasm_confidence": 0.7 if sarcasm_detected else 0.0,
                "sarcasm_explanation": "Detected potential sarcastic language patterns" if sarcasm_detected else "",
                "adjusted_sentiment": "negative" if sarcasm_detected and sentiment == "positive" else sentiment,
                "sarcasm_indicators": [kw for kw in sarcasm_keywords if kw in response_lower] if sarcasm_detected else [],
                "topics_detected": topics_detected,
                "primary_topic": topics_detected[0]["topic"] if topics_detected else "",
                "topic_summary": f"Discussion about {', '.join([t['display_name'] for t in topics_detected])}" if topics_detected else "",
                "aspects_analysis": aspects_analysis,
                "aspects_summary": f"Analysis covers {len(aspects_analysis)} aspects with mixed sentiments" if aspects_analysis else ""
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
            "sarcasm_indicators": [],
            "topics_detected": [],
            "primary_topic": "",
            "topic_summary": "",
            "aspects_analysis": [],
            "aspects_summary": ""
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
            sarcasm_indicators=analysis_result.get("sarcasm_indicators", []),
            topics_detected=analysis_result.get("topics_detected", []),
            primary_topic=analysis_result.get("primary_topic", ""),
            topic_summary=analysis_result.get("topic_summary", ""),
            aspects_analysis=analysis_result.get("aspects_analysis", []),
            aspects_summary=analysis_result.get("aspects_summary", "")
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

@api_router.post("/upload-file", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload and parse file for batch sentiment analysis"""
    try:
        # Validate file size (5MB limit)
        MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes
        file_size = len(await file.read())
        await file.seek(0)  # Reset file pointer
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File size exceeds 5MB limit")
        
        # Validate file type
        allowed_extensions = ['txt', 'csv', 'xlsx', 'xls', 'pdf']
        file_extension = file.filename.split('.')[-1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"File type '{file_extension}' not supported. Allowed types: {allowed_extensions}")
        
        # Extract text from file
        extracted_texts = await extract_text_from_file(file)
        
        if not extracted_texts:
            raise HTTPException(status_code=400, detail="No text content could be extracted from the file")
        
        # Limit number of entries to prevent overwhelming the system
        if len(extracted_texts) > 100:
            extracted_texts = extracted_texts[:100]
            logger.warning(f"File {file.filename} had {len(extracted_texts)} entries, limiting to 100")
        
        # Create response
        response = FileUploadResponse(
            filename=file.filename,
            file_type=file_extension,
            total_entries=len(extracted_texts),
            extracted_texts=extracted_texts
        )
        
        # Store file metadata in database
        file_metadata = response.dict()
        file_metadata['timestamp'] = file_metadata['timestamp'].isoformat()
        await db.uploaded_files.insert_one(file_metadata)
        
        logger.info(f"Successfully processed file {file.filename}: {len(extracted_texts)} texts extracted")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.post("/analyze-batch", response_model=BatchAnalysisResponse)
async def analyze_batch(request: BatchAnalysisRequest):
    """Perform batch sentiment analysis on extracted texts"""
    try:
        if not request.texts:
            raise HTTPException(status_code=400, detail="No texts provided for analysis")
        
        # Get file metadata
        file_metadata = await db.uploaded_files.find_one({"file_id": request.file_id})
        if not file_metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        results = []
        processed_count = 0
        
        for text_entry in request.texts:
            try:
                text_content = text_entry.get("text", "")
                if not text_content.strip():
                    continue
                
                # Perform sentiment analysis
                analysis_result = await analyze_sentiment(text_content)
                
                # Create result with metadata
                result = {
                    "id": str(uuid.uuid4()),
                    "text": text_content,
                    "row_number": text_entry.get("row_number"),
                    "metadata": text_entry.get("metadata", {}),
                    "sentiment": analysis_result["sentiment"],
                    "confidence": analysis_result["confidence"],
                    "analysis": analysis_result["analysis"],
                    "emotions": analysis_result.get("emotions", {}),
                    "dominant_emotion": analysis_result.get("dominant_emotion", ""),
                    "sarcasm_detected": analysis_result.get("sarcasm_detected", False),
                    "sarcasm_confidence": analysis_result.get("sarcasm_confidence", 0.0),
                    "sarcasm_explanation": analysis_result.get("sarcasm_explanation", ""),
                    "adjusted_sentiment": analysis_result.get("adjusted_sentiment", analysis_result["sentiment"]),
                    "sarcasm_indicators": analysis_result.get("sarcasm_indicators", []),
                    "topics_detected": analysis_result.get("topics_detected", []),
                    "primary_topic": analysis_result.get("primary_topic", ""),
                    "topic_summary": analysis_result.get("topic_summary", ""),
                    "aspects_analysis": analysis_result.get("aspects_analysis", []),
                    "aspects_summary": analysis_result.get("aspects_summary", ""),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                results.append(result)
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error analyzing text entry {text_entry.get('row_number', 'unknown')}: {e}")
                # Continue processing other entries
                continue
        
        # Create batch response
        batch_response = BatchAnalysisResponse(
            file_id=request.file_id,
            filename=file_metadata.get("filename", "unknown"),
            total_processed=processed_count,
            results=results
        )
        
        # Store batch results in database
        batch_data = batch_response.dict()
        batch_data['timestamp'] = batch_data['timestamp'].isoformat()
        await db.batch_analyses.insert_one(batch_data)
        
        logger.info(f"Batch analysis completed: {processed_count} texts processed")
        return batch_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
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