import React from 'react';
import Home from './pages/Home';
import Header from './components/Header';
import './styles/global.css';

function App() {
  return (
    <div className="app">
      <Header />
      <Home />
    </div>
  );
}

export default App;