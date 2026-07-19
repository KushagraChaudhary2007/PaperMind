import {
  useEffect,
  useState,
} from "react";

import {
  Link,
  useNavigate,
} from "react-router";

import {
  generateComparison,
  getComparison,
  getComparisons,
} from "../services/comparisonService";

import {
  getUserPapers,
} from "../services/paperService";

import "../styles/ComparePapers.css";


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


function ComparisonList({
  items,
  emptyMessage,
}) {
  if (
    !Array.isArray(items) ||
    items.length === 0
  ) {
    return (
      <p className="comparison-empty-text">
        {emptyMessage}
      </p>
    );
  }

  return (
    <ul className="comparison-list">
      {items.map((item, index) => (
        <li key={`${item}-${index}`}>
          {item}
        </li>
      ))}
    </ul>
  );
}


function ComparePapers() {
  const navigate = useNavigate();

  const [papers, setPapers] =
    useState([]);

  const [
    savedComparisons,
    setSavedComparisons,
  ] = useState([]);

  const [paperAId, setPaperAId] =
    useState("");

  const [paperBId, setPaperBId] =
    useState("");

  const [
    activeComparison,
    setActiveComparison,
  ] = useState(null);

  const [isLoading, setIsLoading] =
    useState(true);

  const [
    isGenerating,
    setIsGenerating,
  ] = useState(false);

  const [
    loadingComparisonId,
    setLoadingComparisonId,
  ] = useState(null);

  const [
    errorMessage,
    setErrorMessage,
  ] = useState("");


  function redirectToLogin() {
    navigate("/login", {
      replace: true,

      state: {
        from: "/compare",

        message:
          "Your session has expired. Please sign in again.",
      },
    });
  }


  useEffect(() => {
    let cancelled = false;


    async function loadComparisonPage() {
      setIsLoading(true);
      setErrorMessage("");

      try {
        const [
          paperData,
          comparisonData,
        ] = await Promise.all([
          getUserPapers(),
          getComparisons(),
        ]);

        if (cancelled) {
          return;
        }

        setPapers(
          Array.isArray(paperData)
            ? paperData
            : [],
        );

        setSavedComparisons(
          Array.isArray(comparisonData)
            ? comparisonData
            : [],
        );
      } catch (error) {
        if (cancelled) {
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
              "PaperMind could not load "
              + "the comparison workspace."
            ),
        );
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }


    loadComparisonPage();


    return () => {
      cancelled = true;
    };
  }, [navigate]);


  const summarizedPapers =
    papers.filter(
      (paper) =>
        paper.processing_status ===
        "summarized",
    );


  const selectedPaperA =
    summarizedPapers.find(
      (paper) =>
        paper.id === Number(paperAId),
    );

  const selectedPaperB =
    summarizedPapers.find(
      (paper) =>
        paper.id === Number(paperBId),
    );


  async function handleCompare(event) {
    event.preventDefault();

    setErrorMessage("");

    if (!paperAId || !paperBId) {
      setErrorMessage(
        "Please select two research papers.",
      );

      return;
    }

    if (paperAId === paperBId) {
      setErrorMessage(
        "Please select two different research papers.",
      );

      return;
    }

    setIsGenerating(true);

    try {
      const comparison =
        await generateComparison(
          paperAId,
          paperBId,
        );

      setActiveComparison(
        comparison,
      );

      setSavedComparisons(
        (currentComparisons) => {
          const alreadyExists =
            currentComparisons.some(
              (item) =>
                item.id ===
                comparison.id,
            );

          if (alreadyExists) {
            return currentComparisons;
          }

          return [
            comparison,
            ...currentComparisons,
          ];
        },
      );

      requestAnimationFrame(() => {
        document
          .getElementById(
            "comparison-result",
          )
          ?.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
      });
    } catch (error) {
      if (error?.status === 401) {
        redirectToLogin();
        return;
      }

      setErrorMessage(
        error instanceof Error
          ? error.message
          : (
            "The papers could not "
            + "be compared."
          ),
      );
    } finally {
      setIsGenerating(false);
    }
  }


  async function openSavedComparison(
    comparisonId,
  ) {
    setErrorMessage("");
    setLoadingComparisonId(
      comparisonId,
    );

    try {
      const comparison =
        await getComparison(
          comparisonId,
        );

      setActiveComparison(
        comparison,
      );

      requestAnimationFrame(() => {
        document
          .getElementById(
            "comparison-result",
          )
          ?.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
      });
    } catch (error) {
      if (error?.status === 401) {
        redirectToLogin();
        return;
      }

      setErrorMessage(
        error instanceof Error
          ? error.message
          : (
            "The saved comparison "
            + "could not be opened."
          ),
      );
    } finally {
      setLoadingComparisonId(
        null,
      );
    }
  }


  if (isLoading) {
    return (
      <main className="comparison-loading-page">
        <div className="comparison-spinner">
        </div>

        <p>
          Loading your PaperMind comparison
          workspace...
        </p>
      </main>
    );
  }


  return (
    <div className="comparison-page">
      <header className="comparison-topbar">
        <Link
          to="/dashboard"
          className="comparison-back"
        >
          ← Dashboard
        </Link>

        <Link
          to="/dashboard"
          className="comparison-logo"
        >
          <span>📄</span>
          PaperMind
        </Link>
      </header>

      <main className="comparison-main">
        <section className="comparison-title-section">
          <div>
            <p className="comparison-eyebrow">
              AI Research Comparison
            </p>

            <h1>
              Compare research papers
            </h1>

            <p>
              Select two analysed papers and
              PaperMind will compare their research
              problems, methodologies, findings,
              limitations, similarities, and
              differences.
            </p>
          </div>

          <Link
            to="/upload"
            className="comparison-upload-link"
          >
            + Upload Paper
          </Link>
        </section>

        {errorMessage && (
          <div className="comparison-error">
            <span>⚠️</span>

            <div>
              <strong>
                Comparison problem
              </strong>

              <p>{errorMessage}</p>
            </div>
          </div>
        )}

        <section className="comparison-builder-card">
          <div className="comparison-builder-heading">
            <p className="comparison-eyebrow">
              Select Papers
            </p>

            <h2>
              Choose two papers to compare
            </h2>

            <p>
              Only papers with generated AI
              summaries are available for
              comparison.
            </p>
          </div>

          {summarizedPapers.length < 2 ? (
            <div className="comparison-not-ready">
              <span>📚</span>

              <div>
                <h3>
                  You need at least two
                  summarized papers
                </h3>

                <p>
                  Upload papers and generate their
                  AI summaries before comparing
                  them.
                </p>
              </div>

              <Link to="/dashboard">
                View My Papers
              </Link>
            </div>
          ) : (
            <form
              className="comparison-form"
              onSubmit={handleCompare}
            >
              <div className="comparison-selector-grid">
                <div className="comparison-selector">
                  <div className="comparison-paper-label">
                    <span>A</span>

                    <div>
                      <strong>
                        Paper A
                      </strong>

                      <small>
                        First research paper
                      </small>
                    </div>
                  </div>

                  <select
                    value={paperAId}
                    onChange={(event) => {
                      setPaperAId(
                        event.target.value,
                      );
                    }}
                    disabled={isGenerating}
                    required
                  >
                    <option value="">
                      Select Paper A
                    </option>

                    {summarizedPapers.map(
                      (paper) => (
                        <option
                          key={paper.id}
                          value={paper.id}
                          disabled={
                            String(paper.id) ===
                            paperBId
                          }
                        >
                          {
                            paper
                              .original_filename
                          }
                        </option>
                      ),
                    )}
                  </select>

                  {selectedPaperA && (
                    <div className="selected-comparison-paper">
                      <span>📑</span>

                      <div>
                        <strong>
                          {
                            selectedPaperA
                              .original_filename
                          }
                        </strong>

                        <small>
                          AI summary ready
                        </small>
                      </div>
                    </div>
                  )}
                </div>

                <div className="comparison-versus">
                  VS
                </div>

                <div className="comparison-selector">
                  <div className="comparison-paper-label">
                    <span>B</span>

                    <div>
                      <strong>
                        Paper B
                      </strong>

                      <small>
                        Second research paper
                      </small>
                    </div>
                  </div>

                  <select
                    value={paperBId}
                    onChange={(event) => {
                      setPaperBId(
                        event.target.value,
                      );
                    }}
                    disabled={isGenerating}
                    required
                  >
                    <option value="">
                      Select Paper B
                    </option>

                    {summarizedPapers.map(
                      (paper) => (
                        <option
                          key={paper.id}
                          value={paper.id}
                          disabled={
                            String(paper.id) ===
                            paperAId
                          }
                        >
                          {
                            paper
                              .original_filename
                          }
                        </option>
                      ),
                    )}
                  </select>

                  {selectedPaperB && (
                    <div className="selected-comparison-paper">
                      <span>📑</span>

                      <div>
                        <strong>
                          {
                            selectedPaperB
                              .original_filename
                          }
                        </strong>

                        <small>
                          AI summary ready
                        </small>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <button
                type="submit"
                className="generate-comparison-button"
                disabled={
                  isGenerating ||
                  !paperAId ||
                  !paperBId ||
                  paperAId === paperBId
                }
              >
                {isGenerating
                  ? (
                    <>
                      <span className="comparison-button-spinner">
                      </span>

                      Comparing Papers...
                    </>
                  )
                  : (
                    <>
                      ✨ Generate AI Comparison
                    </>
                  )}
              </button>
            </form>
          )}
        </section>

        {activeComparison && (
          <section
            id="comparison-result"
            className="comparison-result-section"
          >
            <header className="comparison-result-header">
              <div>
                <p className="comparison-eyebrow">
                  AI Comparison Result
                </p>

                <h2>
                  {
                    activeComparison
                      .comparison_title
                  }
                </h2>
              </div>

              <div className="comparison-result-meta">
                <span>
                  {
                    activeComparison
                      .model_name
                  }
                </span>

                <span>
                  {formatGeneratedDate(
                    activeComparison
                      .generated_at,
                  )}
                </span>
              </div>
            </header>

            <div className="comparison-paper-headings">
              <article>
                <span>A</span>

                <div>
                  <small>
                    Paper A
                  </small>

                  <h3>
                    {
                      activeComparison
                        .paper_a_title
                    }
                  </h3>

                  <p>
                    {
                      activeComparison
                        .paper_a_filename
                    }
                  </p>
                </div>
              </article>

              <article>
                <span>B</span>

                <div>
                  <small>
                    Paper B
                  </small>

                  <h3>
                    {
                      activeComparison
                        .paper_b_title
                    }
                  </h3>

                  <p>
                    {
                      activeComparison
                        .paper_b_filename
                    }
                  </p>
                </div>
              </article>
            </div>

            <article className="comparison-overview-card">
              <div className="comparison-card-icon">
                🧠
              </div>

              <div>
                <p className="comparison-eyebrow">
                  Overall Comparison
                </p>

                <p>
                  {
                    activeComparison
                      .overview
                  }
                </p>
              </div>
            </article>

            <div className="comparison-two-column">
              <article className="comparison-detail-card">
                <div className="comparison-detail-title">
                  <span>🤝</span>

                  <h3>
                    Similarities
                  </h3>
                </div>

                <ComparisonList
                  items={
                    activeComparison
                      .similarities
                  }
                  emptyMessage={
                    "No major similarities were returned."
                  }
                />
              </article>

              <article className="comparison-detail-card">
                <div className="comparison-detail-title">
                  <span>⚖️</span>

                  <h3>
                    Differences
                  </h3>
                </div>

                <ComparisonList
                  items={
                    activeComparison
                      .differences
                  }
                  emptyMessage={
                    "No major differences were returned."
                  }
                />
              </article>
            </div>

            <div className="comparison-analysis-grid">
              <article className="comparison-analysis-card">
                <div className="comparison-detail-title">
                  <span>🎯</span>

                  <h3>
                    Research Problems
                  </h3>
                </div>

                <p>
                  {
                    activeComparison
                      .research_problem_comparison
                  }
                </p>
              </article>

              <article className="comparison-analysis-card">
                <div className="comparison-detail-title">
                  <span>🧪</span>

                  <h3>
                    Methodologies
                  </h3>
                </div>

                <p>
                  {
                    activeComparison
                      .methodology_comparison
                  }
                </p>
              </article>

              <article className="comparison-analysis-card">
                <div className="comparison-detail-title">
                  <span>📊</span>

                  <h3>
                    Findings
                  </h3>
                </div>

                <p>
                  {
                    activeComparison
                      .findings_comparison
                  }
                </p>
              </article>

              <article className="comparison-analysis-card">
                <div className="comparison-detail-title">
                  <span>⚠️</span>

                  <h3>
                    Limitations
                  </h3>
                </div>

                <p>
                  {
                    activeComparison
                      .limitations_comparison
                  }
                </p>
              </article>
            </div>

            <article className="comparison-guidance-card">
              <div className="comparison-card-icon">
                💡
              </div>

              <div>
                <p className="comparison-eyebrow">
                  Practical Guidance
                </p>

                <h3>
                  When is each paper more useful?
                </h3>

                <p>
                  {
                    activeComparison
                      .practical_guidance
                  }
                </p>
              </div>
            </article>
          </section>
        )}

        <section className="saved-comparisons-section">
          <div className="saved-comparisons-heading">
            <div>
              <p className="comparison-eyebrow">
                Comparison History
              </p>

              <h2>
                Saved comparisons
              </h2>
            </div>

            <span>
              {savedComparisons.length}
              {" "}
              saved
            </span>
          </div>

          {savedComparisons.length === 0 ? (
            <div className="saved-comparisons-empty">
              <span>⚖️</span>

              <h3>
                No comparisons yet
              </h3>

              <p>
                Generate your first AI paper
                comparison above.
              </p>
            </div>
          ) : (
            <div className="saved-comparison-grid">
              {savedComparisons.map(
                (comparison) => (
                  <button
                    key={comparison.id}
                    type="button"
                    className="saved-comparison-card"
                    onClick={() => {
                      openSavedComparison(
                        comparison.id,
                      );
                    }}
                    disabled={
                      loadingComparisonId ===
                      comparison.id
                    }
                  >
                    <div className="saved-comparison-icon">
                      ⚖️
                    </div>

                    <div className="saved-comparison-content">
                      <strong>
                        {
                          comparison
                            .comparison_title
                        }
                      </strong>

                      <p>
                        {
                          comparison
                            .paper_a_filename
                        }
                      </p>

                      <span>vs</span>

                      <p>
                        {
                          comparison
                            .paper_b_filename
                        }
                      </p>
                    </div>

                    <div className="saved-comparison-footer">
                      <span>
                        {loadingComparisonId ===
                        comparison.id
                          ? "Opening..."
                          : "Open Comparison"}
                      </span>

                      <strong>→</strong>
                    </div>
                  </button>
                ),
              )}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default ComparePapers;