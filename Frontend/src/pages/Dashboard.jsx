import {
  useEffect,
  useState,
} from "react";

import {
  Link,
  useNavigate,
} from "react-router";

import {
  clearStoredToken,
  getCurrentUser,
} from "../services/authService";

import {
  getUserPapers,
} from "../services/paperService";

import "../styles/Dashboard.css";


function formatFileSize(bytes) {
  const numericBytes = Number(bytes) || 0;

  if (numericBytes < 1024) {
    return `${numericBytes} bytes`;
  }

  if (numericBytes < 1024 * 1024) {
    return `${(
      numericBytes / 1024
    ).toFixed(1)} KB`;
  }

  return `${(
    numericBytes /
    (1024 * 1024)
  ).toFixed(2)} MB`;
}


function formatUploadDate(value) {
  if (!value) {
    return "Unknown date";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Unknown date";
  }

  return new Intl.DateTimeFormat(
    undefined,
    {
      dateStyle: "medium",
    },
  ).format(date);
}


function getPaperStatusDetails(status) {
  switch (status) {
    case "summarized":
      return {
        label: "AI summary ready",
        className: "paper-list-status-complete",
      };

    case "ready":
      return {
        label: "Ready for summary",
        className: "paper-list-status-ready",
      };

    case "needs_ocr":
      return {
        label: "OCR required",
        className: "paper-list-status-warning",
      };

    case "uploaded":
      return {
        label: "Uploaded",
        className: "paper-list-status-neutral",
      };

    default:
      return {
        label: status || "Processing",
        className: "paper-list-status-neutral",
      };
  }
}


