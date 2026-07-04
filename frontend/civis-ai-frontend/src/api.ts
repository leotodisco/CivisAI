type StreamChatOptions = {
  maxRetries?: number; // default 3
  retryDelayMs?: number; // delay base, default 500ms (raddoppia ad ogni tentativo)
  signal?: AbortSignal; // per permettere lo stop manuale dall'esterno
};

class StreamChatError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "StreamChatError";
    this.status = status;
  }
}

export async function streamChat(
  message: string,
  chatId: string | null,
  onChunk: (text: string) => void,
  onChatId?: (id: string) => void,
  options: StreamChatOptions = {},
): Promise<void> {
  const { maxRetries = 3, retryDelayMs = 500, signal } = options;

  let attempt = 0;

  while (true) {
    try {
      await attemptStream(message, chatId, onChunk, onChatId, signal);
      return; // successo, esci dal ciclo di retry
    } catch (err) {
      // Se l'utente ha annullato volontariamente, non fare retry
      if (err instanceof DOMException && err.name === "AbortError") {
        throw err;
      }

      attempt++;

      // Errori 4xx (client) non hanno senso da ritentare: il problema è nella richiesta
      if (
        err instanceof StreamChatError &&
        err.status &&
        err.status >= 400 &&
        err.status < 500
      ) {
        throw err;
      }

      if (attempt > maxRetries) {
        throw err;
      }

      const delay = retryDelayMs * 2 ** (attempt - 1);
      await sleep(delay, signal);
    }
  }
}

async function attemptStream(
  message: string,
  chatId: string | null,
  onChunk: (text: string) => void,
  onChatId: ((id: string) => void) | undefined,
  signal: AbortSignal | undefined,
): Promise<void> {
  const API_URL = import.meta.env.VITE_BACKEND_URL;
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(chatId ? { "X-chat_id": chatId } : {}),
    },
    body: JSON.stringify({ query: message }),
    signal,
  });

  if (!res.ok) {
    throw new StreamChatError(`Errore server: ${res.status}`, res.status);
  }

  const returnedChatId = res.headers.get("X-chat_id");
  if (returnedChatId && onChatId) {
    onChatId(returnedChatId);
  }

  if (!res.body) {
    throw new StreamChatError(
      "Risposta senza body, impossibile leggere lo stream",
    );
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");

  let buffer = "";

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split("\n");
      buffer = lines.pop() ?? ""; // riga incompleta, la teniamo per il prossimo giro

      for (const line of lines) {
        if (line.startsWith("data:")) {
          onChunk(line.replace(/^data:\s?/, ""));
        }
      }
    }

    // flush finale: se il buffer contiene una riga valida senza newline finale
    if (buffer.startsWith("data:")) {
      onChunk(buffer.replace(/^data:\s?/, ""));
    }
  } finally {
    reader.releaseLock();
  }
}

function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(resolve, ms);
    if (signal) {
      signal.addEventListener(
        "abort",
        () => {
          clearTimeout(timeout);
          reject(new DOMException("Aborted", "AbortError"));
        },
        { once: true },
      );
    }
  });
}
