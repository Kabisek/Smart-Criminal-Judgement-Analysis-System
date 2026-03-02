import { useEffect, useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { Layout } from '../components/Layout';
import { Container, Card, PageHeader } from '../components/ui';
import { colors, spacing, typography } from '../theme';

const STAGES = [
  { id: 'stage1', name: 'File Upload', icon: '📄', duration: 800 },
  { id: 'stage2', name: 'Similarity Search', icon: '🔍', duration: 2500 },
  { id: 'stage3', name: 'Case Analysis (RAG)', icon: '🧠', duration: 4000 },
  { id: 'stage4', name: 'Arguments Report', icon: '⚔', duration: 1500 },
];

export default function ProcessingScreen() {
  const router = useRouter();
  const [currentStage, setCurrentStage] = useState(0);
  const [progress, setProgress] = useState(0);
  const [statusDesc, setStatusDesc] = useState('Initializing analysis pipeline');

  useEffect(() => {
    if (currentStage >= STAGES.length) {
      const demoResult = {
        analyzed_case: {
          case_header: { file_number: 'L-SYN-2026-XXXX', date_of_analysis: new Date().toLocaleDateString(), subject: 'Criminal Case Analysis' },
          incident_timeline: { what_happened: 'Case timeline from analysis.', where_it_happened: '' },
          argument_synthesis: {
            prosecution_logic: ['Evidence of offence', 'Documented facts', 'Witness statements'],
            defense_logic: ['Alternative explanations', 'Procedural points', 'Reasonable doubt'],
          },
        },
        arguments_report: {
          similar_cases: [
            { case_id: '2024_AppealCourt_September_criminal_judgment_1151', similarity: 0.52 },
            { case_id: '2023_AppealCourt_March_criminal_judgment_1166', similarity: 0.5 },
          ],
          arguments: [
            { perspective: 'prosecution', title: 'Precedent Support - Prosecution', content: 'Strong precedent support for prosecution based on similar cases.', strength_score: 0.8, supporting_cases: ['Case-1151', 'Case-1166'] },
            { perspective: 'defense', title: 'Precedent Support - Defense', content: 'Defense finds support in cases with procedural and evidence issues.', strength_score: 0.6, model_extracted_points: ['Evidence chain concerns', 'Witness credibility'] },
          ],
        },
      };
      try {
        if (typeof window !== 'undefined' && (window as unknown as { sessionStorage?: Storage }).sessionStorage) {
          (window as unknown as { sessionStorage: Storage }).sessionStorage.setItem('analysisResult', JSON.stringify(demoResult));
        }
      } catch (_) {}
      const t = setTimeout(() => router.replace('/results'), 800);
      return () => clearTimeout(t);
    }

    const stage = STAGES[currentStage];
    setStatusDesc('Processing...');
    const targetProgress = ((currentStage + 1) / STAGES.length) * 100;
    const iv = setInterval(() => {
      setProgress((p) => {
        if (p >= targetProgress) {
          clearInterval(iv);
          return targetProgress;
        }
        return p + 1.5;
      });
    }, 30);
    const timeout = setTimeout(() => {
      setStatusDesc('Completed');
      setCurrentStage((s) => s + 1);
    }, stage.duration);
    return () => {
      clearInterval(iv);
      clearTimeout(timeout);
    };
  }, [currentStage, router]);

  const stage = STAGES[currentStage];
  const stageIcon = stage?.icon ?? '✓';
  const stageName = stage?.name ?? 'Done';

  return (
    <Layout>
      <Container>
        <PageHeader title="Processing Case Analysis" backHref="/component2" />
        <Card>
          <View style={styles.status}>
            <Text style={styles.statusIcon}>{stageIcon}</Text>
            <Text style={styles.statusTitle}>{stageName}</Text>
            <Text style={styles.statusDesc}>{statusDesc}</Text>
          </View>
          <View style={styles.progressWrap}>
            <View style={styles.progressBar}>
              <View style={[styles.progressFill, { width: `${progress}%` }]} />
            </View>
            <View style={styles.progressText}>
              <Text style={styles.progressPercent}>{Math.round(progress)}%</Text>
              <Text style={styles.progressStage}>{stageName}</Text>
            </View>
          </View>
          <View style={styles.stagesList}>
            {STAGES.map((s, i) => (
              <View key={s.id} style={styles.stageItem}>
                <Text style={styles.stageIcon}>{s.icon}</Text>
                <View style={styles.stageContent}>
                  <Text style={styles.stageName}>{s.name}</Text>
                  <Text style={styles.stageStatus}>
                    {i < currentStage ? 'Completed' : i === currentStage ? 'Processing...' : 'Waiting...'}
                  </Text>
                </View>
                <Text style={styles.stageCheck}>{i < currentStage ? '✓' : i === currentStage ? '⏳' : '—'}</Text>
              </View>
            ))}
          </View>
        </Card>
      </Container>
    </Layout>
  );
}

const styles = StyleSheet.create({
  status: { alignItems: 'center', marginBottom: spacing.lg },
  statusIcon: { fontSize: 48, marginBottom: spacing.sm },
  statusTitle: { fontSize: typography.sizes.xl, fontWeight: '700', color: colors.primaryDark, marginBottom: spacing.sm },
  statusDesc: { color: colors.textSecondary },
  progressWrap: { marginVertical: spacing.lg },
  progressBar: { height: 12, backgroundColor: colors.bgSection, borderRadius: 6, overflow: 'hidden', marginBottom: spacing.sm },
  progressFill: { height: '100%', backgroundColor: colors.primary },
  progressText: { flexDirection: 'row', justifyContent: 'space-between', fontSize: 14, color: colors.textMuted },
  progressPercent: { fontSize: 14, color: colors.textMuted },
  progressStage: { fontSize: 14, color: colors.textMuted },
  stagesList: { marginTop: spacing.lg },
  stageItem: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, padding: spacing.md, backgroundColor: colors.bgSection, borderRadius: 6, marginBottom: spacing.sm },
  stageIcon: { fontSize: 20 },
  stageContent: { flex: 1 },
  stageName: { fontWeight: '600', marginBottom: 2 },
  stageStatus: { fontSize: 14, color: colors.textMuted },
  stageCheck: { fontSize: 16 },
});
