#!/usr/bin/env python3

import sys
import os
sys.path.append('/app')

from backend_test import BrandWatchAPITester

def test_workflow_fix():
    """Test the fixed workflow functionality"""
    tester = BrandWatchAPITester()
    
    print("🔧 Testing Fixed Complete File Upload Workflow...")
    
    # Run the specific workflow test that was failing
    success, response = tester.test_complete_file_upload_workflow()
    
    if success:
        print("✅ WORKFLOW TEST FIXED: Complete file upload workflow now passes!")
        return True
    else:
        print("❌ WORKFLOW TEST STILL FAILING")
        return False

if __name__ == "__main__":
    success = test_workflow_fix()
    sys.exit(0 if success else 1)