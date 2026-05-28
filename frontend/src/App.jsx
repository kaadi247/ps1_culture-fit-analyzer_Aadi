import React, { useState, useEffect, useRef, useCallback } from 'react'
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer } from 'recharts'
import { analyzeCompany, generateReport, submitQuiz } from './services/api'

/* ─── Design tokens ────────────────────────────────────────────────── */
const T = {
  bg:      '#080808',
  surface: '#0F0F0F',
  border:  '#1A1A1A',
  accent:  '#C8FF00',
  muted:   '#555',
  text:    '#E0E0E0',
  mono:    "'DM Mono', 'Courier New', monospace",
  sans:    "'Inter', system-ui, sans-serif",
}

/* ─── Global reset injected once ──────────────────────────────────── */
const globalStyle = `
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  html, body, #root { height: 100%; }
  body {
    background: ${T.bg};
    color: ${T.text};
    font-family: ${T.mono};
    -webkit-font-smoothing: antialiased;
  }
  ::selection { background: ${T.accent}; color: #000; }
  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: ${T.bg}; }
  ::-webkit-scrollbar-thumb { background: ${T.border}; border-radius: 2px; }
  a { color: ${T.accent}; text-decoration: none; }
  a:hover { text-decoration: underline; }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.3; }
  }
  @keyframes blink {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0; }
  }
`

/* ─── Shared layout ────────────────────────────────────────────────── */
function Shell({ children, maxWidth = 760 }) {
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      padding: '60px 24px 80px',
      animation: 'fadeIn 0.35s ease',
    }}>
      <div style={{ width: '100%', maxWidth }}>
        {children}
      </div>
    </div>
  )
}

function Label({ children }) {
  return (
    <div style={{
      fontFamily: T.mono,
      fontSize: 10,
      letterSpacing: '0.18em',
      color: T.muted,
      textTransform: 'uppercase',
      marginBottom: 8,
    }}>
      {children}
    </div>
  )
}

function Btn({ children, onClick, disabled, variant = 'primary', style = {} }) {
  const base = {
    fontFamily: T.mono,
    fontSize: 13,
    letterSpacing: '0.06em',
    border: 'none',
    cursor: disabled ? 'not-allowed' : 'pointer',
    padding: '12px 24px',
    borderRadius: 2,
    transition: 'opacity 0.15s, background 0.15s',
    opacity: disabled ? 0.35 : 1,
    ...style,
  }
  const variants = {
    primary:  { background: T.accent,   color: '#000', fontWeight: 600 },
    ghost:    { background: 'transparent', color: T.text, border: `1px solid ${T.border}` },
    danger:   { background: 'transparent', color: '#FF5555', border: '1px solid #FF5555' },
  }
  return (
    <button
      onClick={disabled ? undefined : onClick}
      style={{ ...base, ...variants[variant] }}
    >
      {children}
    </button>
  )
}

function ErrorBanner({ message, onRetry }) {
  if (!message) return null
  return (
    <div style={{
      marginTop: 24,
      padding: '16px 20px',
      border: '1px solid #FF5555',
      borderRadius: 4,
      background: 'rgba(255,85,85,0.05)',
      fontFamily: T.mono,
      fontSize: 13,
      color: '#FF5555',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'flex-start',
      gap: 16,
    }}>
      <span style={{ flex: 1, lineHeight: 1.6 }}>{message}</span>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            background: 'transparent',
            border: '1px solid #FF5555',
            color: '#FF5555',
            fontFamily: T.mono,
            fontSize: 11,
            letterSpacing: '0.08em',
            padding: '6px 14px',
            borderRadius: 2,
            cursor: 'pointer',
            flexShrink: 0,
          }}
        >
          Try Again
        </button>
      )}
    </div>
  )
}

