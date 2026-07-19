import { Link } from "react-router";

import {
  getStoredToken,
} from "../services/authService";
import "../styles/UploadCard.css";

function UploadCard() {
    const uploadDestination =
        getStoredToken()
        ? "/upload"
        : "/login";
  return (
    <div className="hero-card">
      <div className="paper-preview">
        <div className="preview-header">
          <span className="preview-dot"></span>
          <span className="preview-dot"></span>
          <span className="preview-dot"></span>
        </div>

        <div className="preview-content">
          <div className="document-icon">📑</div>

          <h3>Upload your research paper</h3>

          <p>
            Drag and drop a PDF here or choose a file from your device.
          </p>

          <Link
            to={uploadDestination}
            className="upload-button"
          >
            Choose PDF
          </Link>
          <small>Maximum file size: 20 MB</small>
        </div>
      </div>
    </div>
  );
}

export default UploadCard;