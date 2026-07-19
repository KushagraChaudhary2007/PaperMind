import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  useNavigate,
} from "react-router";

import {
  generateCitationMetadata,
  getCitationMetadata,
  getFormattedCitations,
} from "../services/paperService";

import "../styles/CitationGenerator.css";


const CITATION_STYLES = [
  {
    key: "apa",
    label: "APA",
  },
  {
    key: "mla",
    label: "MLA",
  },
  {
    key: "ieee",
    label: "IEEE",
  },
  {
    key: "chicago",
    label: "Chicago",
  },
  {
    key: "harvard",
    label: "Harvard",
  },
  {
    key: "bibtex",
    label: "BibTeX",
  },
];


function formatDocumentType(
  value,
) {
  if (!value) {
    return "Unknown";
  }

  return value
    .replaceAll("_", " ")
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase(),
    );
}


function CitationGenerator({
  paperId,
}) {
  const navigate = useNavigate();

  const [metadata, setMetadata] =
    useState(null);

  const [citations, setCitations] =
    useState(null);

  const [
    selectedStyle,
    setSelectedStyle,
  ] = useState("apa");

  const [isLoading, setIsLoading] =
    useState(true);

  const [
    isGenerating,
    setIsGenerating,
  ] = useState(false);

  const [
    errorMessage,
    setErrorMessage,
  ] = useState("");

  const [
    copied,
    setCopied,
  ] = useState(false);


  // =======================================================
  // Session redirect
  // =======================================================

  function redirectToLogin() {
    navigate("/login", {
      replace: true,

      state: {
        from: `/papers/${paperId}`,

        message:
          "Your session has expired. Please sign in again.",
      },
    });
  }


  // =======================================================
  // Load saved metadata + citations
  // =======================================================

  useEffect(() => {
    let cancelled = false;


    async function loadCitationData() {
      setIsLoading(true);

      setErrorMessage("");


      try {
        const savedMetadata =
          await getCitationMetadata(
            paperId,
          );


        if (cancelled) {
          return;
        }


        setMetadata(
          savedMetadata,
        );


        const formattedCitations =
          await getFormattedCitations(
            paperId,
          );


        if (!cancelled) {
          setCitations(
            formattedCitations,
          );
        }

      } catch (error) {

        if (cancelled) {
          return;
        }


        // No citation metadata yet.
        // This is normal.
        if (error?.status === 404) {
          setMetadata(null);
          setCitations(null);

          return;
        }


        if (error?.status === 401) {
          redirectToLogin();

          return;
        }


        setErrorMessage(
          error instanceof Error
            ? error.message
            : (
              "Citation information "
              + "could not be loaded."
            ),
        );

      } finally {

        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }


    loadCitationData();


    return () => {
      cancelled = true;
    };

  }, [paperId]);


  // =======================================================
  // Generate citation metadata
  // =======================================================

  async function handleGenerate() {
    setIsGenerating(true);

    setErrorMessage("");

    setCopied(false);


    try {

      const generatedMetadata =
        await generateCitationMetadata(
          paperId,
        );


      setMetadata(
        generatedMetadata,
      );


      const formattedCitations =
        await getFormattedCitations(
          paperId,
        );


      setCitations(
        formattedCitations,
      );

    } catch (error) {

      if (error?.status === 401) {
        redirectToLogin();

        return;
      }


      setErrorMessage(
        error instanceof Error
          ? error.message
          : (
            "PaperMind could not generate "
            + "citations for this document."
          ),
      );

    } finally {

      setIsGenerating(false);
    }
  }


  // =======================================================
  // Active citation
  // =======================================================

  const activeCitation =
    useMemo(
      () => {

        if (!citations) {
          return "";
        }

        return (
          citations[
            selectedStyle
          ] || ""
        );

      },
      [
        citations,
        selectedStyle,
      ],
    );


  // =======================================================
  // Copy
  // =======================================================

  async function handleCopy() {

    if (!activeCitation) {
      return;
    }


    try {

      await navigator.clipboard.writeText(
        activeCitation,
      );


      setCopied(true);


      window.setTimeout(
        () => {
          setCopied(false);
        },
        1800,
      );

    } catch {

      setErrorMessage(
        "The citation could not be copied automatically.",
      );
    }
  }


  // =======================================================
  // Loading
  // =======================================================

  if (isLoading) {
    return (

      <section 
        id="paper-citation-section"
        className="citation-generator-section">

        <div className="citation-loading">

          <div className="citation-spinner">
          </div>

          <div>

            <strong>
              Loading citation tools
            </strong>

            <p>
              Checking saved bibliographic
              information...
            </p>

          </div>

        </div>

      </section>

    );
  }


  return (

    <section 
        id="paper-citation-section"
        className="citation-generator-section">

      {/* =================================================
          HEADER
      ================================================= */}

      <header className="citation-generator-header">

        <div>

          <p className="citation-eyebrow">
            Academic Writing Tool
          </p>

          <h2>
            📚 Citation Generator
          </h2>

          <p>
            Create citations from the metadata
            available in this document.
          </p>

        </div>


        {metadata && (

          <span className="citation-ready-badge">
            ✓ Metadata Ready
          </span>

        )}

      </header>


      {/* =================================================
          ERROR
      ================================================= */}

      {errorMessage && (

        <div className="citation-error">

          <span>
            ⚠️
          </span>

          <div>

            <strong>
              Citation problem
            </strong>

            <p>
              {errorMessage}
            </p>

          </div>

        </div>

      )}


      {/* =================================================
          EMPTY / GENERATE
      ================================================= */}

      {!metadata && (

        <div className="citation-empty-state">

          <div className="citation-empty-icon">
            📖
          </div>


          <div>

            <p className="citation-eyebrow">
              Bibliographic Assistant
            </p>

            <h3>
              Generate citations for this document
            </h3>

            <p>
              PaperMind will extract available
              bibliographic information and create
              multiple citation formats without
              inventing missing metadata.
            </p>


            <div className="citation-style-preview">

              <span>
                APA
              </span>

              <span>
                MLA
              </span>

              <span>
                IEEE
              </span>

              <span>
                Chicago
              </span>

              <span>
                Harvard
              </span>

              <span>
                BibTeX
              </span>

            </div>


            <button
              type="button"
              className="generate-citation-button"
              onClick={
                handleGenerate
              }
              disabled={
                isGenerating
              }
            >

              {isGenerating ? (

                <>
                  <span className="citation-button-spinner">
                  </span>

                  Extracting Citation Data...
                </>

              ) : (

                <>
                  ✨ Generate Citations
                </>

              )}

            </button>

          </div>

        </div>

      )}


      {/* =================================================
          GENERATED
      ================================================= */}

      {metadata && citations && (

        <div className="citation-generator-content">

          {/* ===============================================
              DOCUMENT CLASSIFICATION
          =============================================== */}

          <div className="citation-document-card">

            <div>

              <p className="citation-eyebrow">
                Document Classification
              </p>

              <h3>
                {
                  formatDocumentType(
                    metadata.document_type,
                  )
                }
              </h3>

            </div>


            <span
              className={
                metadata
                  .is_academic_publication
                  ? "academic-status academic"
                  : "academic-status non-academic"
              }
            >

              {
                metadata
                  .is_academic_publication
                  ? "Academic Source"
                  : "Non-standard Source"
              }

            </span>

          </div>


          {/* ===============================================
              WARNING
          =============================================== */}

          {metadata.citation_warning && (

            <div className="citation-warning">

              <span>
                ⚠️
              </span>

              <div>

                <strong>
                  Citation Notice
                </strong>

                <p>
                  {
                    metadata
                      .citation_warning
                  }
                </p>

              </div>

            </div>

          )}


          {/* ===============================================
              STYLE SELECTOR
          =============================================== */}

          <div className="citation-workspace">

            <div className="citation-style-selector">

              <p className="citation-eyebrow">
                Citation Style
              </p>

              <div className="citation-style-buttons">

                {CITATION_STYLES.map(
                  (style) => (

                    <button
                      key={style.key}
                      type="button"
                      className={
                        selectedStyle
                          === style.key
                          ? "active"
                          : ""
                      }
                      onClick={
                        () => {
                          setSelectedStyle(
                            style.key,
                          );

                          setCopied(false);
                        }
                      }
                    >

                      {style.label}

                    </button>

                  ),
                )}

              </div>

            </div>


            {/* =============================================
                CITATION OUTPUT
            ============================================= */}

            <div className="citation-output-card">

              <div className="citation-output-heading">

                <div>

                  <p className="citation-eyebrow">
                    Generated Citation
                  </p>

                  <h3>
                    {
                      CITATION_STYLES.find(
                        (style) =>
                          style.key
                          === selectedStyle,
                      )?.label
                    }
                  </h3>

                </div>


                <button
                  type="button"
                  className="citation-copy-button"
                  onClick={handleCopy}
                >

                  {
                    copied
                      ? "✓ Copied"
                      : "Copy Citation"
                  }

                </button>

              </div>


              <div
                className={[
                  "citation-output-text",

                  selectedStyle
                    === "bibtex"
                    ? "citation-code-output"
                    : "",
                ].join(" ")}
              >

                {activeCitation}

              </div>

            </div>

          </div>


          {/* ===============================================
              METADATA
          =============================================== */}

          <div className="citation-metadata-card">

            <div className="citation-metadata-heading">

              <div>

                <p className="citation-eyebrow">
                  Source Information
                </p>

                <h3>
                  Extracted Metadata
                </h3>

              </div>


              {metadata.missing_fields
                ?.length > 0 && (

                <span className="metadata-missing-badge">

                  {
                    metadata
                      .missing_fields
                      .length
                  }{" "}
                  missing

                </span>

              )}

            </div>


            <div className="citation-metadata-grid">

              <div className="metadata-item">

                <span>
                  Title
                </span>

                <strong>
                  {
                    metadata.title
                    || "Not available"
                  }
                </strong>

              </div>


              <div className="metadata-item">

                <span>
                  Authors
                </span>

                <strong>
                  {
                    metadata.authors
                      ?.length
                      ? metadata
                          .authors
                          .join(", ")
                      : "Not available"
                  }
                </strong>

              </div>


              <div className="metadata-item">

                <span>
                  Year
                </span>

                <strong>
                  {
                    metadata
                      .publication_year
                    || "Not available"
                  }
                </strong>

              </div>


              <div className="metadata-item">

                <span>
                  Journal / Conference
                </span>

                <strong>
                  {
                    metadata
                      .journal_or_conference
                    || "Not available"
                  }
                </strong>

              </div>


              <div className="metadata-item">

                <span>
                  DOI
                </span>

                <strong>
                  {
                    metadata.doi
                    || "Not available"
                  }
                </strong>

              </div>


              <div className="metadata-item">

                <span>
                  Publisher
                </span>

                <strong>
                  {
                    metadata.publisher
                    || "Not available"
                  }
                </strong>

              </div>

            </div>


            {metadata.missing_fields
              ?.length > 0 && (

              <div className="missing-fields-box">

                <strong>
                  Missing or uncertain fields
                </strong>

                <div>

                  {
                    metadata
                      .missing_fields
                      .map(
                        (
                          field,
                          index,
                        ) => (

                          <span
                            key={`${field}-${index}`}
                          >

                            {
                              formatDocumentType(
                                field,
                              )
                            }

                          </span>

                        ),
                      )
                  }

                </div>

              </div>

            )}

          </div>

        </div>

      )}

    </section>

  );
}


export default CitationGenerator;