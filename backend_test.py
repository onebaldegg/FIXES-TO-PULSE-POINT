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
        """Validate sentiment analysis response structure including emotion and sarcasm detection"""
        required_fields = ['id', 'text', 'sentiment', 'confidence', 'analysis', 'timestamp', 'emotions', 'dominant_emotion',
                          'sarcasm_detected', 'sarcasm_confidence', 'sarcasm_explanation', 'adjusted_sentiment', 'sarcasm_indicators']
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

        print(f"✅ Response structure is valid")
        print(f"   Sentiment: {response_data['sentiment']} -> {response_data['adjusted_sentiment']}")
        print(f"   Sarcasm: {response_data['sarcasm_detected']} ({response_data['sarcasm_confidence']:.2f})")
        print(f"   Dominant emotion: {dominant_emotion} ({emotions.get(dominant_emotion, 0):.2f})")
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

def main():
    print("🚀 Starting Brand Watch AI Backend API Tests - Sarcasm Detection Feature")
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

    # NEW: Test sarcasm detection feature
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
        # Check if recent entries have sarcasm data
        if len(history_response) > 0:
            recent_entry = history_response[0]
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
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All backend tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())