/* ══════════════════════════════════════════════════════════════════════
   SCREEN 1 — LANDING
══════════════════════════════════════════════════════════════════════ */
function LandingScreen({ onSubmit, error, onClearError }) {
  const [name, setName]     = useState('')
  const [text, setText]     = useState('')
  const [wordErr, setWordErr] = useState('')

  let displayError = error
  if (error) {
    try {
      const parsed = JSON.parse(error)
      if (parsed.detail) displayError = parsed.detail
    } catch (e) {
      // not JSON
    }
    
    if (typeof displayError === 'string' && displayError.includes('high demand')) {
      displayError = 'Something went wrong — Gemini is experiencing high demand. Please wait a moment and try again.'
    }
  }

  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0

  function handleSubmit() {
    if (wordCount < 150) {
      setWordErr(`Too short — ${wordCount} words. Paste at least 150 words from the company's About Us page.`)
      return
    }
    setWordErr('')
    onSubmit(name.trim() || 'Unknown Company', text)
  }

  function handleTextChange(e) {
    setText(e.target.value)
    if (wordErr) setWordErr('')
  }

  return (
    <Shell maxWidth={680}>
      {/* Logo / wordmark */}
      <div style={{ marginBottom: 56 }}>
        <div style={{
          fontFamily: T.mono,
          fontSize: 11,
          letterSpacing: '0.22em',
          color: T.accent,
          textTransform: 'uppercase',
          marginBottom: 14,
        }}>
          Culture Fit Analyzer
        </div>
        <h1 style={{
          fontFamily: T.sans,
          fontSize: 'clamp(28px, 5vw, 44px)',
          fontWeight: 700,
          color: '#fff',
          lineHeight: 1.15,
          letterSpacing: '-0.02em',
        }}>
          Know before you go.
        </h1>
        <p style={{
          fontFamily: T.mono,
          fontSize: 13,
          color: T.muted,
          marginTop: 12,
          lineHeight: 1.7,
          maxWidth: 520,
        }}>
          Paste any company's About Us text. Get a grounded culture report,
          real research citations, and a diagnostic quiz mapped across 5 dimensions.
        </p>
      </div>

      {/* Form */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

        {displayError && (
          <div style={{
            background: '#E53E3E',
            color: '#FFFFFF',
            padding: '14px 18px',
            borderRadius: '6px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontFamily: T.sans,
            fontSize: '14px',
            fontWeight: 500,
            boxShadow: '0 4px 12px rgba(229, 62, 62, 0.2)'
          }}>
            <span style={{ lineHeight: 1.5 }}>{displayError}</span>
            <button
              onClick={onClearError}
              style={{
                background: 'none',
                border: 'none',
                color: '#FFFFFF',
                fontSize: '22px',
                cursor: 'pointer',
                lineHeight: 1,
                padding: '0 0 0 16px',
              }}
            >
              ×
            </button>
          </div>
        )}

        {/* Company name */}
        <div>
          <Label>Company Name (optional)</Label>
          <input
            id="company-name-input"
            type="text"
            placeholder="e.g. Google, Apple, Stripe"
            value={name}
            onChange={e => setName(e.target.value)}
            style={{
              width: '100%',
              background: T.surface,
              border: `1px solid ${T.border}`,
              borderRadius: 4,
              padding: '12px 16px',
              fontFamily: T.mono,
              fontSize: 13,
              color: T.text,
              outline: 'none',
              transition: 'border-color 0.15s',
            }}
            onFocus={e => { e.target.style.borderColor = T.accent }}
            onBlur={e =>  { e.target.style.borderColor = T.border }}
          />
        </div>

        {/* About Us text */}
        <div>
          <Label>About Us Text</Label>
          <textarea
            id="about-text-input"
            placeholder="Paste the company's About Us, Mission, or Culture page here…"
            value={text}
            onChange={handleTextChange}
            rows={12}
            style={{
              width: '100%',
              background: T.surface,
              border: `1px solid ${wordErr ? '#FF5555' : T.border}`,
              borderRadius: 4,
              padding: '14px 16px',
              fontFamily: T.mono,
              fontSize: 13,
              color: T.text,
              outline: 'none',
              resize: 'vertical',
              lineHeight: 1.7,
              transition: 'border-color 0.15s',
            }}
            onFocus={e => { if (!wordErr) e.target.style.borderColor = T.accent }}
            onBlur={e =>  { if (!wordErr) e.target.style.borderColor = T.border }}
          />
          {/* Word count bar */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginTop: 6,
          }}>
            {wordErr
              ? <span style={{ fontFamily: T.mono, fontSize: 11, color: '#FF5555' }}>{wordErr}</span>
              : <span style={{ fontFamily: T.mono, fontSize: 11, color: T.muted }}>
                  {wordCount} words {wordCount >= 150
                    ? <span style={{ color: T.accent }}>✓</span>
                    : <span style={{ color: T.muted }}>— need {150 - wordCount} more</span>
                  }
                </span>
            }
          </div>
        </div>

        {/* Submit */}
        <Btn
          id="analyze-btn"
          onClick={handleSubmit}
          style={{ alignSelf: 'flex-start', marginTop: 4 }}
        >
          Analyze Culture →
        </Btn>
      </div>

      {/* Footer */}
      <div style={{
        marginTop: 64,
        paddingTop: 24,
        borderTop: `1px solid ${T.border}`,
        fontFamily: T.mono,
        fontSize: 11,
        color: T.muted,
        letterSpacing: '0.06em',
        display: 'flex',
        gap: 24,
      }}>
        <span>RAG Pipeline</span>
        <span>pgvector</span>
        <span>Gemini 2.5 Flash</span>
        <span>Serper Search</span>
      </div>
    </Shell>
  )
}

