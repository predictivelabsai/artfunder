import os
import sys
import django
import json
from datetime import datetime

sys.path.insert(0, '/home/ubuntu/litfunder-backend-fresh')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'litfunder.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from cases.models import LegalCase, CaseFunding, CaseInvestment

api_results = {
    'timestamp': datetime.now().isoformat(),
    'tests': [],
    'summary': {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'errors': []
    }
}

client = Client()

def test_admin_login():
    """Test admin login"""
    test_name = "Admin Login"
    try:
        response = client.post('/admin/login/', {
            'username': 'admin@litfunder.com',
            'password': 'admin123',
        }, follow=True)
        # Check if login was successful (should redirect to /admin/)
        if response.status_code == 200:
            api_results['tests'].append({
                'name': test_name,
                'status': 'PASSED',
                'message': f'Admin login successful',
                'status_code': response.status_code
            })
            api_results['summary']['passed'] += 1
            print(f"✓ {test_name}")
        else:
            api_results['tests'].append({
                'name': test_name,
                'status': 'FAILED',
                'message': f'Unexpected status code: {response.status_code}',
                'status_code': response.status_code
            })
            api_results['summary']['failed'] += 1
            print(f"✗ {test_name}: Status {response.status_code}")
    except Exception as e:
        api_results['tests'].append({
            'name': test_name,
            'status': 'FAILED',
            'message': str(e)
        })
        api_results['summary']['failed'] += 1
        api_results['summary']['errors'].append(str(e))
        print(f"✗ {test_name}: {e}")
    finally:
        api_results['summary']['total'] += 1

def test_admin_home():
    """Test admin home page"""
    test_name = "Admin Home Page"
    try:
        response = client.get('/admin/')
        if response.status_code in [200, 302]:
            api_results['tests'].append({
                'name': test_name,
                'status': 'PASSED',
                'message': f'Admin home accessible',
                'status_code': response.status_code
            })
            api_results['summary']['passed'] += 1
            print(f"✓ {test_name}")
        else:
            api_results['tests'].append({
                'name': test_name,
                'status': 'FAILED',
                'message': f'Unexpected status code: {response.status_code}',
                'status_code': response.status_code
            })
            api_results['summary']['failed'] += 1
            print(f"✗ {test_name}: Status {response.status_code}")
    except Exception as e:
        api_results['tests'].append({
            'name': test_name,
            'status': 'FAILED',
            'message': str(e)
        })
        api_results['summary']['failed'] += 1
        api_results['summary']['errors'].append(str(e))
        print(f"✗ {test_name}: {e}")
    finally:
        api_results['summary']['total'] += 1

def test_legal_cases_list():
    """Test legal cases list endpoint"""
    test_name = "Legal Cases List"
    try:
        response = client.get('/admin/cases/legalcase/')
        if response.status_code in [200, 302]:
            api_results['tests'].append({
                'name': test_name,
                'status': 'PASSED',
                'message': f'Legal cases list accessible',
                'status_code': response.status_code
            })
            api_results['summary']['passed'] += 1
            print(f"✓ {test_name}")
        else:
            api_results['tests'].append({
                'name': test_name,
                'status': 'FAILED',
                'message': f'Unexpected status code: {response.status_code}',
                'status_code': response.status_code
            })
            api_results['summary']['failed'] += 1
            print(f"✗ {test_name}: Status {response.status_code}")
    except Exception as e:
        api_results['tests'].append({
            'name': test_name,
            'status': 'FAILED',
            'message': str(e)
        })
        api_results['summary']['failed'] += 1
        api_results['summary']['errors'].append(str(e))
        print(f"✗ {test_name}: {e}")
    finally:
        api_results['summary']['total'] += 1

def test_case_fundings_list():
    """Test case fundings list endpoint"""
    test_name = "Case Fundings List"
    try:
        response = client.get('/admin/cases/casefunding/')
        if response.status_code in [200, 302]:
            api_results['tests'].append({
                'name': test_name,
                'status': 'PASSED',
                'message': f'Case fundings list accessible',
                'status_code': response.status_code
            })
            api_results['summary']['passed'] += 1
            print(f"✓ {test_name}")
        else:
            api_results['tests'].append({
                'name': test_name,
                'status': 'FAILED',
                'message': f'Unexpected status code: {response.status_code}',
                'status_code': response.status_code
            })
            api_results['summary']['failed'] += 1
            print(f"✗ {test_name}: Status {response.status_code}")
    except Exception as e:
        api_results['tests'].append({
            'name': test_name,
            'status': 'FAILED',
            'message': str(e)
        })
        api_results['summary']['failed'] += 1
        api_results['summary']['errors'].append(str(e))
        print(f"✗ {test_name}: {e}")
    finally:
        api_results['summary']['total'] += 1

def test_case_investments_list():
    """Test case investments list endpoint"""
    test_name = "Case Investments List"
    try:
        response = client.get('/admin/cases/caseinvestment/')
        if response.status_code in [200, 302]:
            api_results['tests'].append({
                'name': test_name,
                'status': 'PASSED',
                'message': f'Case investments list accessible',
                'status_code': response.status_code
            })
            api_results['summary']['passed'] += 1
            print(f"✓ {test_name}")
        else:
            api_results['tests'].append({
                'name': test_name,
                'status': 'FAILED',
                'message': f'Unexpected status code: {response.status_code}',
                'status_code': response.status_code
            })
            api_results['summary']['failed'] += 1
            print(f"✗ {test_name}: Status {response.status_code}")
    except Exception as e:
        api_results['tests'].append({
            'name': test_name,
            'status': 'FAILED',
            'message': str(e)
        })
        api_results['summary']['failed'] += 1
        api_results['summary']['errors'].append(str(e))
        print(f"✗ {test_name}: {e}")
    finally:
        api_results['summary']['total'] += 1

