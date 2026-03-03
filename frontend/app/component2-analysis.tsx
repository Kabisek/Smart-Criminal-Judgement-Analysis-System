import {
  View,
  Text,
  Pressable,
  StyleSheet,
  Platform,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Layout } from '../components/Layout';
import { Container, Card, PageHeader } from '../components/ui';
import { DocumentViewer } from '../components/DocumentViewer';
import { CaseAnalysisPanel } from '../components/CaseAnalysisPanel';
import { useComp2 } from '../components/Comp2Context';
import { colors, spacing } from '../theme';
import React, { useState, useEffect, useMemo } from 'react';
import { analyzeCaseOnly, SourceSpanData } from '../api';

export default function CaseAnalysisScreen() {
  const router = useRouter();
  const { file, textInput, analysisResult, setAnalysisResult } = useComp2();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeFieldId, setActiveFieldId] = useState<string | null>(null);

  useEffect(() => {
    if (analysisResult) return;
    if (!file && !textInput) {
      setError('No document selected. Go back and upload a file first.');
      return;
    }
    runAnalysis();
  }, []);

  const runAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      if (file) {
        const result = await analyzeCaseOnly(file.uri, file.name);
        setAnalysisResult(result);
      } else {
        setError('Text-based case analysis requires a document file. Please upload a document on the previous page.');
      }
    } catch (err: any) {
      console.error('Case analysis failed:', err);
      setError(err?.message || 'Case analysis failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const documentPages = analysisResult?.document_text ?? [];
  const sourceSpans: SourceSpanData[] = analysisResult?.source_spans ?? [];
  const hasBoundingBox = documentPages.length > 0 && analysisResult?.analyzed_case != null;

  const activeHighlight = useMemo(() => {
    if (!activeFieldId) return null;
    const span = sourceSpans.find(s => s.field_id === activeFieldId);
    if (!span) return null;
    return { page: span.page, start_char: span.start_char, end_char: span.end_char };
  }, [activeFieldId, sourceSpans]);

  const handleFieldClick = (fieldId: string) => {
    setActiveFieldId(prev => (prev === fieldId ? null : fieldId));
  };

  return (
    <Layout>
      <Container style={Platform.OS === 'web' ? { maxWidth: 1500 } : undefined}>
        <PageHeader
          title="Case Analysis"
          breadcrumb="Argument Synthesis Engine → Case Analysis"
        />

        <Pressable onPress={() => router.back()} style={styles.backRow}>
          <Text style={styles.backLink}>← Back to Hub</Text>
        </Pressable>

        {loading && (
          <View style={styles.center}>
            <ActivityIndicator size="large" color={colors.accent} />
            <Text style={styles.loadingText}>Analyzing case document...</Text>
            <Text style={styles.loadingHint}>This may take a minute for large files.</Text>
          </View>
        )}

        {error && !loading && (
          <Card title="Error" style={styles.errorCard}>
            <Text style={styles.errorText}>{error}</Text>
            <Pressable onPress={() => router.back()} style={styles.retryBtn}>
              <Text style={styles.retryText}>← Go Back</Text>
            </Pressable>
          </Card>
        )}

        {!loading && !error && hasBoundingBox && (
          <View style={styles.bbSplit}>
            <View style={styles.bbLeft}>
              <DocumentViewer
                pages={documentPages}
                activeHighlight={activeHighlight}
                onClearHighlight={() => setActiveFieldId(null)}
              />
            </View>
            <View style={styles.bbRight}>
              <CaseAnalysisPanel
                analyzedCase={analysisResult!.analyzed_case!}
                sourceSpans={sourceSpans}
                activeFieldId={activeFieldId}
                onFieldClick={handleFieldClick}
              />
            </View>
          </View>
        )}

        {!loading && !error && analysisResult && !hasBoundingBox && (
          <Card title="Analysis Complete">
            <Text style={styles.noData}>
              Analysis completed but no bounding-box data was returned. The document may not contain extractable text positions.
            </Text>
          </Card>
        )}
      </Container>
    </Layout>
  );
}

const styles = StyleSheet.create({
  backRow: {
    marginBottom: spacing.md,
  },
  backLink: {
    color: colors.accent,
    fontWeight: '600',
    fontSize: 14,
  },
  center: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 80,
    gap: 12,
  },
  loadingText: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.primary,
    marginTop: 12,
  },
  loadingHint: {
    fontSize: 12,
    color: colors.textMuted,
  },
  errorCard: {
    marginVertical: spacing.lg,
  },
  errorText: {
    fontSize: 14,
    color: '#DC2626',
    lineHeight: 22,
    marginBottom: 12,
  },
  retryBtn: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: '#F1F5F9',
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  retryText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.primary,
  },
  bbSplit: {
    flexDirection: Platform.OS === 'web' ? 'row' : 'column',
    gap: spacing.md,
    marginBottom: spacing.lg,
    minHeight: 500,
  },
  bbLeft: { flex: 1, minWidth: 0 },
  bbRight: { flex: 1, minWidth: 0 },
  noData: {
    color: colors.textMuted,
    fontStyle: 'italic',
    textAlign: 'center',
    padding: 20,
  },
});
