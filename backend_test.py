import requests
import sys
import json
import time
import io
import tempfile
import os
from datetime import datetime

class BrandWatchAPITester:
    def __init__(self, base_url="https://sentimentmatrix.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else self.api_url
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            print(f"   Status Code: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Expected {expected_status}, got {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timed out after {timeout} seconds")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test GET /api/ endpoint"""
        return self.run_test("Root API Endpoint", "GET", "", 200)

    def test_analyze_sentiment_positive(self):
        """Test sentiment analysis with positive text"""
        positive_text = "I absolutely love this product! It's amazing and works perfectly."
        return self.run_test(
            "Analyze Positive Sentiment",
            "POST",
            "analyze-sentiment",
            200,
            data={"text": positive_text},
            timeout=60  # LLM calls can take longer
        )

    def test_analyze_sentiment_negative(self):
        """Test sentiment analysis with negative text"""
        negative_text = "This service is terrible. Worst experience ever."
        return self.run_test(
            "Analyze Negative Sentiment",
            "POST",
            "analyze-sentiment",
            200,
            data={"text": negative_text},
            timeout=60
        )

    def test_analyze_sentiment_neutral(self):
        """Test sentiment analysis with neutral text"""
        neutral_text = "The weather is cloudy today."
        return self.run_test(
            "Analyze Neutral Sentiment",
            "POST",
            "analyze-sentiment",
            200,
            data={"text": neutral_text},
            timeout=60
        )

    def test_analyze_sentiment_empty_text(self):
        """Test error handling with empty text"""
        return self.run_test(
            "Analyze Empty Text (Error Case)",
            "POST",
            "analyze-sentiment",
            400,
            data={"text": ""}
        )

    def test_analyze_sentiment_whitespace_only(self):
        """Test error handling with whitespace only"""
        return self.run_test(
            "Analyze Whitespace Only (Error Case)",
            "POST",
            "analyze-sentiment",
            400,
            data={"text": "   "}
        )

    def test_sentiment_history(self):
        """Test GET /api/sentiment-history endpoint"""
        return self.run_test("Get Sentiment History", "GET", "sentiment-history", 200)

    def validate_sentiment_response(self, response_data):
        """Validate sentiment analysis response structure including emotion, sarcasm, topic, and aspect detection"""
        required_fields = ['id', 'text', 'sentiment', 'confidence', 'analysis', 'timestamp', 'emotions', 'dominant_emotion',
                          'sarcasm_detected', 'sarcasm_confidence', 'sarcasm_explanation', 'adjusted_sentiment', 'sarcasm_indicators',
                          'topics_detected', 'primary_topic', 'topic_summary', 'aspects_analysis', 'aspects_summary']
        valid_sentiments = ['positive', 'negative', 'neutral']
        expected_emotions = ['joy', 'sadness', 'anger', 'fear', 'trust', 'disgust', 'surprise', 'anticipation']
        valid_topics = ['customer_service', 'product_quality', 'pricing', 'delivery_shipping', 'user_experience', 
                       'technical_issues', 'marketing_advertising', 'company_policies', 'competitor_comparison', 
                       'feature_requests', 'security_privacy', 'performance_speed']
        
        print(f"\n🔍 Validating sentiment response structure...")
        
        for field in required_fields:
            if field not in response_data:
                print(f"❌ Missing required field: {field}")
                return False
        
        if response_data['sentiment'] not in valid_sentiments:
            print(f"❌ Invalid sentiment value: {response_data['sentiment']}")
            return False
            
        if not (0 <= response_data['confidence'] <= 1):
            print(f"❌ Invalid confidence value: {response_data['confidence']}")
            return False

        # Validate sarcasm fields
        if not isinstance(response_data['sarcasm_detected'], bool):
            print(f"❌ sarcasm_detected must be boolean")
            return False
        
        if not isinstance(response_data['sarcasm_confidence'], (int, float)) or not (0 <= response_data['sarcasm_confidence'] <= 1):
            print(f"❌ Invalid sarcasm_confidence value: {response_data['sarcasm_confidence']}")
            return False
        
        if not isinstance(response_data['sarcasm_indicators'], list):
            print(f"❌ sarcasm_indicators must be a list")
            return False
        
        if response_data['adjusted_sentiment'] not in valid_sentiments:
            print(f"❌ Invalid adjusted_sentiment value: {response_data['adjusted_sentiment']}")
            return False

        # Validate emotions structure
        emotions = response_data.get('emotions', {})
        if not isinstance(emotions, dict):
            print(f"❌ Emotions field should be a dictionary")
            return False

        # Check if all 8 emotions are present
        for emotion in expected_emotions:
            if emotion not in emotions:
                print(f"❌ Missing emotion: {emotion}")
                return False
            
            emotion_score = emotions[emotion]
            if not isinstance(emotion_score, (int, float)) or not (0 <= emotion_score <= 1):
                print(f"❌ Invalid emotion score for {emotion}: {emotion_score}")
                return False

        # Validate dominant emotion
        dominant_emotion = response_data.get('dominant_emotion', '')
        if dominant_emotion not in expected_emotions:
            print(f"❌ Invalid dominant emotion: {dominant_emotion}")
            return False

        # Check if dominant emotion has the highest score
        if emotions:
            actual_dominant = max(emotions, key=emotions.get)
            if dominant_emotion != actual_dominant:
                print(f"⚠️  Warning: Dominant emotion mismatch. Expected {actual_dominant}, got {dominant_emotion}")

        # Validate topic detection fields
        topics_detected = response_data.get('topics_detected', [])
        if not isinstance(topics_detected, list):
            print(f"❌ topics_detected must be a list")
            return False

        # Validate each topic in topics_detected
        for topic in topics_detected:
            if not isinstance(topic, dict):
                print(f"❌ Each topic must be a dictionary")
                return False
            
            required_topic_fields = ['topic', 'display_name', 'confidence', 'keywords']
            for field in required_topic_fields:
                if field not in topic:
                    print(f"❌ Missing topic field: {field}")
                    return False
            
            if topic['topic'] not in valid_topics:
                print(f"❌ Invalid topic category: {topic['topic']}")
                return False
            
            if not (0 <= topic['confidence'] <= 1):
                print(f"❌ Invalid topic confidence: {topic['confidence']}")
                return False
            
            if not isinstance(topic['keywords'], list):
                print(f"❌ Topic keywords must be a list")
                return False

        # Validate primary_topic
        primary_topic = response_data.get('primary_topic', '')
        if primary_topic and primary_topic not in valid_topics:
            print(f"❌ Invalid primary topic: {primary_topic}")
            return False

        # Check if primary_topic matches highest confidence topic
        if topics_detected and primary_topic:
            highest_confidence_topic = max(topics_detected, key=lambda x: x.get('confidence', 0))
            if primary_topic != highest_confidence_topic.get('topic'):
                print(f"⚠️  Warning: Primary topic mismatch. Expected {highest_confidence_topic.get('topic')}, got {primary_topic}")

        # Validate topic_summary
        topic_summary = response_data.get('topic_summary', '')
        if not isinstance(topic_summary, str):
            print(f"❌ topic_summary must be a string")
            return False

        # Validate aspect analysis fields - NEW FEATURE
        aspects_analysis = response_data.get('aspects_analysis', [])
        if not isinstance(aspects_analysis, list):
            print(f"❌ aspects_analysis must be a list")
            return False

        # Validate each aspect in aspects_analysis
        for aspect in aspects_analysis:
            if not isinstance(aspect, dict):
                print(f"❌ Each aspect must be a dictionary")
                return False
            
            required_aspect_fields = ['aspect', 'sentiment', 'confidence', 'keywords', 'explanation']
            for field in required_aspect_fields:
                if field not in aspect:
                    print(f"❌ Missing aspect field: {field}")
                    return False
            
            # Validate aspect sentiment
            if aspect['sentiment'] not in ['positive', 'negative', 'neutral']:
                print(f"❌ Invalid aspect sentiment: {aspect['sentiment']}")
                return False
            
            # Validate aspect confidence
            if not (0 <= aspect['confidence'] <= 1):
                print(f"❌ Invalid aspect confidence: {aspect['confidence']}")
                return False
            
            # Validate aspect keywords
            if not isinstance(aspect['keywords'], list):
                print(f"❌ Aspect keywords must be a list")
                return False
            
            # Validate aspect explanation
            if not isinstance(aspect['explanation'], str):
                print(f"❌ Aspect explanation must be a string")
                return False

        # Validate aspects_summary
        aspects_summary = response_data.get('aspects_summary', '')
        if not isinstance(aspects_summary, str):
            print(f"❌ aspects_summary must be a string")
            return False

        print(f"✅ Response structure is valid")
        print(f"   Sentiment: {response_data['sentiment']} -> {response_data['adjusted_sentiment']}")
        print(f"   Sarcasm: {response_data['sarcasm_detected']} ({response_data['sarcasm_confidence']:.2f})")
        print(f"   Dominant emotion: {dominant_emotion} ({emotions.get(dominant_emotion, 0):.2f})")
        print(f"   Topics detected: {len(topics_detected)} topics")
        print(f"   Aspects detected: {len(aspects_analysis)} aspects")
        if primary_topic:
            print(f"   Primary topic: {primary_topic}")
        if topic_summary:
            print(f"   Topic summary: {topic_summary[:100]}...")
        if aspects_summary:
            print(f"   Aspects summary: {aspects_summary[:100]}...")
        if response_data['sarcasm_indicators']:
            print(f"   Sarcasm indicators: {response_data['sarcasm_indicators']}")
        return True

    def test_emotion_detection_joy(self):
        """Test emotion detection with joyful text"""
        joyful_text = "I'm so excited about this amazing product! This is absolutely fantastic and wonderful!"
        return self.run_test(
            "Emotion Detection - Joy",
            "POST",
            "analyze-sentiment",
            200,
            data={"text": joyful_text},
            timeout=60
        )

    def test_emotion_detection_mixed(self):
        """Test emotion detection with mixed emotions"""
        mixed_text = "I'm thrilled about the launch but nervous about the reaction. The team worked hard and I trust they've done amazing work!"
        return self.run_test(
            "Emotion Detection - Mixed Emotions",
            "POST",
            "analyze-sentiment",
            200,
            data={"text": mixed_text},
            timeout=60
        )

    def test_emotion_detection_anger(self):
        """Test emotion detection with angry text"""
        angry_text = "This service is absolutely terrible and frustrating! I'm furious about this experience!"
        return self.run_test(
            "Emotion Detection - Anger",
            "POST",
            "analyze-sentiment",
            200,
            data={"text": angry_text},
            timeout=60
        )

    def test_emotion_detection_fear(self):
        """Test emotion detection with fearful text"""
        fearful_text = "I'm worried about the security of my data. This makes me anxious and concerned."
        return self.run_test(
            "Emotion Detection - Fear",
            "POST",
            "analyze-sentiment",
            200,
            data={"text": fearful_text},
            timeout=60
        )

    # SARCASM DETECTION TESTS
    def test_high_sarcasm_detection(self):
        """Test high sarcasm detection"""
        sarcastic_text = "Oh great, another system crash. Just what I needed today. Thanks a lot!"
        success, response = self.run_test(
            "High Sarcasm Detection",
            "POST",
            "analyze-sentiment",
            200,
            data={"text": sarcastic_text},
            timeout=60
        )
        
        if success:
            # Validate sarcasm was detected
            if not response.get('sarcasm_detected', False):
                print(f"❌ Sarcasm should be detected in obvious sarcastic text")
                return False, response
            
            if response.get('sarcasm_confidence', 0) < 0.5:
                print(f"⚠️  Low sarcasm confidence: {response.get('sarcasm_confidence', 0)}")
            
            if len(response.get('sarcasm_indicators', [])) == 0:
                print(f"⚠️  No sarcasm indicators found")
            
            print(f"✅ Sarcasm detected with confidence: {response.get('sarcasm_confidence', 0):.2f}")
            print(f"   Indicators: {response.get('sarcasm_indicators', [])}")
        
        return success, response

    def test_subtle_sarcasm_detection(self):
        """Test subtle sarcasm detection with quotes"""
        sarcastic_text = "Thanks for the 'help' with my account issue."
        success, response = self.run_test(
            "Subtle Sarcasm Detection",
            "POST",
            "analyze-sentiment",
            200,
            data={"text": sarcastic_text},
            timeout=60
        )
        
        if success:
            if response.get('sarcasm_detected', False):
                print(f"✅ Subtle sarcasm detected with confidence: {response.get('sarcasm_confidence', 0):.2f}")
            else:
                print(f"⚠️  Subtle sarcasm not detected (quotes around 'help')")
        
        return success, response

    def test_quoted_sarcasm_detection(self):
        """Test quoted sarcasm detection"""
        sarcastic_text = "The 'premium' service is really living up to its name."
        success, response = self.run_test(
            "Quoted Sarcasm Detection",
            "POST",
            "analyze-sentiment",
            200,
            data={"text": sarcastic_text},
            timeout=60
        )
        
        if success:
            if response.get('sarcasm_detected', False):
                print(f"✅ Quoted sarcasm detected with confidence: {response.get('sarcasm_confidence', 0):.2f}")
            else:
                print(f"⚠️  Quoted sarcasm not detected ('premium' in quotes)")
        
        return success, response

    def test_non_sarcastic_positive(self):
        """Test genuine positive text should NOT be sarcastic"""
        positive_text = "This is genuinely great! I'm so happy and excited about this wonderful product."
        success, response = self.run_test(
            "Non-Sarcastic Positive Text",
            "POST",
            "analyze-sentiment",
            200,
            data={"text": positive_text},
            timeout=60
        )
        
        if success:
            if response.get('sarcasm_detected', False):
                print(f"❌ False positive: Genuine positive text detected as sarcastic")
                return False, response
            
            if response.get('sentiment') != 'positive':
                print(f"❌ Expected positive sentiment, got: {response.get('sentiment')}")
                return False, response
            
            if response.get('adjusted_sentiment') != response.get('sentiment'):
                print(f"❌ Adjusted sentiment should match original when no sarcasm")
                return False, response
            
            print(f"✅ Genuine positive text correctly identified (no sarcasm)")
        
        return success, response

    def test_non_sarcastic_negative(self):
        """Test genuine negative text should NOT be sarcastic"""
        negative_text = "This service is terrible and frustrating. I'm really disappointed with the poor quality."
        success, response = self.run_test(
            "Non-Sarcastic Negative Text",
            "POST",
            "analyze-sentiment",
            200,
            data={"text": negative_text},
            timeout=60
        )
        
        if success:
            if response.get('sarcasm_detected', False):
                print(f"❌ False positive: Genuine negative text detected as sarcastic")
                return False, response
            
            if response.get('sentiment') != 'negative':
                print(f"❌ Expected negative sentiment, got: {response.get('sentiment')}")
                return False, response
            
            print(f"✅ Genuine negative text correctly identified (no sarcasm)")
        
        return success, response

    def test_mixed_sarcasm_emotions(self):
        """Test mixed sarcasm with emotions"""
        mixed_text = "I'm thrilled about the launch but the timing is just perfect"
        success, response = self.run_test(
            "Mixed Sarcasm with Emotions",
            "POST",
            "analyze-sentiment",
            200,
            data={"text": mixed_text},
            timeout=60
        )
        
        if success:
            has_emotions = 'emotions' in response and response['emotions']
            has_sarcasm = response.get('sarcasm_detected', False)
            
            print(f"   Emotions detected: {has_emotions}")
            print(f"   Sarcasm detected: {has_sarcasm}")
            
            if has_sarcasm:
                print(f"   Sarcasm confidence: {response.get('sarcasm_confidence', 0):.2f}")
                print(f"   Surface sentiment: {response.get('sentiment')} -> Adjusted: {response.get('adjusted_sentiment')}")
        
        return success, response

    def test_sentiment_adjustment_logic(self):
        """Test that sarcasm properly adjusts sentiment"""
        sarcastic_text = "Wonderful customer support as always."
        success, response = self.run_test(
            "Sentiment Adjustment Logic",
            "POST",
            "analyze-sentiment",
            200,
            data={"text": sarcastic_text},
            timeout=60
        )
        
        if success:
            sarcasm_detected = response.get('sarcasm_detected', False)
            sarcasm_confidence = response.get('sarcasm_confidence', 0)
            surface_sentiment = response.get('sentiment')
            adjusted_sentiment = response.get('adjusted_sentiment')
            
            print(f"   Surface sentiment: {surface_sentiment}")
            print(f"   Adjusted sentiment: {adjusted_sentiment}")
            print(f"   Sarcasm detected: {sarcasm_detected} ({sarcasm_confidence:.2f})")
            
            # If high-confidence sarcasm is detected and surface is positive, adjusted should be negative
            if sarcasm_detected and sarcasm_confidence > 0.6 and surface_sentiment == 'positive':
                if adjusted_sentiment == 'positive':
                    print(f"⚠️  High-confidence sarcasm should flip positive to negative")
                else:
                    print(f"✅ Sarcasm correctly adjusted sentiment")
        
        return success, response

    # TOPIC DETECTION TESTS - NEW FEATURE
    def test_single_topic_customer_service(self):
        """Test single topic detection - Customer Service"""
        customer_service_text = "The customer support team was incredibly helpful and responsive."
        success, response = self.run_test(
            "Single Topic - Customer Service",
            "POST",
            "analyze-sentiment",
            200,
            data={"text": customer_service_text},
            timeout=60
        )
        
        if success:
            topics = response.get('topics_detected', [])
            primary_topic = response.get('primary_topic', '')
            
            # Check if customer service topic is detected
            customer_service_found = any(topic['topic'] == 'customer_service' for topic in topics)
            if customer_service_found:
                print(f"✅ Customer service topic detected")
            else:
                print(f"❌ Customer service topic not detected in obvious customer service text")
                return False, response
            
            if primary_topic == 'customer_service':
                print(f"✅ Customer service correctly identified as primary topic")
            else:
                print(f"⚠️  Expected customer_service as primary topic, got: {primary_topic}")
        
        return success, response

    def test_multi_topic_business_text(self):
        """Test multi-topic detection - Business scenario"""
        multi_topic_text = "Great product quality but terrible customer support and overpriced."
        success, response = self.run_test(
            "Multi-Topic - Business Scenario",
            "POST",
            "analyze-sentiment",
            200,
            data={"text": multi_topic_text},
            timeout=60
        )
        
        if success:
            topics = response.get('topics_detected', [])
            primary_topic = response.get('primary_topic', '')
            topic_summary = response.get('topic_summary', '')
            
            expected_topics = ['product_quality', 'customer_service', 'pricing']
            detected_topic_names = [topic['topic'] for topic in topics]
            
            print(f"   Expected topics: {expected_topics}")
            print(f"   Detected topics: {detected_topic_names}")
            
            # Check if multiple topics are detected
            if len(topics) >= 2:
                print(f"✅ Multiple topics detected ({len(topics)} topics)")
            else:
                print(f"⚠️  Expected multiple topics, only got {len(topics)}")
            
            # Check for specific expected topics
            for expected_topic in expected_topics:
                if expected_topic in detected_topic_names:
                    print(f"✅ {expected_topic} topic detected")
                else:
                    print(f"⚠️  {expected_topic} topic not detected")
            
            if topic_summary:
                print(f"✅ Topic summary provided: {topic_summary}")
            else:
                print(f"⚠️  No topic summary provided")
        
        return success, response

    def test_technical_focus_topics(self):
        """Test technical issues topic detection"""
        technical_text = "The app keeps crashing and loading times are very slow."
        success, response = self.run_test(
            "Technical Focus Topics",
            "POST",
            "analyze-sentiment",
            200,
            data={"text": technical_text},
            timeout=60
        )
        
        if success:
            topics = response.get('topics_detected', [])
            detected_topic_names = [topic['topic'] for topic in topics]
            
            expected_topics = ['technical_issues', 'performance_speed']
            
            for expected_topic in expected_topics:
                if expected_topic in detected_topic_names:
                    print(f"✅ {expected_topic} topic detected")
                else:
                    print(f"⚠️  {expected_topic} topic not detected in technical text")
        
        return success, response

    def test_competitor_comparison_topic(self):
        """Test competitor comparison topic detection"""
        competitor_text = "Competitor X has better pricing and their delivery is faster."
        success, response = self.run_test(
            "Competitor Comparison Topic",
            "POST",
            "analyze-sentiment",
            200,
            data={"text": competitor_text},
            timeout=60
        )
        
        if success:
            topics = response.get('topics_detected', [])
            detected_topic_names = [topic['topic'] for topic in topics]
            
            expected_topics = ['competitor_comparison', 'pricing', 'delivery_shipping']
            
            for expected_topic in expected_topics:
                if expected_topic in detected_topic_names:
                    print(f"✅ {expected_topic} topic detected")
                else:
                    print(f"⚠️  {expected_topic} topic not detected")
        
        return success, response

    def test_complex_business_topics(self):
        """Test complex business scenario with multiple topics"""
        complex_text = "Love the new features but concerned about security and privacy policies."
        success, response = self.run_test(
            "Complex Business Topics",
            "POST",
            "analyze-sentiment",
            200,
            data={"text": complex_text},
            timeout=60
        )
        
        if success:
            topics = response.get('topics_detected', [])
            detected_topic_names = [topic['topic'] for topic in topics]
            
            expected_topics = ['feature_requests', 'security_privacy', 'company_policies']
            
            for expected_topic in expected_topics:
                if expected_topic in detected_topic_names:
                    print(f"✅ {expected_topic} topic detected")
                else:
                    print(f"⚠️  {expected_topic} topic not detected")
        
        return success, response

    def test_topic_confidence_scores(self):
        """Test topic confidence scores and keywords"""
        confidence_text = "The customer support team was incredibly helpful, but the product quality is disappointing. The pricing seems reasonable, but the delivery took way too long."
        success, response = self.run_test(
            "Topic Confidence Scores",
            "POST",
            "analyze-sentiment",
            200,
            data={"text": confidence_text},
            timeout=60
        )
        
        if success:
            topics = response.get('topics_detected', [])
            
            print(f"   Topic confidence analysis:")
            for topic in topics:
                topic_name = topic.get('topic', 'unknown')
                confidence = topic.get('confidence', 0)
                keywords = topic.get('keywords', [])
                display_name = topic.get('display_name', topic_name)
                
                print(f"     {display_name}: {confidence:.2f} confidence, keywords: {keywords}")
                
                # Validate confidence is reasonable (>0.3 as per system message)
                if confidence < 0.3:
                    print(f"⚠️  Low confidence topic detected: {topic_name} ({confidence:.2f})")
                
                # Validate keywords exist
                if not keywords:
                    print(f"⚠️  No keywords provided for topic: {topic_name}")
        
        return success, response

    def test_all_topic_categories(self):
        """Test detection of all 12 topic categories"""
        topic_test_cases = {
            'customer_service': "The support team helped me resolve my issue quickly",
            'product_quality': "The build quality and materials are excellent", 
            'pricing': "The cost is too expensive for what you get",
            'delivery_shipping': "The package arrived late and shipping was slow",
            'user_experience': "The interface is confusing and hard to navigate",
            'technical_issues': "The software has bugs and keeps crashing",
            'marketing_advertising': "Their ads are misleading and annoying",
            'company_policies': "The terms and conditions are unclear",
            'competitor_comparison': "Brand Y offers better features than this",
            'feature_requests': "Please add dark mode and better search",
            'security_privacy': "I'm worried about my data being shared",
            'performance_speed': "The app is slow and takes forever to load"
        }
        
        detected_categories = set()
        
        for expected_topic, test_text in topic_test_cases.items():
            success, response = self.run_test(
                f"Topic Category - {expected_topic}",
                "POST",
                "analyze-sentiment",
                200,
                data={"text": test_text},
                timeout=60
            )
            
            if success:
                topics = response.get('topics_detected', [])
                detected_topic_names = [topic['topic'] for topic in topics]
                
                if expected_topic in detected_topic_names:
                    print(f"✅ {expected_topic} category detected")
                    detected_categories.add(expected_topic)
                else:
                    print(f"❌ {expected_topic} category NOT detected in relevant text")
            
            time.sleep(0.5)  # Brief pause between AI calls
        
        print(f"\n📊 Topic Category Coverage: {len(detected_categories)}/12 categories detected")
        missing_categories = set(topic_test_cases.keys()) - detected_categories
        if missing_categories:
            print(f"❌ Missing categories: {missing_categories}")
        else:
            print(f"✅ All topic categories successfully detected")
        
        return len(detected_categories) == 12, detected_categories

    # ASPECT-BASED SENTIMENT ANALYSIS TESTS - NEW FEATURE
    def test_restaurant_review_aspects(self):
        """Test aspect-based analysis with restaurant review"""
        restaurant_text = "The food was amazing and fresh, but the service was incredibly slow and the prices were too high"
        success, response = self.run_test(
            "Restaurant Review - Mixed Aspects",
            "POST",
            "analyze-sentiment",
            200,
            data={"text": restaurant_text},
            timeout=60
        )
        
        if success:
            aspects = response.get('aspects_analysis', [])
            aspects_summary = response.get('aspects_summary', '')
            
            print(f"   Aspects detected: {len(aspects)}")
            
            # Expected aspects for restaurant review
            expected_aspects = ['Food Quality', 'Service Quality', 'Price/Value']
            detected_aspect_names = [aspect['aspect'] for aspect in aspects]
            
            print(f"   Expected aspects: {expected_aspects}")
            print(f"   Detected aspects: {detected_aspect_names}")
            
            # Check for food quality (should be positive)
            food_aspects = [a for a in aspects if 'food' in a['aspect'].lower() or 'quality' in a['aspect'].lower()]
            if food_aspects:
                food_aspect = food_aspects[0]
                if food_aspect['sentiment'] == 'positive':
                    print(f"✅ Food quality correctly identified as positive")
                else:
                    print(f"⚠️  Food quality sentiment: {food_aspect['sentiment']} (expected positive)")
            else:
                print(f"⚠️  Food quality aspect not detected")
            
            # Check for service (should be negative)
            service_aspects = [a for a in aspects if 'service' in a['aspect'].lower()]
            if service_aspects:
                service_aspect = service_aspects[0]
                if service_aspect['sentiment'] == 'negative':
                    print(f"✅ Service quality correctly identified as negative")
                else:
                    print(f"⚠️  Service quality sentiment: {service_aspect['sentiment']} (expected negative)")
            else:
                print(f"⚠️  Service quality aspect not detected")
            
            # Check for price (should be negative)
            price_aspects = [a for a in aspects if 'price' in a['aspect'].lower() or 'value' in a['aspect'].lower()]
            if price_aspects:
                price_aspect = price_aspects[0]
                if price_aspect['sentiment'] == 'negative':
                    print(f"✅ Price/Value correctly identified as negative")
                else:
                    print(f"⚠️  Price/Value sentiment: {price_aspect['sentiment']} (expected negative)")
            else:
                print(f"⚠️  Price/Value aspect not detected")
            
            # Check aspects summary
            if aspects_summary:
                print(f"✅ Aspects summary provided: {aspects_summary}")
            else:
                print(f"⚠️  No aspects summary provided")
        
        return success, response

    def test_product_review_aspects(self):
        """Test aspect-based analysis with product review"""
        product_text = "Great build quality and fast shipping, but customer support was unhelpful when I had questions"
        success, response = self.run_test(
            "Product Review - Mixed Aspects",
            "POST",
            "analyze-sentiment",
            200,
            data={"text": product_text},
            timeout=60
        )
        
        if success:
            aspects = response.get('aspects_analysis', [])
            
            print(f"   Aspects detected: {len(aspects)}")
            
            # Expected aspects for product review
            expected_categories = ['build', 'shipping', 'support']
            
            for aspect in aspects:
                aspect_name = aspect['aspect']
                sentiment = aspect['sentiment']
                confidence = aspect['confidence']
                keywords = aspect['keywords']
                explanation = aspect['explanation']
                
                print(f"     {aspect_name}: {sentiment} ({confidence:.2f}) - {keywords}")
                print(f"       Explanation: {explanation}")
                
                # Validate confidence is reasonable
                if confidence < 0.4:
                    print(f"⚠️  Low confidence for aspect: {aspect_name}")
                
                # Check for expected positive aspects
                if any(word in aspect_name.lower() for word in ['build', 'quality', 'shipping']):
                    if sentiment == 'positive':
                        print(f"✅ {aspect_name} correctly positive")
                    else:
                        print(f"⚠️  {aspect_name} expected positive, got {sentiment}")
                
                # Check for expected negative aspects
                if any(word in aspect_name.lower() for word in ['support', 'customer']):
                    if sentiment == 'negative':
                        print(f"✅ {aspect_name} correctly negative")
                    else:
                        print(f"⚠️  {aspect_name} expected negative, got {sentiment}")
        
        return success, response

    def test_simple_positive_aspects(self):
        """Test aspect analysis with simple positive text"""
        simple_text = "I love this product!"
        success, response = self.run_test(
            "Simple Positive - Aspect Analysis",
            "POST",
            "analyze-sentiment",
            200,
            data={"text": simple_text},
            timeout=60
        )
        
        if success:
            aspects = response.get('aspects_analysis', [])
            aspects_summary = response.get('aspects_summary', '')
            
            print(f"   Aspects detected: {len(aspects)}")
            
            # Simple text may not have clear aspects
            if len(aspects) == 0:
                print(f"✅ No aspects detected in simple text (expected)")
            else:
                print(f"   Detected aspects in simple text:")
                for aspect in aspects:
                    print(f"     {aspect['aspect']}: {aspect['sentiment']}")
            
            # Aspects summary should handle case with no aspects
            if not aspects and not aspects_summary:
                print(f"✅ Empty aspects summary for text with no clear aspects")
            elif aspects_summary:
                print(f"   Aspects summary: {aspects_summary}")
        
        return success, response

    def test_empty_text_aspects(self):
        """Test aspect analysis error handling with empty text"""
        return self.run_test(
            "Empty Text - Aspect Analysis (Error Case)",
            "POST",
            "analyze-sentiment",
            400,
            data={"text": ""}
        )

    def test_service_feedback_aspects(self):
        """Test aspect analysis with service feedback"""
        service_text = "The staff was friendly and knowledgeable, but the location is hard to find and parking is terrible"
        success, response = self.run_test(
            "Service Feedback - Mixed Aspects",
            "POST",
            "analyze-sentiment",
            200,
            data={"text": service_text},
            timeout=60
        )
        
        if success:
            aspects = response.get('aspects_analysis', [])
            
            print(f"   Aspects detected: {len(aspects)}")
            
            # Look for staff/service aspects (should be positive)
            staff_aspects = [a for a in aspects if any(word in a['aspect'].lower() for word in ['staff', 'service', 'behavior'])]
            if staff_aspects:
                staff_aspect = staff_aspects[0]
                print(f"   Staff aspect: {staff_aspect['aspect']} - {staff_aspect['sentiment']}")
                if staff_aspect['sentiment'] == 'positive':
                    print(f"✅ Staff aspect correctly positive")
            
            # Look for location/parking aspects (should be negative)
            location_aspects = [a for a in aspects if any(word in a['aspect'].lower() for word in ['location', 'parking', 'ambiance'])]
            if location_aspects:
                location_aspect = location_aspects[0]
                print(f"   Location aspect: {location_aspect['aspect']} - {location_aspect['sentiment']}")
                if location_aspect['sentiment'] == 'negative':
                    print(f"✅ Location aspect correctly negative")
        
        return success, response

    def test_aspect_confidence_validation(self):
        """Test aspect confidence scores and validation"""
        confidence_text = "The user interface is intuitive and well-designed, the performance is lightning fast, but the documentation is confusing and incomplete"
        success, response = self.run_test(
            "Aspect Confidence Validation",
            "POST",
            "analyze-sentiment",
            200,
            data={"text": confidence_text},
            timeout=60
        )
        
        if success:
            aspects = response.get('aspects_analysis', [])
            
            print(f"   Aspect confidence analysis:")
            for aspect in aspects:
                aspect_name = aspect['aspect']
                sentiment = aspect['sentiment']
                confidence = aspect['confidence']
                keywords = aspect['keywords']
                
                print(f"     {aspect_name}: {sentiment} (confidence: {confidence:.2f})")
                print(f"       Keywords: {keywords}")
                
                # Validate confidence is in valid range
                if not (0 <= confidence <= 1):
                    print(f"❌ Invalid confidence range: {confidence}")
                    return False, response
                
                # Check for reasonable confidence (should be > 0.4 as per system message)
                if confidence < 0.4:
                    print(f"⚠️  Low confidence aspect: {aspect_name} ({confidence:.2f})")
                
                # Validate keywords exist and are relevant
                if not keywords:
                    print(f"⚠️  No keywords for aspect: {aspect_name}")
                elif len(keywords) > 5:
                    print(f"⚠️  Too many keywords for aspect: {aspect_name} ({len(keywords)} keywords)")
        
        return success, response

    def test_aspect_integration_with_existing_features(self):
        """Test that aspect analysis works alongside existing features"""
        integration_text = "Oh great, another 'premium' service with terrible customer support and overpriced features. Just what I needed!"
        success, response = self.run_test(
            "Aspect Integration with Sarcasm/Topics",
            "POST",
            "analyze-sentiment",
            200,
            data={"text": integration_text},
            timeout=60
        )
        
        if success:
            # Check all features are present
            has_sentiment = 'sentiment' in response
            has_sarcasm = 'sarcasm_detected' in response
            has_topics = 'topics_detected' in response
            has_aspects = 'aspects_analysis' in response
            has_emotions = 'emotions' in response
            
            print(f"   Feature integration check:")
            print(f"     Sentiment: {'✅' if has_sentiment else '❌'}")
            print(f"     Sarcasm: {'✅' if has_sarcasm else '❌'}")
            print(f"     Topics: {'✅' if has_topics else '❌'}")
            print(f"     Aspects: {'✅' if has_aspects else '❌'}")
            print(f"     Emotions: {'✅' if has_emotions else '❌'}")
            
            # Check sarcasm detection
            sarcasm_detected = response.get('sarcasm_detected', False)
            if sarcasm_detected:
                print(f"✅ Sarcasm detected in sarcastic text")
            else:
                print(f"⚠️  Sarcasm not detected in obvious sarcastic text")
            
            # Check aspects are detected despite sarcasm
            aspects = response.get('aspects_analysis', [])
            if aspects:
                print(f"✅ Aspects detected alongside sarcasm ({len(aspects)} aspects)")
                for aspect in aspects:
                    print(f"     {aspect['aspect']}: {aspect['sentiment']}")
            else:
                print(f"⚠️  No aspects detected in text with clear service/pricing mentions")
            
            # Check topics are detected
            topics = response.get('topics_detected', [])
            if topics:
                print(f"✅ Topics detected alongside aspects ({len(topics)} topics)")
            else:
                print(f"⚠️  No topics detected")
        
        return success, response

    def test_aspect_data_structure_validation(self):
        """Test aspect data structure validation thoroughly"""
        structure_text = "The mobile app crashes frequently but the web version works perfectly fine"
        success, response = self.run_test(
            "Aspect Data Structure Validation",
            "POST",
            "analyze-sentiment",
            200,
            data={"text": structure_text},
            timeout=60
        )
        
        if success:
            aspects = response.get('aspects_analysis', [])
            
            print(f"   Validating aspect data structures:")
            
            for i, aspect in enumerate(aspects):
                print(f"     Aspect {i+1}: {aspect.get('aspect', 'MISSING')}")
                
                # Check required fields
                required_fields = ['aspect', 'sentiment', 'confidence', 'keywords', 'explanation']
                for field in required_fields:
                    if field not in aspect:
                        print(f"❌ Missing required field: {field}")
                        return False, response
                    else:
                        print(f"       ✅ {field}: {type(aspect[field]).__name__}")
                
                # Validate field types
                if not isinstance(aspect['aspect'], str):
                    print(f"❌ aspect must be string, got {type(aspect['aspect'])}")
                    return False, response
                
                if aspect['sentiment'] not in ['positive', 'negative', 'neutral']:
                    print(f"❌ Invalid sentiment: {aspect['sentiment']}")
                    return False, response
                
                if not isinstance(aspect['confidence'], (int, float)) or not (0 <= aspect['confidence'] <= 1):
                    print(f"❌ Invalid confidence: {aspect['confidence']}")
                    return False, response
                
                if not isinstance(aspect['keywords'], list):
                    print(f"❌ keywords must be list, got {type(aspect['keywords'])}")
                    return False, response
                
                if not isinstance(aspect['explanation'], str):
                    print(f"❌ explanation must be string, got {type(aspect['explanation'])}")
                    return False, response
            
            print(f"✅ All aspect data structures are valid")
        
        return success, response

    # FILE UPLOAD AND BATCH PROCESSING TESTS - NEW FEATURE
    def run_file_upload_test(self, name, file_content, filename, expected_status, timeout=30):
        """Run a file upload test"""
        url = f"{self.api_url}/upload-file"
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        print(f"   File: {filename}")
        
        try:
            # Create file-like object
            files = {'file': (filename, file_content, 'application/octet-stream')}
            
            response = requests.post(url, files=files, timeout=timeout)
            print(f"   Status Code: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Expected {expected_status}, got {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:300]}...")
                    return True, response_data
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timed out after {timeout} seconds")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_upload_txt_file(self):
        """Test uploading a TXT file"""
        txt_content = """This product is amazing! I love the quality and design.
The customer service was excellent and very helpful.
However, the price is a bit high for what you get.
Overall, I'm satisfied with my purchase."""
        
        return self.run_file_upload_test(
            "Upload TXT File",
            txt_content.encode('utf-8'),
            "sample_reviews.txt",
            200
        )

    def test_upload_csv_file(self):
        """Test uploading a CSV file"""
        csv_content = """review_text,rating,category
"The food was delicious but service was slow",4,restaurant
"Great product quality and fast shipping",5,product
"Terrible customer support experience",1,service
"Amazing user interface and features",5,software"""
        
        return self.run_file_upload_test(
            "Upload CSV File",
            csv_content.encode('utf-8'),
            "reviews.csv",
            200
        )

    def test_upload_excel_file(self):
        """Test uploading an Excel file"""
        # Create a simple Excel file in memory
        try:
            import pandas as pd
            
            data = {
                'feedback': [
                    'Excellent service and quality products',
                    'Poor delivery experience and damaged items',
                    'Great value for money and fast support'
                ],
                'source': ['website', 'mobile_app', 'email'],
                'date': ['2024-01-01', '2024-01-02', '2024-01-03']
            }
            
            df = pd.DataFrame(data)
            excel_buffer = io.BytesIO()
            df.to_excel(excel_buffer, index=False)
            excel_content = excel_buffer.getvalue()
            
            return self.run_file_upload_test(
                "Upload Excel File",
                excel_content,
                "feedback.xlsx",
                200
            )
        except ImportError:
            print("⚠️  Pandas not available for Excel test, skipping...")
            return True, {}

    def test_upload_pdf_file(self):
        """Test uploading a PDF file"""
        # Create a simple PDF content (this is a minimal PDF structure)
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(This is a test review text.) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
299
%%EOF"""
        
        return self.run_file_upload_test(
            "Upload PDF File",
            pdf_content,
            "review.pdf",
            200
        )

    def test_upload_unsupported_file(self):
        """Test uploading unsupported file type"""
        content = b"This is a test file with unsupported extension"
        
        return self.run_file_upload_test(
            "Upload Unsupported File Type",
            content,
            "test.docx",
            400
        )

    def test_upload_large_file(self):
        """Test uploading file exceeding size limit"""
        # Create content larger than 5MB
        large_content = b"A" * (6 * 1024 * 1024)  # 6MB
        
        return self.run_file_upload_test(
            "Upload Large File (>5MB)",
            large_content,
            "large_file.txt",
            413
        )

    def test_upload_empty_file(self):
        """Test uploading empty file"""
        return self.run_file_upload_test(
            "Upload Empty File",
            b"",
            "empty.txt",
            400
        )

    def validate_file_upload_response(self, response_data):
        """Validate file upload response structure"""
        required_fields = ['file_id', 'filename', 'file_type', 'total_entries', 'extracted_texts', 'timestamp']
        
        print(f"\n🔍 Validating file upload response structure...")
        
        for field in required_fields:
            if field not in response_data:
                print(f"❌ Missing required field: {field}")
                return False
        
        # Validate file_id is UUID-like string
        if not isinstance(response_data['file_id'], str) or len(response_data['file_id']) < 10:
            print(f"❌ Invalid file_id format: {response_data['file_id']}")
            return False
        
        # Validate total_entries matches extracted_texts length
        if response_data['total_entries'] != len(response_data['extracted_texts']):
            print(f"❌ total_entries mismatch: {response_data['total_entries']} vs {len(response_data['extracted_texts'])}")
            return False
        
        # Validate extracted_texts structure
        for i, text_entry in enumerate(response_data['extracted_texts']):
            if not isinstance(text_entry, dict):
                print(f"❌ extracted_texts[{i}] must be dict")
                return False
            
            required_text_fields = ['text', 'row_number', 'metadata']
            for field in required_text_fields:
                if field not in text_entry:
                    print(f"❌ Missing field in extracted_texts[{i}]: {field}")
                    return False
            
            if not isinstance(text_entry['text'], str) or not text_entry['text'].strip():
                print(f"❌ Invalid text content in extracted_texts[{i}]")
                return False
        
        print(f"✅ File upload response structure is valid")
        print(f"   File ID: {response_data['file_id']}")
        print(f"   Filename: {response_data['filename']}")
        print(f"   File Type: {response_data['file_type']}")
        print(f"   Total Entries: {response_data['total_entries']}")
        
        return True

    def test_batch_analysis(self, file_id, extracted_texts, filename="test_file"):
        """Test batch sentiment analysis"""
        batch_data = {
            "file_id": file_id,
            "texts": extracted_texts[:3]  # Limit to first 3 entries for testing
        }
        
        return self.run_test(
            f"Batch Analysis - {filename}",
            "POST",
            "analyze-batch",
            200,
            data=batch_data,
            timeout=120  # Batch processing can take longer
        )

    def validate_batch_analysis_response(self, response_data):
        """Validate batch analysis response structure"""
        required_fields = ['batch_id', 'file_id', 'filename', 'total_processed', 'results', 'timestamp']
        
        print(f"\n🔍 Validating batch analysis response structure...")
        
        for field in required_fields:
            if field not in response_data:
                print(f"❌ Missing required field: {field}")
                return False
        
        # Validate batch_id is UUID-like string
        if not isinstance(response_data['batch_id'], str) or len(response_data['batch_id']) < 10:
            print(f"❌ Invalid batch_id format: {response_data['batch_id']}")
            return False
        
        # Validate total_processed matches results length
        if response_data['total_processed'] != len(response_data['results']):
            print(f"❌ total_processed mismatch: {response_data['total_processed']} vs {len(response_data['results'])}")
            return False
        
        # Validate each result has complete sentiment analysis
        for i, result in enumerate(response_data['results']):
            if not isinstance(result, dict):
                print(f"❌ results[{i}] must be dict")
                return False
            
            # Check for all sentiment analysis fields
            required_result_fields = [
                'id', 'text', 'row_number', 'metadata', 'sentiment', 'confidence', 
                'analysis', 'emotions', 'dominant_emotion', 'sarcasm_detected',
                'topics_detected', 'aspects_analysis', 'timestamp'
            ]
            
            for field in required_result_fields:
                if field not in result:
                    print(f"❌ Missing field in results[{i}]: {field}")
                    return False
            
            # Validate sentiment values
            if result['sentiment'] not in ['positive', 'negative', 'neutral']:
                print(f"❌ Invalid sentiment in results[{i}]: {result['sentiment']}")
                return False
            
            if not (0 <= result['confidence'] <= 1):
                print(f"❌ Invalid confidence in results[{i}]: {result['confidence']}")
                return False
        
        print(f"✅ Batch analysis response structure is valid")
        print(f"   Batch ID: {response_data['batch_id']}")
        print(f"   File ID: {response_data['file_id']}")
        print(f"   Filename: {response_data['filename']}")
        print(f"   Total Processed: {response_data['total_processed']}")
        
        # Show sample results
        if response_data['results']:
            sample_result = response_data['results'][0]
            print(f"   Sample Result:")
            print(f"     Text: {sample_result['text'][:50]}...")
            print(f"     Sentiment: {sample_result['sentiment']} ({sample_result['confidence']:.2f})")
            print(f"     Emotions: {len(sample_result.get('emotions', {}))} detected")
            print(f"     Topics: {len(sample_result.get('topics_detected', []))} detected")
            print(f"     Aspects: {len(sample_result.get('aspects_analysis', []))} detected")
        
        return True

    def test_batch_analysis_invalid_file_id(self):
        """Test batch analysis with invalid file ID"""
        batch_data = {
            "file_id": "invalid-file-id-12345",
            "texts": [{"text": "Test text", "row_number": 1, "metadata": {}}]
        }
        
        return self.run_test(
            "Batch Analysis - Invalid File ID",
            "POST",
            "analyze-batch",
            404,
            data=batch_data
        )

    def test_batch_analysis_empty_texts(self):
        """Test batch analysis with empty texts array"""
        batch_data = {
            "file_id": "test-file-id",
            "texts": []
        }
        
        return self.run_test(
            "Batch Analysis - Empty Texts",
            "POST",
            "analyze-batch",
            400,
            data=batch_data
        )

    def test_file_processing_dependencies(self):
        """Test that required file processing dependencies are available"""
        print(f"\n🔍 Testing File Processing Dependencies...")
        
        dependencies_available = True
        
        try:
            import pandas as pd
            print(f"✅ pandas: {pd.__version__}")
        except ImportError:
            print(f"❌ pandas: Not available")
            dependencies_available = False
        
        try:
            import PyPDF2
            print(f"✅ PyPDF2: {PyPDF2.__version__}")
        except ImportError:
            print(f"❌ PyPDF2: Not available")
            dependencies_available = False
        
        try:
            import openpyxl
            print(f"✅ openpyxl: {openpyxl.__version__}")
        except ImportError:
            print(f"❌ openpyxl: Not available")
            dependencies_available = False
        
        if dependencies_available:
            print(f"✅ All file processing dependencies are available")
            self.tests_passed += 1
        else:
            print(f"❌ Some file processing dependencies are missing")
        
        self.tests_run += 1
        return dependencies_available, {}

    def test_complete_file_upload_workflow(self):
        """Test complete workflow: upload file -> extract texts -> batch analyze"""
        print(f"\n🔄 Testing Complete File Upload Workflow...")
        
        # Step 1: Upload a file
        txt_content = """Great product with excellent build quality!
Terrible customer service experience.
The pricing is reasonable for the features offered.
Fast delivery and good packaging."""
        
        upload_success, upload_response = self.run_file_upload_test(
            "Workflow Step 1 - Upload File",
            txt_content.encode('utf-8'),
            "workflow_test.txt",
            200
        )
        
        if not upload_success:
            print(f"❌ Workflow failed at upload step")
            return False, {}
        
        # Validate upload response
        if not self.validate_file_upload_response(upload_response):
            print(f"❌ Workflow failed at upload validation")
            return False, {}
        
        # Step 2: Perform batch analysis
        file_id = upload_response['file_id']
        extracted_texts = upload_response['extracted_texts']
        
        batch_success, batch_response = self.test_batch_analysis(
            file_id, extracted_texts, "workflow_test.txt"
        )
        
        if not batch_success:
            print(f"❌ Workflow failed at batch analysis step")
            return False, {}
        
        # Validate batch response
        if not self.validate_batch_analysis_response(batch_response):
            print(f"❌ Workflow failed at batch validation")
            return False, {}
        
        # Step 3: Verify results make sense
        results = batch_response['results']
        # Note: test_batch_analysis limits to first 3 entries for testing efficiency
        expected_results = min(len(extracted_texts), 3)
        if len(results) != expected_results:
            print(f"❌ Results count mismatch: {len(results)} vs {expected_results} (limited from {len(extracted_texts)} total)")
            return False, {}
        
        # Check that different sentiments are detected
        sentiments = [result['sentiment'] for result in results]
        unique_sentiments = set(sentiments)
        
        print(f"   Detected sentiments: {sentiments}")
        print(f"   Unique sentiments: {list(unique_sentiments)}")
        
        if len(unique_sentiments) > 1:
            print(f"✅ Multiple sentiments detected in batch (good variation)")
        else:
            print(f"⚠️  All texts have same sentiment: {list(unique_sentiments)[0]}")
        
        # Check that aspects are detected in some results
        results_with_aspects = [r for r in results if r.get('aspects_analysis')]
        if results_with_aspects:
            print(f"✅ Aspects detected in {len(results_with_aspects)}/{len(results)} results")
        else:
            print(f"⚠️  No aspects detected in any results")
        
        # Check that topics are detected in some results
        results_with_topics = [r for r in results if r.get('topics_detected')]
        if results_with_topics:
            print(f"✅ Topics detected in {len(results_with_topics)}/{len(results)} results")
        else:
            print(f"⚠️  No topics detected in any results")
        
        print(f"✅ Complete workflow test passed")
        return True, batch_response

def main():
    print("🚀 Starting Brand Watch AI Backend API Tests - File Upload & Batch Processing Feature")
    print("=" * 80)
    
    tester = BrandWatchAPITester()
    
    # Test basic connectivity
    success, _ = tester.test_root_endpoint()
    if not success:
        print("\n❌ Basic API connectivity failed. Stopping tests.")
        return 1

    # NEW: Test file processing dependencies first - MAIN FOCUS
    print("\n📦 Testing File Processing Dependencies - NEW FEATURE")
    print("-" * 55)
    deps_success, _ = tester.test_file_processing_dependencies()
    if not deps_success:
        print("\n⚠️  Some dependencies missing, but continuing with tests...")

    # NEW: Test file upload functionality - MAIN FOCUS
    print("\n📁 Testing File Upload Functionality - NEW FEATURE")
    print("-" * 50)
    
    # Test TXT file upload
    txt_success, txt_response = tester.test_upload_txt_file()
    if txt_success:
        tester.validate_file_upload_response(txt_response)
    
    # Test CSV file upload
    csv_success, csv_response = tester.test_upload_csv_file()
    if csv_success:
        tester.validate_file_upload_response(csv_response)
    
    # Test Excel file upload
    excel_success, excel_response = tester.test_upload_excel_file()
    if excel_success and excel_response:  # Skip if pandas not available
        tester.validate_file_upload_response(excel_response)
    
    # Test PDF file upload
    pdf_success, pdf_response = tester.test_upload_pdf_file()
    if pdf_success:
        tester.validate_file_upload_response(pdf_response)
    
    # Test file upload error cases
    print("\n🚨 Testing File Upload Error Handling")
    print("-" * 40)
    tester.test_upload_unsupported_file()
    tester.test_upload_large_file()
    tester.test_upload_empty_file()

    # NEW: Test batch analysis functionality - MAIN FOCUS
    print("\n⚡ Testing Batch Analysis Functionality - NEW FEATURE")
    print("-" * 55)
    
    # Test batch analysis with uploaded files
    if txt_success and txt_response:
        batch_success, batch_response = tester.test_batch_analysis(
            txt_response['file_id'], 
            txt_response['extracted_texts'], 
            txt_response['filename']
        )
        if batch_success:
            tester.validate_batch_analysis_response(batch_response)
    
    if csv_success and csv_response:
        batch_success, batch_response = tester.test_batch_analysis(
            csv_response['file_id'], 
            csv_response['extracted_texts'], 
            csv_response['filename']
        )
        if batch_success:
            tester.validate_batch_analysis_response(batch_response)
    
    # Test batch analysis error cases
    print("\n🚨 Testing Batch Analysis Error Handling")
    print("-" * 45)
    tester.test_batch_analysis_invalid_file_id()
    tester.test_batch_analysis_empty_texts()

    # NEW: Test complete workflow - MAIN FOCUS
    print("\n🔄 Testing Complete File Upload & Batch Analysis Workflow - NEW FEATURE")
    print("-" * 70)
    workflow_success, workflow_response = tester.test_complete_file_upload_workflow()

    # Test sentiment analysis with different text types
    print("\n📊 Testing Basic Sentiment Analysis Functionality")
    print("-" * 50)
    
    # Test positive sentiment
    success, positive_response = tester.test_analyze_sentiment_positive()
    if success:
        tester.validate_sentiment_response(positive_response)
    
    # Test negative sentiment  
    success, negative_response = tester.test_analyze_sentiment_negative()
    if success:
        tester.validate_sentiment_response(negative_response)
    
    # Test neutral sentiment
    success, neutral_response = tester.test_analyze_sentiment_neutral()
    if success:
        tester.validate_sentiment_response(neutral_response)

    # NEW: Test topic detection feature - MAIN FOCUS
    print("\n🏷️  Testing Topic Detection Feature - NEW FEATURE")
    print("-" * 50)
    
    # Test single topic detection
    success, single_topic_response = tester.test_single_topic_customer_service()
    if success:
        tester.validate_sentiment_response(single_topic_response)
    time.sleep(1)
    
    # Test multi-topic business scenario
    success, multi_topic_response = tester.test_multi_topic_business_text()
    if success:
        tester.validate_sentiment_response(multi_topic_response)
    time.sleep(1)
    
    # Test technical focus topics
    success, technical_response = tester.test_technical_focus_topics()
    if success:
        tester.validate_sentiment_response(technical_response)
    time.sleep(1)
    
    # Test competitor comparison
    success, competitor_response = tester.test_competitor_comparison_topic()
    if success:
        tester.validate_sentiment_response(competitor_response)
    time.sleep(1)
    
    # Test complex business topics
    success, complex_response = tester.test_complex_business_topics()
    if success:
        tester.validate_sentiment_response(complex_response)
    time.sleep(1)
    
    # Test topic confidence scores and keywords
    success, confidence_response = tester.test_topic_confidence_scores()
    if success:
        tester.validate_sentiment_response(confidence_response)
    time.sleep(1)
    
    # Test all 12 topic categories
    print("\n🎯 Testing All 12 Topic Categories")
    print("-" * 40)
    all_categories_success, detected_categories = tester.test_all_topic_categories()

    # NEW: Test aspect-based sentiment analysis feature - MAIN FOCUS
    print("\n🎯 Testing Aspect-Based Sentiment Analysis Feature - NEW FEATURE")
    print("-" * 60)
    
    # Test restaurant review with mixed aspects
    success, restaurant_response = tester.test_restaurant_review_aspects()
    if success:
        tester.validate_sentiment_response(restaurant_response)
    time.sleep(1)
    
    # Test product review with mixed aspects
    success, product_response = tester.test_product_review_aspects()
    if success:
        tester.validate_sentiment_response(product_response)
    time.sleep(1)
    
    # Test simple positive text
    success, simple_response = tester.test_simple_positive_aspects()
    if success:
        tester.validate_sentiment_response(simple_response)
    time.sleep(1)
    
    # Test service feedback
    success, service_response = tester.test_service_feedback_aspects()
    if success:
        tester.validate_sentiment_response(service_response)
    time.sleep(1)
    
    # Test aspect confidence validation
    success, confidence_response = tester.test_aspect_confidence_validation()
    if success:
        tester.validate_sentiment_response(confidence_response)
    time.sleep(1)
    
    # Test integration with existing features
    success, integration_response = tester.test_aspect_integration_with_existing_features()
    if success:
        tester.validate_sentiment_response(integration_response)
    time.sleep(1)
    
    # Test aspect data structure validation
    success, structure_response = tester.test_aspect_data_structure_validation()
    if success:
        tester.validate_sentiment_response(structure_response)
    time.sleep(1)
    
    # Test empty text error handling for aspects
    tester.test_empty_text_aspects()

    # Test emotion detection with specific emotional texts
    print("\n🎭 Testing Emotion Detection Feature")
    print("-" * 40)
    
    # Test joy detection
    success, joy_response = tester.test_emotion_detection_joy()
    if success:
        tester.validate_sentiment_response(joy_response)
    
    # Test mixed emotions
    success, mixed_response = tester.test_emotion_detection_mixed()
    if success:
        tester.validate_sentiment_response(mixed_response)
    
    # Test anger detection
    success, anger_response = tester.test_emotion_detection_anger()
    if success:
        tester.validate_sentiment_response(anger_response)
    
    # Test fear detection
    success, fear_response = tester.test_emotion_detection_fear()
    if success:
        tester.validate_sentiment_response(fear_response)

    # Test sarcasm detection feature
    print("\n🎭 Testing Sarcasm Detection Feature")
    print("-" * 40)
    
    # Test high sarcasm
    success, high_sarcasm_response = tester.test_high_sarcasm_detection()
    if success:
        tester.validate_sentiment_response(high_sarcasm_response)
    time.sleep(1)  # Brief pause between AI calls
    
    # Test subtle sarcasm
    success, subtle_sarcasm_response = tester.test_subtle_sarcasm_detection()
    if success:
        tester.validate_sentiment_response(subtle_sarcasm_response)
    time.sleep(1)
    
    # Test quoted sarcasm
    success, quoted_sarcasm_response = tester.test_quoted_sarcasm_detection()
    if success:
        tester.validate_sentiment_response(quoted_sarcasm_response)
    time.sleep(1)
    
    # Test non-sarcastic positive (should NOT detect sarcasm)
    success, non_sarcastic_pos_response = tester.test_non_sarcastic_positive()
    if success:
        tester.validate_sentiment_response(non_sarcastic_pos_response)
    time.sleep(1)
    
    # Test non-sarcastic negative (should NOT detect sarcasm)
    success, non_sarcastic_neg_response = tester.test_non_sarcastic_negative()
    if success:
        tester.validate_sentiment_response(non_sarcastic_neg_response)
    time.sleep(1)
    
    # Test mixed sarcasm with emotions
    success, mixed_sarcasm_response = tester.test_mixed_sarcasm_emotions()
    if success:
        tester.validate_sentiment_response(mixed_sarcasm_response)
    time.sleep(1)
    
    # Test sentiment adjustment logic
    success, adjustment_response = tester.test_sentiment_adjustment_logic()
    if success:
        tester.validate_sentiment_response(adjustment_response)

    # Test error handling
    print("\n🚨 Testing Error Handling")
    print("-" * 30)
    tester.test_analyze_sentiment_empty_text()
    tester.test_analyze_sentiment_whitespace_only()

    # Test history endpoint
    print("\n📚 Testing History Functionality")
    print("-" * 35)
    success, history_response = tester.test_sentiment_history()
    if success and isinstance(history_response, list):
        print(f"   History contains {len(history_response)} entries")
        # Check if recent entries have topic data
        if len(history_response) > 0:
            recent_entry = history_response[0]
            has_topic_fields = all(field in recent_entry for field in ['topics_detected', 'primary_topic', 'topic_summary'])
            if has_topic_fields:
                print(f"✅ Recent entries include topic detection data")
                # Show topic stats from history
                entries_with_topics = [entry for entry in history_response if entry.get('topics_detected') and len(entry.get('topics_detected', [])) > 0]
                print(f"   Entries with topics in history: {len(entries_with_topics)}/{len(history_response)}")
                
                # Show primary topic distribution
                primary_topics = [entry.get('primary_topic') for entry in entries_with_topics if entry.get('primary_topic')]
                if primary_topics:
                    from collections import Counter
                    topic_counts = Counter(primary_topics)
                    print(f"   Primary topic distribution: {dict(topic_counts)}")
            else:
                print(f"⚠️  Recent entries may not have topic detection data")
            
            # Check sarcasm data too
            has_sarcasm_fields = all(field in recent_entry for field in ['sarcasm_detected', 'sarcasm_confidence', 'adjusted_sentiment'])
            if has_sarcasm_fields:
                print(f"✅ Recent entries include sarcasm detection data")
                # Show sarcasm stats from history
                sarcastic_entries = [entry for entry in history_response if entry.get('sarcasm_detected', False)]
                print(f"   Sarcastic entries in history: {len(sarcastic_entries)}/{len(history_response)}")
            else:
                print(f"⚠️  Recent entries may not have sarcasm detection data")

    # Print final results
    print("\n" + "=" * 70)
    print(f"📊 FINAL RESULTS: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    # Special focus on file upload and batch processing results - MAIN FOCUS
    print(f"\n📁 FILE UPLOAD & BATCH PROCESSING SUMMARY - NEW FEATURE:")
    print(f"   Dependencies available: {'✅ YES' if deps_success else '❌ NO'}")
    print(f"   TXT file upload: {'✅ WORKING' if txt_success else '❌ FAILED'}")
    print(f"   CSV file upload: {'✅ WORKING' if csv_success else '❌ FAILED'}")
    print(f"   Excel file upload: {'✅ WORKING' if excel_success and excel_response else '⚠️ SKIPPED/FAILED'}")
    print(f"   PDF file upload: {'✅ WORKING' if pdf_success else '❌ FAILED'}")
    print(f"   Complete workflow: {'✅ WORKING' if workflow_success else '❌ FAILED'}")
    
    # Check if all file formats are supported
    file_formats_working = sum([txt_success, csv_success, pdf_success, excel_success and bool(excel_response)])
    print(f"   Supported file formats: {file_formats_working}/4 (TXT, CSV, Excel, PDF)")
    
    # Special focus on topic detection results
    print(f"\n🏷️  TOPIC DETECTION SUMMARY:")
    print(f"   All 12 categories detected: {'✅ YES' if all_categories_success else '❌ NO'}")
    if not all_categories_success:
        print(f"   Categories detected: {len(detected_categories)}/12")
    
    # Special focus on aspect-based analysis results
    print(f"\n🎯 ASPECT-BASED ANALYSIS SUMMARY:")
    print(f"   Restaurant review aspects: {'✅ TESTED' if 'restaurant_response' in locals() else '❌ NOT TESTED'}")
    print(f"   Product review aspects: {'✅ TESTED' if 'product_response' in locals() else '❌ NOT TESTED'}")
    print(f"   Integration with existing features: {'✅ TESTED' if 'integration_response' in locals() else '❌ NOT TESTED'}")
    print(f"   Data structure validation: {'✅ TESTED' if 'structure_response' in locals() else '❌ NOT TESTED'}")
    
    # Overall assessment
    critical_features_working = all([
        txt_success,  # TXT upload must work
        csv_success,  # CSV upload must work  
        workflow_success,  # Complete workflow must work
        deps_success  # Dependencies must be available
    ])
    
    if critical_features_working:
        print(f"\n🎉 All critical file upload and batch processing features are working!")
    else:
        print(f"\n⚠️  Some critical file upload and batch processing features failed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All backend tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())