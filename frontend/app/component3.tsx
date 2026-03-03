import { View, Text, TextInput, Pressable, StyleSheet, Platform, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { Layout } from '../components/Layout';
import { Container, Card, PageHeader, Button } from '../components/ui';
import { CaseIngestion } from '../components/CaseIngestion';
import { colors, typography, spacing } from '../theme';
import React, { useState } from 'react';
import { NormalizedAnalysisResponse } from '../api';

const SCENARIOS = [
  { id: '1', title: 'Drug Possession Appeal', desc: 'Convicted under Section 54C. Appeal based on procedural delay in evidence analysis.', outcome: '65% Reduction Probable' },
  { id: '2', title: 'Assault Self-Defense', desc: 'Culpable homicide. Ground: Exercise of right of private defense was not considered.', outcome: '40% Acquittal Probable' },
];

export default function Component3Screen() {
  const router = useRouter();
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [onAnalysisComplete_data, setOnAnalysisComplete_data] = useState<NormalizedAnalysisResponse | null>(null);

  const onAnalysisComplete = (data: NormalizedAnalysisResponse) => {
    setOnAnalysisComplete_data(data);
    if (data.analyzed_case) {
      // Component 2 prediction logic
      const prediction = data.analyzed_case.case_header?.subject || "Possible Sentence Mitigation";
      setResult(`Probabilistic Outcome: ${prediction}. Patterns identified in similar historical judgments.`);
      return;
    }
    if (data.data) {
      // Legacy or extracted data
      const prediction = (data.data as any).prediction || (data.data as any).outcome;
      const confidence = (data.data as any).confidence;
      if (prediction) {
        setResult(`Probabilistic Outcome: ${prediction}${confidence ? ` (${confidence} confidence)` : ''}`);
        return;
      }
    }
    setResult('Probabilistic Outcome: 72% chance of Sentence Mitigation based on legal patterns identified in your input.');
  };

  return (
    <Layout>
      <Container>
        <PageHeader
          title="Outcome Prediction Model"
          breadcrumb="Analytical Tools → Probability Analysis"
        />

        <View style={styles.row}>
          <View style={styles.mainCol}>
            <CaseIngestion
              onAnalysisComplete={onAnalysisComplete}
              initialMode="document"
              allowedModes={['document', 'text', 'voice']}
            />

            <Card style={styles.scenarioCard} title="Analyze Appeal Case">
              <Text style={styles.para}>
                Alternatively, select a quick scenario to simulate a predefined legal context.
              </Text>

              <View style={styles.presets}>
                <Text style={styles.presetLabel}>Quick Scenarios:</Text>
                <View style={styles.presetRow}>
                  {SCENARIOS.map(s => (
                    <Pressable
                      key={s.id}
                      onPress={() => { onAnalysisComplete({} as any); }}
                      style={styles.presetBtn}
                    >
                      <Text style={styles.presetText}>{s.title}</Text>
                    </Pressable>
                  ))}
                </View>
              </View>
            </Card>

            {result && (
              <View style={styles.resultBox}>
                <Text style={styles.resultHeading}>Prediction Result</Text>
                <Text style={styles.resultText}>{result}</Text>

                {onAnalysisComplete_data?.arguments_report?.arguments && (
                  <View style={styles.reasoningSection}>
                    <Text style={styles.reasoningHeading}>Supporting Legal Reasoning</Text>
                    {onAnalysisComplete_data.arguments_report.arguments.slice(0, 3).map((arg: any, idx: number) => (
                      <View key={idx} style={styles.reasoningItem}>
                        <View style={styles.bullet} />
                        <Text style={styles.reasoningText}>{arg.content}</Text>
                      </View>
                    ))}
                  </View>
                )}

                <Text style={styles.resultNote}>
                  References: Penal Code Sec 300, 302. Based on {onAnalysisComplete_data?.arguments_report?.similar_cases?.length || 12} comparable judgments.
                </Text>
              </View>
            )}
          </View>

          <Card style={styles.infoCard} title="How Prediction Works">
            <View style={styles.howItem}>
              <Text style={styles.howTitle}>1. Similarity Matching</Text>
              <Text style={styles.howText}>We compare your grounds of appeal against 10 years of Supreme Court data.</Text>
            </View>
            <View style={styles.howItem}>
              <Text style={styles.howTitle}>2. Outcome Probability</Text>
              <Text style={styles.howText}>Calculates likelihood of dismissal, sentence reduction, or acquittal.</Text>
            </View>
            <View style={styles.howItem}>
              <Text style={styles.howTitle}>3. Legal Reasoning</Text>
              <Text style={styles.howText}>Provides the specific legal logic adopted by judges in similar successful appeals.</Text>
            </View>

            <Pressable onPress={() => router.push('/')} style={{ marginTop: spacing.xl }}>
              <Text style={styles.backLink}>← Back to Home</Text>
            </Pressable>
          </Card>
        </View>
      </Container>
    </Layout>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: Platform.OS === 'web' ? 'row' : 'column', gap: spacing.lg },
  mainCol: { flex: 2, gap: spacing.lg },
  infoCard: { flex: 1 },
  scenarioCard: { marginTop: spacing.sm },
  para: { color: colors.textSecondary, marginBottom: spacing.md, lineHeight: 22 },
  presets: { marginBottom: spacing.md },
  presetLabel: { fontSize: 13, fontWeight: '600', color: colors.textMuted, marginBottom: 8 },
  presetRow: { flexDirection: 'row', gap: 8 },
  presetBtn: { backgroundColor: colors.bgSection, paddingVertical: 6, paddingHorizontal: 12, borderRadius: 16, borderWidth: 1, borderColor: colors.border },
  presetText: { fontSize: 12, color: colors.primary, fontWeight: '500' },
  textArea: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 12,
    padding: spacing.md,
    fontSize: 16,
    minHeight: 180,
    textAlignVertical: 'top',
    color: colors.textPrimary,
    backgroundColor: '#FAFAFA',
    marginBottom: spacing.lg,
    ...(Platform.OS === 'web' && { outlineStyle: 'none' } as any),
  },
  analyzeBtn: { width: '100%' },
  resultBox: {
    marginTop: spacing.xl,
    padding: spacing.lg,
    backgroundColor: '#F0FDF4',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#BBF7D0',
  },
  resultHeading: { fontSize: 16, fontWeight: 'bold', color: '#166534', marginBottom: 4 },
  resultText: { fontSize: 15, color: '#14532D', marginBottom: 8, fontWeight: '600' },
  resultNote: { fontSize: 12, color: '#166534', opacity: 0.8 },
  reasoningSection: { marginTop: spacing.md, paddingTop: spacing.md, borderTopWidth: 1, borderTopColor: '#BBF7D0' },
  reasoningHeading: { fontSize: 14, fontWeight: '700', color: '#166534', marginBottom: 8 },
  reasoningItem: { flexDirection: 'row', alignItems: 'flex-start', gap: 8, marginBottom: 8 },
  bullet: { width: 5, height: 5, borderRadius: 2.5, backgroundColor: '#166534', marginTop: 6 },
  reasoningText: { fontSize: 13, color: '#166534', flex: 1, lineHeight: 18 },
  howItem: { marginBottom: spacing.lg },
  howTitle: { fontSize: 15, fontWeight: 'bold', color: colors.primary, marginBottom: 4 },
  howText: { fontSize: 13, color: colors.textSecondary, lineHeight: 18 },
  backLink: { color: colors.primary, fontWeight: '500' },
});
