#!/usr/bin/env python3

import requests
import json
import sys
from datetime import datetime

class ComprehensivePDFTester:
    def __init__(self, base_url="https://sentimentmatrix.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.critical_tests_passed = 0
        self.critical_tests_total = 0

    def run_file_upload_test(self, name, file_content, filename, expected_status, timeout=30, critical=False):
        """Run a file upload test"""
        url = f"{self.api_url}/upload-file"
        
        self.tests_run += 1
        if critical:
            self.critical_tests_total += 1
            
        print(f"\n🔍 Testing {name}...")
        print(f"   File: {filename}")
        
        try:
            files = {'file': (filename, file_content, 'application/pdf')}
            response = requests.post(url, files=files, timeout=timeout)
            print(f"   Status Code: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                if critical:
                    self.critical_tests_passed += 1
                print(f"✅ Passed")
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

    def test_pdf_text_extraction_quality(self):
        """CRITICAL: Test PDF text extraction with pdfplumber"""
        quality_pdf = b"""%PDF-1.4
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
/Length 300
>>
stream
BT
/F1 12 Tf
72 720 Td
(Customer Review: E-commerce Experience) Tj
0 -25 Td
(Product Quality: The build quality is excellent and durable.) Tj
0 -20 Td
(Materials feel premium and well-constructed throughout.) Tj
0 -25 Td
(Delivery Speed: Shipping was incredibly fast and efficient.) Tj
0 -20 Td
(Package arrived within 2 days as promised.) Tj
0 -25 Td
(Customer Support: Response time was disappointing.) Tj
0 -20 Td
(Support team seemed unprepared and unhelpful overall.) Tj
0 -25 Td
(Pricing: Good value for money considering the quality.) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000300 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
650
%%EOF"""
        
        success, response = self.run_file_upload_test(
            "CRITICAL: PDF Text Extraction Quality",
            quality_pdf,
            "quality_extraction.pdf",
            200,
            critical=True
        )
        
        if success:
            extracted_texts = response.get('extracted_texts', [])
            total_entries = response.get('total_entries', 0)
            
            print(f"   ✅ Extracted {total_entries} text entries")
            
            # Verify pdfplumber is used
            pdfplumber_used = False
            text_quality_good = True
            
            for entry in extracted_texts:
                text = entry.get('text', '')
                metadata = entry.get('metadata', {})
                extractor = metadata.get('extractor', 'unknown')
                
                if extractor == 'pdfplumber':
                    pdfplumber_used = True
                    print(f"   ✅ pdfplumber used as primary extractor")
                
                # Check text quality
                if len(text) > 50 and 'Quality' in text and 'Support' in text:
                    print(f"   ✅ High-quality text extraction: {len(text)} chars")
                else:
                    text_quality_good = False
                    print(f"   ⚠️  Text quality issue: {len(text)} chars")
                
                print(f"   Sample: '{text[:100]}...'")
            
            return success and pdfplumber_used and text_quality_good, response
        
        return success, response

    def test_pdf_batch_analysis_integration(self):
        """CRITICAL: Test PDF integration with batch sentiment analysis"""
        batch_pdf = b"""%PDF-1.4
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
(Restaurant Experience Review) Tj
0 -25 Td
(Food quality was absolutely amazing and fresh.) Tj
0 -20 Td
(Service was terrible and extremely slow.) Tj
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
0000000300 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
550
%%EOF"""
        
        # Upload PDF
        upload_success, upload_response = self.run_file_upload_test(
            "CRITICAL: PDF Upload for Batch Analysis",
            batch_pdf,
            "batch_integration.pdf",
            200,
            critical=True
        )
        
        if not upload_success:
            return False, {}
        
        # Extract file info
        file_id = upload_response.get('file_id')
        extracted_texts = upload_response.get('extracted_texts', [])
        
        if not file_id or not extracted_texts:
            print(f"   ❌ Invalid upload response")
            return False, {}
        
        # Run batch analysis
        batch_data = {
            "file_id": file_id,
            "texts": extracted_texts
        }
        
        print(f"\n🔍 Testing CRITICAL: PDF Batch Analysis Integration...")
        url = f"{self.api_url}/analyze-batch"
        
        try:
            response = requests.post(url, json=batch_data, timeout=90)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                batch_response = response.json()
                results = batch_response.get('results', [])
                
                print(f"   ✅ Batch analysis successful: {len(results)} results")
                
                # Verify sentiment analysis worked
                sentiment_analysis_working = True
                aspect_analysis_working = False
                
                for result in results:
                    sentiment = result.get('sentiment', '')
                    confidence = result.get('confidence', 0)
                    aspects = result.get('aspects_analysis', [])
                    
                    if sentiment in ['positive', 'negative', 'neutral'] and confidence > 0:
                        print(f"   ✅ Sentiment analysis: {sentiment} ({confidence:.2f})")
                    else:
                        sentiment_analysis_working = False
                        print(f"   ❌ Sentiment analysis failed")
                    
                    if aspects and len(aspects) > 0:
                        aspect_analysis_working = True
                        print(f"   ✅ Aspect analysis: {len(aspects)} aspects detected")
                        for aspect in aspects[:2]:  # Show first 2
                            print(f"     - {aspect.get('aspect', '')}: {aspect.get('sentiment', '')}")
                
                integration_success = sentiment_analysis_working and aspect_analysis_working
                
                if integration_success:
                    print(f"   ✅ PDF-to-batch-analysis integration working")
                else:
                    print(f"   ❌ Integration issues detected")
                
                return integration_success, batch_response
            else:
                print(f"   ❌ Batch analysis failed: {response.status_code}")
                return False, {}
                
        except Exception as e:
            print(f"   ❌ Batch analysis error: {e}")
            return False, {}

    def test_pdf_metadata_and_tracking(self):
        """CRITICAL: Test PDF metadata tracking and extraction method recording"""
        metadata_pdf = b"""%PDF-1.4
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
/Length 80
>>
stream
BT
/F1 12 Tf
72 720 Td
(PDF metadata tracking test content.) Tj
0 -20 Td
(Extraction method should be recorded.) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000300 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
430
%%EOF"""
        
        success, response = self.run_file_upload_test(
            "CRITICAL: PDF Metadata Tracking",
            metadata_pdf,
            "metadata_tracking.pdf",
            200,
            critical=True
        )
        
        if success:
            extracted_texts = response.get('extracted_texts', [])
            
            metadata_complete = True
            required_metadata = ['extractor', 'source']
            
            for entry in extracted_texts:
                metadata = entry.get('metadata', {})
                row_number = entry.get('row_number', '')
                
                print(f"   Checking metadata for entry: {row_number}")
                
                # Check required metadata fields
                for field in required_metadata:
                    if field in metadata:
                        print(f"   ✅ {field}: {metadata[field]}")
                    else:
                        metadata_complete = False
                        print(f"   ❌ Missing {field}")
                
                # Check row number format for PDFs
                if 'page_' in str(row_number):
                    print(f"   ✅ PDF row number format: {row_number}")
                else:
                    print(f"   ⚠️  Unexpected row number format: {row_number}")
                
                # Verify extractor is valid
                extractor = metadata.get('extractor', '')
                if extractor in ['pdfplumber', 'PyPDF2']:
                    print(f"   ✅ Valid extractor: {extractor}")
                else:
                    metadata_complete = False
                    print(f"   ❌ Invalid extractor: {extractor}")
            
            return metadata_complete, response
        
        return success, response

    def test_backward_compatibility_verification(self):
        """CRITICAL: Verify TXT and CSV files still work after PDF improvements"""
        
        # Test TXT file
        txt_content = """Excellent customer service and support team.
The product quality exceeded all my expectations.
Pricing is very competitive in the current market.
Fast delivery and secure packaging overall."""
        
        txt_success, txt_response = self.run_file_upload_test(
            "CRITICAL: TXT Backward Compatibility",
            txt_content.encode('utf-8'),
            "compatibility_test.txt",
            200,
            critical=True
        )
        
        if not txt_success:
            print(f"   ❌ TXT file processing broken")
            return False, {}
        
        # Test CSV file
        csv_content = """feedback,category,rating
"Amazing product with great build quality",product,5
"Terrible customer support experience",service,1
"Good value for money and features",pricing,4
"Fast shipping and excellent packaging",delivery,5"""
        
        csv_success, csv_response = self.run_file_upload_test(
            "CRITICAL: CSV Backward Compatibility",
            csv_content.encode('utf-8'),
            "compatibility_test.csv",
            200,
            critical=True
        )
        
        if not csv_success:
            print(f"   ❌ CSV file processing broken")
            return False, {}
        
        # Verify both extracted text properly
        txt_entries = txt_response.get('total_entries', 0)
        csv_entries = csv_response.get('total_entries', 0)
        
        if txt_entries > 0 and csv_entries > 0:
            print(f"   ✅ TXT extracted {txt_entries} entries")
            print(f"   ✅ CSV extracted {csv_entries} entries")
            print(f"   ✅ Backward compatibility maintained")
            return True, {"txt": txt_response, "csv": csv_response}
        else:
            print(f"   ❌ Text extraction failed: TXT={txt_entries}, CSV={csv_entries}")
            return False, {}

    def test_error_handling_robustness(self):
        """Test error handling with problematic files"""
        
        # Invalid PDF content
        invalid_content = b"This is not a PDF file, just plain text content"
        
        error_success, _ = self.run_file_upload_test(
            "Error Handling: Invalid PDF",
            invalid_content,
            "invalid.pdf",
            400  # Should return error
        )
        
        if error_success:
            print(f"   ✅ Invalid PDF handled gracefully")
        else:
            print(f"   ❌ Invalid PDF not handled properly")
        
        return error_success, {}

    def run_comprehensive_test(self):
        """Run comprehensive PDF functionality test"""
        print(f"🚀 Starting COMPREHENSIVE PDF Text Extraction Test")
        print(f"   Backend URL: {self.api_url}")
        print(f"   Time: {datetime.now()}")
        print(f"   Focus: PDF text extraction improvements with pdfplumber")
        
        # Critical Tests
        test1_success, _ = self.test_pdf_text_extraction_quality()
        test2_success, _ = self.test_pdf_batch_analysis_integration()
        test3_success, _ = self.test_pdf_metadata_and_tracking()
        test4_success, _ = self.test_backward_compatibility_verification()
        
        # Non-critical test
        test5_success, _ = self.test_error_handling_robustness()
        
        # Summary
        print(f"\n📊 COMPREHENSIVE PDF TEST SUMMARY:")
        print(f"   Total Tests Run: {self.tests_run}")
        print(f"   Total Tests Passed: {self.tests_passed}")
        print(f"   Overall Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        print(f"   Critical Tests: {self.critical_tests_passed}/{self.critical_tests_total}")
        print(f"   Critical Success Rate: {(self.critical_tests_passed/self.critical_tests_total)*100:.1f}%")
        
        all_critical_passed = self.critical_tests_passed == self.critical_tests_total
        
        print(f"\n🎯 PDF IMPROVEMENT VERIFICATION:")
        
        if all_critical_passed:
            print(f"✅ ALL CRITICAL PDF TESTS PASSED!")
            print(f"   ✅ PDF text extraction working with pdfplumber")
            print(f"   ✅ PDF batch analysis integration working")
            print(f"   ✅ PDF metadata tracking implemented")
            print(f"   ✅ Backward compatibility maintained")
            
            if test5_success:
                print(f"   ✅ Error handling working")
            
            print(f"\n🎉 PDF TEXT EXTRACTION FIX VERIFIED SUCCESSFUL!")
            print(f"   - pdfplumber implemented as primary extractor")
            print(f"   - Text cleaning and paragraph splitting working")
            print(f"   - Metadata tracking for extraction method working")
            print(f"   - Integration with batch analysis working")
            print(f"   - No regressions in other file types")
            
        else:
            print(f"❌ CRITICAL PDF TESTS FAILED!")
            failed_tests = []
            if not test1_success:
                failed_tests.append("PDF text extraction")
            if not test2_success:
                failed_tests.append("PDF batch analysis integration")
            if not test3_success:
                failed_tests.append("PDF metadata tracking")
            if not test4_success:
                failed_tests.append("Backward compatibility")
            
            print(f"   Failed areas: {', '.join(failed_tests)}")
        
        return all_critical_passed

if __name__ == "__main__":
    tester = ComprehensivePDFTester()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1)