/* ══════════════════════════════════════════════════════════════════════
   SCREEN 2 — LOADING
══════════════════════════════════════════════════════════════════════ */
const STEPS = [
  'Chunking document',
  'Generating embeddings',
  'Retrieving semantic context',
  'Searching research',
  'Generating analysis',
]

function LoadingScreen({ companyName, apiPromise, onDone, onError }) {
  const [activeStep, setActiveStep] = useState(0)
  const intervalRef = useRef(null)

  useEffect(() => {
    // Step animation — light up one step every 1100ms
    intervalRef.current = setInterval(() => {
      setActiveStep(s => Math.min(s + 1, STEPS.length - 1))
    }, 1100)

    const minWait = new Promise(r => setTimeout(r, 5000))

    Promise.all([apiPromise, minWait])
      .then(([result]) => {
        clearInterval(intervalRef.current)
        onDone(result)
      })
      .catch(err => {
        clearInterval(intervalRef.current)
        onError(err.message || 'Analysis failed. Please try again.')
      })

    return () => clearInterval(intervalRef.current)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <Shell maxWidth={480}>
      <div style={{ paddingTop: 40 }}>
        {/* Blinking cursor indicator */}
        <div style={{
          fontFamily: T.mono,
          fontSize: 11,
          letterSpacing: '0.18em',
          color: T.accent,
          textTransform: 'uppercase',
          marginBottom: 24,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}>
          <span style={{ animation: 'blink 1s step-end infinite', display: 'inline-block', fontSize: 14 }}>▌</span>
          Running
        </div>

        <h2 style={{
          fontFamily: T.sans,
          fontSize: 'clamp(20px, 4vw, 28px)',
          fontWeight: 600,
          color: '#fff',
          letterSpacing: '-0.02em',
          marginBottom: 48,
          lineHeight: 1.3,
        }}>
          Analyzing {companyName}…
        </h2>

        {/* Steps */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
          {STEPS.map((step, i) => {
            const done    = i < activeStep
            const current = i === activeStep
            return (
              <div
                key={step}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 16,
                  padding: '14px 0',
                  borderBottom: i < STEPS.length - 1 ? `1px solid ${T.border}` : 'none',
                  transition: 'opacity 0.4s',
                  opacity: done || current ? 1 : 0.3,
                }}
              >
                {/* Dot */}
                <div style={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  flexShrink: 0,
                  background: done ? T.accent : current ? T.accent : T.border,
                  animation: current ? 'pulse 1s ease-in-out infinite' : 'none',
                  boxShadow: (done || current) ? `0 0 8px ${T.accent}55` : 'none',
                  transition: 'background 0.3s',
                }} />

                <span style={{
                  fontFamily: T.mono,
                  fontSize: 13,
                  color: done ? T.text : current ? '#fff' : T.muted,
                  letterSpacing: '0.02em',
                  transition: 'color 0.3s',
                }}>
                  {step}
                </span>

                {done && (
                  <span style={{
                    marginLeft: 'auto',
                    fontFamily: T.mono,
                    fontSize: 11,
                    color: T.accent,
                    letterSpacing: '0.08em',
                  }}>
                    done
                  </span>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </Shell>
  )
}

/* ══════════════════════════════════════════════════════════════════════
   SCREEN 3 — REPORT
══════════════════════════════════════════════════════════════════════ */
const SOURCE_REGEX = /\(source: (https?:\/\/[^\s)]+)\)/g

function linkifyResearch(text) {
  if (!text) return null
  // Split by the (source: url) pattern, preserving the captured URL group
  const parts = text.split(SOURCE_REGEX)
  return parts.map((part, i) => {
    // Even indices are plain text; odd indices are the captured URL from the group
    if (i % 2 === 1) {
      return (
        <a
          key={i}
          href={part}
          target="_blank"
          rel="noreferrer"
          style={{
            color: '#C8FF00',
            textDecoration: 'underline',
            wordBreak: 'break-all',
          }}
        >
          {part}
        </a>
      )
    }
    return <span key={i}>{part}</span>
  })
}

function Tab({ label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        background: 'transparent',
        border: 'none',
        borderBottom: active ? `2px solid ${T.accent}` : '2px solid transparent',
        color: active ? '#fff' : T.muted,
        fontFamily: T.mono,
        fontSize: 12,
        letterSpacing: '0.1em',
        textTransform: 'uppercase',
        padding: '10px 0',
        cursor: 'pointer',
        transition: 'color 0.15s, border-color 0.15s',
      }}
    >
      {label}
    </button>
  )
}

function ReportScreen({ companyName, report, onStartQuiz }) {
  const [activeTab, setActiveTab] = useState('culture')

  const cultureText = report.culture_report || ''
  const researchText = typeof report.research_insights === 'string'
    ? report.research_insights : JSON.stringify(report.research_insights)

  let valuesData = report.values_to_thrive
  if (typeof valuesData === 'string') {
    try { valuesData = JSON.parse(valuesData) } catch { valuesData = null }
  }
  // If it's still a string (plain text) or null, fall back to splitting by newline
  const valuesIsArray = Array.isArray(valuesData)

  return (
    <Shell maxWidth={760}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: 40,
        gap: 16,
        flexWrap: 'wrap',
      }}>
        <div>
          <div style={{
            fontFamily: T.mono,
            fontSize: 10,
            letterSpacing: '0.2em',
            color: T.accent,
            textTransform: 'uppercase',
            marginBottom: 8,
          }}>
            Culture Intelligence Report
          </div>
          <h1 style={{
            fontFamily: T.sans,
            fontSize: 'clamp(18px, 3.5vw, 26px)',
            fontWeight: 600,
            color: '#fff',
            letterSpacing: '-0.02em',
            lineHeight: 1.2,
          }}>
            {companyName}
          </h1>
        </div>
        <Btn id="take-quiz-btn" onClick={onStartQuiz} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '10px 20px' }}>
          <div>Take the Quiz →</div>
          <div style={{ fontSize: '9px', fontWeight: 400, opacity: 0.7, marginTop: '4px', letterSpacing: '0.04em' }}>
            Diagnostic test to test your compatibility
          </div>
        </Btn>
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex',
        gap: 28,
        borderBottom: `1px solid ${T.border}`,
        marginBottom: 32,
      }}>
        <Tab label="Culture Report"   active={activeTab === 'culture'}   onClick={() => setActiveTab('culture')} />
        <Tab label="Values to Thrive" active={activeTab === 'values'}    onClick={() => setActiveTab('values')} />
        <Tab label="Research"         active={activeTab === 'research'}  onClick={() => setActiveTab('research')} />
      </div>

      {/* Tab: Culture Report */}
      {activeTab === 'culture' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20, animation: 'fadeIn 0.25s ease' }}>
          {cultureText.split(/\n\n+/).filter(Boolean).map((para, i) => (
            <p key={i} style={{
              fontFamily: T.mono,
              fontSize: 13,
              lineHeight: 1.9,
              color: T.text,
            }}>
              {para}
            </p>
          ))}
        </div>
      )}

      {/* Tab: Values to Thrive */}
      {activeTab === 'values' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, animation: 'fadeIn 0.25s ease' }}>
          {valuesIsArray
            ? valuesData.map((val, i) => {
                const title = typeof val === 'object' ? (val.value || val.title || val.name || Object.values(val)[0]) : val
                const body  = typeof val === 'object' ? (val.explanation || val.description || Object.values(val)[1] || '') : ''
                return (
                  <div key={i} style={{
                    padding: '20px 24px',
                    border: `1px solid ${T.border}`,
                    borderRadius: 4,
                    background: T.surface,
                    display: 'flex',
                    gap: 20,
                    alignItems: 'flex-start',
                  }}>
                    <span style={{
                      fontFamily: T.mono,
                      fontSize: 20,
                      fontWeight: 600,
                      color: T.accent,
                      lineHeight: 1,
                      flexShrink: 0,
                      minWidth: 28,
                    }}>
                      {i + 1}
                    </span>
                    <div>
                      <div style={{
                        fontFamily: T.sans,
                        fontSize: 14,
                        fontWeight: 600,
                        color: '#fff',
                        marginBottom: 6,
                      }}>
                        {String(title)}
                      </div>
                      {body && (
                        <div style={{
                          fontFamily: T.mono,
                          fontSize: 12,
                          color: T.muted,
                          lineHeight: 1.7,
                        }}>
                          {String(body)}
                        </div>
                      )}
                    </div>
                  </div>
                )
              })
            : (
              /* Fallback: plain text split by newlines */
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {String(valuesData || '').split(/\n/).filter(Boolean).map((line, i) => (
                  <div key={i} style={{
                    padding: '14px 18px',
                    border: `1px solid ${T.border}`,
                    borderRadius: 4,
                    background: T.surface,
                    fontFamily: T.mono,
                    fontSize: 13,
                    color: T.text,
                    lineHeight: 1.7,
                  }}>
                    {line}
                  </div>
                ))}
              </div>
            )
          }
        </div>
      )}

      {/* Tab: Research */}
      {activeTab === 'research' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20, animation: 'fadeIn 0.25s ease' }}>
          {researchText.split(/\n\n+/).filter(Boolean).map((para, i) => (
            <p key={i} style={{
              fontFamily: T.mono,
              fontSize: 13,
              lineHeight: 1.9,
              color: T.text,
            }}>
              {linkifyResearch(para)}
            </p>
          ))}
        </div>
      )}
    </Shell>
  )
}

