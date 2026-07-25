// Entry point — mount HELL FACTORY into the fixed #stage (scaled by index.html).
import React from 'react';
import { createRoot } from 'react-dom/client';
import '@fontsource/press-start-2p'; // vendored pixel fonts (replaces the Google Fonts CDN links)
import '@fontsource/vt323';
import App from './App.jsx';
import './styles.css';

createRoot(document.getElementById('root')).render(<App />);
