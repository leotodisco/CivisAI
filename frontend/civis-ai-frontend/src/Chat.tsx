import { useEffect, useRef, useState } from "react";
import { streamChat } from "./api";

type Message = {
  role: "user" | "assistant";
  content: string;
};

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [chatId, setChatId] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  // auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // auto-grow textarea, like ChatGPT's composer
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "0px";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }, [input]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const currentInput = input;

    setMessages((prev) => [
      ...prev,
      { role: "user", content: currentInput },
      { role: "assistant", content: "" },
    ]);

    setInput("");
    setLoading(true);

    const controller = new AbortController();
    abortRef.current = controller;

    let assistantText = "";

    try {
      await streamChat(
        currentInput,
        chatId,
        (token) => {
          assistantText += token;

          setMessages((prev) => {
            const copy = [...prev];
            const last = copy.length - 1;

            if (copy[last]?.role === "assistant") {
              copy[last] = {
                role: "assistant",
                content: assistantText,
              };
            }

            return copy;
          });
        },
        (id) => {
          if (!chatId) setChatId(id);
        },
        { signal: controller.signal, maxRetries: 3 }
      );
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        // stop volontario dell'utente, nessun errore da mostrare
      } else {
        console.error("Errore streaming:", err);

        setMessages((prev) => {
          const copy = [...prev];
          const last = copy.length - 1;

          if (copy[last]?.role === "assistant") {
            copy[last] = {
              role: "assistant",
              content:
                assistantText ||
                "Si è verificato un errore. Riprova più tardi.",
            };
          }

          return copy;
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const stop = () => {
    abortRef.current?.abort();
    setLoading(false);
  };

  const isWaitingForFirstToken =
    loading &&
    messages.length > 0 &&
    messages[messages.length - 1].role === "assistant" &&
    messages[messages.length - 1].content === "";

  return (
    <div style={styles.page}>
      {/* HEADER */}
      <div style={styles.header}>CivisAI</div>

      {/* CHAT AREA */}
      <div style={styles.chat}>
        <div style={styles.chatInner}>
          {messages.length === 0 && (
            <div style={styles.emptyState}>
              <div style={styles.emptyTitle}>Come posso aiutarti oggi?</div>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} style={styles.row}>
              {m.role === "user" ? (
                <div style={styles.userRow}>
                  <div style={styles.userBubble}>{m.content}</div>
                </div>
              ) : (
                <div style={styles.assistantRow}>
                  <div style={styles.avatar}>
                    <span style={styles.avatarDot} />
                  </div>
                  <div style={styles.assistantContent}>
                    {m.content === "" && isWaitingForFirstToken ? (
                      <TypingDots />
                    ) : (
                      m.content
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* INPUT BAR */}
      <div style={styles.inputWrapper}>
        <div style={styles.inputBox}>
          <textarea
            ref={textareaRef}
            rows={1}
            style={styles.input}
            value={input}
            placeholder="Scrivi un messaggio..."
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
          />

          {!loading ? (
            <button
              style={{
                ...styles.sendBase,
                ...(input.trim() ? styles.sendActive : styles.sendDisabled),
              }}
              onClick={sendMessage}
              disabled={!input.trim()}
              aria-label="Invia messaggio"
            >
              <ArrowUpIcon />
            </button>
          ) : (
            <button
              style={{ ...styles.sendBase, ...styles.stop }}
              onClick={stop}
              aria-label="Interrompi generazione"
            >
              <StopIcon />
            </button>
          )}
        </div>
        <div style={styles.disclaimer}>
          Le risposte generate potrebbero contenere errori.
        </div>
      </div>
    </div>
  );
}

function TypingDots() {
  return (
    <span style={styles.typingWrap}>
      <span style={{ ...styles.typingDot, animationDelay: "0ms" }} />
      <span style={{ ...styles.typingDot, animationDelay: "150ms" }} />
      <span style={{ ...styles.typingDot, animationDelay: "300ms" }} />
      <style>{`
        @keyframes chatgpt-typing-bounce {
          0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
          40% { transform: scale(1); opacity: 1; }
        }
      `}</style>
    </span>
  );
}

function ArrowUpIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
      <path
        d="M12 19V5M12 5L5 12M12 5L19 12"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function StopIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
      <rect x="4" y="4" width="16" height="16" rx="2" />
    </svg>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    height: "100vh",
    display: "flex",
    flexDirection: "column",
    background: "#212121",
    color: "#ececec",
    fontFamily:
      "'Söhne', ui-sans-serif, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif",
  },

  header: {
    height: "52px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "16px",
    fontWeight: 600,
    color: "#ececec",
    borderBottom: "1px solid #2f2f2f",
    flexShrink: 0,
  },

  chat: {
    flex: 1,
    overflowY: "auto",
  },

  chatInner: {
    maxWidth: "768px",
    margin: "0 auto",
    padding: "32px 16px 24px",
    display: "flex",
    flexDirection: "column",
    gap: "4px",
    minHeight: "100%",
  },

  emptyState: {
    flex: 1,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    minHeight: "50vh",
  },

  emptyTitle: {
    fontSize: "28px",
    fontWeight: 600,
    color: "#ececec",
  },

  row: {
    display: "flex",
    width: "100%",
  },

  userRow: {
    display: "flex",
    justifyContent: "flex-end",
    width: "100%",
    padding: "8px 0",
  },

  userBubble: {
    maxWidth: "70%",
    background: "#2f2f2f",
    color: "#ececec",
    padding: "10px 16px",
    borderRadius: "20px",
    fontSize: "15px",
    lineHeight: 1.6,
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
  },

  assistantRow: {
    display: "flex",
    alignItems: "flex-start",
    gap: "12px",
    width: "100%",
    padding: "12px 0",
  },

  avatar: {
    width: "28px",
    height: "28px",
    borderRadius: "50%",
    background: "#10a37f",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
    marginTop: "2px",
  },

  avatarDot: {
    width: "12px",
    height: "12px",
    borderRadius: "3px",
    background: "#ffffff",
  },

  assistantContent: {
    fontSize: "15px",
    lineHeight: 1.7,
    color: "#ececec",
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
    paddingTop: "3px",
    flex: 1,
  },

  typingWrap: {
    display: "inline-flex",
    gap: "4px",
    alignItems: "center",
    height: "20px",
  },

  typingDot: {
    width: "6px",
    height: "6px",
    borderRadius: "50%",
    background: "#a0a0a0",
    display: "inline-block",
    animation: "chatgpt-typing-bounce 1.2s infinite ease-in-out",
  },

  inputWrapper: {
    flexShrink: 0,
    padding: "12px 16px 20px",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    background: "#212121",
  },

  inputBox: {
    width: "100%",
    maxWidth: "768px",
    display: "flex",
    alignItems: "flex-end",
    gap: "8px",
    background: "#2f2f2f",
    border: "1px solid #4d4d4d",
    padding: "10px 10px 10px 18px",
    borderRadius: "28px",
    boxShadow: "0 2px 10px rgba(0,0,0,0.25)",
  },

  input: {
    flex: 1,
    border: "none",
    outline: "none",
    fontSize: "15px",
    lineHeight: 1.5,
    background: "transparent",
    color: "#ececec",
    resize: "none",
    maxHeight: "200px",
    fontFamily: "inherit",
    padding: "6px 0",
  },

  sendBase: {
    width: "32px",
    height: "32px",
    borderRadius: "50%",
    border: "none",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
    cursor: "pointer",
    transition: "background 0.15s ease",
  },

  sendActive: {
    background: "#ececec",
    color: "#212121",
  },

  sendDisabled: {
    background: "#4d4d4d",
    color: "#8e8e8e",
    cursor: "not-allowed",
  },

  stop: {
    background: "#ececec",
    color: "#212121",
  },

  disclaimer: {
    fontSize: "12px",
    color: "#8e8e8e",
    marginTop: "10px",
    textAlign: "center",
  },
};