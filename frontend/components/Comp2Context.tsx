import React, { createContext, useContext, useState, useCallback } from 'react';
import type { NormalizedAnalysisResponse, SourceSpanData, PageTextData } from '../api';

interface PickedFile {
  uri: string;
  name: string;
  blob?: Blob;
}

interface Comp2State {
  file: PickedFile | null;
  textInput: string | null;
  analysisResult: NormalizedAnalysisResponse | null;
  argumentsResult: NormalizedAnalysisResponse | null;
}

interface Comp2ContextValue extends Comp2State {
  setFile: (file: PickedFile | null) => void;
  setTextInput: (text: string | null) => void;
  setAnalysisResult: (r: NormalizedAnalysisResponse | null) => void;
  setArgumentsResult: (r: NormalizedAnalysisResponse | null) => void;
  clear: () => void;
}

const INITIAL: Comp2State = {
  file: null,
  textInput: null,
  analysisResult: null,
  argumentsResult: null,
};

const Comp2Context = createContext<Comp2ContextValue>({
  ...INITIAL,
  setFile: () => {},
  setTextInput: () => {},
  setAnalysisResult: () => {},
  setArgumentsResult: () => {},
  clear: () => {},
});

export function Comp2Provider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<Comp2State>(INITIAL);

  const setFile = useCallback((file: PickedFile | null) => {
    setState(prev => ({ ...prev, file, analysisResult: null, argumentsResult: null }));
  }, []);

  const setTextInput = useCallback((textInput: string | null) => {
    setState(prev => ({ ...prev, textInput, analysisResult: null, argumentsResult: null }));
  }, []);

  const setAnalysisResult = useCallback((analysisResult: NormalizedAnalysisResponse | null) => {
    setState(prev => ({ ...prev, analysisResult }));
  }, []);

  const setArgumentsResult = useCallback((argumentsResult: NormalizedAnalysisResponse | null) => {
    setState(prev => ({ ...prev, argumentsResult }));
  }, []);

  const clear = useCallback(() => setState(INITIAL), []);

  return (
    <Comp2Context.Provider
      value={{
        ...state,
        setFile,
        setTextInput,
        setAnalysisResult,
        setArgumentsResult,
        clear,
      }}
    >
      {children}
    </Comp2Context.Provider>
  );
}

export function useComp2() {
  return useContext(Comp2Context);
}
