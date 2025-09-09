#!/usr/bin/env python3
"""
Test script to verify PDF text extraction improvements
"""
import requests
import io

# Create a simple PDF with actual text content for testing
def create_test_pdf():
    """Create a proper PDF with text content"""
    # This is a minimal but valid PDF with text content
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
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 125
>>
stream
BT
/F1 12 Tf
72 720 Td
(This is a test review of the restaurant.) Tj
0 -20 Td
(The food was delicious and the service was excellent.) Tj
0 -20 Td
(However, the prices were quite expensive.) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000015 00000 n 
0000000064 00000 n 
0000000121 00000 n 
0000000331 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
507
%%EOF"""
    return pdf_content

def test_pdf_upload():
    """Test PDF upload with improved extraction"""
    
    # Backend URL
    backend_url = "https://sentimentmatrix.preview.emergentagent.com/api"
    
    # Create test PDF
    pdf_content = create_test_pdf()
    
    # Test file upload
    print("🔍 Testing improved PDF text extraction...")
    
    files = {'file': ('test_review.pdf', pdf_content, 'application/pdf')}
    
    try:
        response = requests.post(f"{backend_url}/upload-file", files=files, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ PDF upload successful!")
            print(f"   File ID: {result['file_id']}")
            print(f"   Total entries extracted: {result['total_entries']}")
            
            # Check extracted texts
            if result['extracted_texts']:
                print(f"✅ Text extraction successful!")
                for i, text_entry in enumerate(result['extracted_texts']):
                    print(f"   Entry {i+1}: {text_entry['text'][:100]}...")
                    print(f"   Metadata: {text_entry['metadata']}")
                return True, result
            else:
                print(f"❌ No text extracted from PDF")
                return False, result
        else:
            print(f"❌ Upload failed: {response.text}")
            return False, {}
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, {}

if __name__ == "__main__":
    success, result = test_pdf_upload()
    if success:
        print(f"\n🎉 PDF text extraction fix verified!")
    else:
        print(f"\n❌ PDF text extraction still has issues")