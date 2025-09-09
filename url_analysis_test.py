#!/usr/bin/env python3
"""
Focused URL Analysis Testing Script
Tests the newly implemented URL analysis functionality
"""

import requests
import json
import time
import sys

class URLAnalysisTester:
    def __init__(self, base_url="https://brand-monitor-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=60):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
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

    def test_web_scraping_dependencies(self):
        """Test that web scraping dependencies are available"""
        print(f"\n🔍 Testing Web Scraping Dependencies...")
        
        dependencies_available = True
        
        try:
            import requests
            print(f"✅ requests: {requests.__version__}")
        except ImportError:
            print(f"❌ requests: Not available")
            dependencies_available = False
        
        try:
            import bs4
            print(f"✅ beautifulsoup4: {bs4.__version__}")
        except ImportError:
            print(f"❌ beautifulsoup4: Not available")
            dependencies_available = False
        
        try:
            import newspaper
            print(f"✅ newspaper3k: Available")
        except ImportError:
            print(f"❌ newspaper3k: Not available")
            dependencies_available = False
        
        try:
            import lxml
            print(f"✅ lxml: {lxml.__version__}")
        except ImportError:
            print(f"❌ lxml: Not available")
            dependencies_available = False
        
        try:
            import html5lib
            print(f"✅ html5lib: {html5lib.__version__}")
        except ImportError:
            print(f"❌ html5lib: Not available")
            dependencies_available = False
        
        if dependencies_available:
            print(f"✅ All web scraping dependencies are available")
            self.tests_passed += 1
        else:
            print(f"❌ Some web scraping dependencies are missing")
        
        self.tests_run += 1
        return dependencies_available

    def test_single_url_analysis(self):
        """Test single URL analysis"""
        url_data = {
            "url": "https://httpbin.org/html",  # Simple HTML page for testing
            "extract_full_content": True,
            "include_metadata": True
        }
        
        return self.run_test(
            "Single URL Analysis",
            "POST",
            "analyze-url",
            200,
            data=url_data,
            timeout=90
        )

    def test_url_validation_invalid_format(self):
        """Test URL validation with invalid format"""
        url_data = {
            "url": "not-a-valid-url",
            "extract_full_content": True,
            "include_metadata": True
        }
        
        return self.run_test(
            "URL Validation - Invalid Format",
            "POST",
            "analyze-url",
            400,
            data=url_data
        )

    def test_url_validation_unsupported_protocol(self):
        """Test URL validation with unsupported protocol"""
        url_data = {
            "url": "ftp://example.com/file.txt",
            "extract_full_content": True,
            "include_metadata": True
        }
        
        return self.run_test(
            "URL Validation - Unsupported Protocol",
            "POST",
            "analyze-url",
            400,
            data=url_data
        )

    def test_batch_url_analysis(self):
        """Test batch URL analysis"""
        batch_data = {
            "urls": [
                "https://httpbin.org/html",
                "https://httpbin.org/json"
            ],
            "extract_full_content": True,
            "include_metadata": True
        }
        
        return self.run_test(
            "Batch URL Analysis",
            "POST",
            "analyze-batch-urls",
            200,
            data=batch_data,
            timeout=120
        )

    def test_batch_url_empty_list(self):
        """Test batch URL analysis with empty list"""
        batch_data = {
            "urls": [],
            "extract_full_content": True,
            "include_metadata": True
        }
        
        return self.run_test(
            "Batch URL Analysis - Empty List",
            "POST",
            "analyze-batch-urls",
            400,
            data=batch_data
        )

    def test_batch_url_too_many(self):
        """Test batch URL analysis with too many URLs"""
        urls = [f"https://httpbin.org/status/{200 + i}" for i in range(21)]  # 21 URLs
        batch_data = {
            "urls": urls,
            "extract_full_content": True,
            "include_metadata": True
        }
        
        return self.run_test(
            "Batch URL Analysis - Too Many URLs",
            "POST",
            "analyze-batch-urls",
            400,
            data=batch_data
        )

    def validate_url_response(self, response_data):
        """Validate URL analysis response structure"""
        required_fields = [
            'id', 'url', 'extracted_text', 'text_length', 'sentiment', 
            'confidence', 'analysis', 'emotions', 'dominant_emotion',
            'sarcasm_detected', 'topics_detected', 'aspects_analysis',
            'metadata', 'processing_time', 'timestamp'
        ]
        
        print(f"\n🔍 Validating URL analysis response...")
        
        for field in required_fields:
            if field not in response_data:
                print(f"❌ Missing required field: {field}")
                return False
        
        # Validate basic structure
        if not isinstance(response_data['url'], str):
            print(f"❌ URL must be string")
            return False
        
        if not isinstance(response_data['extracted_text'], str):
            print(f"❌ extracted_text must be string")
            return False
        
        if response_data['sentiment'] not in ['positive', 'negative', 'neutral']:
            print(f"❌ Invalid sentiment: {response_data['sentiment']}")
            return False
        
        if not (0 <= response_data['confidence'] <= 1):
            print(f"❌ Invalid confidence: {response_data['confidence']}")
            return False
        
        print(f"✅ URL analysis response structure is valid")
        print(f"   URL: {response_data['url']}")
        print(f"   Text Length: {response_data['text_length']} characters")
        print(f"   Sentiment: {response_data['sentiment']} ({response_data['confidence']:.2f})")
        print(f"   Processing Time: {response_data['processing_time']:.2f}s")
        print(f"   Topics: {len(response_data.get('topics_detected', []))} detected")
        print(f"   Aspects: {len(response_data.get('aspects_analysis', []))} detected")
        
        return True

    def validate_batch_url_response(self, response_data):
        """Validate batch URL analysis response structure"""
        required_fields = [
            'batch_id', 'total_requested', 'total_processed', 'total_failed',
            'results', 'failed_urls', 'processing_time', 'timestamp'
        ]
        
        print(f"\n🔍 Validating batch URL analysis response...")
        
        for field in required_fields:
            if field not in response_data:
                print(f"❌ Missing required field: {field}")
                return False
        
        # Validate counts
        total_requested = response_data['total_requested']
        total_processed = response_data['total_processed']
        total_failed = response_data['total_failed']
        
        if total_processed + total_failed != total_requested:
            print(f"❌ Count mismatch: processed({total_processed}) + failed({total_failed}) != requested({total_requested})")
            return False
        
        print(f"✅ Batch URL analysis response structure is valid")
        print(f"   Total Requested: {total_requested}")
        print(f"   Successfully Processed: {total_processed}")
        print(f"   Failed: {total_failed}")
        print(f"   Processing Time: {response_data['processing_time']:.2f}s")
        
        return True

def main():
    print("🌐 URL Analysis Testing - Brand Watch AI")
    print("=" * 50)
    
    tester = URLAnalysisTester()
    
    # Test basic API connectivity
    print("\n🔍 Testing Basic API Connectivity...")
    try:
        response = requests.get(f"{tester.api_url}/", timeout=10)
        if response.status_code == 200:
            print("✅ API is accessible")
        else:
            print(f"❌ API returned status {response.status_code}")
            return 1
    except Exception as e:
        print(f"❌ API connectivity failed: {e}")
        return 1
    
    # Test web scraping dependencies
    print("\n🔧 Testing Web Scraping Dependencies")
    print("-" * 40)
    deps_success = tester.test_web_scraping_dependencies()
    
    # Test single URL analysis
    print("\n🌐 Testing Single URL Analysis")
    print("-" * 35)
    single_success, single_response = tester.test_single_url_analysis()
    if single_success:
        tester.validate_url_response(single_response)
    
    # Test URL validation
    print("\n🚨 Testing URL Validation")
    print("-" * 30)
    tester.test_url_validation_invalid_format()
    tester.test_url_validation_unsupported_protocol()
    
    # Test batch URL analysis
    print("\n⚡ Testing Batch URL Analysis")
    print("-" * 35)
    batch_success, batch_response = tester.test_batch_url_analysis()
    if batch_success:
        tester.validate_batch_url_response(batch_response)
    
    # Test batch URL validation
    print("\n🚨 Testing Batch URL Validation")
    print("-" * 40)
    tester.test_batch_url_empty_list()
    tester.test_batch_url_too_many()
    
    # Final results
    print("\n" + "=" * 50)
    print(f"📊 FINAL RESULTS: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    print(f"\n🌐 URL ANALYSIS SUMMARY:")
    print(f"   Dependencies: {'✅ WORKING' if deps_success else '❌ FAILED'}")
    print(f"   Single URL Analysis: {'✅ WORKING' if single_success else '❌ FAILED'}")
    print(f"   Batch URL Analysis: {'✅ WORKING' if batch_success else '❌ FAILED'}")
    
    # Overall assessment
    critical_features_working = all([deps_success, single_success, batch_success])
    
    if critical_features_working:
        print(f"\n🎉 All critical URL analysis features are working!")
        return 0
    else:
        print(f"\n⚠️  Some critical URL analysis features failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())