#!/usr/bin/env python3

import sys
import os
sys.path.append('/app')

from backend_test import BrandWatchAPITester

def test_file_upload_comprehensive():
    """Comprehensive test of file upload and batch processing functionality"""
    tester = BrandWatchAPITester()
    
    print("🔍 COMPREHENSIVE FILE UPLOAD & BATCH PROCESSING TEST")
    print("=" * 60)
    
    # Test 1: File Upload Tests
    print("\n📁 Testing File Upload Functionality...")
    
    tests = [
        ("TXT File Upload", tester.test_upload_txt_file),
        ("CSV File Upload", tester.test_upload_csv_file), 
        ("Excel File Upload", tester.test_upload_excel_file),
        ("PDF File Upload", tester.test_upload_pdf_file),
        ("Unsupported File Type", tester.test_upload_unsupported_file),
        ("Large File (>5MB)", tester.test_upload_large_file),
        ("Empty File", tester.test_upload_empty_file),
    ]
    
    upload_results = []
    for test_name, test_func in tests:
        try:
            success, response = test_func()
            upload_results.append((test_name, success))
            print(f"   {test_name}: {'✅ PASS' if success else '❌ FAIL'}")
        except Exception as e:
            upload_results.append((test_name, False))
            print(f"   {test_name}: ❌ ERROR - {e}")
    
    # Test 2: Batch Analysis Tests
    print("\n⚡ Testing Batch Analysis Functionality...")
    
    # First upload a file to get data for batch testing
    txt_content = """Amazing product quality and design!
Terrible customer service experience.
Reasonable pricing for the features.
Fast shipping and delivery."""
    
    upload_success, upload_response = tester.run_file_upload_test(
        "Test File for Batch Analysis",
        txt_content.encode('utf-8'),
        "batch_test.txt",
        200
    )
    
    if upload_success:
        file_id = upload_response['file_id']
        extracted_texts = upload_response['extracted_texts']
        
        batch_tests = [
            ("Valid Batch Analysis", lambda: tester.test_batch_analysis(file_id, extracted_texts)),
            ("Invalid File ID", tester.test_batch_analysis_invalid_file_id),
            ("Empty Texts Array", tester.test_batch_analysis_empty_texts),
        ]
        
        batch_results = []
        for test_name, test_func in batch_tests:
            try:
                success, response = test_func()
                batch_results.append((test_name, success))
                print(f"   {test_name}: {'✅ PASS' if success else '❌ FAIL'}")
            except Exception as e:
                batch_results.append((test_name, False))
                print(f"   {test_name}: ❌ ERROR - {e}")
    else:
        print("   ❌ Could not test batch analysis - file upload failed")
        batch_results = [("Batch Analysis Tests", False)]
    
    # Test 3: Complete Workflow Test
    print("\n🔄 Testing Complete Workflow...")
    
    try:
        workflow_success, workflow_response = tester.test_complete_file_upload_workflow()
        print(f"   Complete Workflow: {'✅ PASS' if workflow_success else '❌ FAIL'}")
    except Exception as e:
        workflow_success = False
        print(f"   Complete Workflow: ❌ ERROR - {e}")
    
    # Test 4: Dependencies Test
    print("\n📦 Testing File Processing Dependencies...")
    
    try:
        deps_success, deps_response = tester.test_file_processing_dependencies()
        print(f"   Dependencies Available: {'✅ PASS' if deps_success else '❌ FAIL'}")
    except Exception as e:
        deps_success = False
        print(f"   Dependencies Available: ❌ ERROR - {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(upload_results) + len(batch_results) + 2  # +2 for workflow and deps
    passed_tests = sum(1 for _, success in upload_results if success)
    passed_tests += sum(1 for _, success in batch_results if success)
    passed_tests += (1 if workflow_success else 0)
    passed_tests += (1 if deps_success else 0)
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print(f"\n📁 File Upload Tests: {sum(1 for _, success in upload_results if success)}/{len(upload_results)} passed")
    print(f"⚡ Batch Analysis Tests: {sum(1 for _, success in batch_results if success)}/{len(batch_results)} passed")
    print(f"🔄 Workflow Test: {'✅ PASSED' if workflow_success else '❌ FAILED'}")
    print(f"📦 Dependencies Test: {'✅ PASSED' if deps_success else '❌ FAILED'}")
    
    # Detailed failure analysis
    failed_tests = []
    for test_name, success in upload_results:
        if not success:
            failed_tests.append(f"Upload: {test_name}")
    
    for test_name, success in batch_results:
        if not success:
            failed_tests.append(f"Batch: {test_name}")
    
    if not workflow_success:
        failed_tests.append("Workflow: Complete File Upload Workflow")
    
    if not deps_success:
        failed_tests.append("Dependencies: File Processing Dependencies")
    
    if failed_tests:
        print(f"\n❌ FAILED TESTS:")
        for failed_test in failed_tests:
            print(f"   - {failed_test}")
    else:
        print(f"\n🎉 ALL FILE UPLOAD & BATCH PROCESSING TESTS PASSED!")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = test_file_upload_comprehensive()
    sys.exit(0 if success else 1)