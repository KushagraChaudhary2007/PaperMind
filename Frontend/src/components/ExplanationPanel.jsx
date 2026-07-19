import {
  useEffect,
  useState,
} from "react";

import {
  useNavigate,
} from "react-router";

import {
  generatePaperExplanation,
  getPaperExplanation,
} from "../services/paperService";

import "../styles/ExplanationPanel.css";


const EXPLANATION_LEVELS = [
  {
    id: "beginner",
    icon: "🌱",
    title: "Beginner",
    description:
      "Simple language, basic examples, and minimal jargon.",
  },
  {
    id: "intermediate",
    icon: "🎓",
    title: "Intermediate",
    description:
      "College-level detail with important technical concepts.",
  },
  {
    id: "expert",
    icon: "🔬",
    title: "Expert",
    description:
      "Advanced terminology, methodology, and technical depth.",
  },
];


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


function ExplanationList({
  items,
  emptyMessage,
}) {
  if (
    !Array.isArray(items) ||
    items.length === 0
  ) {
    return (
      <p className="explanation-empty-message">
        {emptyMessage}
      </p>
    );
  }

  return (
    <ul className="explanation-list">
      {items.map((item, index) => (
        <li key={`${item}-${index}`}>
          {item}
        </li>
      ))}
    </ul>
  );
}


