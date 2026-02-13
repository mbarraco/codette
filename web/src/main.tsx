import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";
import "./index.css";
import App from "./App.tsx";
import ProblemPage from "./ProblemPage.tsx";
import ProblemsPage from "./ProblemsPage.tsx";

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <nav className="nav">
        <NavLink to="/" className="nav-brand">
          Codette
        </NavLink>
        <NavLink
          to="/problems"
          className={({ isActive }) => (isActive ? "active" : "")}
        >
          Problems
        </NavLink>
      </nav>
      {children}
    </>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<App />} />
          <Route path="/problems" element={<ProblemsPage />} />
          <Route path="/problem/:uuid" element={<ProblemPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  </React.StrictMode>,
);
