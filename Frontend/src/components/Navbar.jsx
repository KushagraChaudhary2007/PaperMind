import { Link } from "react-router";
import "../styles/Navbar.css";

function Navbar() {
  return (
    <nav className="navbar">
      <Link to="/" className="logo">
        <span className="logo-icon">📄</span>
        <span>PaperMind</span>
      </Link>

      <div className="nav-links">
        <a href="#home">Home</a>
        <a href="#features">Features</a>
        <a href="#about">About</a>
      </div>

      <div className="nav-actions">
        <Link to="/login" className="sign-in-link">
          Sign In
        </Link>

        <Link to="/register" className="nav-button">
          Get Started
        </Link>
      </div>
    </nav>
  );
}

export default Navbar;