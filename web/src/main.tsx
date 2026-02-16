import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";
import "./index.css";
import App from "./App.tsx";
import AuthProvider, { useAuth } from "./contexts/AuthContext.tsx";
import ProtectedRoute from "./components/ProtectedRoute.tsx";
import LoginPage from "./pages/LoginPage.tsx";
import SignupPage from "./pages/SignupPage.tsx";
import ProblemPage from "./pages/ProblemPage.tsx";
import ProblemsPage from "./pages/ProblemsPage.tsx";
import MonitorPage from "./pages/MonitorPage.tsx";
import SubmissionsPage from "./pages/SubmissionsPage.tsx";

function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();

  return (
    <>
      <nav className="nav">
        <NavLink to="/" className="nav-brand">
          Codette
        </NavLink>
        {user ? (
          <>
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
          </>
        ) : null}
        <div className="navRight">
          {user ? (
            <>
              <span>
                {user.email} ({user.role})
              </span>
              <button type="button" onClick={logout}>
                Log out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login">Log in</NavLink>
              <NavLink to="/signup">Sign up</NavLink>
            </>
          )}
        </div>
      </nav>
      {children}
    </>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <Layout>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route element={<ProtectedRoute />}>
              <Route path="/" element={<App />} />
              <Route path="/problems" element={<ProblemsPage />} />
              <Route path="/problem/:uuid" element={<ProblemPage />} />
              <Route path="/submissions" element={<SubmissionsPage />} />
              <Route path="/monitor" element={<MonitorPage />} />
            </Route>
          </Routes>
        </Layout>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
