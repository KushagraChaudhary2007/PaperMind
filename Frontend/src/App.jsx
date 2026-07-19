import UploadPaper from "./pages/UploadPaper";
import ComparePapers from "./pages/ComparePapers";
import PaperAnalysis from "./pages/PaperAnalysis";
import {
  Route,
  Routes,
} from "react-router";

import ProtectedRoute from "./components/ProtectedRoute";

import Dashboard from "./pages/Dashboard";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";


function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={<Home />}
      />

      <Route
        path="/login"
        element={<Login />}
      />

      <Route
        path="/register"
        element={<Register />}
      />

      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />

      <Route
        path="/upload"
        element={
          <ProtectedRoute>
            <UploadPaper />
          </ProtectedRoute>
        }
      />
      <Route
        path="/papers/:paperId"
        element={
          <ProtectedRoute>
            <PaperAnalysis />
          </ProtectedRoute>
        }
      />

      <Route
        path="/compare"
        element={
          <ProtectedRoute>
            <ComparePapers />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

export default App;