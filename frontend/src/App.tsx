import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ROUTES } from './utils/constants';
import { MainLayout, AuthLayout } from './layouts';

// Original PharmAI pages
import { Home } from './pages/Home';
import { ClinicalTrialsTest } from './pages/testing/ClinicalTrialsTest';
import { GeminiTest } from './pages/testing/GeminiTest';
import { LLMTest } from './pages/testing/LLMTest';

// New Repurpose.ai-style pages
import Chat from './pages/Chat';
import SearchPage from './pages/SearchPage';
import Results from './pages/Results';
import History from './pages/History';
import SavedOpportunities from './pages/SavedOpportunities';
import Compare from './pages/Compare';
import Settings from './pages/Settings';
import Integrations from './pages/Integrations';
import Architecture from './pages/Architecture';
import Login from './pages/Login';
import RepurposeDashboard from './pages/RepurposeDashboard';

import './App.css';

function App() {
  return (
    <Routes>
      {/* Landing page */}
      <Route path="/" element={<Home />} />

      {/* Auth routes */}
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<Login />} />
      </Route>

      {/* Main app routes with layout */}
      <Route element={<MainLayout />}>
        <Route path="/chat" element={<Chat />} />
        <Route path="/dashboard" element={<RepurposeDashboard />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/results" element={<Results />} />
        <Route path="/results/:drugName" element={<Results />} />
        <Route path="/history" element={<History />} />
        <Route path="/saved" element={<SavedOpportunities />} />
        <Route path="/compare" element={<Compare />} />
        <Route path="/integrations" element={<Integrations />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/architecture" element={<Architecture />} />

        <Route path="/dash" element={<Navigate to={ROUTES.SEARCH} replace />} />

        {/* Testing routes */}
        <Route path="/geminitest" element={<GeminiTest />} />
        <Route path="/clinical-trials-test" element={<ClinicalTrialsTest />} />
        <Route path="/llm-test" element={<LLMTest />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
