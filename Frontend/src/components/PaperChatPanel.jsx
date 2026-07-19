import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  useNavigate,
} from "react-router";

import {
  askPaperQuestion,
  getPaperChatHistory,
} from "../services/paperService";

import "../styles/PaperChatPanel.css";


const SUGGESTED_QUESTIONS = [
  "What problem is this paper trying to solve?",
  "Explain the methodology used in this paper.",
  "What are the most important findings?",
  "What limitations does the paper mention?",
];


function formatMessageTime(value) {
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
      hour: "numeric",
      minute: "2-digit",
    },
  ).format(date);
}


function PaperChatPanel({ paperId }) {
  const navigate = useNavigate();

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const [messages, setMessages] =
    useState([]);

  const [question, setQuestion] =
    useState("");

  const [isLoading, setIsLoading] =
    useState(true);

  const [isSending, setIsSending] =
    useState(false);

  const [errorMessage, setErrorMessage] =
    useState("");


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


    async function loadChatHistory() {
      setIsLoading(true);
      setErrorMessage("");

      try {
        const history =
          await getPaperChatHistory(
            paperId,
          );

        if (!cancelled) {
          setMessages(
            Array.isArray(history)
              ? history
              : [],
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

        setErrorMessage(
          error instanceof Error
            ? error.message
            : "The paper chat could not be loaded.",
        );
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }


    loadChatHistory();


    return () => {
      cancelled = true;
    };
  }, [navigate, paperId]);


  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "nearest",
    });
  }, [messages, isSending]);


  function selectSuggestedQuestion(
    suggestedQuestion,
  ) {
    setQuestion(suggestedQuestion);

    requestAnimationFrame(() => {
      textareaRef.current?.focus();
    });
  }


  async function handleSubmit(event) {
    event.preventDefault();

    const cleanedQuestion =
      question.trim();

    if (!cleanedQuestion) {
      setErrorMessage(
        "Please enter a question about the paper.",
      );

      return;
    }

    if (cleanedQuestion.length > 1000) {
      setErrorMessage(
        "Your question cannot exceed 1000 characters.",
      );

      return;
    }

    setErrorMessage("");
    setQuestion("");
    setIsSending(true);

    const temporaryMessageId =
       `temporary-user-${Date.now()}`;

    const temporaryUserMessage = {
      id: `temporary-user-${Date.now()}`,
      role: "user",
      content: cleanedQuestion,
      sources: [],
      model_name: null,
      created_at: new Date().toISOString(),
      temporary: true,
    };

    setMessages((currentMessages) => [
      ...currentMessages,
      temporaryUserMessage,
    ]);

    try {
      const response =
        await askPaperQuestion(
          paperId,
          cleanedQuestion,
        );

      const assistantMessage = {
        id: `temporary-assistant-${Date.now()}`,
        role: "assistant",
        content: response.answer,
        sources: Array.isArray(
          response.sources,
        )
          ? response.sources
          : [],
        model_name: response.model_name,
        created_at: response.created_at,
        temporary: true,
      };

      setMessages((currentMessages) => [
        ...currentMessages,
        assistantMessage,
      ]);
    } catch (error) {
      if (error?.status === 401) {
        redirectToLogin();
        return;
      }

      setMessages((currentMessages) =>
        currentMessages.filter(
          (message) =>
            message.id !== temporaryMessageId,
        ),
      );
   

setQuestion(cleanedQuestion);

      setErrorMessage(
        error instanceof Error
          ? error.message
          : "PaperMind could not answer the question.",
      );
    } finally {
      setIsSending(false);
    }
  }


  function handleTextareaKeyDown(event) {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();

      if (!isSending) {
        handleSubmit(event);
      }
    }
  }


  return (
    <section  id="paper-chat-section" 
        className="paper-chat-section">
      <header className="paper-chat-header">
        <div>
          <p className="paper-section-label">
            Research Assistant
          </p>

          <h2>
            Ask questions about this paper
          </h2>

          <p>
            PaperMind searches the paper and answers
            using the most relevant extracted sections.
          </p>
        </div>

        <div className="paper-chat-status">
          <span></span>
          Grounded in this paper
        </div>
      </header>

      <div className="paper-chat-layout">
        <aside className="paper-chat-suggestions">
          <h3>
            Suggested questions
          </h3>

          <p>
            Select a question or write your own.
          </p>

          <div className="suggested-question-list">
            {SUGGESTED_QUESTIONS.map(
              (suggestedQuestion) => (
                <button
                  key={suggestedQuestion}
                  type="button"
                  onClick={() => {
                    selectSuggestedQuestion(
                      suggestedQuestion,
                    );
                  }}
                  disabled={isSending}
                >
                  <span>＋</span>

                  {suggestedQuestion}
                </button>
              ),
            )}
          </div>

          <div className="paper-chat-note">
            <span>🔍</span>

            <p>
              Answers are generated from retrieved
              sections of the uploaded paper.
            </p>
          </div>
        </aside>

        <div className="paper-chat-workspace">
          <div className="paper-chat-messages">
            {isLoading && (
              <div className="paper-chat-loading">
                <div className="paper-chat-spinner">
                </div>

                <p>
                  Loading your paper conversation...
                </p>
              </div>
            )}

            {!isLoading &&
              messages.length === 0 && (
                <div className="paper-chat-empty">
                  <div className="paper-chat-empty-icon">
                    💬
                  </div>

                  <h3>
                    Start exploring the paper
                  </h3>

                  <p>
                    Ask about the research problem,
                    methodology, findings, limitations,
                    datasets, or technical concepts.
                  </p>
                </div>
              )}

            {!isLoading &&
              messages.map((message) => {
                const isAssistant =
                  message.role === "assistant";

                return (
                  <article
                    key={message.id}
                    className={[
                      "paper-chat-message",

                      isAssistant
                        ? "paper-chat-message-assistant"
                        : "paper-chat-message-user",
                    ].join(" ")}
                  >
                    <div className="paper-chat-avatar">
                      {isAssistant
                        ? "🧠"
                        : "👤"}
                    </div>

                    <div className="paper-chat-bubble">
                      <div className="paper-chat-message-meta">
                        <strong>
                          {isAssistant
                            ? "PaperMind"
                            : "You"}
                        </strong>

                        <span>
                          {formatMessageTime(
                            message.created_at,
                          )}
                        </span>
                      </div>

                      <p className="paper-chat-message-text">
                        {message.content}
                      </p>

                      {isAssistant &&
                        Array.isArray(
                          message.sources,
                        ) &&
                        message.sources.length > 0 && (
                          <details className="paper-chat-sources">
                            <summary>
                              View supporting paper
                              sections (
                              {message.sources.length})
                            </summary>

                            <div className="paper-chat-source-list">
                              {message.sources.map(
                                (
                                  source,
                                  index,
                                ) => (
                                  <div
                                    className="paper-chat-source"
                                    key={`${source.chunk_index}-${index}`}
                                  >
                                    <strong>
                                      Source chunk{" "}
                                      {
                                        source.chunk_index
                                      }
                                    </strong>

                                    <p>
                                      {source.excerpt}
                                    </p>
                                  </div>
                                ),
                              )}
                            </div>
                          </details>
                        )}

                      {isAssistant &&
                        message.model_name && (
                          <span className="paper-chat-model">
                            {message.model_name}
                          </span>
                        )}
                    </div>
                  </article>
                );
              })}

            {isSending && (
              <article className="paper-chat-message paper-chat-message-assistant">
                <div className="paper-chat-avatar">
                  🧠
                </div>

                <div className="paper-chat-bubble paper-chat-thinking">
                  <div className="paper-chat-thinking-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>

                  <p>
                    Searching the paper and preparing
                    an answer...
                  </p>
                </div>
              </article>
            )}

            <div ref={messagesEndRef}></div>
          </div>

          {errorMessage && (
            <div className="paper-chat-error">
              <span>⚠️</span>

              <div>
                <strong>
                  Chat problem
                </strong>

                <p>{errorMessage}</p>
              </div>
            </div>
          )}

          <form
            className="paper-chat-form"
            onSubmit={handleSubmit}
          >
            <textarea
              ref={textareaRef}
              value={question}
              onChange={(event) => {
                setQuestion(
                  event.target.value,
                );
              }}
              onKeyDown={
                handleTextareaKeyDown
              }
              placeholder="Ask something about this research paper..."
              maxLength={1000}
              rows={3}
              disabled={
                isSending || isLoading
              }
            />

            <div className="paper-chat-form-footer">
              <span>
                {question.length}/1000
                · Enter to send
                · Shift + Enter for a new line
              </span>

              <button
                type="submit"
                disabled={
                  isSending ||
                  isLoading ||
                  !question.trim()
                }
              >
                {isSending
                  ? "Answering..."
                  : "Ask PaperMind"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </section>
  );
}

export default PaperChatPanel;