/* ══════════════════════════════════════════════════════════════════════
   SCREEN 4 — QUIZ
══════════════════════════════════════════════════════════════════════ */
const OPTION_LABELS = ['A', 'B', 'C', 'D']

function QuizScreen({ report, reportId, onDone, onError }) {
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [answers, setAnswers]                 = useState([])
  const [selectedOption, setSelectedOption]   = useState(null)
  const [submitting, setSubmitting]           = useState(false)

  let qs = report.quiz_questions
  if (typeof qs === 'string') {
    try { qs = JSON.parse(qs) } catch { qs = [] }
  }
  if (!Array.isArray(qs)) qs = []

  const total    = qs.length
  const question = qs[currentQuestion]
  const isLast   = currentQuestion === total - 1
  const progress = total > 0 ? (currentQuestion / total) * 100 : 0

  async function handleNext() {
    const updatedAnswers = [
      ...answers,
      { question_index: currentQuestion, selected_option: selectedOption },
    ]

    if (!isLast) {
      setAnswers(updatedAnswers)
      setCurrentQuestion(q => q + 1)
      setSelectedOption(null)
      return
    }

    // Final answer — submit
    setSubmitting(true)
    try {
      const result = await submitQuiz(reportId, updatedAnswers)
      onDone(result)
    } catch (err) {
      onError(err.message || 'Failed to submit quiz. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  if (!question) {
    return (
      <Shell maxWidth={580}>
        <div style={{ color: '#FF5555', fontFamily: T.mono, fontSize: 13 }}>
          No quiz questions found. Please re-generate the report.
        </div>
      </Shell>
    )
  }

  return (
    <Shell maxWidth={580}>
      {/* Progress */}
      <div style={{ marginBottom: 36 }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 10,
        }}>
          <span style={{ fontFamily: T.mono, fontSize: 11, color: T.muted, letterSpacing: '0.1em' }}>
            Question {currentQuestion + 1} of {total}
          </span>
          <span style={{
            fontFamily: T.mono,
            fontSize: 10,
            letterSpacing: '0.18em',
            color: T.accent,
            textTransform: 'uppercase',
          }}>
            {question.dimension}
          </span>
        </div>
        {/* Progress track */}
        <div style={{
          height: 2,
          background: T.border,
          borderRadius: 1,
          overflow: 'hidden',
        }}>
          <div style={{
            height: '100%',
            width: `${progress}%`,
            background: T.accent,
            transition: 'width 0.4s ease',
            borderRadius: 1,
          }} />
        </div>
      </div>

      {/* Question */}
      <h2 style={{
        fontFamily: T.sans,
        fontSize: 'clamp(17px, 3vw, 22px)',
        fontWeight: 600,
        color: '#fff',
        lineHeight: 1.45,
        letterSpacing: '-0.01em',
        marginBottom: 32,
      }}>
        {question.question}
      </h2>

      {/* Options */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 32 }}>
        {(question.options || []).map((opt, i) => {
          const sel = selectedOption === i
          return (
            <button
              key={i}
              id={`option-${i}`}
              onClick={() => setSelectedOption(i)}
              style={{
                textAlign: 'left',
                background: sel ? '#111800' : T.surface,
                border: `1px solid ${sel ? T.accent : T.border}`,
                borderRadius: 4,
                padding: '14px 18px',
                cursor: 'pointer',
                fontFamily: T.mono,
                fontSize: 13,
                color: sel ? T.accent : '#888',
                display: 'flex',
                gap: 14,
                alignItems: 'flex-start',
                transition: 'background 0.15s, border-color 0.15s, color 0.15s',
              }}
            >
              <span style={{
                fontWeight: 600,
                color: sel ? T.accent : T.muted,
                flexShrink: 0,
                minWidth: 18,
              }}>
                {OPTION_LABELS[i]}.
              </span>
              <span style={{ lineHeight: 1.6 }}>{opt.replace(/^[A-D]\.\s*/i, '')}</span>
            </button>
          )
        })}
      </div>

      {/* Next / Submit */}
      <Btn
        id="next-question-btn"
        onClick={handleNext}
        disabled={selectedOption === null || submitting}
      >
        {submitting ? 'Submitting…' : isLast ? 'See Results →' : 'Next Question →'}
      </Btn>
    </Shell>
  )
}

