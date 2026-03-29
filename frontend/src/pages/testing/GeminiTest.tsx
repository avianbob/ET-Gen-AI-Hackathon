import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

export const GeminiTest: React.FC = () => {
  const [apiKey, setApiKey] = useState('');
  const [testQuery, setTestQuery] = useState('Say "Hello, Gemini API is working!" in a creative way.');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{
    success: boolean;
    message: string;
    response?: string;
    error?: string;
  } | null>(null);

  const handleTest = async () => {
    if (!apiKey.trim()) {
      setResult({
        success: false,
        message: 'Please enter a Gemini API key',
      });
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      // Test the API key by making a request to Gemini API
      const response = await axios.post(
        'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent',
        {
          contents: [{
            parts: [{
              text: testQuery
            }]
          }]
        },
        {
          params: {
            key: apiKey
          },
          headers: {
            'Content-Type': 'application/json',
          },
          timeout: 30000, // 30 second timeout
        }
      );

      if (response.data && response.data.candidates && response.data.candidates[0]) {
        const generatedText = response.data.candidates[0].content?.parts?.[0]?.text || 'No text generated';
        setResult({
          success: true,
          message: '✅ Gemini API is working correctly!',
          response: generatedText,
        });
      } else {
        setResult({
          success: false,
          message: '⚠️ API responded but with unexpected format',
          error: JSON.stringify(response.data, null, 2),
        });
      }
    } catch (error: any) {
      let errorMessage = 'Unknown error occurred';
      
      if (error.response) {
        // API responded with error status
        const status = error.response.status;
        const data = error.response.data;
        
        if (status === 400) {
          errorMessage = 'Invalid API key or request format';
        } else if (status === 403) {
          errorMessage = 'API key is invalid or has insufficient permissions';
        } else if (status === 429) {
          errorMessage = 'Rate limit exceeded. Please try again later.';
        } else if (status === 500) {
          errorMessage = 'Gemini API server error';
        } else {
          errorMessage = `API Error (${status}): ${data?.error?.message || 'Unknown error'}`;
        }
        
        setResult({
          success: false,
          message: `❌ API Error: ${errorMessage}`,
          error: JSON.stringify(data, null, 2),
        });
      } else if (error.request) {
        // Request was made but no response received
        setResult({
          success: false,
          message: '❌ No response from Gemini API. Check your internet connection.',
          error: error.message,
        });
      } else {
        // Error setting up the request
        setResult({
          success: false,
          message: `❌ Request Error: ${error.message}`,
          error: error.toString(),
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleTestWithBackend = async () => {
    setLoading(true);
    setResult(null);

    try {
      // Test using the backend endpoint
      const response = await axios.post(
        'http://localhost:8000/api/test-gemini',
        {
          query: testQuery,
        },
        {
          timeout: 30000,
        }
      );

      if (response.data && response.data.success) {
        setResult({
          success: true,
          message: '✅ Gemini API is working correctly via backend!',
          response: response.data.response || response.data.message,
        });
      } else {
        setResult({
          success: false,
          message: '⚠️ Backend responded but with unexpected format',
          error: JSON.stringify(response.data, null, 2),
        });
      }
    } catch (error: any) {
      let errorMessage = 'Unknown error occurred';
      
      if (error.response) {
        const status = error.response.status;
        const data = error.response.data;
        
        if (status === 500 && data?.detail) {
          errorMessage = data.detail;
        } else {
          errorMessage = `Backend Error (${status}): ${data?.detail || data?.message || 'Unknown error'}`;
        }
        
        setResult({
          success: false,
          message: `❌ Backend Error: ${errorMessage}`,
          error: JSON.stringify(data, null, 2),
        });
      } else if (error.code === 'ECONNREFUSED') {
        setResult({
          success: false,
          message: '❌ Cannot connect to backend. Make sure the backend server is running on http://localhost:8000',
          error: error.message,
        });
      } else {
        setResult({
          success: false,
          message: `❌ Request Error: ${error.message}`,
          error: error.toString(),
        });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-4">
          <Link to="/search" className="text-sm font-medium text-slate-600 hover:text-blue-600">
            ← Back to Drug Search
          </Link>
        </div>
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-lg border border-slate-200 p-6 mb-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
              <i className="fas fa-robot text-white text-xl"></i>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-800">Gemini API Key Tester</h1>
              <p className="text-sm text-slate-500">Test your Google Gemini API key connectivity</p>
            </div>
          </div>
        </div>

        {/* Test Configuration */}
        <div className="bg-white rounded-2xl shadow-lg border border-slate-200 p-6 mb-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">Test Configuration</h2>
          
          {/* API Key Input */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Gemini API Key
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter your GEMINI_API_KEY here..."
              className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
            />
            <p className="text-xs text-slate-500 mt-1">
              Get your API key from: <a href="https://makersuite.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Google AI Studio</a>
            </p>
          </div>

          {/* Test Query Input */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Test Query
            </label>
            <textarea
              value={testQuery}
              onChange={(e) => setTestQuery(e.target.value)}
              rows={3}
              placeholder="Enter a test query..."
              className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition resize-none"
            />
          </div>

          {/* Test Buttons */}
          <div className="flex gap-3">
            <button
              onClick={handleTest}
              disabled={loading || !apiKey.trim()}
              className="flex-1 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition shadow-md hover:shadow-lg flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <i className="fas fa-spinner fa-spin"></i>
                  <span>Testing...</span>
                </>
              ) : (
                <>
                  <i className="fas fa-flask"></i>
                  <span>Test Direct API</span>
                </>
              )}
            </button>
            
            <button
              onClick={handleTestWithBackend}
              disabled={loading}
              className="flex-1 px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-400 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition shadow-md hover:shadow-lg flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <i className="fas fa-spinner fa-spin"></i>
                  <span>Testing...</span>
                </>
              ) : (
                <>
                  <i className="fas fa-server"></i>
                  <span>Test via Backend</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Results */}
        {result && (
          <div className={`bg-white rounded-2xl shadow-lg border-2 ${
            result.success ? 'border-emerald-200 bg-emerald-50/30' : 'border-red-200 bg-red-50/30'
          } p-6`}>
            <div className="flex items-start gap-3">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                result.success ? 'bg-emerald-100' : 'bg-red-100'
              }`}>
                <i className={`fas ${result.success ? 'fa-check-circle text-emerald-600' : 'fa-exclamation-circle text-red-600'} text-xl`}></i>
              </div>
              <div className="flex-1">
                <h3 className={`text-lg font-semibold mb-2 ${
                  result.success ? 'text-emerald-800' : 'text-red-800'
                }`}>
                  {result.message}
                </h3>
                
                {result.response && (
                  <div className="bg-white rounded-lg p-4 border border-slate-200 mb-3">
                    <p className="text-sm font-medium text-slate-700 mb-2">Response:</p>
                    <p className="text-slate-800 whitespace-pre-wrap">{result.response}</p>
                  </div>
                )}
                
                {result.error && (
                  <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
                    <p className="text-xs font-medium text-slate-400 mb-2">Error Details:</p>
                    <pre className="text-xs text-slate-300 overflow-x-auto whitespace-pre-wrap font-mono">
                      {result.error}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Instructions */}
        <div className="bg-blue-50 rounded-2xl border border-blue-200 p-6 mt-6">
          <h3 className="text-sm font-semibold text-blue-900 mb-3 flex items-center gap-2">
            <i className="fas fa-info-circle"></i>
            Testing Instructions
          </h3>
          <ul className="text-sm text-blue-800 space-y-2">
            <li className="flex items-start gap-2">
              <span className="text-blue-500 mt-1">•</span>
              <span><strong>Test Direct API:</strong> Tests the API key directly against Google's Gemini API endpoint. Requires a valid API key.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-500 mt-1">•</span>
              <span><strong>Test via Backend:</strong> Tests using your backend server (must be running on port 8000). Uses the API key from your backend's .env file.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-500 mt-1">•</span>
              <span>If direct API test fails, check your API key validity and internet connection.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-500 mt-1">•</span>
              <span>If backend test fails, ensure your backend server is running and GEMINI_API_KEY is set in the .env file.</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};