function ExplanationPanel({ paperId }) {
  const navigate = useNavigate();

  const [
    selectedLevel,
    setSelectedLevel,
  ] = useState("beginner");

  const [
    explanation,
    setExplanation,
  ] = useState(null);

  const [
    isLoading,
    setIsLoading,
  ] = useState(true);

  const [
    isGenerating,
    setIsGenerating,
  ] = useState(false);

  const [
    errorMessage,
    setErrorMessage,
  ] = useState("");


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


  useEffect(() => {
    let cancelled = false;


    async function loadExplanation() {
      setIsLoading(true);
      setErrorMessage("");
      setExplanation(null);

      try {
        const savedExplanation =
          await getPaperExplanation(
            paperId,
            selectedLevel,
          );

        if (!cancelled) {
          setExplanation(
            savedExplanation,
          );
        }
      } catch (error) {
        if (cancelled) {
          return;
        }

        if (error?.status === 401) {
          redirectToLogin();
          return;
        }

        // A 404 means that the selected level
        // has not been generated yet.
        if (error?.status !== 404) {
          setErrorMessage(
            error instanceof Error
              ? error.message
              : "The explanation could not be loaded.",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }


    loadExplanation();


    return () => {
      cancelled = true;
    };
  }, [
    navigate,
    paperId,
    selectedLevel,
  ]);


  async function handleGenerateExplanation() {
    setErrorMessage("");
    setIsGenerating(true);

    try {
      const generatedExplanation =
        await generatePaperExplanation(
          paperId,
          selectedLevel,
        );

      setExplanation(
        generatedExplanation,
      );
    } catch (error) {
      if (error?.status === 401) {
        redirectToLogin();
        return;
      }

      setErrorMessage(
        error instanceof Error
          ? error.message
          : "The explanation could not be generated.",
      );
    } finally {
      setIsGenerating(false);
    }
  }


  const selectedLevelDetails =
    EXPLANATION_LEVELS.find(
      (level) =>
        level.id === selectedLevel,
    );

  const generatedDate =
    formatGeneratedDate(
      explanation?.generated_at,
    );


  return (
    <section 
      id="paper-explanation-section"
      className="explanation-section"
    >
      <div className="explanation-heading">
        <div>
          <p className="paper-section-label">
            Adaptive Learning
          </p>

          <h2>
            Explain this paper at my level
          </h2>

          <p>
            Choose how deeply PaperMind should
            explain the research paper.
          </p>
        </div>
      </div>

      <div className="explanation-level-grid">
        {EXPLANATION_LEVELS.map(
          (level) => (
            <button
              key={level.id}
              type="button"
              className={[
                "explanation-level-button",

                selectedLevel === level.id
                  ? "explanation-level-button-active"
                  : "",
              ].join(" ")}
              onClick={() => {
                setSelectedLevel(level.id);
              }}
              disabled={isGenerating}
              aria-pressed={
                selectedLevel === level.id
              }
            >
              <span className="explanation-level-icon">
                {level.icon}
              </span>

              <span className="explanation-level-content">
                <strong>
                  {level.title}
                </strong>

                <small>
                  {level.description}
                </small>
              </span>

              <span className="explanation-level-check">
                {selectedLevel === level.id
                  ? "✓"
                  : ""}
              </span>
            </button>
          ),
        )}
      </div>

      {errorMessage && (
        <div className="explanation-error">
          <span>⚠️</span>

          <div>
            <strong>
              Explanation problem
            </strong>

            <p>{errorMessage}</p>
          </div>
        </div>
      )}

      {isLoading && (
        <div className="explanation-loading">
          <div className="explanation-spinner">
          </div>

          <p>
            Checking for a saved{" "}
            {selectedLevelDetails?.title.toLowerCase()}{" "}
            explanation...
          </p>
        </div>
      )}

      {!isLoading &&
        !explanation &&
        !isGenerating && (
          <div className="explanation-generate-card">
            <div className="explanation-generate-icon">
              {selectedLevelDetails?.icon}
            </div>

            <div className="explanation-generate-content">
              <p className="paper-section-label">
                {selectedLevelDetails?.title} Level
              </p>

              <h3>
                Generate a{" "}
                {selectedLevelDetails?.title.toLowerCase()}{" "}
                explanation
              </h3>

              <p>
                PaperMind will analyse the extracted
                text and rewrite the important ideas
                for this understanding level.
              </p>
            </div>

            <button
              type="button"
              onClick={
                handleGenerateExplanation
              }
            >
              Generate Explanation
            </button>
          </div>
        )}

      {isGenerating && (
        <div className="explanation-generating">
          <div className="explanation-spinner">
          </div>

          <div>
            <strong>
              Creating the{" "}
              {selectedLevelDetails?.title.toLowerCase()}{" "}
              explanation
            </strong>

            <p>
              PaperMind is analysing the paper.
              This may take several seconds.
            </p>
          </div>
        </div>
      )}

      {!isLoading &&
        explanation &&
        !isGenerating && (
          <div className="generated-explanation">
            <header className="generated-explanation-header">
              <div>
                <p className="paper-section-label">
                  {explanation.level} Explanation
                </p>

                <h3>
                  {
                    explanation
                      .explanation_title
                  }
                </h3>
              </div>

              <div className="explanation-meta">
                <span>
                  {
                    explanation
                      .model_name
                  }
                </span>

                {generatedDate && (
                  <span>
                    {generatedDate}
                  </span>
                )}
              </div>
            </header>

            <article className="explanation-main-card">
              <div className="explanation-main-icon">
                {selectedLevelDetails?.icon}
              </div>

              <div>
                <p className="paper-section-label">
                  Complete Explanation
                </p>

                <p className="explanation-main-text">
                  {
                    explanation
                      .explanation
                  }
                </p>
              </div>
            </article>

            <div className="explanation-content-grid">
              <article className="explanation-content-card">
                <div className="explanation-card-title">
                  <span>🧩</span>

                  <h3>
                    Key Concepts
                  </h3>
                </div>

                <ExplanationList
                  items={
                    explanation.key_concepts
                  }
                  emptyMessage={
                    "No key concepts were returned."
                  }
                />
              </article>

              <article className="explanation-content-card">
                <div className="explanation-card-title">
                  <span>📝</span>

                  <h3>
                    Study Takeaways
                  </h3>
                </div>

                <ExplanationList
                  items={
                    explanation
                      .study_takeaways
                  }
                  emptyMessage={
                    "No study takeaways were returned."
                  }
                />
              </article>
            </div>

            <article className="explanation-glossary-card">
              <div className="explanation-card-title">
                <span>📖</span>

                <h3>
                  Technical Glossary
                </h3>
              </div>

              {Array.isArray(
                explanation.glossary,
              ) &&
              explanation.glossary.length > 0 ? (
                <div className="explanation-glossary-grid">
                  {explanation.glossary.map(
                    (item, index) => (
                      <div
                        className="explanation-glossary-item"
                        key={`${item.term}-${index}`}
                      >
                        <strong>
                          {item.term}
                        </strong>

                        <p>
                          {item.meaning}
                        </p>
                      </div>
                    ),
                  )}
                </div>
              ) : (
                <p className="explanation-empty-message">
                  No glossary terms were returned.
                </p>
              )}
            </article>
          </div>
        )}
    </section>
  );
}

export default ExplanationPanel;