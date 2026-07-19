import {
  useEffect,
  useState,
} from "react";

import {
  useNavigate,
} from "react-router";

import {
  generatePaperRoadmap,
  getPaperRoadmap,
} from "../services/paperService";

import "../styles/ResearchRoadmapPanel.css";


function ResearchRoadmapPanel({
  paperId,
}) {
  const navigate = useNavigate();

  const [roadmap, setRoadmap] =
    useState(null);

  const [isLoading, setIsLoading] =
    useState(true);

  const [isGenerating, setIsGenerating] =
    useState(false);

  const [errorMessage, setErrorMessage] =
    useState("");


  // =======================================================
  // Redirect expired sessions
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
  // Load existing roadmap
  // =======================================================

  useEffect(() => {
    let cancelled = false;


    async function loadRoadmap() {
      setIsLoading(true);
      setErrorMessage("");

      try {
        const roadmapData =
          await getPaperRoadmap(
            paperId,
          );

        if (!cancelled) {
          setRoadmap(
            roadmapData,
          );
        }

      } catch (error) {
        if (cancelled) {
          return;
        }


        // No roadmap yet.
        // This is normal.
        if (error?.status === 404) {
          setRoadmap(null);
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
              "The research roadmap "
              + "could not be loaded."
            ),
        );

      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }


    loadRoadmap();


    return () => {
      cancelled = true;
    };

  }, [paperId]);


  // =======================================================
  // Generate roadmap
  // =======================================================

  async function handleGenerateRoadmap() {
    setErrorMessage("");
    setIsGenerating(true);

    try {
      const generatedRoadmap =
        await generatePaperRoadmap(
          paperId,
        );

      setRoadmap(
        generatedRoadmap,
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
            + "the research roadmap."
          ),
      );

    } finally {
      setIsGenerating(false);
    }
  }


  // =======================================================
  // Loading
  // =======================================================

  if (isLoading) {
    return (
      <section 
        id="paper-roadmap-section"
        className="research-roadmap-section">

        <div className="roadmap-loading">

          <div className="roadmap-spinner">
          </div>

          <div>
            <strong>
              Loading research roadmap
            </strong>

            <p>
              Checking whether this paper
              already has a saved roadmap...
            </p>
          </div>

        </div>

      </section>
    );
  }


  // =======================================================
  // UI
  // =======================================================

  return (
    <section 
        id="paper-roadmap-section"
        className="research-roadmap-section"
    >

      {/* =================================================
          HEADER
      ================================================= */}

      <header className="roadmap-header">

        <div>

          <p className="roadmap-section-label">
            AI Learning Path
          </p>

          <h2>
            🧭 Research Learning Roadmap
          </h2>

          <p>
            Turn this research paper into a
            step-by-step path of concepts,
            skills, and research directions
            you can learn next.
          </p>

        </div>


        {roadmap && (
          <span className="roadmap-ready-badge">
            ✓ Roadmap Ready
          </span>
        )}

      </header>


      {/* =================================================
          ERROR
      ================================================= */}

      {errorMessage && (
        <div className="roadmap-error">

          <span>
            ⚠️
          </span>

          <div>

            <strong>
              Roadmap problem
            </strong>

            <p>
              {errorMessage}
            </p>

          </div>

        </div>
      )}


      {/* =================================================
          ROADMAP NOT GENERATED
      ================================================= */}

      {!roadmap && (

        <div className="roadmap-empty-state">

          <div className="roadmap-empty-visual">

            <div className="roadmap-empty-icon">
              🧭
            </div>

            <div className="roadmap-preview-line">
              <span>1</span>
              <div></div>
            </div>

            <div className="roadmap-preview-line">
              <span>2</span>
              <div></div>
            </div>

            <div className="roadmap-preview-line">
              <span>3</span>
              <div></div>
            </div>

          </div>


          <div className="roadmap-empty-content">

            <p className="roadmap-section-label">
              Personalized Learning Path
            </p>

            <h3>
              Not sure what to learn after
              reading this paper?
            </h3>

            <p>
              PaperMind will analyse the
              paper's research domain,
              prerequisites, methodology,
              findings, and future work to
              create a structured learning
              roadmap.
            </p>


            <div className="roadmap-feature-list">

              <span>
                ✓ Required prerequisites
              </span>

              <span>
                ✓ Step-by-step learning stages
              </span>

              <span>
                ✓ Advanced research directions
              </span>

              <span>
                ✓ Practical project ideas
              </span>

            </div>


            <button
              type="button"
              className="generate-roadmap-button"
              onClick={
                handleGenerateRoadmap
              }
              disabled={
                isGenerating
              }
            >

              {isGenerating ? (
                <>
                  <span className="roadmap-button-spinner">
                  </span>

                  Building Your Roadmap...
                </>
              ) : (
                <>
                  ✨ Generate Research Roadmap
                </>
              )}

            </button>

          </div>

        </div>

      )}


      {/* =================================================
          GENERATED ROADMAP
      ================================================= */}

      {roadmap && (

        <div className="roadmap-content">

          {/* ===============================================
              ROADMAP INTRODUCTION
          =============================================== */}

          <div className="roadmap-introduction">

            <div>

              <p className="roadmap-section-label">
                Your Personalized Path
              </p>

              <h3>
                {roadmap.roadmap_title}
              </h3>

              <p>
                {roadmap.overview}
              </p>

            </div>


            <div className="roadmap-domain-card">

              <span>
                Research Domain
              </span>

              <strong>
                {roadmap.research_domain}
              </strong>

            </div>

          </div>


          {/* ===============================================
              PREREQUISITES
          =============================================== */}

          <article className="roadmap-prerequisites">

            <div className="roadmap-card-heading">

              <span className="roadmap-heading-icon">
                🎒
              </span>

              <div>

                <p className="roadmap-section-label">
                  Before You Begin
                </p>

                <h3>
                  Recommended Prerequisites
                </h3>

              </div>

            </div>


            <div className="roadmap-prerequisite-grid">

              {roadmap.prerequisites.map(
                (
                  prerequisite,
                  index,
                ) => (

                  <div
                    key={`${prerequisite}-${index}`}
                    className="roadmap-prerequisite-item"
                  >

                    <span>
                      ✓
                    </span>

                    <p>
                      {prerequisite}
                    </p>

                  </div>

                ),
              )}

            </div>

          </article>


          {/* ===============================================
              LEARNING TIMELINE
          =============================================== */}

          <div className="roadmap-timeline-section">

            <div className="roadmap-timeline-heading">

              <p className="roadmap-section-label">
                Step-by-Step Learning Path
              </p>

              <h3>
                Follow the roadmap
              </h3>

              <p>
                Move through each stage in order
                to build the knowledge required
                to understand and extend this
                research.
              </p>

            </div>


            <div className="roadmap-timeline">

              {roadmap.roadmap_steps.map(
                (
                  step,
                  index,
                ) => (

                  <article
                    key={`${step.stage}-${step.title}`}
                    className="roadmap-stage"
                  >

                    <div className="roadmap-stage-marker">

                      <span>
                        {step.stage}
                      </span>

                      {index <
                        roadmap
                          .roadmap_steps
                          .length -
                          1 && (

                        <div className="roadmap-stage-line">
                        </div>

                      )}

                    </div>


                    <div className="roadmap-stage-card">

                      <div className="roadmap-stage-top">

                        <span>
                          Stage {step.stage}
                        </span>

                        <small>
                          Learning Phase
                        </small>

                      </div>


                      <h4>
                        {step.title}
                      </h4>


                      <p className="roadmap-stage-goal">
                        {step.goal}
                      </p>


                      <div className="roadmap-topics">

                        <strong>
                          What to learn
                        </strong>


                        <div className="roadmap-topic-list">

                          {step.topics.map(
                            (
                              topic,
                              topicIndex,
                            ) => (

                              <span
                                key={`${topic}-${topicIndex}`}
                              >
                                {topic}
                              </span>

                            ),
                          )}

                        </div>

                      </div>

                    </div>

                  </article>

                ),
              )}

            </div>

          </div>


          {/* ===============================================
              RESEARCH DIRECTIONS
          =============================================== */}

          <article className="roadmap-research-card">

            <div className="roadmap-card-heading">

              <span className="roadmap-heading-icon">
                🔬
              </span>


              <div>

                <p className="roadmap-section-label">
                  Go Beyond the Paper
                </p>

                <h3>
                  Possible Research Directions
                </h3>

              </div>

            </div>


            <div className="roadmap-research-list">

              {roadmap.research_directions.map(
                (
                  direction,
                  index,
                ) => (

                  <div
                    key={`${direction}-${index}`}
                    className="roadmap-research-item"
                  >

                    <span>
                      {index + 1}
                    </span>

                    <p>
                      {direction}
                    </p>

                  </div>

                ),
              )}

            </div>

          </article>


          {/* ===============================================
              SUGGESTED PROJECTS
          =============================================== */}

          <article className="roadmap-projects-card">

            <div className="roadmap-card-heading">

              <span className="roadmap-heading-icon">
                💻
              </span>


              <div>

                <p className="roadmap-section-label">
                  Learn by Building
                </p>

                <h3>
                  Suggested Projects
                </h3>

              </div>

            </div>


            <div className="roadmap-project-grid">

              {roadmap.suggested_projects.map(
                (
                  project,
                  index,
                ) => (

                  <div
                    key={`${project}-${index}`}
                    className="roadmap-project-item"
                  >

                    <div>
                      {index + 1}
                    </div>

                    <p>
                      {project}
                    </p>

                  </div>

                ),
              )}

            </div>

          </article>

        </div>

      )}

    </section>
  );
}


export default ResearchRoadmapPanel;