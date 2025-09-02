import requests
import sys
import json
import time
from datetime import datetime

class BrandWatchAPITester:
    def __init__(self, base_url="https://prinsight.preview.emergentagent.com"):
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
        """Validate sentiment analysis response structure including emotion detection"""
        required_fields = ['id', 'text', 'sentiment', 'confidence', 'analysis', 'timestamp', 'emotions', 'dominant_emotion']
        valid_sentiments = ['positive', 'negative', 'neutral']
        expected_emotions = ['joy', 'sadness', 'anger', 'fear', 'trust', 'disgust', 'surprise', 'anticipation']
        
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

        print(f"✅ Response structure is valid")
        print(f"   Dominant emotion: {dominant_emotion} ({emotions.get(dominant_emotion, 0):.2f})")
        print(f"   Top 3 emotions: {sorted(emotions.items(), key=lambda x: x[1], reverse=True)[:3]}")
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

def main():
    print("🚀 Starting Brand Watch AI Backend API Tests - Emotion Detection Feature")
    print("=" * 70)
    
    tester = BrandWatchAPITester()
    
    # Test basic connectivity
    success, _ = tester.test_root_endpoint()
    if not success:
        print("\n❌ Basic API connectivity failed. Stopping tests.")
        return 1

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
        # Check if recent entries have emotion data
        if len(history_response) > 0:
            recent_entry = history_response[0]
            if 'emotions' in recent_entry and 'dominant_emotion' in recent_entry:
                print(f"✅ Recent entries include emotion data")
            else:
                print(f"⚠️  Recent entries may not have emotion data")

    # Print final results
    print("\n" + "=" * 70)
    print(f"📊 FINAL RESULTS: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All backend tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())