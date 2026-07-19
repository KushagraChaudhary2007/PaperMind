import { useState } from "react";
import {
  Link,
  useLocation,
  useNavigate,
} from "react-router";

import {
  loginUser,
  saveToken,
} from "../services/authService";

import "../styles/Auth.css";


const initialFormData = {
  email: "",
  password: "",
  rememberMe: false,
};


function Login() {
  const navigate = useNavigate();
  const location = useLocation();

  const [formData, setFormData] =
    useState(initialFormData);

  const [errorMessage, setErrorMessage] =
    useState("");

  const [isSubmitting, setIsSubmitting] =
    useState(false);

  const successMessage =
    location.state?.message || "";


  function handleChange(event) {
    const {
      name,
      value,
      type,
      checked,
    } = event.target;

    setFormData((currentData) => ({
      ...currentData,

      [name]:
        type === "checkbox"
          ? checked
          : value,
    }));
  }


  async function handleSubmit(event) {
    event.preventDefault();

    setErrorMessage("");
    setIsSubmitting(true);

    try {
      const tokenData = await loginUser({
        email: formData.email,
        password: formData.password,
      });

      saveToken(
        tokenData.access_token,
        formData.rememberMe,
      );

      const destination =
        location.state?.from || "/dashboard";

      navigate(destination, {
        replace: true,
      });
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Login failed. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }


  return (
    <main className="auth-page">
      <section className="auth-brand-panel">
        <Link to="/" className="auth-logo">
          <span>📄</span>
          PaperMind
        </Link>

        <div className="auth-brand-content">
          <p className="auth-badge">
            AI-Powered Research Assistant
          </p>

          <h1>
            Welcome back to
            <span> PaperMind.</span>
          </h1>

          <p>
            Continue simplifying papers, exploring
            research, and building your knowledge.
          </p>
        </div>

        <p className="auth-brand-footer">
          Turn Complex Research Into Clear Knowledge.
        </p>
      </section>

      <section className="auth-form-panel">
        <div className="auth-form-container">
          <Link
            to="/"
            className="mobile-auth-logo"
          >
            📄 PaperMind
          </Link>

          <div className="auth-heading">
            <p>Welcome back</p>

            <h2>Sign in to your account</h2>

            <span>
              New to PaperMind?{" "}
              <Link to="/register">
                Create an account
              </Link>
            </span>
          </div>

          {successMessage && (
            <div className="auth-alert auth-alert-success">
              {successMessage}
            </div>
          )}

          {errorMessage && (
            <div className="auth-alert auth-alert-error">
              {errorMessage}
            </div>
          )}

          <form
            className="auth-form"
            onSubmit={handleSubmit}
          >
            <div className="form-group">
              <label htmlFor="login-email">
                Email address
              </label>

              <input
                id="login-email"
                name="email"
                type="email"
                placeholder="you@example.com"
                autoComplete="email"
                value={formData.email}
                onChange={handleChange}
                disabled={isSubmitting}
                required
              />
            </div>

            <div className="form-group">
              <div className="password-label-row">
                <label htmlFor="login-password">
                  Password
                </label>

                <button
                  type="button"
                  className="forgot-password"
                  disabled
                >
                  Forgot password?
                </button>
              </div>

              <input
                id="login-password"
                name="password"
                type="password"
                placeholder="Enter your password"
                autoComplete="current-password"
                value={formData.password}
                onChange={handleChange}
                disabled={isSubmitting}
                required
              />
            </div>

            <label className="remember-row">
              <input
                name="rememberMe"
                type="checkbox"
                checked={formData.rememberMe}
                onChange={handleChange}
                disabled={isSubmitting}
              />

              <span>Remember me</span>
            </label>

            <button
              className="auth-submit-button"
              type="submit"
              disabled={isSubmitting}
            >
              {isSubmitting
                ? "Signing In..."
                : "Sign In"}
            </button>
          </form>

          <div className="auth-divider">
            <span>or continue with</span>
          </div>

          <div className="social-buttons">
            <button
              type="button"
              className="social-button"
              disabled
            >
              <span>G</span>
              Google
            </button>

            <button
              type="button"
              className="social-button"
              disabled
            >
              <span>⌘</span>
              GitHub
            </button>
          </div>

          <p className="auth-terms">
            Social sign-in and password recovery will
            be added later.
          </p>
        </div>
      </section>
    </main>
  );
}

export default Login;