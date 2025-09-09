#!/usr/bin/env python3

import requests
import json
import sys
from datetime import datetime

class PDFFallbackTester:
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

    def test_standard_pdf_pdfplumber(self):
        """Test that standard PDFs use pdfplumber as primary extractor"""
        standard_pdf = b"""%PDF-1.4
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
/Length 120
>>
stream
BT
/F1 12 Tf
72 720 Td
(This is a standard PDF that should work with pdfplumber.) Tj
0 -20 Td
(The text extraction should be clean and accurate.) Tj
0 -20 Td
(Primary extractor method should be recorded in metadata.) Tj
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
470
%%EOF"""
        
        success, response = self.run_file_upload_test(
            "Standard PDF - pdfplumber Primary",
            standard_pdf,
            "standard.pdf",
            200
        )
        
        if success:
            extracted_texts = response.get('extracted_texts', [])
            
            # Check that pdfplumber was used
            pdfplumber_used = False
            for entry in extracted_texts:
                metadata = entry.get('metadata', {})
                extractor = metadata.get('extractor', '')
                
                if extractor == 'pdfplumber':
                    pdfplumber_used = True
                    print(f"   ✅ pdfplumber used as primary extractor")
                    break
            
            if not pdfplumber_used:
                print(f"   ⚠️  pdfplumber not used - check primary extractor logic")
            
            return pdfplumber_used, response
        
        return success, response

    def test_minimal_pdf_structure(self):
        """Test with minimal PDF structure that might challenge pdfplumber"""
        # Very minimal PDF structure
        minimal_pdf = b"""%PDF-1.3
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 50 >>
stream
BT
72 720 Td
(Minimal PDF test content) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000100 00000 n 
0000000153 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
230
%%EOF"""
        
        success, response = self.run_file_upload_test(
            "Minimal PDF Structure",
            minimal_pdf,
            "minimal.pdf",
            200
        )
        
        if success:
            extracted_texts = response.get('extracted_texts', [])
            
            if extracted_texts:
                print(f"   ✅ Text extracted from minimal PDF structure")
                
                # Check which extractor was used
                for entry in extracted_texts:
                    metadata = entry.get('metadata', {})
                    extractor = metadata.get('extractor', 'unknown')
                    text = entry.get('text', '')
                    
                    print(f"   Extractor used: {extractor}")
                    print(f"   Extracted text: '{text}'")
                    
                    if extractor in ['pdfplumber', 'PyPDF2']:
                        print(f"   ✅ Valid extractor used: {extractor}")
                    else:
                        print(f"   ⚠️  Unknown extractor: {extractor}")
            else:
                print(f"   ❌ No text extracted from minimal PDF")
                return False, response
            
            return True, response
        
        return success, response

    def test_error_handling_robustness(self):
        """Test error handling with various problematic PDF structures"""
        
        # Test 1: Completely invalid PDF
        invalid_pdf = b"This is not a PDF file at all, just plain text"
        
        success1, _ = self.run_file_upload_test(
            "Invalid PDF Content",
            invalid_pdf,
            "invalid.pdf",
            400  # Should return error
        )
        
        # Test 2: PDF header but corrupted structure
        corrupted_pdf = b"""%PDF-1.4
This PDF has a valid header but corrupted structure
No proper objects or xref table
%%EOF"""
        
        success2, _ = self.run_file_upload_test(
            "Corrupted PDF Structure",
            corrupted_pdf,
            "corrupted.pdf",
            400  # Should return error
        )
        
        # Test 3: Empty PDF (just header and EOF)
        empty_pdf = b"""%PDF-1.4
%%EOF"""
        
        success3, _ = self.run_file_upload_test(
            "Empty PDF",
            empty_pdf,
            "empty.pdf",
            400  # Should return error for no content
        )
        
        # All should handle errors gracefully
        error_handling_success = success1 and success2 and success3
        
        if error_handling_success:
            print(f"\n✅ All error cases handled gracefully")
        else:
            print(f"\n⚠️  Some error cases not handled properly")
        
        return error_handling_success, {}

    def test_extraction_method_consistency(self):
        """Test that extraction method is consistently recorded"""
        
        # Create multiple PDFs and check extraction method consistency
        test_pdfs = []
        
        # PDF 1: Simple structure
        pdf1 = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/Contents 4 0 R>>endobj
