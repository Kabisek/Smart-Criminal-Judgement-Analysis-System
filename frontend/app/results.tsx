import { useState, useEffect } from 'react';
import { View, Text, StyleSheet, Pressable, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { Layout } from '../components/Layout';
import { Container, Card, PageHeader } from '../components/ui';
import { colors, spacing, typography } from '../theme';
import type { AnalyzedCase, ArgumentsReport } from '../api';

export default function ResultsScreen() {
  const router = useRouter();
  const [tab, setTab] = useState<'analysis' | 'arguments'>('analysis');
  const [stored, setStored] = useState<{ analyzed_case?: AnalyzedCase; arguments_report?: ArgumentsReport } | null>(null);

  useEffect(() => {
    try {
      if (typeof window !== 'undefined' && (window as unknown as { sessionStorage?: Storage }).sessionStorage) {
        const raw = (window as unknown as { sessionStorage: Storage }).sessionStorage.getItem('analysisResult');
        if (raw) setStored(JSON.parse(raw));
      }
    } catch (_) { }
  }, []);

  const analysis = stored?.analyzed_case;
  const report = stored?.arguments_report;
  const header = analysis?.case_header ?? {};
  const timeline = analysis?.incident_timeline ?? {};
  const synthesis = analysis?.argument_synthesis ?? {};
  const similarCases = report?.similar_cases ?? [
    { case_id: '2024_AppealCourt_September_criminal_judgment_1151', similarity: 0.52 },
    { case_id: '2023_AppealCourt_March_criminal_judgment_1166', similarity: 0.5 },
  ];
  const argumentsList = report?.arguments ?? [
    { perspective: 'prosecution', title: 'Precedent Support - Prosecution', content: 'Strong precedent support for prosecution based on similar cases.', strength_score: 0.8, supporting_cases: ['Case-1151', 'Case-1166'] },
    { perspective: 'defense', title: 'Precedent Support - Defense', content: 'Defense finds support in cases with procedural and evidence issues.', strength_score: 0.6, model_extracted_points: ['Evidence chain concerns', 'Witness credibility'] },
  ];

  return (
    <Layout>
      <Container>
        <PageHeader title="Analysis Results" backHref="/component2" />
        <View style={styles.tabs}>
          <Pressable onPress={() => setTab('analysis')} style={[styles.tab, tab === 'analysis' && styles.tabActive]}>
            <Text style={[styles.tabText, tab === 'analysis' && styles.tabTextActive]}>Case Analysis</Text>
          </Pressable>
          <Pressable onPress={() => setTab('arguments')} style={[styles.tab, tab === 'arguments' && styles.tabActive]}>
            <Text style={[styles.tabText, tab === 'arguments' && styles.tabTextActive]}>Arguments Report</Text>
          </Pressable>
        </View>

        <View key={tab} style={styles.cardWrapper}>
          {tab === 'analysis' && (
            <Card title="Case Analysis Report">
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Case Information</Text>
                <View style={styles.infoGrid}>
                  <View style={styles.infoItem}>
                    <Text style={styles.infoLabel}>File Number:</Text>
                    <Text style={styles.infoValue}>{header.file_number ?? '—'}</Text>
                  </View>
                  <View style={styles.infoItem}>
                    <Text style={styles.infoLabel}>Date:</Text>
                    <Text style={styles.infoValue}>{header.date_of_analysis ?? '—'}</Text>
                  </View>
                  <View style={styles.infoItem}>
                    <Text style={styles.infoLabel}>Subject:</Text>
                    <Text style={styles.infoValue}>{header.subject ?? '—'}</Text>
                  </View>
                </View>
              </View>
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Incident Timeline</Text>
                <Text style={styles.sectionText}>
                  {(timeline.what_happened || '') + (timeline.where_it_happened ? ' Where: ' + timeline.where_it_happened : '') || '—'}
                </Text>
              </View>
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Argument Synthesis</Text>
                <View style={[styles.argumentBox, styles.prosecutionBox]}>
                  <Text style={styles.argumentBoxTitle}>Prosecution Logic</Text>
                  {(synthesis.prosecution_logic ?? []).map((item, i) => (
                    <Text key={i} style={styles.argumentItem}>• {item}</Text>
                  ))}
                </View>
                <View style={[styles.argumentBox, styles.defenseBox]}>
                  <Text style={styles.argumentBoxTitle}>Defense Logic</Text>
                  {(synthesis.defense_logic ?? []).map((item, i) => (
                    <Text key={i} style={styles.argumentItem}>• {item}</Text>
                  ))}
                </View>
              </View>
            </Card>
          )}

          {tab === 'arguments' && (
            <>
              <Card title="Similar Cases Found">
                {similarCases.map((c, i) => (
                  <View key={i} style={styles.similarItem}>
                    <View style={styles.caseRank}>
                      <Text style={styles.caseRankText}>#{i + 1}</Text>
                    </View>
                    <View style={styles.caseDetails}>
                      <Text style={styles.caseId}>{c.case_id ?? c.id ?? `Case ${i + 1}`}</Text>
                      <Text style={styles.caseSim}>
                        Similarity: {c.similarity != null ? (c.similarity * 100).toFixed(1) : (c.similarity_score != null ? (c.similarity_score * 100).toFixed(1) : '—')}%
                      </Text>
                    </View>
                  </View>
                ))}
              </Card>
              <Card title="Strategic Arguments">
                <View style={styles.argsGrid}>
                  {argumentsList.map((a, i) => (
                    <View key={i} style={[styles.argumentCard, a.perspective === 'defense' ? styles.argumentCardDefense : styles.argumentCardProsecution]}>
                      <View style={styles.argumentHeader}>
                        <Text style={styles.argumentCardTitle}>{a.title ?? a.perspective ?? 'Argument'}</Text>
                        <View style={styles.scoreBadge}>
                          <Text style={styles.scoreText}>{a.strength_score != null ? a.strength_score.toFixed(2) : '—'}</Text>
                        </View>
                      </View>
                      <Text style={styles.argumentContent}>{a.content ?? ''}</Text>
                      {a.supporting_cases?.length ? (
                        <Text style={styles.supporting}>Supporting Cases: {a.supporting_cases.join(', ')}</Text>
                      ) : null}
                      {a.model_extracted_points?.length ? (
                        <Text style={styles.points}>Model-Extracted Points: {a.model_extracted_points.join('; ')}</Text>
                      ) : null}
                    </View>
                  ))}
                </View>
              </Card>
            </>
          )}
        </View>
      </Container>
    </Layout>
  );
}

const styles = StyleSheet.create({
  tabs: {
    flexDirection: 'row',
    gap: spacing.xs,
    marginBottom: spacing.lg,
    borderBottomWidth: 2,
    borderBottomColor: colors.border
  },
  tab: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    marginBottom: -2,
    borderBottomWidth: 3,
    borderBottomColor: 'transparent',
    ...(Platform.OS === 'web' && { transition: 'all 0.3s ease' }),
  },
  tabActive: { borderBottomColor: colors.primary },
  tabText: { fontSize: 16, color: colors.textSecondary },
  tabTextActive: { color: colors.primary, fontWeight: '600' },
  cardWrapper: {
    opacity: 1,
  },
  section: { marginBottom: spacing.lg, paddingBottom: spacing.md, borderBottomWidth: 1, borderBottomColor: colors.border },
  sectionTitle: { fontSize: 16, fontWeight: '600', color: colors.primary, marginBottom: spacing.sm },
  sectionText: { color: colors.textSecondary, lineHeight: 24 },
  infoGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md },
  infoItem: {},
  infoLabel: { fontWeight: '500', color: colors.textMuted, fontSize: 14 },
  infoValue: { fontSize: 16, color: colors.textPrimary },
  argumentBox: { padding: spacing.md, borderRadius: 6, marginBottom: spacing.md },
  prosecutionBox: { backgroundColor: colors.prosecutionBg, borderLeftWidth: 4, borderLeftColor: colors.prosecution },
  defenseBox: { backgroundColor: colors.defenseBg, borderLeftWidth: 4, borderLeftColor: colors.defense },
  argumentBoxTitle: { fontWeight: '600', marginBottom: spacing.sm },
  argumentItem: { color: colors.textSecondary, marginLeft: spacing.md, marginBottom: 2 },
  similarItem: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, padding: spacing.md, backgroundColor: colors.bgSection, borderRadius: 6, marginBottom: spacing.sm },
  caseRank: { width: 36, height: 36, borderRadius: 18, backgroundColor: colors.primary, alignItems: 'center', justifyContent: 'center' },
  caseRankText: { color: colors.textOnPrimary, fontWeight: '700', fontSize: 14 },
  caseDetails: { flex: 1 },
  caseId: { fontWeight: '600', marginBottom: 2 },
  caseSim: { fontSize: 14, color: colors.textMuted },
  argsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md },
  argumentCard: { flex: 1, minWidth: 280, padding: spacing.md, borderRadius: 10, borderWidth: 2 },
  argumentCardProsecution: { borderColor: colors.prosecution, backgroundColor: colors.prosecutionBg },
  argumentCardDefense: { borderColor: colors.defense, backgroundColor: colors.defenseBg },
  argumentHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: spacing.sm },
  argumentCardTitle: { fontSize: 16, fontWeight: '600', flex: 1 },
  scoreBadge: { backgroundColor: colors.primary, paddingHorizontal: spacing.sm, paddingVertical: 4, borderRadius: 6 },
  scoreText: { color: colors.textOnPrimary, fontSize: 13, fontWeight: '700' },
  argumentContent: { color: colors.textSecondary, marginBottom: spacing.sm },
  supporting: { fontSize: 14, marginTop: spacing.sm },
  points: { fontSize: 14, marginTop: 4 },
});
