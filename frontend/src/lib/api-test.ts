// API Test Suite for React-Django Connection
import { api, endpoints, healthCheck, testConnection, validateToken } from './api';

interface TestResult {
  name: string;
  passed: boolean;
  error?: string;
  data?: any;
}

export class APITestSuite {
  private results: TestResult[] = [];

  private addResult(name: string, passed: boolean, error?: string, data?: any) {
    this.results.push({ name, passed, error, data });
    console.log(`${passed ? '✅' : '❌'} ${name}${error ? ': ' + error : ''}`);
  }

  async runBasicConnectivityTests(): Promise<TestResult[]> {
    console.log('🔗 Running Basic Connectivity Tests...');

    // Test 1: Health Check
    try {
      const healthy = await healthCheck();
      this.addResult('Health Check', healthy);
    } catch (error: any) {
      this.addResult('Health Check', false, error.message);
    }

    // Test 2: Connection Test
    try {
      const connectionResult = await testConnection();
      this.addResult(
        'Connection Test',
        connectionResult.healthy,
        connectionResult.error,
        { latency: connectionResult.latency }
      );
    } catch (error: any) {
      this.addResult('Connection Test', false, error.message);
    }

    // Test 3: CORS Test
    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE || 'http://65.108.91.110:12000'}/admin/`, {
        method: 'HEAD',
        mode: 'cors',
        credentials: 'include',
      });
      this.addResult('CORS Test', response.ok || response.status < 500);
    } catch (error: any) {
      this.addResult('CORS Test', false, error.message);
    }

    return this.results.slice(-3);
  }

  async runAuthenticationTests(email?: string, password?: string): Promise<TestResult[]> {
    console.log('🔐 Running Authentication Tests...');

    // Test 1: Login endpoint accessibility
    try {
      const response = await api.post(endpoints.login, {});
      this.addResult('Login Endpoint', false, 'Should return error for empty credentials');
    } catch (error: any) {
      const expectedError = error.response?.status === 400;
      this.addResult(
        'Login Endpoint Accessibility',
        expectedError,
        expectedError ? undefined : `Unexpected status: ${error.response?.status}`
      );
    }

    // Test 2: Me endpoint without token
    try {
      const tempToken = localStorage.getItem('authToken');
      localStorage.removeItem('authToken');
      
      const response = await api.get(endpoints.me);
      this.addResult('Me Endpoint Security', false, 'Should require authentication');
      
      if (tempToken) localStorage.setItem('authToken', tempToken);
    } catch (error: any) {
      const expectedError = error.response?.status === 401;
      this.addResult(
        'Me Endpoint Security',
        expectedError,
        expectedError ? undefined : `Unexpected status: ${error.response?.status}`
      );
    }

    // Test 3: Token validation (if credentials provided)
    if (email && password) {
      try {
        const loginResponse = await api.post(endpoints.login, { email, password });
        
        if (loginResponse.token) {
          // Test token validation
          const isValid = await validateToken(loginResponse.token);
          this.addResult('Token Validation', isValid);
          
          // Test me endpoint with valid token
          localStorage.setItem('authToken', loginResponse.token);
          const meResponse = await api.get(endpoints.me);
          this.addResult('Authenticated Me Endpoint', !!meResponse.id);
          
          // Test logout
          const logoutResponse = await api.post(endpoints.logout);
          this.addResult('Logout', true);
          
        } else {
          this.addResult('Login Response', false, 'No token in response');
        }
      } catch (error: any) {
        this.addResult('Full Auth Flow', false, error.message);
      }
    }

    return this.results.slice(-4);
  }

  async runEndpointTests(): Promise<TestResult[]> {
    console.log('🎯 Running Endpoint Tests...');

    const endpointsToTest = [
      { name: 'Login', url: endpoints.login, method: 'POST' },
      { name: 'Register', url: endpoints.register, method: 'POST' },
      { name: 'Me', url: endpoints.me, method: 'GET' },
      { name: 'Doctors', url: endpoints.doctors, method: 'GET' },
      { name: 'Patients', url: endpoints.patients, method: 'GET' },
    ];

    for (const endpoint of endpointsToTest) {
      try {
        const response = await fetch(
          `${import.meta.env.VITE_API_BASE || 'http://65.108.91.110:12000'}${endpoint.url}`,
          {
            method: 'HEAD', // Use HEAD to avoid CSRF issues
            mode: 'cors',
            credentials: 'include',
          }
        );
        
        // Accept any response that's not a network error
        const accessible = response.status !== 0;
        this.addResult(
          `${endpoint.name} Endpoint`,
          accessible,
          accessible ? undefined : 'Network error'
        );
      } catch (error: any) {
        this.addResult(`${endpoint.name} Endpoint`, false, error.message);
      }
    }

    return this.results.slice(-endpointsToTest.length);
  }

  async runFullTestSuite(email?: string, password?: string): Promise<TestResult[]> {
    console.log('🚀 Running Full API Test Suite...');
    this.results = [];

    await this.runBasicConnectivityTests();
    await this.runEndpointTests();
    await this.runAuthenticationTests(email, password);

    console.log('\n📊 Test Summary:');
    const passed = this.results.filter(r => r.passed).length;
    const total = this.results.length;
    console.log(`✅ Passed: ${passed}/${total}`);
    console.log(`❌ Failed: ${total - passed}/${total}`);

    if (total - passed > 0) {
      console.log('\n❌ Failed Tests:');
      this.results
        .filter(r => !r.passed)
        .forEach(r => console.log(`  • ${r.name}: ${r.error}`));
    }

    return this.results;
  }

  getResults(): TestResult[] {
    return this.results;
  }

  getSummary() {
    const passed = this.results.filter(r => r.passed).length;
    const total = this.results.length;
    return {
      passed,
      failed: total - passed,
      total,
      successRate: total > 0 ? (passed / total) * 100 : 0,
    };
  }
}

// Export a default instance for easy use
export const apiTest = new APITestSuite();

// Console helper for quick testing
if (typeof window !== 'undefined') {
  (window as any).testAPI = apiTest;
  (window as any).quickTest = () => apiTest.runFullTestSuite();
}