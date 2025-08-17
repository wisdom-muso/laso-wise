import React from 'react';

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('React Error Boundary caught an error:', error);
    console.error('Error Info:', errorInfo);
    
    this.setState({
      error,
      errorInfo
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ 
          padding: '20px', 
          backgroundColor: '#fee', 
          border: '1px solid #fcc',
          borderRadius: '4px',
          margin: '20px'
        }}>
          <h2 style={{ color: '#c00' }}>Something went wrong in the React app</h2>
          <details style={{ whiteSpace: 'pre-wrap', marginTop: '10px' }}>
            <summary>Error Details (click to expand)</summary>
            <div style={{ marginTop: '10px', fontSize: '14px' }}>
              <strong>Error:</strong> {this.state.error?.toString()}
              <br /><br />
              <strong>Stack Trace:</strong>
              <pre>{this.state.error?.stack}</pre>
              <br />
              <strong>Component Stack:</strong>
              <pre>{this.state.errorInfo?.componentStack}</pre>
            </div>
          </details>
          <div style={{ marginTop: '15px' }}>
            <button 
              onClick={() => window.location.reload()}
              style={{
                padding: '10px 15px',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Reload Page
            </button>
          </div>
          <div style={{ marginTop: '15px', fontSize: '14px', color: '#666' }}>
            <p><strong>Debugging Information:</strong></p>
            <p>API Base URL: {import.meta.env.VITE_API_BASE || 'Not set'}</p>
            <p>Node Environment: {import.meta.env.NODE_ENV || 'Not set'}</p>
            <p>Mode: {import.meta.env.MODE || 'Not set'}</p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;