import { useEffect, useRef, useState } from 'react'
import {
  DashboardPayload,
  mentorChat,
} from '../dashboardApi'

interface Msg {
  role: 'user' | 'bot'
  text: string
  language?: 'English' | 'Hindi'
}

type VoiceLanguage = 'English' | 'Hindi'

interface SpeechRecognitionEventLike {
  results: {
    [index: number]: {
      [index: number]: {
        transcript: string
      }
    }
  }
}

interface SpeechRecognitionLike {
  lang: string
  continuous: boolean
  interimResults: boolean
  onresult:
    | ((event: SpeechRecognitionEventLike) => void)
    | null
  onerror: (() => void) | null
  onend: (() => void) | null
  start: () => void
  stop: () => void
}

interface SpeechRecognitionConstructor {
  new (): SpeechRecognitionLike
}


function detectLanguage(text: string): 'English' | 'Hindi' {
  const lower = text.toLowerCase()

  // Hindi written in Devanagari
  const hindiScript = text.match(/[\u0900-\u097F]/g)

  if (hindiScript && hindiScript.length >= 2) {
    return 'Hindi'
  }

  // Common Hinglish words written using English letters
  const hinglishWords = [
    'main',
    'mein',
    'mujhe',
    'mera',
    'meri',
    'mere',
    'hum',
    'ham',
    'aap',
    'apka',
    'apni',
    'kaise',
    'kya',
    'kyun',
    'kyon',
    'kab',
    'kahan',
    'ka',
    'ke',
    'ki',
    'ko',
    'se',
    'par',
    'liye',
    'chahiye',
    'sakta',
    'sakti',
    'sakte',
    'kar',
    'karna',
    'karo',
    'karen',
    'hai',
    'hain',
    'ho',
    'hua',
    'hoga',
    'business',
    'loan',
    'yojana',
    'sarkari',
    'paise',
    'kitna',
    'kitne',
    'kahan',
    'apply',
  ]

  const words = lower.split(/\s+/)

  const hinglishMatches = words.filter(word =>
    hinglishWords.includes(
      word.replace(/[.,!?;:'"()]/g, ''),
    ),
  ).length

  if (hinglishMatches >= 2) {
    return 'Hindi'
  }

  return 'English'
}

export default function Advisor({
  payload,
}: {
  payload: DashboardPayload | null
}) {
  const [convs] = useState([
    {
      title: 'Market Demand Analysis',
      sub: 'Understanding local customer base…',
    },
    {
      title: 'Loan Application Requirements',
      sub: 'Documents needed for the scheme…',
    },
    {
      title: 'Competitor Pricing',
      sub: 'How to price against local rivals…',
    },
  ])

  const [messages, setMessages] = useState<Msg[]>([
    {
      role: 'bot',
      language: 'English',
      text:
        "I've analyzed the latest market data for your district. " +
        'Here is a breakdown of key factors and recommended actions. ' +
        'Ask me anything about your business plan.',
    },
  ])

  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)

  // English is the default voice-recognition language.
  const [voiceLanguage, setVoiceLanguage] =
    useState<VoiceLanguage>('English')

  const [listening, setListening] = useState(false)
  const [speakingIndex, setSpeakingIndex] =
    useState<number | null>(null)

  const recognitionRef = useRef<any>(null)

  /*
   * ------------------------------------------------------------
   * SPEECH SYNTHESIS
   * ------------------------------------------------------------
   */

  function stopSpeaking() {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel()
    }

    setSpeakingIndex(null)
  }

  function speakAnswer(
    text: string,
    language: 'English' | 'Hindi',
    index: number,
  ) {
    if (!('speechSynthesis' in window)) {
      return
    }

    // If this exact answer is already speaking, stop it.
    if (speakingIndex === index) {
      stopSpeaking()
      return
    }

    window.speechSynthesis.cancel()

    const utterance = new SpeechSynthesisUtterance(text)

    if (language === 'Hindi') {
      utterance.lang = 'hi-IN'
    } else {
      utterance.lang = 'en-IN'
    }

    utterance.rate = 0.95
    utterance.pitch = 1

    const voices = window.speechSynthesis.getVoices()

    const preferredVoice = voices.find(voice => {
      const lang = voice.lang.toLowerCase()

      if (language === 'Hindi') {
        return (
          lang === 'hi-in' ||
          lang.startsWith('hi')
        )
      }

      return (
        lang === 'en-in' ||
        lang.startsWith('en')
      )
    })

    if (preferredVoice) {
      utterance.voice = preferredVoice
    }

    utterance.onend = () => {
      setSpeakingIndex(null)
    }

    utterance.onerror = () => {
      setSpeakingIndex(null)
    }

    setSpeakingIndex(index)

    window.speechSynthesis.speak(utterance)
  }

  /*
   * ------------------------------------------------------------
   * SEND MESSAGE
   * ------------------------------------------------------------
   */

  async function send(question?: string) {
    const text = (question ?? input).trim()

    if (!text || busy) {
      return
    }

    const language = detectLanguage(text)

    setMessages(current => [
      ...current,
      {
        role: 'user',
        text,
        language,
      },
    ])

    setInput('')
    setBusy(true)

    try {
      /*
       * Send language explicitly to backend.
       *
       * We use the main api client directly here instead of
       * mentorChat() so this file works even if dashboardApi.ts
       * still has the old two-argument mentorChat signature.
       */
      const detectedLanguage = detectLanguage(text)
      console.log("Question:", text)
      console.log("Detected language:", detectedLanguage)

      const { answer } = await mentorChat(
        text,
        payload?.report_id,
        detectedLanguage
      )

      const finalAnswer =
        answer ||
        (language === 'Hindi'
          ? 'माफ़ कीजिए, इस समय मैं इसका उत्तर नहीं दे पा रहा हूँ।'
          : 'Sorry, I could not generate an answer right now.')

      setMessages(current => [
        ...current,
        {
          role: 'bot',
          text: finalAnswer,
          language,
        },
      ])
    } catch (error) {
      console.error('Advisor request failed:', error)

      setMessages(current => [
        ...current,
        {
          role: 'bot',
          language,
          text:
            language === 'Hindi'
              ? 'माफ़ कीजिए, अभी कुछ समस्या हुई है। कृपया दोबारा प्रयास करें।'
              : 'Sorry — something went wrong. Please retry.',
        },
      ])
    } finally {
      setBusy(false)
    }
  }

  /*
   * ------------------------------------------------------------
   * VOICE INPUT
   * ------------------------------------------------------------
   */

  function startVoiceInput() {
    if (listening) {
      recognitionRef.current?.stop()
      setListening(false)
      return
    }

    const speechWindow = window as any

    const Recognition =
      speechWindow.SpeechRecognition ||
      speechWindow.webkitSpeechRecognition

    if (!Recognition) {
      alert(
        'Voice input is not supported by this browser. Please use Chrome or Edge.',
      )
      return
    }

    const recognition = new Recognition()

    recognition.lang =
      voiceLanguage === 'Hindi'
        ? 'hi-IN'
        : 'en-IN'

    recognition.continuous = false
    recognition.interimResults = false

    recognition.onresult = (event: any) => {
      const transcript =
        event.results?.[0]?.[0]?.transcript?.trim()

      if (!transcript) {
        return
      }

      setInput(transcript)

      send(transcript)
    }

    recognition.onerror = () => {
      setListening(false)
      recognitionRef.current = null
    }

    recognition.onend = () => {
      setListening(false)
      recognitionRef.current = null
    }

    recognitionRef.current = recognition

    setListening(true)

    recognition.start()
  }

  /*
   * ------------------------------------------------------------
   * NEW CONVERSATION
   * ------------------------------------------------------------
   */

  function newConversation() {
    stopSpeaking()

    recognitionRef.current?.stop()

    setMessages([
      {
        role: 'bot',
        language: 'English',
        text:
          "I've analyzed the latest market data for your district. " +
          'Ask me anything about your business plan.',
      },
    ])

    setInput('')
    setBusy(false)
    setListening(false)
  }

  /*
   * Stop speech if user leaves/reloads this page component.
   */
  useEffect(() => {
    return () => {
      window.speechSynthesis?.cancel()
      recognitionRef.current?.stop()
    }
  }, [])

  /*
   * ------------------------------------------------------------
   * UI
   * ------------------------------------------------------------
   */

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '240px minmax(0, 1fr)',
        gap: 20,
        minHeight: 'calc(100vh - 140px)',
      }}
    >
      {/* ======================================================
          CONVERSATIONS SIDEBAR
         ====================================================== */}

      <div
        className="card"
        style={{
          padding: 16,
          height: 'fit-content',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 16,
          }}
        >
          <div>
            <div className="mono-label muted">
              CONVERSATIONS
            </div>

            <div
              style={{
                fontWeight: 800,
                marginTop: 4,
              }}
            >
              Your Advisor
            </div>
          </div>

          <button
            type="button"
            className="btn btn-sm"
            onClick={newConversation}
            title="New conversation"
            aria-label="New conversation"
            style={{
              width: 36,
              height: 36,
              minWidth: 36,
              minHeight: 36,
              padding: 0,
              margin: 0,
              borderRadius: '50%',
              border: 'none',
              background: 'var(--primary)',
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              flexShrink: 0,
              lineHeight: 1,
              fontSize: 22,
              fontWeight: 500,
            }}
          >
            +
          </button>
        </div>

        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
          }}
        >
          {convs.map((conv, index) => (
            <div
              key={conv.title}
              className="card-low"
              style={{
                padding: 12,
                cursor: 'default',
                opacity: index === 0 ? 1 : 0.8,
              }}
            >
              <div
                style={{
                  fontWeight: 700,
                  fontSize: 14,
                }}
              >
                {conv.title}
              </div>

              <div
                className="label-sm muted"
                style={{
                  marginTop: 4,
                  lineHeight: 1.4,
                }}
              >
                {conv.sub}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ======================================================
          ADVISOR
         ====================================================== */}

      <div
        className="card"
        style={{
          padding: 30,
          display: 'flex',
          flexDirection: 'column',
          minHeight: 650,
        }}
      >
        {/* HEADER */}

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            paddingBottom: 16,
            borderBottom:
              '1px solid var(--surface-container-highest)',
          }}
        >
          <div
            style={{
              width: 54,
              height: 54,
              borderRadius: '50%',
              background: 'var(--primary)',
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <span className="material-symbols-outlined">
              support_agent
            </span>
          </div>

          <div>
            <h2
              style={{
                margin: 0,
                fontSize: 21,
              }}
            >
              GramAI Advisor
            </h2>

            <div
              style={{
                color: 'var(--primary)',
                marginTop: 3,
              }}
            >
              • Specialized in Rural Business Intelligence
            </div>
          </div>
        </div>

        {/* MESSAGES */}

        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '20px 0',
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
          }}
        >
          {messages.map((message, index) => {
            const isBot = message.role === 'bot'

            return (
              <div
                key={`${index}-${message.text}`}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: isBot
                    ? 'flex-start'
                    : 'flex-end',
                  gap: 6,
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 10,
                    maxWidth: '82%',
                  }}
                >
                  {isBot && (
                    <button
                      onClick={() =>
                        speakAnswer(
                          message.text,
                          message.language ?? 'English',
                          index,
                        )
                      }
                      title={
                        speakingIndex === index
                          ? 'Stop speaking'
                          : 'Hear this answer'
                      }
                      style={{
                        width: 44,
                        height: 44,
                        borderRadius: '50%',
                        border:
                          '1px solid #dce1f0',
                        background: '#fff',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: 'pointer',
                        flexShrink: 0,
                        color: 'var(--text)',
                      }}
                    >
                      <span className="material-symbols-outlined">
                        {speakingIndex === index
                          ? 'stop'
                          : 'volume_up'}
                      </span>
                    </button>
                  )}

                  <div
                    style={{
                      padding: '14px 18px',
                      borderRadius: isBot
                        ? '18px 18px 18px 4px'
                        : '18px 18px 4px 18px',
                      background: isBot
                        ? '#f0f2ff'
                        : 'var(--primary)',
                      color: isBot
                        ? 'var(--text)'
                        : '#fff',
                      lineHeight: 1.55,
                      whiteSpace: 'pre-wrap',
                    }}
                  >
                    {message.text}
                  </div>
                </div>
              </div>
            )
          })}

          {busy && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
              }}
            >
              <div
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: '50%',
                  border:
                    '1px solid #dce1f0',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <span className="material-symbols-outlined">
                  smart_toy
                </span>
              </div>

              <div
                style={{
                  background: '#f0f2ff',
                  borderRadius:
                    '18px 18px 18px 4px',
                  padding: '14px 18px',
                }}
              >
                Thinking…
              </div>
            </div>
          )}
        </div>

        {/* QUICK QUESTIONS */}

        <div
          style={{
            display: 'flex',
            gap: 8,
            flexWrap: 'wrap',
            marginBottom: 14,
          }}
        >
          {[
            'How do I apply for a loan?',
            'Show market map nearby',
            'Analyze my competitors',
          ].map(question => (
            <button
              key={question}
              className="btn btn-sm btn-outline"
              disabled={busy}
              onClick={() => send(question)}
            >
              {question}
            </button>
          ))}
        </div>

        {/* INPUT */}

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <input
            value={input}
            onChange={e =>
              setInput(e.target.value)
            }
            onKeyDown={e => {
              if (
                e.key === 'Enter' &&
                !e.shiftKey
              ) {
                e.preventDefault()
                send()
              }
            }}
            placeholder="Ask Advisor anything about your business data…"
            disabled={busy}
            style={{
              flex: 1,
              minWidth: 0,
              height: 60,
              borderRadius: 999,
              border:
                '1px solid #cfd5e5',
              padding: '0 24px',
              fontSize: 15,
              outline: 'none',
            }}
          />

          {/* VOICE LANGUAGE */}

          <select
            value={voiceLanguage}
            onChange={e =>
              setVoiceLanguage(
                e.target.value as VoiceLanguage,
              )
            }
            disabled={listening}
            title="Voice input language"
            style={{
              height: 44,
              borderRadius: 999,
              border:
                '1px solid #cfd5e5',
              padding: '0 12px',
              background: '#fff',
              cursor: 'pointer',
              fontSize: 13,
            }}
          >
            <option value="English">
              English
            </option>
            <option value="Hindi">
              Hindi
            </option>
          </select>

          {/* MIC */}

          <button
            onClick={startVoiceInput}
            disabled={busy}
            title={
              listening
                ? 'Stop listening'
                : `Speak in ${voiceLanguage}`
            }
            style={{
              width: 60,
              height: 60,
              borderRadius: '50%',
              border: 'none',
              background: listening
                ? '#d93025'
                : 'var(--primary)',
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: busy
                ? 'not-allowed'
                : 'pointer',
              flexShrink: 0,
            }}
          >
            <span className="material-symbols-outlined">
              {listening
                ? 'mic_off'
                : 'mic'}
            </span>
          </button>

          {/* SEND */}

          <button
            onClick={() => send()}
            disabled={!input.trim() || busy}
            title="Send"
            style={{
              width: 60,
              height: 60,
              borderRadius: '50%',
              border: 'none',
              background:
                input.trim() && !busy
                  ? '#7ea2e4'
                  : '#c9d2e8',
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor:
                input.trim() && !busy
                  ? 'pointer'
                  : 'not-allowed',
              flexShrink: 0,
            }}
          >
            <span className="material-symbols-outlined">
              send
            </span>
          </button>
        </div>

        {/* FOOTER HINT */}

        <div
          style={{
            textAlign: 'center',
            marginTop: 12,
            fontSize: 13,
            letterSpacing: 1,
            color: '#4b4f61',
          }}
        >
          🎙 ASK IN HINDI OR ENGLISH • 🔊 TAP THE SPEAKER TO HEAR ANY ANSWER
        </div>
      </div>
    </div>
  )
}