function Dashboard() {
  const navigate = useNavigate();

  const [user, setUser] = useState(null);
  const [papers, setPapers] = useState([]);

  const [isLoading, setIsLoading] =
    useState(true);

  const [
    paperErrorMessage,
    setPaperErrorMessage,
  ] = useState("");


  // =======================================================
  // Load dashboard data
  // =======================================================

  useEffect(() => {
    let cancelled = false;


    async function loadDashboard() {
      try {
        const userData =
          await getCurrentUser();

        if (cancelled) {
          return;
        }

        setUser(userData);
      } catch {
        if (!cancelled) {
          clearStoredToken();

          navigate("/login", {
            replace: true,

            state: {
              message:
                "Your session is invalid or expired. Please sign in again.",
            },
          });
        }

        return;
      }


      try {
        const paperData =
          await getUserPapers();

        if (!cancelled) {
          setPapers(
            Array.isArray(paperData)
              ? paperData
              : [],
          );
        }
      } catch (error) {
        if (cancelled) {
          return;
        }

        if (error?.status === 401) {
          clearStoredToken();

          navigate("/login", {
            replace: true,

            state: {
              message:
                "Your session has expired. Please sign in again.",
            },
          });

          return;
        }

        setPaperErrorMessage(
          error instanceof Error
            ? error.message
            : "Your research papers could not be loaded.",
        );
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }


    loadDashboard();


    return () => {
      cancelled = true;
    };
  }, [navigate]);


  // =======================================================
  // Navigation
  // =======================================================

  function openUploadPage() {
    navigate("/upload");
  }


  // NEW:
  // Opens the Paper Comparison page.
  function openComparePage() {
    navigate("/compare");
  }


  function scrollToPapers() {
    document
      .getElementById("recent-papers")
      ?.scrollIntoView({
        behavior: "smooth",
      });
  }


  function handleLogout() {
    clearStoredToken();

    navigate("/login", {
      replace: true,

      state: {
        message:
          "You have been signed out successfully.",
      },
    });
  }


  // =======================================================
  // Loading screen
  // =======================================================

  if (isLoading) {
    return (
      <main className="dashboard-loading">
        <div className="dashboard-loader">
        </div>

        <p>
          Loading your PaperMind workspace...
        </p>
      </main>
    );
  }


  // =======================================================
  // Dashboard statistics
  // =======================================================

  const totalPapers =
    papers.length;

  const summarizedPapers =
    papers.filter(
      (paper) =>
        paper.processing_status ===
        "summarized",
    ).length;

  const readyPapers =
    papers.filter(
      (paper) =>
        paper.processing_status ===
        "ready",
    ).length;

  const recentPapers =
    papers.slice(0, 6);


  // =======================================================
  // Dashboard UI
  // =======================================================

  return (
    <div className="dashboard-layout">

      {/* =================================================
          SIDEBAR
      ================================================= */}

      <aside className="dashboard-sidebar">

        <Link
          to="/dashboard"
          className="dashboard-logo"
        >
          <span>📄</span>

          PaperMind
        </Link>


        <nav className="dashboard-nav">

          <button
            type="button"
            className="dashboard-nav-item active"
          >
            <span>⌂</span>

            Overview
          </button>


          <button
            type="button"
            className="dashboard-nav-item"
            onClick={openUploadPage}
          >
            <span>＋</span>

            Upload Paper
          </button>


          <button
            type="button"
            className="dashboard-nav-item"
            onClick={scrollToPapers}
          >
            <span>▤</span>

            My Papers
          </button>


          {/* NEW: Paper Comparison */}

          <button
            type="button"
            className="dashboard-nav-item"
            onClick={openComparePage}
          >
            <span>⚖️</span>

            Compare Papers
          </button>


          <button
            type="button"
            className="dashboard-nav-item"
            disabled
          >
            <span>★</span>

            Bookmarks
          </button>


          <button
            type="button"
            className="dashboard-nav-item"
            disabled
          >
            <span>◷</span>

            History
          </button>

        </nav>


        <button
          type="button"
          className="dashboard-logout"
          onClick={handleLogout}
        >
          Sign Out
        </button>

      </aside>


      {/* =================================================
          MAIN DASHBOARD
      ================================================= */}

      <main className="dashboard-main">

        {/* =================================================
            HEADER
        ================================================= */}

        <header className="dashboard-header">

          <div>

            <p>
              Your research workspace
            </p>

            <h1>
              Welcome,{" "}
              {user?.full_name ||
                "Researcher"}
            </h1>

          </div>


          <div className="dashboard-profile">

            <div className="profile-avatar">
              {user?.full_name
                ?.charAt(0)
                ?.toUpperCase() || "U"}
            </div>


            <div>

              <strong>
                {user?.full_name}
              </strong>

              <span>
                {user?.email}
              </span>

            </div>

          </div>

        </header>


        {/* =================================================
            HERO
        ================================================= */}

        <section className="dashboard-hero-card">

          <div>

            <p className="dashboard-badge">
              AI Research Assistant
            </p>


            <h2>
              Turn your next research paper into
              clear knowledge.
            </h2>


            <p>
              Upload a PDF to extract its text and
              generate an AI-powered summary,
              methodology, findings, limitations,
              future work, and keywords.
            </p>

          </div>


          <button
            type="button"
            onClick={openUploadPage}
          >
            Upload Research Paper
          </button>

        </section>


        {/* =================================================
            STATISTICS
        ================================================= */}

        <section className="dashboard-stat-grid">

          <article className="dashboard-stat-card">

            <span>
              📚
            </span>

            <div>

              <strong>
                {totalPapers}
              </strong>

              <p>
                Papers uploaded
              </p>

            </div>

          </article>


          <article className="dashboard-stat-card">

            <span>
              🧠
            </span>

            <div>

              <strong>
                {summarizedPapers}
              </strong>

              <p>
                AI summaries generated
              </p>

            </div>

          </article>


          <article className="dashboard-stat-card">

            <span>
              ✨
            </span>

            <div>

              <strong>
                {readyPapers}
              </strong>

              <p>
                Ready for summary
              </p>

            </div>

          </article>

        </section>

        {/* =================================================
    PAPERMIND AI TOOLKIT
================================================= */}

<section className="dashboard-toolkit">

  <div className="dashboard-toolkit-heading">

    <div>

      <p>
        PaperMind AI Toolkit
      </p>

      <h2>
        Everything you need for research
      </h2>

      <span>
        Analyze, understand, compare, explore,
        and cite research papers from one workspace.
      </span>

    </div>

  </div>


  <div className="dashboard-tool-grid">

    {/* =============================================
        ANALYZE PAPER
    ============================================= */}

    <button
      type="button"
      className="dashboard-tool-card"
      onClick={openUploadPage}
    >

      <div className="dashboard-tool-icon">
        📄
      </div>

      <div>

        <span className="dashboard-tool-label">
          Analyze
        </span>

        <h3>
          Analyze a Paper
        </h3>

        <p>
          Upload a research PDF and generate
          summaries, explanations, and insights.
        </p>

      </div>

      <strong>
        →
      </strong>

    </button>


    {/* =============================================
        COMPARE PAPERS
    ============================================= */}

    <button
      type="button"
      className="dashboard-tool-card"
      onClick={openComparePage}
    >

      <div className="dashboard-tool-icon">
        ⚖️
      </div>

      <div>

        <span className="dashboard-tool-label">
          Compare
        </span>

        <h3>
          Compare Papers
        </h3>

        <p>
          Compare research problems,
          methodologies, findings, and limitations.
        </p>

      </div>

      <strong>
        →
      </strong>

    </button>


    {/* =============================================
        RESEARCH ROADMAP
    ============================================= */}

    <button
      type="button"
      className="dashboard-tool-card"
      onClick={scrollToPapers}
    >

      <div className="dashboard-tool-icon">
        🧭
      </div>

      <div>

        <span className="dashboard-tool-label">
          Explore
        </span>

        <h3>
          Research Roadmap
        </h3>

        <p>
          Open a paper to build a personalized
          learning and research roadmap.
        </p>

      </div>

      <strong>
        →
      </strong>

    </button>


    {/* =============================================
        CITATION GENERATOR
    ============================================= */}

    <button
      type="button"
      className="dashboard-tool-card"
      onClick={scrollToPapers}
    >

      <div className="dashboard-tool-icon">
        📚
      </div>

      <div>

        <span className="dashboard-tool-label">
          Write
        </span>

        <h3>
          Citation Generator
        </h3>

        <p>
          Generate APA, MLA, IEEE, Chicago,
          Harvard, and BibTeX citations.
        </p>

      </div>

      <strong>
        →
      </strong>

    </button>

  </div>

</section>


        {/* =================================================
            RECENT PAPERS
        ================================================= */}

        <section
          id="recent-papers"
          className="recent-papers"
        >

          <div className="recent-papers-heading">

            <div className="section-heading">

              <div>

                <p>
                  Your library
                </p>

                <h2>
                  Recent research papers
                </h2>

              </div>

            </div>


            {papers.length > 0 && (
              <button
                type="button"
                className="upload-new-paper-button"
                onClick={openUploadPage}
              >
                + Upload New Paper
              </button>
            )}

          </div>


          {/* ===============================================
              PAPER LOAD ERROR
          =============================================== */}

          {paperErrorMessage && (
            <div className="dashboard-error-banner">

              <span>
                ⚠️
              </span>


              <div>

                <strong>
                  Papers could not be loaded
                </strong>

                <p>
                  {paperErrorMessage}
                </p>

              </div>

            </div>
          )}


          {/* ===============================================
              EMPTY LIBRARY
          =============================================== */}

          {!paperErrorMessage &&
            recentPapers.length === 0 && (

              <div className="empty-library">

                <span>
                  📑
                </span>

                <h3>
                  No research papers yet
                </h3>

                <p>
                  Upload your first paper to begin
                  using PaperMind.
                </p>

                <button
                  type="button"
                  onClick={openUploadPage}
                >
                  Upload Your First Paper
                </button>

              </div>

            )}


          {/* ===============================================
              PAPER CARDS
          =============================================== */}

          {!paperErrorMessage &&
            recentPapers.length > 0 && (

              <div className="recent-paper-grid">

                {recentPapers.map(
                  (paper) => {

                    const statusDetails =
                      getPaperStatusDetails(
                        paper.processing_status,
                      );


                    return (

                      <Link
                        key={paper.id}
                        to={`/papers/${paper.id}`}
                        className="recent-paper-card"
                      >

                        <div className="recent-paper-top">

                          <div className="recent-paper-icon">
                            PDF
                          </div>


                          <span
                            className={[
                              "paper-list-status",
                              statusDetails.className,
                            ].join(" ")}
                          >
                            {
                              statusDetails
                                .label
                            }
                          </span>

                        </div>


                        <div className="recent-paper-content">

                          <h3>
                            {
                              paper
                                .original_filename
                            }
                          </h3>


                          <div className="recent-paper-meta">

                            <span>
                              {
                                formatFileSize(
                                  paper.file_size,
                                )
                              }
                            </span>


                            <span>
                              •
                            </span>


                            <span>
                              {
                                formatUploadDate(
                                  paper.uploaded_at,
                                )
                              }
                            </span>

                          </div>

                        </div>


                        <div className="recent-paper-footer">

                          <span>
                            Open analysis
                          </span>

                          <strong>
                            →
                          </strong>

                        </div>

                      </Link>

                    );
                  },
                )}

              </div>

            )}

        </section>

      </main>

    </div>
  );
}


export default Dashboard;