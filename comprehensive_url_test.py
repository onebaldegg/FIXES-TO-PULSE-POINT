#!/usr/bin/env python3
"""
Comprehensive URL Analysis Testing
Tests real-world scenarios and content extraction quality
"""

import requests
import json
import time

def test_real_world_urls():
    """Test URL analysis with real-world URLs"""
    api_url = "https://sentimentmatrix.preview.emergentagent.com/api"
    
    # Test cases with different types of content
    test_urls = [
        {
            "name": "News Article (BBC)",
            "url": "https://www.bbc.com/news",
            "expected_topics": ["news", "current_events"]
        },
        {
            "name": "Tech Blog (GitHub)",
            "url": "https://github.blog",
            "expected_topics": ["technology", "software"]
        },
        {
            "name": "Simple HTML (httpbin)",
            "url": "https://httpbin.org/html",
            "expected_topics": []
        }
    ]
    
    print("🌐 Testing Real-World URL Analysis")
    print("=" * 40)
    
    for test_case in test_urls:
        print(f"\n🔍 Testing {test_case['name']}")
        print(f"   URL: {test_case['url']}")
        
        try:
            # Test single URL analysis
            url_data = {
                "url": test_case['url'],
                "extract_full_content": True,
                "include_metadata": True
            }
            
            response = requests.post(
                f"{api_url}/analyze-url",
                json=url_data,
                headers={'Content-Type': 'application/json'},
                timeout=90
            )
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"✅ Successfully analyzed")
                print(f"   Title: {data.get('title', 'N/A')[:60]}...")
                print(f"   Author: {data.get('author', 'N/A')}")
                print(f"   Text Length: {data.get('text_length', 0)} characters")
                print(f"   Sentiment: {data.get('sentiment')} ({data.get('confidence', 0):.2f})")
                print(f"   Processing Time: {data.get('processing_time', 0):.2f}s")
                
                # Check metadata
                metadata = data.get('metadata', {})
                if metadata:
                    print(f"   Extraction Method: {metadata.get('extraction_method', 'unknown')}")
                    print(f"   Domain: {metadata.get('domain', 'unknown')}")
                    print(f"   Word Count: {metadata.get('word_count', 0)}")
                
                # Check sentiment analysis features
                emotions = data.get('emotions', {})
                topics = data.get('topics_detected', [])
                aspects = data.get('aspects_analysis', [])
                
                print(f"   Emotions: {len(emotions)} detected")
                if emotions:
                    dominant = max(emotions, key=emotions.get)
                    print(f"     Dominant: {dominant} ({emotions[dominant]:.2f})")
                
                print(f"   Topics: {len(topics)} detected")
                for topic in topics[:3]:  # Show first 3 topics
                    print(f"     {topic.get('display_name', topic.get('topic', 'unknown'))}: {topic.get('confidence', 0):.2f}")
                
                print(f"   Aspects: {len(aspects)} detected")
                for aspect in aspects[:3]:  # Show first 3 aspects
                    print(f"     {aspect.get('aspect', 'unknown')}: {aspect.get('sentiment', 'unknown')} ({aspect.get('confidence', 0):.2f})")
                
                # Check sarcasm detection
                if data.get('sarcasm_detected'):
                    print(f"   Sarcasm: Detected ({data.get('sarcasm_confidence', 0):.2f})")
                    print(f"     Adjusted Sentiment: {data.get('adjusted_sentiment')}")
                
            else:
                print(f"❌ Failed with status {response.status_code}")
                try:
                    error = response.json()
                    print(f"   Error: {error}")
                except:
                    print(f"   Error: {response.text}")
        
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        time.sleep(2)  # Brief pause between requests

def test_batch_url_analysis():
    """Test batch URL analysis with multiple URLs"""
    api_url = "https://sentimentmatrix.preview.emergentagent.com/api"
    
    print(f"\n⚡ Testing Batch URL Analysis")
    print("=" * 35)
    
    # Test with a mix of URLs
    batch_data = {
        "urls": [
            "https://httpbin.org/html",
            "https://httpbin.org/json",
            "https://www.example.com"  # Simple page
        ],
        "extract_full_content": True,
        "include_metadata": True
    }
    
    try:
        response = requests.post(
            f"{api_url}/analyze-batch-urls",
            json=batch_data,
            headers={'Content-Type': 'application/json'},
            timeout=180
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Batch analysis completed")
            print(f"   Batch ID: {data.get('batch_id')}")
            print(f"   Total Requested: {data.get('total_requested')}")
            print(f"   Successfully Processed: {data.get('total_processed')}")
            print(f"   Failed: {data.get('total_failed')}")
            print(f"   Processing Time: {data.get('processing_time', 0):.2f}s")
            
            # Show results summary
            results = data.get('results', [])
            failed_urls = data.get('failed_urls', [])
            
            print(f"\n   Results Summary:")
            for i, result in enumerate(results):
                print(f"     {i+1}. {result.get('url')}")
                print(f"        Text: {result.get('text_length', 0)} chars")
                print(f"        Sentiment: {result.get('sentiment')} ({result.get('confidence', 0):.2f})")
                print(f"        Topics: {len(result.get('topics_detected', []))}")
                print(f"        Aspects: {len(result.get('aspects_analysis', []))}")
            
            if failed_urls:
                print(f"\n   Failed URLs:")
                for failed in failed_urls:
                    print(f"     {failed.get('url')}: {failed.get('error')}")
        
        else:
            print(f"❌ Failed with status {response.status_code}")
            try:
                error = response.json()
                print(f"   Error: {error}")
            except:
                print(f"   Error: {response.text}")
    
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_error_handling():
    """Test error handling scenarios"""
    api_url = "https://sentimentmatrix.preview.emergentagent.com/api"
    
    print(f"\n🚨 Testing Error Handling")
    print("=" * 30)
    
    error_test_cases = [
        {
            "name": "Invalid URL Format",
            "data": {"url": "not-a-url", "extract_full_content": True},
            "expected_status": 400
        },
        {
            "name": "Non-existent Domain",
            "data": {"url": "https://this-domain-does-not-exist-12345.com", "extract_full_content": True},
            "expected_status": 500
        },
        {
            "name": "Unsupported Protocol",
            "data": {"url": "ftp://example.com/file.txt", "extract_full_content": True},
            "expected_status": 400
        }
    ]
    
    for test_case in error_test_cases:
        print(f"\n🔍 Testing {test_case['name']}")
        
        try:
            response = requests.post(
                f"{api_url}/analyze-url",
                json=test_case['data'],
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == test_case['expected_status']:
                print(f"✅ Correct error handling (status {response.status_code})")
                try:
                    error_data = response.json()
                    print(f"   Error message: {error_data.get('detail', 'No detail')}")
                except:
                    pass
            else:
                print(f"❌ Unexpected status: {response.status_code} (expected {test_case['expected_status']})")
        
        except Exception as e:
            print(f"❌ Exception: {e}")

def main():
    print("🌐 Comprehensive URL Analysis Testing")
    print("=" * 50)
    
    # Test real-world URLs
    test_real_world_urls()
    
    # Test batch processing
    test_batch_url_analysis()
    
    # Test error handling
    test_error_handling()
    
    print(f"\n🎉 Comprehensive URL analysis testing completed!")

if __name__ == "__main__":
    main()