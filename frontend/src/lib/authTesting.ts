import { authAPI, validateToken, checkNetworkConnectivity } from './apiUtils';

// Test credentials for authentication testing
export const TEST_CREDENTIALS = {
  doctor: {
    email: 'doctor@test.com',
    password: 'testpassword123'
  },
  patient: {
    email: 'patient@test.com', 
    password: 'testpassword123'
  }
};

// Authentication test results interface
interface AuthTestResult {
  test: string;
  success: boolean;
  message: string;
  duration?: number;
  error?: any;
}

// Comprehensive authentication test suite
export class AuthTester {
  private results: AuthTestResult[] = [];

  // Run a single test and record results
  private async runTest(
    testName: string, 
    testFunction: () => Promise<any>
  ): Promise<AuthTestResult> {
    const startTime = Date.now();
    
    try {
      await testFunction();
      const duration = Date.now() - startTime;
      
      const result: AuthTestResult = {
        test: testName,
        success: true,
        message: 'Test passed',
        duration
      };
      
      this.results.push(result);
      return result;
    } catch (error: any) {
      const duration = Date.now() - startTime;
      
      const result: AuthTestResult = {
        test: testName,
        success: false,
        message: error.message || 'Test failed',
        duration,
        error
      };
      
      this.results.push(result);
      return result;
    }
  }

  // Test network connectivity
  async testNetworkConnectivity(): Promise<AuthTestResult> {
    return this.runTest('Network Connectivity', async () => {
      const isConnected = await checkNetworkConnectivity();
      if (!isConnected) {
        throw new Error('Cannot connect to backend server');
      }
    });
  }

  // Test token validation
  async testTokenValidation(): Promise<AuthTestResult> {
    return this.runTest('Token Validation', async () => {
      const token = localStorage.getItem('authToken');
      if (!token) {
        throw new Error('No auth token found');
      }
      
      const isValid = await validateToken(token);
      if (!isValid) {
        throw new Error('Token validation failed');
      }
    });
  }

  // Test login functionality
  async testLogin(credentials = TEST_CREDENTIALS.patient): Promise<AuthTestResult> {
    return this.runTest('Login', async () => {
      // Clear existing token first
      localStorage.removeItem('authToken');
      
      const response = await authAPI.login(credentials);
      if (!response.token) {
        throw new Error('Login did not return a token');
      }
      
      if (!response.user) {
        throw new Error('Login did not return user data');
      }
    });
  }

  // Test registration functionality
  async testRegistration(): Promise<AuthTestResult> {
    return this.runTest('Registration', async () => {
      const testUserData = {
        username: `test_${Date.now()}`,
        email: `test_${Date.now()}@example.com`,
        password: 'testpassword123',
        first_name: 'Test',
        last_name: 'User',
        role: 'patient'
      };

      const response = await authAPI.register(testUserData);
      if (!response.token) {
        throw new Error('Registration did not return a token');
      }
    });
  }

  // Test getting current user
  async testGetCurrentUser(): Promise<AuthTestResult> {
    return this.runTest('Get Current User', async () => {
      const user = await authAPI.getCurrentUser();
      if (!user || !user.id) {
        throw new Error('Failed to get current user data');
      }
    });
  }

  // Test profile update
  async testProfileUpdate(): Promise<AuthTestResult> {
    return this.runTest('Profile Update', async () => {
      const updateData = {
        first_name: 'Updated Name'
      };

      await authAPI.updateProfile(updateData);
    });
  }

  // Test logout functionality
  async testLogout(): Promise<AuthTestResult> {
    return this.runTest('Logout', async () => {
      await authAPI.logout();
      
      // Check that token was cleared
      const token = localStorage.getItem('authToken');
      if (token) {
        throw new Error('Token was not cleared after logout');
      }
    });
  }

  // Test authentication flow with invalid credentials
  async testInvalidLogin(): Promise<AuthTestResult> {
    return this.runTest('Invalid Login', async () => {
      try {
        await authAPI.login({
          email: 'invalid@example.com',
          password: 'wrongpassword'
        });
        throw new Error('Login should have failed with invalid credentials');
      } catch (error: any) {
        if (error.response?.status !== 401) {
          throw new Error('Expected 401 error for invalid login');
        }
        // This is expected behavior
      }
    });
  }

  // Test token expiration handling
  async testTokenExpiration(): Promise<AuthTestResult> {
    return this.runTest('Token Expiration', async () => {
      // Set an invalid token
      localStorage.setItem('authToken', 'invalid_token_12345');
      
      try {
        await authAPI.getCurrentUser();
        throw new Error('Request should have failed with invalid token');
      } catch (error: any) {
        if (error.response?.status !== 401) {
          throw new Error('Expected 401 error for invalid token');
        }
        
        // Check that token was cleared
        const token = localStorage.getItem('authToken');
        if (token) {
          throw new Error('Invalid token should have been cleared');
        }
      }
    });
  }

  // Run all authentication tests
  async runAllTests(): Promise<AuthTestResult[]> {
    console.log('🔐 Starting authentication tests...');
    
    this.results = [];

    // Basic connectivity
    await this.testNetworkConnectivity();

    // Authentication flow tests
    await this.testInvalidLogin();
    await this.testLogin();
    await this.testTokenValidation();
    await this.testGetCurrentUser();
    await this.testProfileUpdate();
    
    // Test token expiration
    await this.testTokenExpiration();
    
    // Test registration (do this after other tests to avoid conflicts)
    // await this.testRegistration();

    // Final cleanup
    await this.testLogout();

    return this.results;
  }

  // Get test results summary
  getTestSummary(): {
    total: number;
    passed: number;
    failed: number;
    passRate: number;
    results: AuthTestResult[];
  } {
    const total = this.results.length;
    const passed = this.results.filter(r => r.success).length;
    const failed = total - passed;
    const passRate = total > 0 ? (passed / total) * 100 : 0;

    return {
      total,
      passed,
      failed,
      passRate,
      results: this.results
    };
  }

  // Print test results to console
  printResults(): void {
    const summary = this.getTestSummary();
    
    console.log('\n🔐 Authentication Test Results');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log(`Total Tests: ${summary.total}`);
    console.log(`✅ Passed: ${summary.passed}`);
    console.log(`❌ Failed: ${summary.failed}`);
    console.log(`📊 Pass Rate: ${summary.passRate.toFixed(1)}%`);
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

    this.results.forEach((result, index) => {
      const icon = result.success ? '✅' : '❌';
      const duration = result.duration ? ` (${result.duration}ms)` : '';
      console.log(`${icon} ${result.test}${duration}`);
      
      if (!result.success) {
        console.log(`   Error: ${result.message}`);
      }
    });

    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  }
}

// Convenience function to run tests
export const runAuthTests = async (): Promise<void> => {
  const tester = new AuthTester();
  await tester.runAllTests();
  tester.printResults();
};

// Quick connectivity test
export const quickConnectivityTest = async (): Promise<boolean> => {
  try {
    const isConnected = await checkNetworkConnectivity();
    if (isConnected) {
      console.log('✅ Backend connectivity: OK');
    } else {
      console.log('❌ Backend connectivity: FAILED');
    }
    return isConnected;
  } catch (error) {
    console.log('❌ Backend connectivity: ERROR', error);
    return false;
  }
};

export default AuthTester;