/* ══════════════════════════════════════════════════════════════════════
   SCREEN 5 — RESULTS
══════════════════════════════════════════════════════════════════════ */
const DIM_LABELS = {
  innovation:    'Innovation',
  collaboration: 'Collaboration',
  mission:       'Mission',
  pace:          'Pace',
  people:        'People',
}

function ResultsScreen({ quizResults, onReset }) {
  let dimScores = quizResults.dimension_scores
  if (typeof dimScores === 'string') {
    try { dimScores = JSON.parse(dimScores) } catch { dimScores = {} }
  }
  if (!dimScores || typeof dimScores !== 'object') dimScores = {}

  const overall = quizResults.overall_fit_score ?? 0

  const chartData = [
    { dimension: 'Innovation',    score: dimScores.innovation    || 0 },
    { dimension: 'Collaboration', score: dimScores.collaboration || 0 },
    { dimension: 'Mission',       score: dimScores.mission       || 0 },
    { dimension: 'Pace',          score: dimScores.pace          || 0 },
    { dimension: 'People',        score: dimScores.people        || 0 },
  ]

  const customTick = ({ payload, x, y, cx, cy }) => {
    return (
      <text x={x} y={y} textAnchor={x > cx ? 'start' : x < cx ? 'end' : 'middle'}
        fill="#666" fontSize={11} fontFamily={T.mono}>
        {payload.value}
      </text>
    )
  }

  return (
    <Shell maxWidth={680}>
      {/* Score header */}
      <div style={{ marginBottom: 48 }}>
        <div style={{
          fontFamily: T.mono,
          fontSize: 10,
          letterSpacing: '0.2em',
          color: T.muted,
          textTransform: 'uppercase',
          marginBottom: 20,
        }}>
          Your Culture Fit
        </div>

        <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
          <span style={{
            fontFamily: T.sans,
            fontSize: 'clamp(52px, 10vw, 88px)',
            fontWeight: 700,
            color: T.accent,
            letterSpacing: '-0.04em',
            lineHeight: 1,
          }}>
            {Number(overall).toFixed(1)}
          </span>
          <span style={{
            fontFamily: T.mono,
            fontSize: 14,
            color: T.muted,
          }}>
            /10 Overall Fit Score
          </span>
        </div>
      </div>

      {/* Spider chart */}
      <div style={{
        background: T.surface,
        border: `1px solid ${T.border}`,
        borderRadius: 4,
        padding: '24px 8px',
        marginBottom: 40,
      }}>
        <ResponsiveContainer width="100%" height={300}>
          <RadarChart data={chartData} margin={{ top: 10, right: 40, bottom: 10, left: 40 }}>
            <PolarGrid stroke={T.border} />
            <PolarAngleAxis
              dataKey="dimension"
              tick={customTick}
            />
            <Radar
              dataKey="score"
              stroke={T.accent}
              fill={T.accent}
              fillOpacity={0.1}
              strokeWidth={1.5}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Dimension bars */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginBottom: 48 }}>
        {Object.entries(DIM_LABELS).map(([key, label]) => {
          const score = dimScores[key] ?? 0
          const pct   = Math.min((score / 10) * 100, 100)
          return (
            <div key={key}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                marginBottom: 6,
              }}>
                <span style={{ fontFamily: T.mono, fontSize: 11, color: T.muted, letterSpacing: '0.1em', textTransform: 'uppercase' }}>
                  {label}
                </span>
                <span style={{ fontFamily: T.mono, fontSize: 11, color: T.accent }}>
                  {Number(score).toFixed(1)}
                </span>
              </div>
              <div style={{
                height: 3,
                background: T.border,
                borderRadius: 2,
                overflow: 'hidden',
              }}>
                <div style={{
                  height: '100%',
                  width: `${pct}%`,
                  background: T.accent,
                  borderRadius: 2,
                  transition: 'width 0.8s cubic-bezier(0.16, 1, 0.3, 1)',
                }} />
              </div>
            </div>
          )
        })}
      </div>

      {/* Reset */}
      <Btn variant="ghost" onClick={onReset}>
        ← Analyze Another Company
      </Btn>
    </Shell>
  )
}

