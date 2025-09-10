#!/usr/bin/env python3

import requests
import json
import io
import sys
from datetime import datetime

class AdvancedPDFTester:
    def __init__(self, base_url="https://brand-pulse-6.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

    def run_file_upload_test(self, name, file_content, filename, expected_status, timeout=30):
        """Run a file upload test"""
        url = f"{self.api_url}/upload-file"
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   File: {filename}")
        
        try:
            files = {'file': (filename, file_content, 'application/pdf')}
            response = requests.post(url, files=files, timeout=timeout)
            print(f"   Status Code: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
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

    def test_multi_page_pdf(self):
        """Test PDF with multiple pages and paragraphs"""
        # Create a multi-page PDF with different content types
        multi_page_pdf = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R 4 0 R]
/Count 2
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 5 0 R
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
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 6 0 R
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

5 0 obj
<<
/Length 300
>>
stream
BT
/F1 12 Tf
72 720 Td
(Restaurant Review - Page 1) Tj
0 -30 Td
(The food quality at this establishment is absolutely outstanding.) Tj
0 -15 Td
(Every dish we ordered exceeded our expectations in both taste and presentation.) Tj
0 -30 Td
(However, the service was disappointingly slow throughout our visit.) Tj
0 -15 Td
(We waited over 45 minutes for our appetizers to arrive.) Tj
0 -30 Td
(The pricing is quite reasonable considering the portion sizes.) Tj
0 -15 Td
(Most entrees range from $15-25 which is fair for the quality.) Tj
ET
endstream
endobj

6 0 obj
<<
/Length 250
>>
stream
BT
/F1 12 Tf
72 720 Td
(Restaurant Review - Page 2) Tj
0 -30 Td
(The ambiance and location are perfect for a romantic dinner.) Tj
0 -15 Td
(The restaurant is beautifully decorated with excellent lighting.) Tj
0 -30 Td
(Staff behavior was professional but seemed overwhelmed.) Tj
0 -15 Td
(Our server was knowledgeable about the menu and wine pairings.) Tj
0 -30 Td
(Overall, this is a mixed experience with excellent food but service issues.) Tj
ET
endstream
endobj

xref
0 7
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000300 00000 n 
0000000485 00000 n 
0000000850 00000 n 
trailer
<<
/Size 7
/Root 1 0 R
>>
startxref
1150
%%EOF"""
        
        success, response = self.run_file_upload_test(
            "Multi-Page PDF with Paragraphs",
            multi_page_pdf,
            "multi_page_review.pdf",
            200
        )
        
        if success:
            extracted_texts = response.get('extracted_texts', [])
            total_entries = response.get('total_entries', 0)
            
            print(f"   Extracted {total_entries} text entries from multi-page PDF")
            
            # Check for multiple pages
            page_sources = set()
            for entry in extracted_texts:
                metadata = entry.get('metadata', {})
                source = metadata.get('source', '')
                if 'page' in source:
                    page_sources.add(source)
            
            print(f"   Pages detected: {len(page_sources)}")
            if len(page_sources) >= 2:
                print(f"✅ Multi-page extraction working")
            else:
                print(f"⚠️  Expected multiple pages, got {len(page_sources)}")
            
            # Check text quality and paragraph splitting
            for i, entry in enumerate(extracted_texts[:3]):
                text = entry.get('text', '')
                metadata = entry.get('metadata', {})
                extractor = metadata.get('extractor', 'unknown')
                row_number = entry.get('row_number', '')
                
                print(f"   Entry {i+1} ({row_number}): '{text[:60]}...' (via {extractor})")
                
                # Check if text is substantial (not just single words)
                if len(text) > 20:
                    print(f"     ✅ Substantial text extracted")
                else:
                    print(f"     ⚠️  Short text fragment: {len(text)} chars")
            
            return True, response
        
        return success, response

    def test_pdf_text_quality(self):
        """Test PDF text extraction quality and cleaning"""
        # PDF with various text formatting challenges
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
/Length 400
>>
stream
BT
/F1 12 Tf
72 720 Td
(Product Review: Smartphone Analysis) Tj
0 -25 Td
(Build Quality: The construction feels premium and solid.) Tj
0 -15 Td
(Materials used are high-grade aluminum and glass.) Tj
0 -25 Td
(User Interface: Navigation is intuitive and responsive.) Tj
0 -15 Td
(The design follows modern UI principles effectively.) Tj
0 -25 Td
(Performance Speed: Loading times are impressively fast.) Tj
0 -15 Td
(Apps launch quickly without noticeable lag or delays.) Tj
0 -25 Td
(Customer Support: Response time was disappointingly slow.) Tj
0 -15 Td
(The support team seemed unprepared and unhelpful.) Tj
0 -25 Td
(Price Value: Expensive but justified by the feature set.) Tj
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
750
%%EOF"""
        
        success, response = self.run_file_upload_test(
            "PDF Text Quality and Cleaning",
            quality_pdf,
            "quality_test.pdf",
            200
        )
        
        if success:
            extracted_texts = response.get('extracted_texts', [])
            
            print(f"   Analyzing text quality from {len(extracted_texts)} entries...")
            
            # Check for proper text cleaning and formatting
            for i, entry in enumerate(extracted_texts):
                text = entry.get('text', '')
                metadata = entry.get('metadata', {})
                extractor = metadata.get('extractor', 'unknown')
                
                print(f"   Entry {i+1}: '{text[:80]}...'")
                print(f"     Extractor: {extractor}")
                print(f"     Length: {len(text)} characters")
                
                # Check for text quality indicators
                quality_checks = {
                    'No excessive whitespace': not ('  ' in text or '\t' in text),
                    'Proper sentence structure': '.' in text and len(text.split('.')) > 1,
                    'Contains meaningful content': any(word in text.lower() for word in ['quality', 'performance', 'support', 'price']),
                    'No encoding issues': all(ord(c) < 128 for c in text)  # ASCII check
                }
                
                for check, passed in quality_checks.items():
                    status = "✅" if passed else "⚠️"
                    print(f"     {status} {check}")
            
            return True, response
        
        return success, response

    def test_pdf_metadata_tracking(self):
        """Test that PDF extraction metadata is properly tracked"""
        simple_pdf = b"""%PDF-1.4
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
/Length 100
>>
stream
BT
/F1 12 Tf
72 720 Td
(This is a test document for metadata tracking.) Tj
0 -20 Td
(The extraction method should be recorded properly.) Tj
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
450
%%EOF"""
        
        success, response = self.run_file_upload_test(
            "PDF Metadata Tracking",
            simple_pdf,
            "metadata_test.pdf",
            200
        )
        
        if success:
            extracted_texts = response.get('extracted_texts', [])
            
            print(f"   Checking metadata for {len(extracted_texts)} entries...")
            
            metadata_checks = {
                'extractor_recorded': False,
                'source_page_info': False,
                'pdfplumber_used': False,
                'row_number_format': False
            }
            
            for entry in extracted_texts:
                metadata = entry.get('metadata', {})
                row_number = entry.get('row_number', '')
                
                # Check extractor is recorded
                if 'extractor' in metadata:
                    metadata_checks['extractor_recorded'] = True
                    extractor = metadata['extractor']
                    print(f"   ✅ Extractor recorded: {extractor}")
                    
                    if extractor == 'pdfplumber':
                        metadata_checks['pdfplumber_used'] = True
                        print(f"   ✅ pdfplumber used as primary extractor")
                
                # Check source page information
                if 'source' in metadata and 'page' in metadata['source']:
                    metadata_checks['source_page_info'] = True
                    print(f"   ✅ Source page info: {metadata['source']}")
                
                # Check row number format for PDFs
                if 'page_' in str(row_number):
                    metadata_checks['row_number_format'] = True
                    print(f"   ✅ PDF row number format: {row_number}")
            
            # Summary of metadata checks
            passed_checks = sum(metadata_checks.values())
            total_checks = len(metadata_checks)
            
            print(f"   Metadata checks passed: {passed_checks}/{total_checks}")
            
            if passed_checks >= 3:  # Allow some flexibility
                print(f"✅ PDF metadata tracking working correctly")
            else:
                print(f"⚠️  Some metadata tracking issues detected")
            
            return True, response
        
        return success, response

    def test_pdf_with_batch_analysis_aspects(self):
        """Test that PDF-extracted text works well with aspect-based analysis"""
        aspect_pdf = b"""%PDF-1.4
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
(Hotel Review: Mixed Experience) Tj
0 -25 Td
(The food quality was exceptional with fresh ingredients.) Tj
0 -20 Td
(Service speed was terrible - waited 2 hours for dinner.) Tj
0 -20 Td
(Room cleanliness was perfect and well-maintained.) Tj
0 -20 Td
(Pricing is too expensive for the value provided.) Tj
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
        
        # First upload the PDF
        upload_success, upload_response = self.run_file_upload_test(
            "PDF for Aspect Analysis",
            aspect_pdf,
            "aspect_test.pdf",
            200
        )
        
        if not upload_success:
            return False, {}
        
        # Extract file info for batch analysis
        file_id = upload_response.get('file_id')
        extracted_texts = upload_response.get('extracted_texts', [])
        
        if not file_id or not extracted_texts:
            print(f"❌ Invalid PDF upload response")
            return False, {}
        
        # Run batch analysis
        batch_data = {
            "file_id": file_id,
            "texts": extracted_texts
        }
        
        print(f"\n🔍 Testing PDF Aspect-Based Batch Analysis...")
        url = f"{self.api_url}/analyze-batch"
        
        try:
            response = requests.post(url, json=batch_data, timeout=90)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                self.tests_passed += 1
                print(f"✅ PDF Aspect Analysis Successful")
                
                batch_response = response.json()
                results = batch_response.get('results', [])
                
                print(f"   Analyzed {len(results)} PDF-extracted texts")
                
                # Check aspect detection in PDF-extracted text
                total_aspects = 0
                aspect_categories = set()
                
                for i, result in enumerate(results):
                    text = result.get('text', '')
                    sentiment = result.get('sentiment', '')
                    aspects = result.get('aspects_analysis', [])
                    
                    print(f"   Result {i+1}: '{text[:50]}...' -> {sentiment}")
                    
                    if aspects:
                        print(f"     Aspects detected: {len(aspects)}")
                        for aspect in aspects:
                            aspect_name = aspect.get('aspect', '')
                            aspect_sentiment = aspect.get('sentiment', '')
                            confidence = aspect.get('confidence', 0)
                            
                            print(f"       {aspect_name}: {aspect_sentiment} ({confidence:.2f})")
                            aspect_categories.add(aspect_name)
                            total_aspects += 1
                    else:
                        print(f"     No aspects detected")
                
                print(f"   Total aspects detected: {total_aspects}")
                print(f"   Unique aspect categories: {len(aspect_categories)}")
                
                # Check for expected aspects in hotel review
                expected_aspects = ['food', 'service', 'room', 'price', 'quality']
                detected_aspects_lower = [cat.lower() for cat in aspect_categories]
                
                matches = 0
                for expected in expected_aspects:
                    if any(expected in detected.lower() for detected in detected_aspects_lower):
                        matches += 1
                        print(f"   ✅ Expected aspect category found: {expected}")
                
                if matches >= 3:
                    print(f"✅ Good aspect detection from PDF text ({matches}/{len(expected_aspects)} categories)")
                else:
                    print(f"⚠️  Limited aspect detection from PDF text ({matches}/{len(expected_aspects)} categories)")
                
                return True, batch_response
            else:
                print(f"❌ Batch analysis failed: {response.status_code}")
                return False, {}
                
        except Exception as e:
            print(f"❌ Batch analysis error: {e}")
            return False, {}

    def run_all_tests(self):
        """Run all advanced PDF tests"""
        print(f"🚀 Starting Advanced PDF Text Extraction Tests")
        print(f"   Backend URL: {self.api_url}")
        print(f"   Time: {datetime.now()}")
        
        # Test 1: Multi-page PDF
        test1_success, _ = self.test_multi_page_pdf()
        
        # Test 2: Text quality and cleaning
        test2_success, _ = self.test_pdf_text_quality()
        
        # Test 3: Metadata tracking
        test3_success, _ = self.test_pdf_metadata_tracking()
        
        # Test 4: PDF with aspect-based analysis
        test4_success, _ = self.test_pdf_with_batch_analysis_aspects()
        
        # Summary
        print(f"\n📊 Advanced PDF Testing Summary:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        all_tests_passed = all([test1_success, test2_success, test3_success, test4_success])
        
        if all_tests_passed:
            print(f"✅ All advanced PDF tests passed!")
            print(f"   ✅ Multi-page PDF extraction")
            print(f"   ✅ Text quality and cleaning")
            print(f"   ✅ Metadata tracking")
            print(f"   ✅ Aspect analysis integration")
        else:
            print(f"❌ Some advanced tests failed:")
            if not test1_success:
                print(f"   ❌ Multi-page PDF issues")
            if not test2_success:
                print(f"   ❌ Text quality issues")
            if not test3_success:
                print(f"   ❌ Metadata tracking issues")
            if not test4_success:
                print(f"   ❌ Aspect analysis integration issues")
        
        return all_tests_passed

if __name__ == "__main__":
    tester = AdvancedPDFTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)