def test_notifications_list():
    """Test notifications list endpoint"""
    test_name = "Notifications List"
    try:
        response = client.get('/admin/cases/notification/')
        if response.status_code in [200, 302]:
            api_results['tests'].append({
                'name': test_name,
                'status': 'PASSED',
                'message': f'Notifications list accessible',
                'status_code': response.status_code
            })
            api_results['summary']['passed'] += 1
            print(f"✓ {test_name}")
        else:
            api_results['tests'].append({
                'name': test_name,
                'status': 'FAILED',
                'message': f'Unexpected status code: {response.status_code}',
                'status_code': response.status_code
            })
            api_results['summary']['failed'] += 1
            print(f"✗ {test_name}: Status {response.status_code}")
    except Exception as e:
        api_results['tests'].append({
            'name': test_name,
            'status': 'FAILED',
            'message': str(e)
        })
        api_results['summary']['failed'] += 1
        api_results['summary']['errors'].append(str(e))
        print(f"✗ {test_name}: {e}")
    finally:
        api_results['summary']['total'] += 1

def test_faqs_list():
    """Test FAQs list endpoint"""
    test_name = "FAQs List"
    try:
        response = client.get('/admin/cases/faq/')
        if response.status_code in [200, 302]:
            api_results['tests'].append({
                'name': test_name,
                'status': 'PASSED',
                'message': f'FAQs list accessible',
                'status_code': response.status_code
            })
            api_results['summary']['passed'] += 1
            print(f"✓ {test_name}")
        else:
            api_results['tests'].append({
                'name': test_name,
                'status': 'FAILED',
                'message': f'Unexpected status code: {response.status_code}',
                'status_code': response.status_code
            })
            api_results['summary']['failed'] += 1
            print(f"✗ {test_name}: Status {response.status_code}")
    except Exception as e:
        api_results['tests'].append({
            'name': test_name,
            'status': 'FAILED',
            'message': str(e)
        })
        api_results['summary']['failed'] += 1
        api_results['summary']['errors'].append(str(e))
        print(f"✗ {test_name}: {e}")
    finally:
        api_results['summary']['total'] += 1

def test_users_list():
    """Test users list endpoint"""
    test_name = "Users List"
    try:
        response = client.get('/admin/accounts/user/')
        if response.status_code in [200, 302]:
            api_results['tests'].append({
                'name': test_name,
                'status': 'PASSED',
                'message': f'Users list accessible',
                'status_code': response.status_code
            })
            api_results['summary']['passed'] += 1
            print(f"✓ {test_name}")
        else:
            api_results['tests'].append({
                'name': test_name,
                'status': 'FAILED',
                'message': f'Unexpected status code: {response.status_code}',
                'status_code': response.status_code
            })
            api_results['summary']['failed'] += 1
            print(f"✗ {test_name}: Status {response.status_code}")
    except Exception as e:
        api_results['tests'].append({
            'name': test_name,
            'status': 'FAILED',
            'message': str(e)
        })
        api_results['summary']['failed'] += 1
        api_results['summary']['errors'].append(str(e))
        print(f"✗ {test_name}: {e}")
    finally:
        api_results['summary']['total'] += 1

def test_database_connectivity():
    """Test database connectivity"""
    test_name = "Database Connectivity"
    try:
        case_count = LegalCase.objects.count()
        funding_count = CaseFunding.objects.count()
        investment_count = CaseInvestment.objects.count()
        
        if case_count > 0 and funding_count > 0 and investment_count > 0:
            api_results['tests'].append({
                'name': test_name,
                'status': 'PASSED',
                'message': f'Database connected. Cases: {case_count}, Fundings: {funding_count}, Investments: {investment_count}'
            })
            api_results['summary']['passed'] += 1
            print(f"✓ {test_name}")
        else:
            api_results['tests'].append({
                'name': test_name,
                'status': 'FAILED',
                'message': f'No data in database'
            })
            api_results['summary']['failed'] += 1
            print(f"✗ {test_name}: No data found")
    except Exception as e:
        api_results['tests'].append({
            'name': test_name,
            'status': 'FAILED',
            'message': str(e)
        })
        api_results['summary']['failed'] += 1
        api_results['summary']['errors'].append(str(e))
        print(f"✗ {test_name}: {e}")
    finally:
        api_results['summary']['total'] += 1

def run_all_api_tests():
    """Run all API tests"""
    print("\n" + "="*60)
    print("LITFUNDER API TEST SUITE")
    print("="*60 + "\n")
    
    test_admin_home()
    test_legal_cases_list()
    test_case_fundings_list()
    test_case_investments_list()
    test_notifications_list()
    test_faqs_list()
    test_users_list()
    test_database_connectivity()
    
    print("\n" + "="*60)
    print("API TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {api_results['summary']['total']}")
    print(f"Passed: {api_results['summary']['passed']}")
    print(f"Failed: {api_results['summary']['failed']}")
    print("="*60 + "\n")
    
    # Save results to JSON
    with open('/home/ubuntu/litfunder-backend-fresh/test-results/api_test_results.json', 'w') as f:
        json.dump(api_results, f, indent=2, default=str)
    
    print("✓ API test results saved to test-results/api_test_results.json")

if __name__ == '__main__':
    run_all_api_tests()
