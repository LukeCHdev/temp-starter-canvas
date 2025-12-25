import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import "@/i18n/i18nConfig"; // Initialize i18next
import App from "@/App";

const rootElement = document.getElementById("root");

// Check if the app was prerendered by react-snap
// If prerendered HTML exists, hydrate; otherwise, create root
if (rootElement.hasChildNodes()) {
  // Prerendered content exists - hydrate
  ReactDOM.hydrateRoot(
    rootElement,
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
} else {
  // No prerendered content - create root
  const root = ReactDOM.createRoot(rootElement);
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}
