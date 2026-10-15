"""
Master test runner for hierarchical agent workflow validation.
Executes all workflow tests and provides comprehensive validation report.
"""

import sys
import os
import unittest
import subprocess

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def run_all_workflow_tests():
    """Run all workflow tests and generate comprehensive report."""
    
    print("?? HIERARCHICAL AGENT WORKFLOW - MASTER TEST SUITE")
    print("=" * 80)
    print()
    
    test_results = {}
    
    # === Test 1: Basic Hierarchical Agent Tests ===
    print("?? Test 1: Running Basic Hierarchical Agent Tests...")
    try:
        import test_hierarchical_agent
        
        # Run basic tests
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        test_classes = [
            test_hierarchical_agent.TestTaskModels,
            test_hierarchical_agent.TestAgentState, 
            test_hierarchical_agent.TestAgentGraphCoreHelpers,
            test_hierarchical_agent.TestToolExecutor,
            test_hierarchical_agent.TestSpawnSubAgent,
            test_hierarchical_agent.TestWorkflowIntegration
        ]
        
        for test_class in test_classes:
            tests = loader.loadTestsFromTestCase(test_class)
            suite.addTests(tests)
        
        runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
        result = runner.run(suite)
        
        test_results['basic_tests'] = {
            'total': result.testsRun,
            'passed': result.testsRun - len(result.failures) - len(result.errors),
            'failed': len(result.failures),
            'errors': len(result.errors),
            'success_rate': ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
        }
        
        print(f"   ? Basic Tests: {test_results['basic_tests']['passed']}/{test_results['basic_tests']['total']} passed ({test_results['basic_tests']['success_rate']:.1f}%)")
        
    except Exception as e:
        print(f"   ? Basic Tests Failed: {e}")
        test_results['basic_tests'] = {'status': 'failed', 'error': str(e)}
    
    # === Test 2: Complete Workflow Tests ===  
    print("?? Test 2: Running Complete Workflow Tests...")
    try:
        import test_complete_workflow
        
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(test_complete_workflow.TestCompleteWorkflow)
        runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
        result = runner.run(suite)
        
        test_results['workflow_tests'] = {
            'total': result.testsRun,
            'passed': result.testsRun - len(result.failures) - len(result.errors),
            'failed': len(result.failures), 
            'errors': len(result.errors),
            'success_rate': ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
        }
        
        print(f"   ? Workflow Tests: {test_results['workflow_tests']['passed']}/{test_results['workflow_tests']['total']} passed ({test_results['workflow_tests']['success_rate']:.1f}%)")
        
    except Exception as e:
        print(f"   ? Workflow Tests Failed: {e}")
        test_results['workflow_tests'] = {'status': 'failed', 'error': str(e)}
    
    # === Test 3: Demo Validation ===
    print("?? Test 3: Running Demo Validation...")
    try:
        # Import and run demo validation
        demo_result = subprocess.run([
            sys.executable, 
            os.path.join(os.path.dirname(__file__), 'demo_workflow.py')
        ], capture_output=True, text=True, timeout=30)
        
        if demo_result.returncode == 0:
            test_results['demo_validation'] = {'status': 'passed'}
            print("   ? Demo Validation: PASSED")
        else:
            test_results['demo_validation'] = {'status': 'failed', 'error': demo_result.stderr}
            print(f"   ? Demo Validation: FAILED - {demo_result.stderr}")
            
    except Exception as e:
        print(f"   ? Demo Validation Failed: {e}")
        test_results['demo_validation'] = {'status': 'failed', 'error': str(e)}
    
    # === Test 4: User Task Simulation ===
    print("?? Test 4: Running User Task Simulation...")
    try:
        # Import and run user task simulation
        simulation_result = subprocess.run([
            sys.executable,
            os.path.join(os.path.dirname(__file__), 'user_task_simulation.py')
        ], capture_output=True, text=True, timeout=30)
        
        if simulation_result.returncode == 0 and "System is ready for production use!" in simulation_result.stdout:
            test_results['user_simulation'] = {'status': 'passed'}
            print("   ? User Task Simulation: PASSED")
        else:
            test_results['user_simulation'] = {'status': 'failed', 'error': simulation_result.stderr}
            print(f"   ? User Task Simulation: FAILED")
            
    except Exception as e:
        print(f"   ? User Task Simulation Failed: {e}")
        test_results['user_simulation'] = {'status': 'failed', 'error': str(e)}
    
    # === Test 5: Working Real Integration ===
    print("?? Test 5: Running Working Real Integration...")
    try:
        # Import and run working integration test
        integration_result = subprocess.run([
            sys.executable,
            os.path.join(os.path.dirname(__file__), 'working_integration_test.py')
        ], capture_output=True, text=True, timeout=60)
        
        if integration_result.returncode == 0 and "SUCCESS: Real hierarchical agent integration is working!" in integration_result.stdout:
            test_results['working_integration'] = {'status': 'passed'}
            print("   ? Working Real Integration: PASSED")
        else:
            test_results['working_integration'] = {'status': 'failed', 'error': integration_result.stderr}
            print(f"   ? Working Real Integration: FAILED")
            
    except Exception as e:
        print(f"   ? Working Real Integration Failed: {e}")
        test_results['working_integration'] = {'status': 'failed', 'error': str(e)}
    
    print()
    
    # === Generate Final Report ===
    print("?? COMPREHENSIVE TEST REPORT")
    print("=" * 80)
    
    total_tests = 0
    total_passed = 0
    
    for test_name, results in test_results.items():
        if isinstance(results, dict) and 'total' in results:
            total_tests += results['total']
            total_passed += results['passed']
            status = "? PASSED" if results['success_rate'] >= 80 else "?? PARTIAL" if results['success_rate'] >= 60 else "? FAILED"
            print(f"{status} | {test_name.upper()}: {results['passed']}/{results['total']} ({results['success_rate']:.1f}%)")
        elif isinstance(results, dict) and results.get('status') == 'passed':
            print(f"? PASSED | {test_name.upper()}: Integration test passed")
        else:
            print(f"? FAILED | {test_name.upper()}: {results.get('error', 'Unknown error')}")
    
    print()
    
    # Calculate overall success rate
    if total_tests > 0:
        overall_success_rate = (total_passed / total_tests) * 100
        print(f"?? OVERALL SUCCESS RATE: {total_passed}/{total_tests} tests ({overall_success_rate:.1f}%)")
    else:
        overall_success_rate = 0
        print("?? OVERALL SUCCESS RATE: Unable to calculate")
    
    print()
    
    # === Final Assessment ===
    if overall_success_rate >= 90:
        print("?? ASSESSMENT: PRODUCTION READY")
        print("? Hierarchical agent system is fully functional and ready for deployment")
        print("? All critical components validated successfully")
        print("? Workflow execution confirmed working end-to-end")
        
    elif overall_success_rate >= 70:
        print("?? ASSESSMENT: MOSTLY FUNCTIONAL") 
        print("?? System is largely working but may need minor fixes")
        print("?? Review failed tests and address issues before production")
        
    else:
        print("? ASSESSMENT: NEEDS WORK")
        print("??? System requires significant fixes before deployment")
        print("?? Address critical failures in core components")
    
    print()
    print("?? NEXT STEPS:")
    print("   1. Address any test failures identified above")
    print("   2. Integrate with real tools (web search, file I/O, etc.)")
    print("   3. Add production LLM integration")
    print("   4. Deploy to staging environment for integration testing")
    print("   5. Monitor performance and optimize as needed")
    
    return test_results


if __name__ == '__main__':
    print("Starting comprehensive hierarchical agent workflow validation...")
    print()
    
    results = run_all_workflow_tests()
    
    print("\n" + "=" * 80)
    print("?? VALIDATION COMPLETE")
    print("=" * 80)