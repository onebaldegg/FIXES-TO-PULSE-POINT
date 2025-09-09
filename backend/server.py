from fastapi import FastAPI, APIRouter, HTTPException, File, UploadFile, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
from emergentintegrations.llm.chat import LlmChat, UserMessage
import pandas as pd
import PyPDF2
import pdfplumber
import io
import tempfile
import json
import requests
from bs4 import BeautifulSoup
from newspaper import Article
import time
from urllib.parse import urlparse, urljoin
import re
from passlib.context import CryptContext
from jose import JWTError, jwt
from itsdangerous import URLSafeTimedSerializer
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, DictLoader


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

class URLAnalysisRequest(BaseModel):
    url: str
    extract_full_content: bool = True
    include_metadata: bool = True

class URLAnalysisResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: str
    title: Optional[str] = None
    author: Optional[str] = None
    publish_date: Optional[str] = None
    extracted_text: str
    text_length: int
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
    metadata: Optional[dict] = {}
    processing_time: Optional[float] = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BatchURLRequest(BaseModel):
    urls: List[str]
    extract_full_content: bool = True
    include_metadata: bool = True

class BatchURLResponse(BaseModel):
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    total_requested: int
    total_processed: int
    total_failed: int
    results: List[URLAnalysisResponse]
    failed_urls: List[dict]  # [{url: str, error: str}]
    processing_time: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# User Authentication Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v
    
    @validator('full_name')
    def validate_name(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError('Name must be at least 2 characters')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    is_active: bool
    is_verified: bool
    subscription_tier: str
    created_at: datetime
    last_login: Optional[datetime] = None
    usage_stats: dict

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if v and len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


# URL Processing Service
class URLProcessor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.timeout = 30
        self.max_content_length = 10 * 1024 * 1024  # 10MB limit
    
    def validate_url(self, url: str) -> tuple[bool, str]:
        """Validate URL format and accessibility"""
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False, "Invalid URL format"
            
            if parsed.scheme not in ['http', 'https']:
                return False, "Only HTTP and HTTPS URLs are supported"
                
            return True, ""
        except Exception as e:
            return False, f"URL validation error: {str(e)}"
    
    def extract_with_newspaper(self, url: str) -> dict:
        """Extract content using newspaper3k library"""
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            return {
                'title': article.title or '',
                'text': article.text or '',
                'authors': article.authors,
                'publish_date': article.publish_date.isoformat() if article.publish_date else None,
                'top_image': article.top_image or '',
                'meta_keywords': article.meta_keywords,
                'meta_description': article.meta_description or '',
                'canonical_link': article.canonical_link or url,
                'method': 'newspaper3k'
            }
        except Exception as e:
            logger.warning(f"Newspaper3k extraction failed for {url}: {e}")
            return None
    
    def extract_with_beautifulsoup(self, url: str) -> dict:
        """Extract content using BeautifulSoup as fallback"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Check content length
            if len(response.content) > self.max_content_length:
                raise Exception(f"Content too large: {len(response.content)} bytes")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()
            
            # Extract title
            title = ''
            if soup.title:
                title = soup.title.string.strip()
            elif soup.find('h1'):
                title = soup.find('h1').get_text().strip()
            
            # Extract main content
            content_selectors = [
                'article', 'main', '.content', '.post-content', 
                '.entry-content', '.article-body', '#content'
            ]
            
            main_content = None
            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if not main_content:
                main_content = soup.find('body')
            
            if main_content:
                # Clean up the text
                text = main_content.get_text(separator=' ', strip=True)
                # Remove extra whitespace
                text = re.sub(r'\s+', ' ', text).strip()
            else:
                text = soup.get_text(separator=' ', strip=True)
                text = re.sub(r'\s+', ' ', text).strip()
            
            # Extract meta information
            meta_description = ''
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                meta_description = meta_desc.get('content', '')
            
            author = ''
            author_meta = soup.find('meta', attrs={'name': 'author'})
            if author_meta:
                author = author_meta.get('content', '')
            
            return {
                'title': title,
                'text': text,
                'authors': [author] if author else [],
                'publish_date': None,
                'top_image': '',
                'meta_keywords': [],
                'meta_description': meta_description,
                'canonical_link': url,
                'method': 'beautifulsoup'
            }
            
        except Exception as e:
            logger.error(f"BeautifulSoup extraction failed for {url}: {e}")
            return None
    
    async def process_url(self, url: str, extract_full_content: bool = True, include_metadata: bool = True) -> dict:
        """Process a single URL and extract content"""
        start_time = time.time()
        
        # Validate URL
        is_valid, error_msg = self.validate_url(url)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Try newspaper3k first (better for articles)
        extracted_data = self.extract_with_newspaper(url)
        
        # Fallback to BeautifulSoup if newspaper3k fails
        if not extracted_data or not extracted_data.get('text'):
            extracted_data = self.extract_with_beautifulsoup(url)
        
        if not extracted_data:
            raise HTTPException(status_code=500, detail="Failed to extract content from URL")
        
        text_content = extracted_data.get('text', '')
        if not text_content or len(text_content.strip()) < 50:
            raise HTTPException(status_code=400, detail="Insufficient text content extracted from URL")
        
        # Limit text length for processing
        if len(text_content) > 50000:  # 50k character limit
            text_content = text_content[:50000] + "... [truncated]"
        
        processing_time = time.time() - start_time
        
        result = {
            'url': url,
            'title': extracted_data.get('title', ''),
            'author': ', '.join(extracted_data.get('authors', [])) if extracted_data.get('authors') else None,
            'publish_date': extracted_data.get('publish_date'),
            'extracted_text': text_content,
            'text_length': len(text_content),
            'processing_time': processing_time
        }
        
        if include_metadata:
            result['metadata'] = {
                'extraction_method': extracted_data.get('method', 'unknown'),
                'top_image': extracted_data.get('top_image', ''),
                'meta_description': extracted_data.get('meta_description', ''),
                'meta_keywords': extracted_data.get('meta_keywords', []),
                'canonical_link': extracted_data.get('canonical_link', url),
                'domain': urlparse(url).netloc,
                'word_count': len(text_content.split()),
                'character_count': len(text_content)
            }
        
        return result

# Initialize URL processor
url_processor = URLProcessor()

# Authentication Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Email Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD") 
FROM_EMAIL = os.getenv("FROM_EMAIL")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://sentimentmatrix.preview.emergentagent.com")

# Security utilities
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Email template engine
email_templates = {
    "verification_email": """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Email Verification</title>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #0a0a0a; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
            .content { padding: 30px; background: linear-gradient(135deg, #1a1a1a, #2a2a2a); border-radius: 0 0 10px 10px; }
            .button { display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #10b981, #059669); 
                      color: white; text-decoration: none; border-radius: 8px; margin: 20px 0; font-weight: bold; }
            .footer { text-align: center; padding: 20px; font-size: 12px; color: #888; }
            .text { color: #e5e5e5; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛡️ Brand Watch AI</h1>
                <h2>Verify Your Email</h2>
            </div>
            <div class="content">
                <p class="text">Hello {{ user_name }},</p>
                <p class="text">Welcome to Brand Watch AI! To complete your registration and unlock full access to our sentiment analysis platform, please verify your email address:</p>
                <p style="text-align: center;">
                    <a href="{{ verification_url }}" class="button">Verify Email Address</a>
                </p>
                <p class="text">If the button doesn't work, copy and paste this link:</p>
                <p style="word-break: break-all; color: #10b981;">{{ verification_url }}</p>
                <p class="text"><strong>This link expires in 24 hours for security.</strong></p>
                <p class="text">If you didn't create an account, please ignore this email.</p>
            </div>
            <div class="footer">
                <p>&copy; 2024 Brand Watch AI. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """,
    "password_reset": """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Password Reset</title>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #0a0a0a; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #dc2626, #b91c1c); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
            .content { padding: 30px; background: linear-gradient(135deg, #1a1a1a, #2a2a2a); border-radius: 0 0 10px 10px; }
            .button { display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #dc2626, #b91c1c); 
                      color: white; text-decoration: none; border-radius: 8px; margin: 20px 0; font-weight: bold; }
            .footer { text-align: center; padding: 20px; font-size: 12px; color: #888; }
            .text { color: #e5e5e5; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 Brand Watch AI</h1>
                <h2>Password Reset Request</h2>
            </div>
            <div class="content">
                <p class="text">Hello {{ user_name }},</p>
                <p class="text">We received a request to reset your password. If you made this request, click the button below to reset your password:</p>
                <p style="text-align: center;">
                    <a href="{{ reset_url }}" class="button">Reset Password</a>
                </p>
                <p class="text">If the button doesn't work, copy and paste this link:</p>
                <p style="word-break: break-all; color: #dc2626;">{{ reset_url }}</p>
                <p class="text"><strong>This link expires in {{ expiry_minutes }} minutes for security.</strong></p>
                <p class="text">If you didn't request a password reset, please ignore this email and your password will remain unchanged.</p>
            </div>
            <div class="footer">
                <p>&copy; 2024 Brand Watch AI. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
}

template_env = Environment(loader=DictLoader(email_templates))

# Authentication Utilities
def hash_password(password: str) -> str:
    """Hash a password using BCrypt algorithm."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token with expiration."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """Create a refresh token with longer expiration."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_token(token: str, token_type: str = "access"):
    """Verify JWT token and return payload if valid."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        token_type_claim: str = payload.get("type")
        
        if email is None or token_type_claim != token_type:
            raise credentials_exception
            
        return payload
    except JWTError:
        raise credentials_exception

# Email Service
class EmailService:
    def __init__(self):
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.username = SMTP_USERNAME
        self.password = SMTP_PASSWORD
        self.from_email = FROM_EMAIL
    
    async def send_email(self, to_email: str, subject: str, html_content: str):
        """Send email using SMTP configuration."""
        if not self.username or not self.password:
            logger.warning("Email credentials not configured - email not sent")
            return True  # Return True in development to avoid blocking
        
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.from_email
        message["To"] = to_email
        
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            server.sendmail(self.from_email, to_email, message.as_string())
            server.quit()
            logger.info(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            return False
    
    def render_template(self, template_name: str, **kwargs):
        """Render email template with provided data."""
        template = template_env.get_template(template_name)
        return template.render(**kwargs)

# Token Service for email verification and password reset
class TokenService:
    def __init__(self):
        self.secret_key = os.getenv("VERIFICATION_SECRET_KEY", SECRET_KEY)
        self.serializer = URLSafeTimedSerializer(self.secret_key)
    
    def generate_verification_token(self, user_id: str, email: str) -> str:
        """Generate secure verification token for email confirmation."""
        token_data = {
            "user_id": user_id,
            "email": email,
            "purpose": "email_verification"
        }
        return self.serializer.dumps(token_data)
    
    def generate_reset_token(self, user_id: str, email: str) -> str:
        """Generate secure password reset token."""
        token_data = {
            "user_id": user_id,
            "email": email,
            "purpose": "password_reset",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        return self.serializer.dumps(token_data)
    
    def verify_token(self, token: str, max_age: int = 86400) -> dict:
        """Verify and decode token."""
        try:
            data = self.serializer.loads(token, max_age=max_age)
            return data
        except Exception as e:
            raise ValueError(f"Invalid or expired token: {str(e)}")

# Initialize services
email_service = EmailService()
token_service = TokenService()

# User Management Functions
async def get_user_by_email(email: str):
    """Get user by email from database."""
    user = await db.users.find_one({"email": email})
    return user

async def get_user_by_id(user_id: str):
    """Get user by ID from database."""
    user = await db.users.find_one({"id": user_id})
    return user

async def create_user(user_data: UserCreate):
    """Create new user account with proper validation."""
    # Check if user already exists
    existing_user = await get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password and create user
    hashed_password = hash_password(user_data.password)
    
    # Check if this is the test account for PRO access
    subscription_tier = "pro" if user_data.email == "onebaldegg@gmail.com" else "free"
    
    user_doc = {
        "id": str(uuid.uuid4()),
        "email": user_data.email,
        "hashed_password": hashed_password,
        "full_name": user_data.full_name,
        "is_active": True,
        "is_verified": False,
        "subscription_tier": subscription_tier,
        "created_at": datetime.now(timezone.utc),
        "last_login": None,
        "usage_stats": {
            "analyses_this_month": 0,
            "files_uploaded": 0,
            "urls_analyzed": 0,
            "monthly_reset_date": datetime.now(timezone.utc).replace(day=1)
        },
        "settings": {
            "email_notifications": True,
            "theme_preference": "matrix"
        }
    }
    
    result = await db.users.insert_one(user_doc)
    
    # Send verification email
    verification_token = token_service.generate_verification_token(user_doc["id"], user_doc["email"])
    verification_url = f"{FRONTEND_URL}/verify-email?token={verification_token}"
    
    html_content = email_service.render_template(
        "verification_email",
        user_name=user_doc["full_name"],
        verification_url=verification_url
    )
    
    await email_service.send_email(
        to_email=user_doc["email"],
        subject="Verify Your Brand Watch AI Account",
        html_content=html_content
    )
    
    return user_doc

async def authenticate_user(email: str, password: str):
    """Authenticate user credentials and return user if valid."""
    user = await get_user_by_email(email)
    if not user or not verify_password(password, user["hashed_password"]):
        return False
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Extract and validate current user from JWT token."""
    payload = await verify_token(token)
    email = payload.get("sub")
    
    user = await get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

async def get_current_active_user(current_user = Depends(get_current_user)):
    """Ensure user account is active and verified."""
    if not current_user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    
    return current_user

async def get_current_verified_user(current_user = Depends(get_current_active_user)):
    """Ensure user account is verified."""
    if not current_user["is_verified"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email verification required"
        )
    
    return current_user

# Usage Tracking
async def check_usage_limits(user: dict, operation: str) -> bool:
    """Check if user is within usage limits for the operation."""
    usage_stats = user.get("usage_stats", {})
    subscription_tier = user.get("subscription_tier", "free")
    
    # Define limits per tier
    limits = {
        "free": {
            "analyses_this_month": 50,
            "files_uploaded": 5,
            "urls_analyzed": 10
        },
        "pro": {
            "analyses_this_month": 10000,
            "files_uploaded": 1000,
            "urls_analyzed": 5000
        }
    }
    
    tier_limits = limits.get(subscription_tier, limits["free"])
    current_usage = usage_stats.get(operation, 0)
    limit = tier_limits.get(operation, 0)
    
    return current_usage < limit

async def increment_usage(user_id: str, operation: str):
    """Increment usage counter for user."""
    await db.users.update_one(
        {"id": user_id},
        {"$inc": {f"usage_stats.{operation}": 1}}
    )

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
            # Process PDF files with improved text extraction
            content = await file.read()
            pdf_stream = io.BytesIO(content)
            
            # Try pdfplumber first (more reliable)
            try:
                with pdfplumber.open(pdf_stream) as pdf:
                    for page_num, page in enumerate(pdf.pages, 1):
                        text_content = page.extract_text()
                        if text_content and text_content.strip():
                            # Clean up the text
                            text_content = text_content.strip()
                            
                            # Split into paragraphs for better analysis
                            paragraphs = [p.strip() for p in text_content.split('\n\n') if p.strip()]
                            
                            if not paragraphs:
                                # If no double newlines, split by single newlines but filter longer chunks
                                lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                                # Group lines into meaningful chunks
                                current_chunk = []
                                for line in lines:
                                    current_chunk.append(line)
                                    # If chunk is substantial, add it
                                    if len(' '.join(current_chunk)) > 50:
                                        paragraphs.append(' '.join(current_chunk))
                                        current_chunk = []
                                # Add remaining chunk if any
                                if current_chunk and len(' '.join(current_chunk)) > 20:
                                    paragraphs.append(' '.join(current_chunk))
                            
                            for para_num, paragraph in enumerate(paragraphs, 1):
                                if len(paragraph) > 20:  # Only process substantial text
                                    # Clean up the paragraph text
                                    paragraph = ' '.join(paragraph.split())  # Normalize whitespace
                                    extracted_texts.append({
                                        "text": paragraph,
                                        "row_number": f"page_{page_num}_para_{para_num}",
                                        "metadata": {
                                            "source": f"PDF page {page_num}",
                                            "extractor": "pdfplumber"
                                        }
                                    })
                        
            except Exception as e:
                logger.warning(f"pdfplumber failed for {file.filename}, trying PyPDF2: {e}")
                
                # Fallback to PyPDF2
                try:
                    pdf_stream.seek(0)  # Reset stream
                    pdf_reader = PyPDF2.PdfReader(pdf_stream)
                    
                    for page_num, page in enumerate(pdf_reader.pages, 1):
                        text_content = page.extract_text()
                        if text_content and text_content.strip():
                            text_content = text_content.strip()
                            
                            # Clean and split text
                            paragraphs = [p.strip() for p in text_content.split('\n\n') if p.strip()]
                            
                            if not paragraphs:
                                # Single paragraph from the page
                                text_content = ' '.join(text_content.split())  # Normalize whitespace
                                if len(text_content) > 20:
                                    paragraphs = [text_content]
                            
                            for para_num, paragraph in enumerate(paragraphs, 1):
                                if len(paragraph) > 20:
                                    extracted_texts.append({
                                        "text": paragraph,
                                        "row_number": f"page_{page_num}_para_{para_num}",
                                        "metadata": {
                                            "source": f"PDF page {page_num}",
                                            "extractor": "PyPDF2"
                                        }
                                    })
                except Exception as e2:
                    logger.error(f"Both PDF extractors failed for {file.filename}: pdfplumber={e}, PyPDF2={e2}")
                    # Still allow the file to be processed, just with no extracted text
                    pass
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

@api_router.post("/analyze-url", response_model=URLAnalysisResponse)
async def analyze_url(request: URLAnalysisRequest):
    """Analyze sentiment of content from a single URL"""
    try:
        # Process URL and extract content
        url_data = await url_processor.process_url(
            request.url, 
            request.extract_full_content, 
            request.include_metadata
        )
        
        # Perform sentiment analysis on extracted text
        analysis_result = await analyze_sentiment(url_data['extracted_text'])
        
        # Create response
        response = URLAnalysisResponse(
            url=url_data['url'],
            title=url_data.get('title'),
            author=url_data.get('author'),
            publish_date=url_data.get('publish_date'),
            extracted_text=url_data['extracted_text'],
            text_length=url_data['text_length'],
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
            aspects_summary=analysis_result.get("aspects_summary", ""),
            metadata=url_data.get('metadata', {}),
            processing_time=url_data.get('processing_time', 0.0)
        )
        
        # Store URL analysis in database
        url_analysis_data = response.dict()
        url_analysis_data['timestamp'] = url_analysis_data['timestamp'].isoformat()
        await db.url_analyses.insert_one(url_analysis_data)
        
        logger.info(f"Successfully analyzed URL: {request.url[:100]}...")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing URL {request.url}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.post("/analyze-batch-urls", response_model=BatchURLResponse)
async def analyze_batch_urls(request: BatchURLRequest):
    """Analyze sentiment of content from multiple URLs"""
    start_time = time.time()
    
    try:
        if not request.urls:
            raise HTTPException(status_code=400, detail="No URLs provided for analysis")
        
        if len(request.urls) > 20:  # Limit batch size
            raise HTTPException(status_code=400, detail="Maximum 20 URLs allowed per batch")
        
        results = []
        failed_urls = []
        
        for url in request.urls:
            try:
                # Process URL and extract content
                url_data = await url_processor.process_url(
                    url, 
                    request.extract_full_content, 
                    request.include_metadata
                )
                
                # Perform sentiment analysis
                analysis_result = await analyze_sentiment(url_data['extracted_text'])
                
                # Create URL analysis response
                url_response = URLAnalysisResponse(
                    url=url_data['url'],
                    title=url_data.get('title'),
                    author=url_data.get('author'),
                    publish_date=url_data.get('publish_date'),
                    extracted_text=url_data['extracted_text'],
                    text_length=url_data['text_length'],
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
                    aspects_summary=analysis_result.get("aspects_summary", ""),
                    metadata=url_data.get('metadata', {}),
                    processing_time=url_data.get('processing_time', 0.0)
                )
                
                results.append(url_response)
                
                # Store in database
                url_analysis_data = url_response.dict()
                url_analysis_data['timestamp'] = url_analysis_data['timestamp'].isoformat()
                await db.url_analyses.insert_one(url_analysis_data)
                
            except Exception as e:
                logger.error(f"Error processing URL {url}: {e}")
                failed_urls.append({
                    "url": url,
                    "error": str(e)
                })
                continue
        
        total_processing_time = time.time() - start_time
        
        # Create batch response
        batch_response = BatchURLResponse(
            total_requested=len(request.urls),
            total_processed=len(results),
            total_failed=len(failed_urls),
            results=results,
            failed_urls=failed_urls,
            processing_time=total_processing_time
        )
        
        # Store batch metadata
        batch_data = {
            "batch_id": batch_response.batch_id,
            "total_requested": batch_response.total_requested,
            "total_processed": batch_response.total_processed,
            "total_failed": batch_response.total_failed,
            "processing_time": batch_response.processing_time,
            "timestamp": batch_response.timestamp.isoformat()
        }
        await db.url_batch_analyses.insert_one(batch_data)
        
        logger.info(f"Batch URL analysis completed: {len(results)}/{len(request.urls)} URLs processed successfully")
        return batch_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch URL analysis: {e}")
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