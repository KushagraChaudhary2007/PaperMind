import {
  Navigate,
  useLocation,
} from "react-router";

import {
  getStoredToken,
} from "../services/authService";


function ProtectedRoute({ children }) {
  const location = useLocation();

  const token = getStoredToken();

  if (!token) {
    return (
      <Navigate
        to="/login"
        replace
        state={{
          from: location.pathname,

          message:
            "Please sign in to continue.",
        }}
      />
    );
  }

  return children;
}

export default ProtectedRoute;