/**
 * CodeEditor — Monaco Editor wrapper.
 *
 * - Dark theme matching the existing QAIP slate/indigo design.
 * - Ctrl/Cmd+S is intercepted — does NOT reload the page.
 * - Language changes update syntax highlighting immediately.
 * - Code is controlled via value/onChange props — parent owns state.
 */
import { useRef, useCallback } from 'react'
import Editor, { type OnMount, type Monaco } from '@monaco-editor/react'
import type { editor as MonacoEditor } from 'monaco-editor'
import { Spinner } from '@/components/ui/Spinner'
import type { CodingLanguage } from '@/types/coding'

interface CodeEditorProps {
  value: string
  onChange: (code: string) => void
  language: CodingLanguage
  readOnly?: boolean
  height?: string
}

/** Custom dark theme colours matching the existing QAIP slate palette */
function defineQaipTheme(monaco: Monaco) {
  monaco.editor.defineTheme('qaip-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'comment',  foreground: '64748b', fontStyle: 'italic' },
      { token: 'keyword',  foreground: '818cf8' },
      { token: 'string',   foreground: '34d399' },
      { token: 'number',   foreground: 'f59e0b' },
      { token: 'type',     foreground: '67e8f9' },
      { token: 'function', foreground: 'c084fc' },
    ],
    colors: {
      'editor.background':          '#0f172a',
      'editor.foreground':          '#e2e8f0',
      'editorLineNumber.foreground': '#334155',
      'editorLineNumber.activeForeground': '#6366f1',
      'editor.lineHighlightBackground': '#1e293b',
      'editorCursor.foreground':    '#6366f1',
      'editor.selectionBackground': '#312e8160',
      'editorIndentGuide.background': '#1e293b',
      'editorWidget.background':    '#1e293b',
      'editorSuggestWidget.background': '#1e293b',
      'editorSuggestWidget.border': '#334155',
      'input.background':           '#0f172a',
    },
  })
}

export function CodeEditor({
  value,
  onChange,
  language,
  readOnly = false,
  height = '100%',
}: CodeEditorProps) {
  const editorRef = useRef<MonacoEditor.IStandaloneCodeEditor | null>(null)

  const handleMount: OnMount = useCallback((editor, monaco) => {
    editorRef.current = editor
    defineQaipTheme(monaco)
    monaco.editor.setTheme('qaip-dark')

    // Intercept Ctrl/Cmd+S — prevent browser save dialog
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
      // intentionally no-op — just prevent default browser behaviour
    })
  }, [])

  return (
    <div className="h-full w-full overflow-hidden rounded-lg border border-surface-border">
      <Editor
        height={height}
        language={language.monacoLanguage}
        value={value}
        onChange={(v) => onChange(v ?? '')}
        onMount={handleMount}
        theme="qaip-dark"
        loading={
          <div className="flex items-center justify-center h-full bg-surface-card">
            <Spinner size="md" />
          </div>
        }
        options={{
          fontSize:          15,
          fontFamily:        "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
          fontLigatures:     true,
          lineNumbers:       'on',
          minimap:           { enabled: false },
          wordWrap:          'off',
          tabSize:           4,
          insertSpaces:      true,
          scrollBeyondLastLine: false,
          smoothScrolling:   true,
          cursorBlinking:    'smooth',
          automaticLayout:   true,
          readOnly,
          padding:           { top: 12, bottom: 12 },
          scrollbar: {
            verticalScrollbarSize:   8,
            horizontalScrollbarSize: 8,
          },
          suggest: {
            showKeywords:  true,
            showSnippets:  true,
          },
          bracketPairColorization: { enabled: true },
          renderLineHighlight: 'gutter',
          contextmenu: false,
        }}
      />
    </div>
  )
}
