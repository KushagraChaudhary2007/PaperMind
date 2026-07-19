import {
  useRef,
  useState,
} from "react";

import {
  Link,
  useNavigate,
} from "react-router";

import {
  uploadPaper,
} from "../services/paperService";

import "../styles/UploadPaper.css";


const MAX_FILE_SIZE =
  20 * 1024 * 1024;


function formatFileSize(bytes) {
  if (bytes < 1024) {
    return `${bytes} bytes`;
  }

  if (bytes < 1024 * 1024) {
    return `${(
      bytes / 1024
    ).toFixed(1)} KB`;
  }

  return `${(
    bytes /
    (1024 * 1024)
  ).toFixed(2)} MB`;
}


function UploadPaper() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [selectedFile, setSelectedFile] =
    useState(null);

  const [isDragging, setIsDragging] =
    useState(false);

  const [isUploading, setIsUploading] =
    useState(false);

  const [uploadProgress, setUploadProgress] =
    useState(0);

  const [errorMessage, setErrorMessage] =
    useState("");

  const [uploadedPaper, setUploadedPaper] =
    useState(null);


  function validateAndSelectFile(file) {
    setErrorMessage("");
    setUploadedPaper(null);
    setUploadProgress(0);

    if (!file) {
      return;
    }

    const hasPdfExtension =
      file.name
        .toLowerCase()
        .endsWith(".pdf");

    if (!hasPdfExtension) {
      setSelectedFile(null);

      setErrorMessage(
        "Only PDF files are allowed.",
      );

      return;
    }

    if (
      file.type &&
      file.type !== "application/pdf"
    ) {
      setSelectedFile(null);

      setErrorMessage(
        "The selected file must be a PDF.",
      );

      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setSelectedFile(null);

      setErrorMessage(
        "PDF size cannot exceed 20 MB.",
      );

      return;
    }

    if (file.size === 0) {
      setSelectedFile(null);

      setErrorMessage(
        "The selected PDF is empty.",
      );

      return;
    }

    setSelectedFile(file);
  }


  function handleInputChange(event) {
    const file = event.target.files?.[0];

    validateAndSelectFile(file);

    event.target.value = "";
  }


  function handleDragOver(event) {
    event.preventDefault();

    if (!isUploading) {
      setIsDragging(true);
    }
  }


  function handleDragLeave(event) {
    event.preventDefault();

    setIsDragging(false);
  }


  function handleDrop(event) {
    event.preventDefault();

    setIsDragging(false);

    if (isUploading) {
      return;
    }

    const file =
      event.dataTransfer.files?.[0];

    validateAndSelectFile(file);
  }


  function openFilePicker() {
    if (!isUploading) {
      fileInputRef.current?.click();
    }
  }


  function removeSelectedFile() {
    if (isUploading) {
      return;
    }

    setSelectedFile(null);
    setErrorMessage("");
    setUploadedPaper(null);
    setUploadProgress(0);
  }


  async function handleUpload() {
    if (!selectedFile) {
      setErrorMessage(
        "Please select a PDF first.",
      );

      return;
    }

    setErrorMessage("");
    setUploadedPaper(null);
    setUploadProgress(0);
    setIsUploading(true);

    try {
      const paper = await uploadPaper(
        selectedFile,
        setUploadProgress,
      );

      setUploadedPaper(paper);
      setSelectedFile(null);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "The PDF could not be uploaded.";

      if (
        message.toLowerCase().includes(
          "sign in",
        ) ||
        message.toLowerCase().includes(
          "credentials",
        )
      ) {
        navigate("/login", {
          replace: true,

          state: {
            message:
              "Please sign in before uploading a paper.",

            from: "/upload",
          },
        });

        return;
      }

      setErrorMessage(message);
    } finally {
      setIsUploading(false);
    }
  }


  return (
    <main className="upload-page">
      <header className="upload-header">
        <Link
          to="/dashboard"
          className="upload-back-link"
        >
          ← Dashboard
        </Link>

        <Link
          to="/dashboard"
          className="upload-page-logo"
        >
          <span>📄</span>
          PaperMind
        </Link>
      </header>

      <section className="upload-page-content">
        <div className="upload-title">
          <p>AI Research Workspace</p>

          <h1>
            Upload a research paper
          </h1>

          <span>
            Add a PDF and PaperMind will prepare it
            for summaries, explanations, citations,
            and question answering.
          </span>
        </div>

        {errorMessage && (
          <div className="upload-alert upload-alert-error">
            {errorMessage}
          </div>
        )}

        {uploadedPaper && (
            <div className="upload-alert upload-alert-success">
                <strong>
                    PDF uploaded and processed successfully!
                </strong>

                <span>
                    {uploadedPaper.original_filename}
                </span>

                <small>
                    Status: {uploadedPaper.processing_status}
                </small>

                <button
                  type="button"
                  className="view-paper-button"
                  onClick={() => {
                    navigate(
                      `/papers/${uploadedPaper.id}`,
                    );
                  }}
                >
                  Open Extracted Paper
                </button>
              </div>
        )}

        <section className="upload-workspace">
          <div
            className={[
              "drop-zone",
              isDragging
                ? "drop-zone-active"
                : "",
              isUploading
                ? "drop-zone-disabled"
                : "",
            ].join(" ")}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={openFilePicker}
            role="button"
            tabIndex={0}
            onKeyDown={(event) => {
              if (
                event.key === "Enter" ||
                event.key === " "
              ) {
                openFilePicker();
              }
            }}
          >
            <input
              ref={fileInputRef}
              className="hidden-file-input"
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleInputChange}
              disabled={isUploading}
            />

            <div className="drop-zone-icon">
              📑
            </div>

            <h2>
              {isDragging
                ? "Drop your PDF here"
                : "Drag and drop your PDF"}
            </h2>

            <p>
              or click this area to choose a file
              from your computer
            </p>

            <button
              type="button"
              disabled={isUploading}
              onClick={(event) => {
                event.stopPropagation();
                openFilePicker();
              }}
            >
              Choose PDF
            </button>

            <small>
              PDF only · Maximum size 20 MB
            </small>
          </div>

          {selectedFile && (
            <article className="selected-file-card">
              <div className="selected-file-icon">
                PDF
              </div>

              <div className="selected-file-details">
                <strong>
                  {selectedFile.name}
                </strong>

                <span>
                  {formatFileSize(
                    selectedFile.size,
                  )}
                </span>
              </div>

              <button
                type="button"
                className="remove-file-button"
                onClick={removeSelectedFile}
                disabled={isUploading}
                aria-label="Remove selected PDF"
              >
                ×
              </button>
            </article>
          )}

          {isUploading && (
            <div className="upload-progress-section">
              <div className="upload-progress-heading">
                <span>
                  Uploading securely...
                </span>

                <strong>
                  {uploadProgress}%
                </strong>
              </div>

              <div className="upload-progress-track">
                <div
                  className="upload-progress-fill"
                  style={{
                    width: `${uploadProgress}%`,
                  }}
                />
              </div>
            </div>
          )}

          <div className="upload-actions">
            <Link
              to="/dashboard"
              className="upload-cancel-button"
            >
              Cancel
            </Link>

            <button
              type="button"
              className="upload-submit-button"
              onClick={handleUpload}
              disabled={
                !selectedFile ||
                isUploading
              }
            >
              {isUploading
                ? "Uploading..."
                : "Upload and Continue"}
            </button>
          </div>
        </section>

        <section className="upload-security-note">
          <span>🔒</span>

          <div>
            <strong>
              Your account is required
            </strong>

            <p>
              Every uploaded paper is connected to
              the authenticated user who uploaded it.
            </p>
          </div>
        </section>
      </section>
    </main>
  );
}

export default UploadPaper;