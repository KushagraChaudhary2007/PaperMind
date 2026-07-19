import { useState } from "react";
import { Link, useNavigate } from "react-router";

import { registerUser } from "../services/authService";
import "../styles/Auth.css";

const initialFormData = {
  fullName: "",
  email: "",
  password: "",
  acceptedTerms: false,
};

function Register() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState(initialFormData);
  const [errorMessage, setErrorMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  function handleChange(event) {
    const { name, value, type, checked } = event.target;

    setFormData((currentData) => ({
      ...currentData,
      [name]: type === "checkbox" ? checked : value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();

    setErrorMessage("");

    if (!formData.acceptedTerms) {
      setErrorMessage(
        "You must accept the Terms of Service and Privacy Policy.",
      );
      return;
    }

    setIsSubmitting(true);

    try {
      await registerUser({
        fullName: formData.fullName,
        email: formData.email,
        password: formData.password,
      });

      navigate("/login", {
        state: {
          message:
            "Account created successfully. You can now sign in.",
        },
      });
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Registration failed. Please try again.",
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
            Your AI Research Workspace
          </p>

          <h1>
            Research becomes easier
            <span> from here.</span>
          </h1>

          <p>
            Create your account to simplify papers, ask
            questions, generate citations, and save your
            research history.
          </p>
        </div>

        <p className="auth-brand-footer">
          One account. Your complete research workspace.
        </p>
      </section>

      <section className="auth-form-panel">
        <div className="auth-form-container">
          <Link to="/" className="mobile-auth-logo">
            📄 PaperMind
          </Link>

          <div className="auth-heading">
            <p>Get started</p>

            <h2>Create your PaperMind account</h2>

            <span>
              Already have an account?{" "}
              <Link to="/login">Sign in</Link>
            </span>
          </div>

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
              <label htmlFor="register-name">
                Full name
              </label>

              <input
                id="register-name"
                name="fullName"
                type="text"
                placeholder="Enter your full name"
                autoComplete="name"
                value={formData.fullName}
                onChange={handleChange}
                disabled={isSubmitting}
                minLength={2}
                maxLength={100}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="register-email">
                Email address
              </label>

              <input
                id="register-email"
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
              <label htmlFor="register-password">
                Password
              </label>

              <input
                id="register-password"
                name="password"
                type="password"
                placeholder="Create a strong password"
                autoComplete="new-password"
                value={formData.password}
                onChange={handleChange}
                disabled={isSubmitting}
                minLength={8}
                maxLength={128}
                required
              />

              <small>
                Use at least 8 characters.
              </small>
            </div>

            <label className="remember-row">
              <input
                name="acceptedTerms"
                type="checkbox"
                checked={formData.acceptedTerms}
                onChange={handleChange}
                disabled={isSubmitting}
              />

              <span>
                I agree to the Terms of Service and Privacy
                Policy.
              </span>
            </label>

            <button
              className="auth-submit-button"
              type="submit"
              disabled={isSubmitting}
            >
              {isSubmitting
                ? "Creating Account..."
                : "Create Account"}
            </button>
          </form>

          <div className="auth-divider">
            <span>or sign up with</span>
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
            Social sign-in will be added later. Email
            registration is currently active.
          </p>
        </div>
      </section>
    </main>
  );
}

export default Register;