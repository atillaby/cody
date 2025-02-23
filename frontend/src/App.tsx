import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Strategies from './pages/Strategies';
import Portfolio from './pages/Portfolio';
import Signals from './pages/Signals';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="strategies" element={<Strategies />} />
          <Route path="portfolio" element={<Portfolio />} />
          <Route path="signals" element={<Signals />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