/* ══════════════════════════════════════════════════════════════════════
   ROOT APP
══════════════════════════════════════════════════════════════════════ */
export default function App() {
  const [screen, setScreen]           = useState('landing')
  const [companyName, setCompanyName] = useState('')
  const [companyId, setCompanyId]     = useState(null)
  const [reportId, setReportId]       = useState(null)
  const [report, setReport]           = useState(null)
  const [quizResults, setQuizResults] = useState(null)
  const [error, setError]             = useState(null)

  // api promise ref so LoadingScreen can receive it
  const apiPromiseRef = useRef(null)

  // Inject global styles once
  useEffect(() => {
    const tag = document.createElement('style')
    tag.innerHTML = globalStyle
    document.head.appendChild(tag)
    return () => document.head.removeChild(tag)
  }, [])

  function resetAll() {
    setScreen('landing')
    setCompanyName('')
    setCompanyId(null)
    setReportId(null)
    setReport(null)
    setQuizResults(null)
    setError(null)
    apiPromiseRef.current = null
  }

  function handleLandingSubmit(name, text) {
    setCompanyName(name)
    setError(null)

    // Build the chained API promise BEFORE switching screens
    apiPromiseRef.current = analyzeCompany(name, text).then(analyzeRes => {
      const cid = analyzeRes.company_id
      setCompanyId(cid)
      return generateReport(cid)
    })

    setScreen('loading')
  }

  function handleLoadingDone(reportData) {
    setReport(reportData)
    setReportId(reportData.id)
    setScreen('report')
  }

  function handleLoadingError(msg) {
    setError(msg)
    setScreen('landing')
  }

  function handleStartQuiz() {
    setScreen('quiz')
  }

  function handleQuizDone(results) {
    setQuizResults(results)
    setScreen('results')
  }

  function handleQuizError(msg) {
    setError(msg)
  }

  /* ── Route to screen ── */
  if (screen === 'landing') {
    return (
      <LandingScreen
        onSubmit={handleLandingSubmit}
        error={error}
        onClearError={() => setError(null)}
      />
    )
  }

  if (screen === 'loading') {
    return (
      <LoadingScreen
        companyName={companyName}
        apiPromise={apiPromiseRef.current}
        onDone={handleLoadingDone}
        onError={handleLoadingError}
      />
    )
  }

  if (screen === 'report') {
    return (
      <ReportScreen
        companyName={companyName}
        report={report}
        onStartQuiz={handleStartQuiz}
      />
    )
  }

  if (screen === 'quiz') {
    return (
      <QuizScreen
        report={report}
        reportId={reportId}
        onDone={handleQuizDone}
        onError={handleQuizError}
      />
    )
  }

  if (screen === 'results') {
    return (
      <ResultsScreen
        quizResults={quizResults}
        onReset={resetAll}
      />
    )
  }

  return null
}
