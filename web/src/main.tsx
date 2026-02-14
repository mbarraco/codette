import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";
import "./index.css";
import App from "./App.tsx";
import ProblemPage from "./pages/ProblemPage.tsx";
import ProblemsPage from "./pages/ProblemsPage.tsx";
import MonitorPage from "./pages/MonitorPage.tsx";
import SubmissionsPage from "./pages/SubmissionsPage.tsx";

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
        <NavLink
          to="/submissions"
          className={({ isActive }) => (isActive ? "active" : "")}
        >
          Submissions
        </NavLink>
        <NavLink
          to="/monitor"
          className={({ isActive }) => (isActive ? "active" : "")}
        >
          Monitor
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
          <Route path="/submissions" element={<SubmissionsPage />} />
          <Route path="/monitor" element={<MonitorPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  </React.StrictMode>,
);
