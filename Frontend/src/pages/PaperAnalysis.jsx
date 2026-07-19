import {
  useEffect,
  useState,
} from "react";

import {
  Link,
  useNavigate,
  useParams,
} from "react-router";

import {
  generatePaperSummary,
  getPaperSummary,
  getPaperText,
} from "../services/paperService";

import "../styles/PaperAnalysis.css";

import ExplanationPanel from "../components/ExplanationPanel";
import PaperChatPanel from "../components/PaperChatPanel";
import ResearchRoadmapPanel from "../components/ResearchRoadmapPanel";
import CitationGenerator from "../components/CitationGenerator";


function formatNumber(value) {
  return new Intl.NumberFormat().format(
    value || 0,
  );
}


function formatGeneratedDate(value) {
  if (!value) {
    return "";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return new Intl.DateTimeFormat(
    undefined,
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(date);
}


function SummaryList({
  items,
  emptyMessage,
}) {
  if (
    !Array.isArray(items)
    || items.length === 0
  ) {
    return (
      <p className="summary-empty-message">
        {emptyMessage}
      </p>
    );
  }

  return (
    <ul className="summary-list">

      {items.map(
        (item, index) => (

          <li
            key={`${item}-${index}`}
          >
            {item}
          </li>

        ),
      )}

    </ul>
  );
}


function PaperAnalysis() {
  const { paperId } = useParams();

  const navigate = useNavigate();


  const [paper, setPaper] =
    useState(null);

  const [summary, setSummary] =
    useState(null);


  const [isLoading, setIsLoading] =
    useState(true);

  const [isGenerating, setIsGenerating] =
    useState(false);

  const [errorMessage, setErrorMessage] =
    useState("");


  const [
    summaryErrorMessage,
    setSummaryErrorMessage,
  ] = useState("");


  // =======================================================
  // Authentication redirect
  // =======================================================

  function redirectToLogin(message) {
    navigate("/login", {
      replace: true,

      state: {
        from: `/papers/${paperId}`,
        message,
      },
    });
  }


  // =======================================================
  // Smooth scroll between analysis tools
  // =======================================================

  function scrollToSection(
    sectionId,
  ) {
    document
      .getElementById(sectionId)
      ?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
  }


  // =======================================================
  // Load paper + saved summary
  // =======================================================

  useEffect(() => {
    let cancelled = false;


    async function loadPaperPage() {
      try {

        const paperData =
          await getPaperText(
            paperId,
          );


        if (cancelled) {
          return;
        }


        setPaper(
          paperData,
        );


        try {

          const savedSummary =
            await getPaperSummary(
              paperId,
            );


          if (!cancelled) {

            setSummary(
              savedSummary,
            );


            setPaper(
              (currentPaper) => ({
                ...currentPaper,

                processing_status:
                  "summarized",
              }),
            );

          }

        } catch (summaryError) {

          if (cancelled) {
            return;
          }


          if (
            summaryError?.status
            === 401
          ) {

            redirectToLogin(
              "Your session has expired. Please sign in again.",
            );

            return;
          }


          // 404 means no summary exists yet.
          if (
            summaryError?.status
            !== 404
          ) {

            setSummaryErrorMessage(
              summaryError
                instanceof Error
                ? summaryError.message
                : (
                  "The saved AI summary "
                  + "could not be loaded."
                ),
            );

          }
        }

      } catch (error) {

        if (cancelled) {
          return;
        }


        if (
          error?.status
          === 401
        ) {

          redirectToLogin(
            "Please sign in to open this paper.",
          );

          return;
        }


        setErrorMessage(
          error instanceof Error
            ? error.message
            : (
              "The research paper "
              + "could not be loaded."
            ),
        );

      } finally {

        if (!cancelled) {
          setIsLoading(false);
        }

      }
    }


    loadPaperPage();


    return () => {
      cancelled = true;
    };

  }, [
    navigate,
    paperId,
  ]);


  // =======================================================
  // Generate AI summary
  // =======================================================

  async function handleGenerateSummary() {
    setSummaryErrorMessage("");

    setIsGenerating(true);


    try {

      const generatedSummary =
        await generatePaperSummary(
          paperId,
        );


      setSummary(
        generatedSummary,
      );


      setPaper(
        (currentPaper) => ({
          ...currentPaper,

          processing_status:
            "summarized",
        }),
      );

    } catch (error) {

      if (
        error?.status
        === 401
      ) {

        redirectToLogin(
          "Your session has expired. Please sign in again.",
        );

        return;
      }


      setSummaryErrorMessage(
        error instanceof Error
          ? error.message
          : (
            "The AI summary could "
            + "not be generated."
          ),
      );

    } finally {

      setIsGenerating(false);

    }
  }


  // =======================================================
  // Loading page
  // =======================================================

  if (isLoading) {

    return (

      <main className="paper-loading-page">

        <div className="paper-loading-spinner">
        </div>

        <p>
          Opening your research paper...
        </p>

      </main>

    );
  }


  // =======================================================
  // Error page
  // =======================================================

  if (errorMessage) {

    return (

      <main className="paper-error-page">

        <div className="paper-error-card">

          <span>
            ⚠️
          </span>

          <h1>
            Paper could not be opened
          </h1>

          <p>
            {errorMessage}
          </p>

          <Link to="/dashboard">
            Return to Dashboard
          </Link>

        </div>

      </main>

    );
  }


  const needsOcr =
    paper?.extraction_status
    === "needs_ocr";


  const summaryGeneratedDate =
    formatGeneratedDate(
      summary?.generated_at,
    );


  return (

    <div className="paper-analysis-page">

      {/* =================================================
          TOP HEADER
      ================================================= */}

      <header className="paper-analysis-header">

        <Link
          to="/dashboard"
          className="paper-analysis-back"
        >
          ← Dashboard
        </Link>


        <Link
          to="/dashboard"
          className="paper-analysis-logo"
        >

          <span>
            📄
          </span>

          PaperMind

        </Link>

      </header>


      <main className="paper-analysis-main">

        {/* =================================================
            PAPER TITLE
        ================================================= */}

        <section className="paper-title-section">

          <div>

            <p className="paper-section-label">
              Research Paper
            </p>

            <h1>
              {paper?.original_filename}
            </h1>


            <span
              className={[
                "paper-status",

                needsOcr
                  ? "paper-status-warning"
                  : "paper-status-ready",

              ].join(" ")}
            >

              {
                needsOcr
                  ? "OCR required"

                  : summary
                    ? "AI summary ready"

                    : "Text extraction ready"
              }

            </span>

          </div>


          <Link
            to="/upload"
            className="upload-another-button"
          >
            Upload Another Paper
          </Link>

        </section>


        {/* =================================================
            PAPER STATS
        ================================================= */}

        <section className="paper-stat-grid">

          <article className="paper-stat-card">

            <span>
              📑
            </span>

            <div>

              <strong>
                {
                  formatNumber(
                    paper?.page_count,
                  )
                }
              </strong>

              <p>
                Pages
              </p>

            </div>

          </article>


          <article className="paper-stat-card">

            <span>
              🔤
            </span>

            <div>

              <strong>
                {
                  formatNumber(
                    paper?.character_count,
                  )
                }
              </strong>

              <p>
                Characters extracted
              </p>

            </div>

          </article>


          <article className="paper-stat-card">

            <span>
              ⚙️
            </span>

            <div>

              <strong>
                { formatProcessingStatus
                (paper?.processing_status,
                )}
              </strong>

              <p>
                Processing status
              </p>

            </div>

          </article>

        </section>


        {/* =================================================
            ANALYSIS TOOL NAVIGATION
        ================================================= */}

        {!needsOcr && (

          <nav className="paper-analysis-tools">

            <button
              type="button"
              onClick={() =>
                scrollToSection(
                  "paper-summary-section",
                )
              }
            >
              🧠 Summary
            </button>


            <button
              type="button"
              onClick={() =>
                scrollToSection(
                  "paper-explanation-section",
                )
              }
            >
              🎓 Explain
            </button>


            <button
              type="button"
              onClick={() =>
                scrollToSection(
                  "paper-chat-section",
                )
              }
            >
              💬 Ask AI
            </button>


            <button
              type="button"
              onClick={() =>
                scrollToSection(
                  "paper-roadmap-section",
                )
              }
            >
              🧭 Roadmap
            </button>


            <button
              type="button"
              onClick={() =>
                scrollToSection(
                  "paper-citation-section",
                )
              }
            >
              📚 Citation
            </button>

          </nav>

        )}


        {/* =================================================
            OCR MESSAGE
        ================================================= */}

        {needsOcr ? (

          <section className="paper-ocr-message">

            <span>
              🖼️
            </span>


            <div>

              <h2>
                This appears to be a scanned PDF
              </h2>

              <p>
                PaperMind could open the document,
                but no readable digital text was detected.
                Please upload a text-based PDF for analysis.
              </p>

            </div>

          </section>

        ) : (

          <>

            {/* =============================================
                SUMMARY ERROR
            ============================================= */}

            {summaryErrorMessage && (

              <div className="summary-error-banner">

                <span>
                  ⚠️
                </span>


                <div>

                  <strong>
                    AI summary problem
                  </strong>

                  <p>
                    {summaryErrorMessage}
                  </p>

                </div>

              </div>

            )}


            {/* =============================================
                SUMMARY ACTION
            ============================================= */}

            <section
              id="paper-summary-section"
              className="paper-action-card"
            >

              <div>

                <p className="paper-section-label">

                  {
                    summary
                      ? "Analysis Complete"
                      : "Next Step"
                  }

                </p>


                <h2>

                  {
                    summary
                      ? (
                        "Your AI research "
                        + "analysis is ready"
                      )

                      : (
                        "Generate an AI "
                        + "explanation"
                      )
                  }

                </h2>


                <p>

                  {
                    summary
                      ? (
                        "PaperMind has analysed the "
                        + "extracted paper text and "
                        + "organised the main "
                        + "information below."
                      )

                      : (
                        "Generate a structured "
                        + "explanation containing "
                        + "the summary, research "
                        + "problem, methodology, "
                        + "findings, limitations "
                        + "and future work."
                      )
                  }

                </p>

              </div>


              <button
                type="button"
                onClick={
                  handleGenerateSummary
                }
                disabled={
                  isGenerating
                  || Boolean(summary)
                }
              >

                {
                  isGenerating
                    ? "Generating Summary..."

                    : summary
                      ? "Summary Generated"

                      : "Generate AI Summary"
                }

              </button>

            </section>


            {/* =============================================
                SUMMARY GENERATING
            ============================================= */}

            {isGenerating && (

              <section className="summary-generating-card">

                <div className="summary-generating-spinner">
                </div>


                <div>

                  <strong>
                    PaperMind is analysing
                    your paper
                  </strong>

                  <p>
                    This may take several
                    seconds. Please keep this
                    page open.
                  </p>

                </div>

              </section>

            )}


            {/* =============================================
                AI SUMMARY
            ============================================= */}

            {summary && (

              <section className="ai-summary-section">

                <div className="ai-summary-heading">

                  <div>

                    <p className="paper-section-label">
                      AI Research Analysis
                    </p>

                    <h2>
                      {summary.paper_title}
                    </h2>

                  </div>


                  <div className="summary-meta">

                    {summaryGeneratedDate && (
                      <span>
                        Generated:{" "}
                        {summaryGeneratedDate}
                      </span>
                    )}

                  </div>

                </div>


                {/* =========================================
                    PLAIN LANGUAGE SUMMARY
                ========================================= */}

                <article className="summary-overview-card">

                  <div className="summary-card-icon">
                    🧠
                  </div>


                  <div>

                    <p className="paper-section-label">
                      Plain-Language Summary
                    </p>

                    <p className="summary-main-text">

                      {
                        summary
                          .plain_language_summary
                      }

                    </p>

                  </div>

                </article>


                {/* =========================================
                    PROBLEM + METHODOLOGY
                ========================================= */}

                <div className="summary-content-grid">

                  <article className="summary-content-card">

                    <div className="summary-content-title">

                      <span>
                        🎯
                      </span>

                      <h3>
                        Research Problem
                      </h3>

                    </div>

                    <p>
                      {
                        summary
                          .research_problem
                      }
                    </p>

                  </article>


                  <article className="summary-content-card">

                    <div className="summary-content-title">

                      <span>
                        🧪
                      </span>

                      <h3>
                        Methodology
                      </h3>

                    </div>

                    <p>
                      {
                        summary.methodology
                      }
                    </p>

                  </article>

                </div>


                {/* =========================================
                    FINDINGS + LIMITATIONS
                ========================================= */}

                <div className="summary-content-grid">

                  <article className="summary-content-card">

                    <div className="summary-content-title">

                      <span>
                        📊
                      </span>

                      <h3>
                        Key Findings
                      </h3>

                    </div>


                    <SummaryList
                      items={
                        summary
                          .key_findings
                      }
                      emptyMessage={
                        "No key findings were returned."
                      }
                    />

                  </article>


                  <article className="summary-content-card">

                    <div className="summary-content-title">

                      <span>
                        ⚠️
                      </span>

                      <h3>
                        Limitations
                      </h3>

                    </div>


                    <SummaryList
                      items={
                        summary.limitations
                      }
                      emptyMessage={
                        "No limitations were clearly stated."
                      }
                    />

                  </article>

                </div>


                {/* =========================================
                    FUTURE WORK
                ========================================= */}

                <article
                  className={[
                    "summary-content-card",
                    "summary-full-width-card",
                  ].join(" ")}
                >

                  <div className="summary-content-title">

                    <span>
                      🚀
                    </span>

                    <h3>
                      Future Work
                    </h3>

                  </div>


                  <SummaryList
                    items={
                      summary.future_work
                    }
                    emptyMessage={
                      "No future work was clearly stated."
                    }
                  />

                </article>


                {/* =========================================
                    KEYWORDS
                ========================================= */}

                <article className="summary-keywords-card">

                  <div className="summary-content-title">

                    <span>
                      🏷️
                    </span>

                    <h3>
                      Keywords
                    </h3>

                  </div>


                  <div className="summary-keyword-list">

                    {
                      summary
                        .keywords
                        ?.length > 0
                        ? (

                          summary
                            .keywords
                            .map(
                              (
                                keyword,
                                index,
                              ) => (

                                <span
                                  className="summary-keyword"
                                  key={`${keyword}-${index}`}
                                >
                                  {keyword}
                                </span>

                              ),
                            )

                        ) : (

                          <p className="summary-empty-message">
                            No keywords were returned.
                          </p>

                        )
                    }

                  </div>

                </article>

              </section>

            )}


            {/* =============================================
                EXPLAIN AT MY LEVEL
            ============================================= */}

            <div
              id="paper-explanation-section"
              className="paper-tool-section-anchor"
            >

              <ExplanationPanel
                paperId={paperId}
              />

            </div>


            {/* =============================================
                ASK PAPERMIND / RAG CHAT
            ============================================= */}

            <div
              id="paper-chat-section"
              className="paper-tool-section-anchor"
            >

              <PaperChatPanel
                paperId={paperId}
              />

            </div>


            {/* =============================================
                RESEARCH ROADMAP
            ============================================= */}

            <div
              id="paper-roadmap-section"
              className="paper-tool-section-anchor"
            >

              <ResearchRoadmapPanel
                paperId={paperId}
              />

            </div>


            {/* =============================================
                CITATION GENERATOR
            ============================================= */}

            <div
              id="paper-citation-section"
              className="paper-tool-section-anchor"
            >

              <CitationGenerator
                paperId={paperId}
              />

            </div>


            {/* =============================================
                EXTRACTED PAPER TEXT
            ============================================= */}

            <section className="paper-text-section">

              <div className="paper-text-heading">

                <div>

                  <p className="paper-section-label">
                    Extracted Content
                  </p>

                  <h2>
                    Paper text preview
                  </h2>

                </div>


                <span>

                  {
                    formatNumber(
                      paper
                        ?.character_count,
                    )
                  }{" "}

                  characters

                </span>

              </div>


              <div className="paper-text-viewer">

                <pre>

                  {
                    paper
                      ?.extracted_text
                    || (
                      "No text was "
                      + "extracted."
                    )
                  }

                </pre>

              </div>

            </section>

          </>

        )}

      </main>

    </div>

  );
}

function formatProcessingStatus(
  status,
) {
  switch (status) {
    case "summarized":
      return "AI Analysis Ready";

    case "ready":
      return "Ready for Analysis";

    case "needs_ocr":
      return "OCR Required";

    case "uploaded":
      return "Uploaded";

    default:
      return "Processing";
  }
}

export default PaperAnalysis;