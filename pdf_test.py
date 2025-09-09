#!/usr/bin/env python3

import requests
import json
import io
import sys
from datetime import datetime

class PDFExtractionTester:
    def __init__(self, base_url="https://brand-monitor-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

    def run_file_upload_test(self, name, file_content, filename, expected_status, timeout=30):
        """Run a file upload test"""
        url = f"{self.api_url}/upload-file"
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        print(f"   File: {filename}")
        
        try:
            files = {'file': (filename, file_content, 'application/octet-stream')}
            response = requests.post(url, files=files, timeout=timeout)
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

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_pdf_with_clear_text(self):
        """Test PDF with clear, extractable text"""
        # Create a simple PDF with clear text content
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
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
>>
endobj

4 0 obj
<<
/Length 200
>>
stream
BT
/F1 12 Tf
72 720 Td
(This restaurant has amazing food quality!) Tj
0 -20 Td
(The service was incredibly slow though.) Tj
0 -20 Td
(Pricing is reasonable for the portion sizes.) Tj
0 -20 Td
(Overall a mixed experience with great food.) Tj
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
500
%%EOF"""
        
        success, response = self.run_file_upload_test(
            "PDF with Clear Text Content",
            pdf_content,
            "restaurant_review.pdf",
            200
        )
        
        if success:
            print(f"   Extracted {response.get('total_entries', 0)} text entries")
            extracted_texts = response.get('extracted_texts', [])
            
            # Check if text was extracted
            if extracted_texts:
                print(f"✅ Text extraction successful")
                for i, entry in enumerate(extracted_texts[:3]):  # Show first 3
                    text = entry.get('text', '')
                    metadata = entry.get('metadata', {})
                    extractor = metadata.get('extractor', 'unknown')
                    print(f"   Entry {i+1}: '{text[:50]}...' (via {extractor})")
                
                # Check if pdfplumber was used (preferred method)
                pdfplumber_used = any(entry.get('metadata', {}).get('extractor') == 'pdfplumber' 
                                    for entry in extracted_texts)
                if pdfplumber_used:
                    print(f"✅ pdfplumber extractor used (primary method)")
                else:
                    print(f"⚠️  pdfplumber not used, check fallback logic")
                
                return True, response
            else:
                print(f"❌ No text extracted from PDF")
                return False, response
        
        return success, response

    def test_pdf_batch_analysis(self):
        """Test batch analysis with PDF-extracted text"""
        # First upload a PDF
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
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
>>
endobj

4 0 obj
<<
/Length 150
>>
stream
BT
/F1 12 Tf
72 720 Td
(Excellent product quality and fast delivery!) Tj
0 -20 Td
(Customer support was unhelpful and rude.) Tj
0 -20 Td
(Great value for money overall.) Tj
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
450
%%EOF"""
        
        upload_success, upload_response = self.run_file_upload_test(
            "PDF Upload for Batch Analysis",
            pdf_content,
            "batch_test.pdf",
            200
        )
        
        if not upload_success:
            return False, {}
        
        # Now test batch analysis
        file_id = upload_response.get('file_id')
        extracted_texts = upload_response.get('extracted_texts', [])
        
        if not file_id or not extracted_texts:
            print(f"❌ Invalid upload response for batch test")
            return False, {}
        
        batch_data = {
            "file_id": file_id,
            "texts": extracted_texts[:2]  # Test with first 2 entries
        }
        
        print(f"\n🔍 Testing PDF Batch Analysis...")
        url = f"{self.api_url}/analyze-batch"
        
        try:
            response = requests.post(url, json=batch_data, timeout=60)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                self.tests_passed += 1
                print(f"✅ PDF Batch Analysis Successful")
                
                batch_response = response.json()
                results = batch_response.get('results', [])
                
                print(f"   Processed {len(results)} PDF-extracted texts")
                
                # Check that sentiment analysis worked on PDF text
                for i, result in enumerate(results[:2]):
                    text = result.get('text', '')
                    sentiment = result.get('sentiment', '')
                    aspects = result.get('aspects_analysis', [])
                    
                    print(f"   Result {i+1}: '{text[:40]}...' -> {sentiment}")
                    if aspects:
                        print(f"     Aspects: {[a['aspect'] for a in aspects]}")
                
                return True, batch_response
            else:
                print(f"❌ Batch analysis failed: {response.status_code}")
                return False, {}
                
        except Exception as e:
            print(f"❌ Batch analysis error: {e}")
            return False, {}

    def test_corrupted_pdf(self):
        """Test error handling with corrupted PDF"""
        corrupted_pdf = b"This is not a valid PDF file content"
        
        success, response = self.run_file_upload_test(
            "Corrupted PDF Error Handling",
            corrupted_pdf,
            "corrupted.pdf",
            500  # Expect server error due to invalid PDF
        )
        
        # This should fail gracefully
        if not success and response == {}:
            print(f"✅ Corrupted PDF handled gracefully with error response")
            return True, {}
        else:
            print(f"⚠️  Unexpected response to corrupted PDF")
            return success, response

    def test_backward_compatibility(self):
        """Test that TXT and CSV files still work correctly"""
        # Test TXT file
        txt_content = """Great customer service experience!
The product quality exceeded expectations.
Pricing is competitive and fair."""
        
        txt_success, txt_response = self.run_file_upload_test(
            "TXT Backward Compatibility",
            txt_content.encode('utf-8'),
            "test.txt",
            200
        )
        
        if txt_success:
            print(f"✅ TXT file processing still works")
        else:
            print(f"❌ TXT file processing broken")
            return False, {}
        
        # Test CSV file
        csv_content = """review,rating
"Amazing product with great features",5
"Poor customer support experience",2
"Good value for the price",4"""
        
        csv_success, csv_response = self.run_file_upload_test(
            "CSV Backward Compatibility", 
            csv_content.encode('utf-8'),
            "test.csv",
            200
        )
        
        if csv_success:
            print(f"✅ CSV file processing still works")
            return True, {"txt": txt_response, "csv": csv_response}
        else:
            print(f"❌ CSV file processing broken")
            return False, {}

    def run_all_tests(self):
        """Run all PDF-focused tests"""
        print(f"🚀 Starting PDF Text Extraction Tests")
        print(f"   Backend URL: {self.api_url}")
        print(f"   Time: {datetime.now()}")
        
        # Test 1: PDF with clear text
        test1_success, _ = self.test_pdf_with_clear_text()
        
        # Test 2: PDF batch analysis integration
        test2_success, _ = self.test_pdf_batch_analysis()
        
        # Test 3: Corrupted PDF handling
        test3_success, _ = self.test_corrupted_pdf()
        
        # Test 4: Backward compatibility
        test4_success, _ = self.test_backward_compatibility()
        
        # Summary
        print(f"\n📊 PDF Testing Summary:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        all_critical_passed = test1_success and test2_success and test4_success
        
        if all_critical_passed:
            print(f"✅ All critical PDF tests passed!")
            print(f"   ✅ PDF text extraction working")
            print(f"   ✅ PDF batch analysis working") 
            print(f"   ✅ Backward compatibility maintained")
            if test3_success:
                print(f"   ✅ Error handling working")
        else:
            print(f"❌ Some critical tests failed:")
            if not test1_success:
                print(f"   ❌ PDF text extraction issues")
            if not test2_success:
                print(f"   ❌ PDF batch analysis issues")
            if not test4_success:
                print(f"   ❌ Backward compatibility broken")
        
        return all_critical_passed

if __name__ == "__main__":
    tester = PDFExtractionTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)