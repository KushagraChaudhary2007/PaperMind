import { Link } from "react-router";

import {
  getStoredToken,
} from "../services/authService";
import "../styles/Hero.css";
import UploadCard from "./UploadCard";

function Hero() {
    const uploadDestination =
  getStoredToken()
    ? "/upload"
    : "/login";
  return (
    <main className="hero" id="home">
      <div className="hero-content">
        <p className="badge">AI-Powered Research Assistant</p>

        <h1>
          Understand Research Papers
          <span> Without the Confusion</span>
        </h1>

        <p className="hero-description">
          Upload any research paper and get simple explanations, concise
          summaries, important findings, and answers to your questions.
        </p>

        <div className="hero-buttons">
          <Link
            to={uploadDestination}
            className="primary-button"
          >
            Upload Research Paper
        </Link>
          <a
            href="#features"
            className="secondary-button"
          >
            Explore Features
        </a>
        </div>

        <div className="hero-points">
          <span>✓ PDF support</span>
          <span>✓ AI summaries</span>
          <span>✓ Ask questions</span>
        </div>
      </div>

      <UploadCard />
    </main>
  );
}

export default Hero;