4 0 obj<</Length 40>>stream
BT 72 720 Td(Test PDF 1 content)Tj ET
endstream endobj
xref 0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000110 00000 n 
0000000159 00000 n 
trailer<</Size 5/Root 1 0 R>>startxref 230 %%EOF"""
        
        # PDF 2: Different structure
        pdf2 = b"""%PDF-1.4
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
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 45
>>
stream
BT
72 720 Td
(Test PDF 2 content) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000168 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
250
%%EOF"""
        
        test_pdfs = [
            (pdf1, "consistency_test1.pdf"),
            (pdf2, "consistency_test2.pdf")
        ]
        
        extractors_used = []
        
        for i, (pdf_content, filename) in enumerate(test_pdfs):
            success, response = self.run_file_upload_test(
                f"Consistency Test {i+1}",
                pdf_content,
                filename,
                200
            )
            
            if success:
                extracted_texts = response.get('extracted_texts', [])
                for entry in extracted_texts:
                    metadata = entry.get('metadata', {})
                    extractor = metadata.get('extractor', 'unknown')
                    extractors_used.append(extractor)
                    print(f"   PDF {i+1} used: {extractor}")
        
        # Check consistency
        unique_extractors = set(extractors_used)
        print(f"\n   Extractors used across tests: {unique_extractors}")
        
        # Should primarily use pdfplumber, but PyPDF2 fallback is acceptable
        valid_extractors = {'pdfplumber', 'PyPDF2'}
        all_valid = all(ext in valid_extractors for ext in unique_extractors)
        
        if all_valid:
            print(f"✅ All extractors are valid")
            if 'pdfplumber' in unique_extractors:
                print(f"✅ pdfplumber is being used (primary method)")
            if 'PyPDF2' in unique_extractors:
                print(f"✅ PyPDF2 fallback available")
        else:
            print(f"❌ Invalid extractors detected: {unique_extractors - valid_extractors}")
        
        return all_valid, {"extractors": list(unique_extractors)}

    def run_all_tests(self):
        """Run all fallback mechanism tests"""
        print(f"🚀 Starting PDF Fallback Mechanism Tests")
        print(f"   Backend URL: {self.api_url}")
        print(f"   Time: {datetime.now()}")
        
        # Test 1: Standard PDF with pdfplumber
        test1_success, _ = self.test_standard_pdf_pdfplumber()
        
        # Test 2: Minimal PDF structure
        test2_success, _ = self.test_minimal_pdf_structure()
        
        # Test 3: Error handling robustness
        test3_success, _ = self.test_error_handling_robustness()
        
        # Test 4: Extraction method consistency
        test4_success, _ = self.test_extraction_method_consistency()
        
        # Summary
        print(f"\n📊 PDF Fallback Testing Summary:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        all_tests_passed = all([test1_success, test2_success, test3_success, test4_success])
        
        if all_tests_passed:
            print(f"✅ All fallback mechanism tests passed!")
            print(f"   ✅ pdfplumber primary extraction")
            print(f"   ✅ Minimal PDF handling")
            print(f"   ✅ Error handling robustness")
            print(f"   ✅ Extraction method consistency")
        else:
            print(f"❌ Some fallback tests failed:")
            if not test1_success:
                print(f"   ❌ pdfplumber primary extraction issues")
            if not test2_success:
                print(f"   ❌ Minimal PDF handling issues")
            if not test3_success:
                print(f"   ❌ Error handling issues")
            if not test4_success:
                print(f"   ❌ Extraction method consistency issues")
        
        return all_tests_passed

if __name__ == "__main__":
    tester = PDFFallbackTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)