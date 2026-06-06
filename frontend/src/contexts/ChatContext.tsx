import { createContext, useContext, useState, ReactNode } from 'react'

interface ChatContextType {
  analysisId: number | null
  setAnalysisId: (id: number | null) => void
}

const ChatContext = createContext<ChatContextType>({
  analysisId: null,
  setAnalysisId: () => {},
})

export function ChatProvider({ children }: { children: ReactNode }) {
  const [analysisId, setAnalysisId] = useState<number | null>(null)
  return (
    <ChatContext.Provider value={{ analysisId, setAnalysisId }}>
      {children}
    </ChatContext.Provider>
  )
}

export const useChatContext = () => useContext(ChatContext)
