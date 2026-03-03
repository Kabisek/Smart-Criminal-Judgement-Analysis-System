import { View, Text, Pressable, StyleSheet, ScrollView, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { Layout } from '../components/Layout';
import { Container, Card, PageHeader } from '../components/ui';
import { colors, typography, spacing } from '../theme';
import React, { useState, useEffect } from 'react';
import { CaseIngestion } from '../components/CaseIngestion';
import { NormalizedAnalysisResponse, saveComp1History, fetchComp1List, fetchComp1Detail, HistorySummary } from '../api';

const CLUSTERS = [
  { id: '1', title: 'Theft & Burglaries', cases: 1240, tags: ['Penal Code 367', 'Burglary', 'Night-time'], icon: '🏠' },
  { id: '2', title: 'Assault & Personal Injury', cases: 850, tags: ['Section 314', 'Grievous Hurt', 'Weaponry'], icon: '⚔' },
  { id: '3', title: 'Financial Fraud', cases: 520, tags: ['Cheating', 'Forgery', 'Money Laundering'], icon: '💰' },
  { id: '4', title: 'Cyber Crimes', cases: 310, tags: ['CMA 2007', 'Harassment', 'Data Theft'], icon: '💻' },
];

export default function Component1Screen() {
  const router = useRouter();
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<NormalizedAnalysisResponse | null>(null);
  const [transcriptView, setTranscriptView] = useState<'original' | 'english'>('english');
  const [expandedHubs, setExpandedHubs] = useState<string[]>([]);
  const [selectedResourceId, setSelectedResourceId] = useState<string | null>(null);
  const [history, setHistory] = useState<HistorySummary[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  useEffect(() => {
    loadHistoryList();
  }, []);

  const loadHistoryList = async () => {
    try {
      setLoadingHistory(true);
      const list = await fetchComp1List();
      setHistory(list);
    } catch (err) {
      console.error('History fetch failed:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  const loadFromHistory = async (caseId: string) => {
    try {
      const detail = await fetchComp1Detail(caseId);
      if (detail?.payload) {
        const p = detail.payload;
        // Re-hydrate the full NormalizedAnalysisResponse from the stored payload
        setAnalysisResult({
          status: 'success',
          analyzed_case: p.analyzed_case,
          arguments_report: p.arguments_report,
          input_metadata: p.input_metadata,
          data: p.data || {
            summary: p.analyzed_case?.incident_timeline?.what_happened || '',
            structured_data: {
              prosecution_resources: p.analyzed_case?.argument_synthesis?.prosecution_logic?.map((s: string) => ({ title: s })),
              defense_resources: p.analyzed_case?.argument_synthesis?.defense_logic?.map((s: string) => ({ title: s })),
            }
          }
        });
        // Auto-select the first category
        const sd = p.data?.structured_data || {};
        const firstCat = Object.keys(sd)[0];
        if (firstCat) setSelectedCategory(firstCat);
      }
    } catch (err) {
      console.error('Failed to load history record:', err);
    }
  };

  const toggleHub = (cat: string) => {
    setExpandedHubs(prev =>
      prev.includes(cat) ? prev.filter(h => h !== cat) : [...prev, cat]
    );
    setSelectedCategory(cat);
  };

  const onAnalysisComplete = async (data: NormalizedAnalysisResponse) => {
    setAnalysisResult(data);
    // Auto-select the first available category in structured_data
    if (data.data?.structured_data) {
      const firstCat = Object.keys(data.data.structured_data)[0];
      if (firstCat) setSelectedCategory(firstCat);
    }

    // Auto-save to MongoDB (Component 1 collection only)
    try {
      const ac = data.analyzed_case;
      const doc = ac?.analyzed_case_file || ac;
      const textSnippet = data.input_metadata?.analyzed_text?.trim().substring(0, 45);
      const langLabel = data.input_metadata?.language ? `[${data.input_metadata.language}]` : '';
      await saveComp1History({
        case_id: `C1_${doc?.case_header?.file_number || Date.now()}`,
        case_name: doc?.case_header?.subject ||
          (textSnippet ? `${langLabel} ${textSnippet}…` : `Extraction ${new Date().toLocaleTimeString()}`),
        payload: {
          analyzed_case: ac,
          data: data.data,
          input_metadata: data.input_metadata,
        },
        subject: doc?.case_header?.subject || data.input_metadata?.language || 'N/A',
        accused: doc?.parties_and_roles?.accused || 'N/A',
      });
      loadHistoryList();
    } catch (err) {
      console.error('Failed to auto-save comp1 history:', err);
    }
  };

  const getCategoryColor = (cat: string) => {
    const lowers = cat.toLowerCase();
    if (lowers.includes('prosecution')) return '#EF4444';
    if (lowers.includes('defense')) return '#10B981';
    if (lowers.includes('procedure')) return '#3B82F6';
    if (lowers.includes('precedent') || lowers.includes('landmark')) return '#F59E0B';
    if (lowers.includes('recent')) return '#F59E0B'; // Orange-ish for judgments
    return '#6366F1'; // Indigo for others
  };

  const getCategoryIcon = (cat: string) => {
    const icons: Record<string, string> = {
      statutory_provisions: '📜',
      landmark_cases: '📚',
      binding_precedents: '🏛️',
      procedural_resources: '⚖️',
      defense_resources: '🛡️',
      prosecution_resources: '🗡️',
      recent_judgments: '📂',
      persuasive_authority: '💡',
    };
    return icons[cat.toLowerCase()] || '🔹';
  };

  const formatCategoryName = (cat: string) => {
    if (cat === 'recent_judgments') return 'Persuasive Authority';
    if (cat === 'binding_precedents') return 'Landmark Cases';
    return cat.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  };

  const categories = analysisResult?.data?.structured_data ? [
    'prosecution_resources',
    'defense_resources',
    'procedural_resources',
    'binding_precedents',
    'recent_judgments',
    'statutory_provisions'
  ].filter(key => (analysisResult.data!.structured_data as any)[key]) : [];

  const calculateOverallSimilarity = () => {
    if (!analysisResult?.data?.structured_data) return 0;
    let total = 0;
    let count = 0;
    Object.values(analysisResult.data.structured_data).forEach((arr: any) => {
      if (Array.isArray(arr)) {
        arr.forEach(item => {
          if (item?.similarity != null) {
            total += item.similarity;
            count++;
          }
        });
      }
    });
    return count > 0 ? (total / count) * 100 : 0;
  };

  const overallAccuracy = calculateOverallSimilarity();

  return (
    <Layout>
      <Container>
        <PageHeader
          title="Legal Resource Extractor"
          breadcrumb="Analytical Tools → Resource Extraction"
        />

        <View style={styles.row}>
          <View style={styles.mainCol}>
            <CaseIngestion
              onAnalysisComplete={onAnalysisComplete}
              initialMode="voice"
              allowedModes={['voice', 'text']}
            />

            {analysisResult && (
              <View style={styles.statsRow}>
                <Card style={[styles.statCard, { flex: 1 }]} title="Summary Accuracy">
                  <View style={styles.accuracyCircle}>
                    <Text style={styles.accuracyValue}>{overallAccuracy.toFixed(1)}%</Text>
                    <Text style={styles.accuracyLabel}>Similarity</Text>
                  </View>
                  <Text style={styles.accuracyDesc}>Average semantic match across all extracted resources.</Text>
                </Card>
                <Card style={[styles.statCard, { flex: 1 }]} title="Resource Audit">
                  <Text style={styles.auditMain}>{analysisResult?.data?.structured_data ? Object.values(analysisResult.data.structured_data).flat().length : 0}</Text>
                  <Text style={styles.auditSub}>Legal nodes identified</Text>
                  <View style={styles.auditGrid}>
                    {categories.slice(0, 4).map(cat => (
                      <View key={cat} style={styles.auditItem}>
                        <View style={[styles.auditDot, { backgroundColor: getCategoryColor(cat) }]} />
                        <Text style={styles.auditText}>{formatCategoryName(cat).split(' ')[0]}</Text>
                      </View>
                    ))}
                  </View>
                </Card>
              </View>
            )}

            {analysisResult && (
              <Card style={styles.transcriptCard} title="Transcription Evidence">
                <View style={styles.transcriptToggle}>
                  <Pressable
                    onPress={() => setTranscriptView('english')}
                    style={[styles.toggleBtn, transcriptView === 'english' && styles.toggleBtnActive]}
                  >
                    <Text style={[styles.toggleText, transcriptView === 'english' && styles.toggleTextActive]}>Legal English</Text>
                  </Pressable>
                  <Pressable
                    onPress={() => setTranscriptView('original')}
                    style={[styles.toggleBtn, transcriptView === 'original' && styles.toggleBtnActive]}
                  >
                    <Text style={[styles.toggleText, transcriptView === 'original' && styles.toggleTextActive]}>Original Transcript</Text>
                  </Pressable>
                </View>
                <View style={styles.transcriptBox}>
                  <Text style={styles.transcriptText}>
                    {transcriptView === 'english'
                      ? analysisResult.input_metadata?.analyzed_text
                      : analysisResult.input_metadata?.original_text || 'No original transcript available.'}
                  </Text>
                  <View style={styles.langTag}>
                    <Text style={styles.langTagText}>Detected: {analysisResult.input_metadata?.language?.toUpperCase() || 'UNKNOWN'}</Text>
                  </View>
                </View>
              </Card>
            )}

            {analysisResult && (() => {
              const sd = analysisResult.data?.structured_data as any;
              const prosecutionItems = sd?.prosecution_resources || [];
              const defenseItems = sd?.defense_resources || [];
              const procedureItems = sd?.procedural_resources || [];
              const precedentItems = sd?.binding_precedents || [];
              const recentItems = sd?.recent_judgments || [];

              const renderResourceList = (items: any[], color: string, cat: string) => (
                items.map((item: any, i: number) => {
                  const itemId = item.id || `${cat}-${i}`;
                  return (
                    <Pressable
                      key={itemId}
                      onPress={() => { setSelectedResourceId(itemId); setSelectedCategory(cat); }}
                      style={[styles.treeItem, { borderLeftColor: color }, selectedResourceId === itemId && styles.treeItemSelected]}
                    >
                      <View style={{ flex: 1 }}>
                        <Text numberOfLines={1} style={styles.treeItemTitle}>{item.title || item.name || 'Resource'}</Text>
                        {item.section ? <Text style={styles.treeItemSub}>§ {item.section}</Text> : null}
                      </View>
                      {item.similarity != null && (
                        <View style={[styles.scoreBadge, { backgroundColor: color }]}>
                          <Text style={styles.scoreBadgeText}>{(item.similarity * 100).toFixed(0)}%</Text>
                        </View>
                      )}
                    </Pressable>
                  );
                })
              );

              return (
                <Card style={styles.graphCard} title="Knowledge Graph — Legal Resource Map">

                  {/* ── ROOT ── */}
                  <View style={styles.zoneRoot}>
                    <View style={styles.zoneRootBadge}>
                      <Text style={styles.zoneRootBadgeText}>⚖</Text>
                    </View>
                    <View>
                      <Text style={styles.zoneRootTitle}>Case Facts</Text>
                      <Text style={styles.zoneRootSub}>Neural-symbolic extraction complete</Text>
                    </View>
                  </View>

                  {/* ── TWO-ZONE ROW ── */}
                  <View style={styles.zoneTwoCol}>

                    {/* LEFT ZONE: Penal Code Resources */}
                    {(prosecutionItems.length > 0 || defenseItems.length > 0) && (
                      <View style={[styles.zoneSection, styles.zoneSectionPenal]}>
                        {/* Zone label */}
                        <View style={styles.zoneLabelRow}>
                          <View style={[styles.zoneLabelDot, { backgroundColor: '#5C2035' }]} />
                          <Text style={[styles.zoneLabel, { color: '#5C2035' }]}>📜 Penal Code Resources</Text>
                        </View>

                        <View style={styles.zoneSideBySide}>
                          {/* Prosecution */}
                          {prosecutionItems.length > 0 && (
                            <View style={styles.zoneColumn}>
                              <Pressable
                                onPress={() => toggleHub('prosecution_resources')}
                                style={[styles.zoneHeader, { backgroundColor: '#8B1A2410', borderColor: '#8B1A24' }]}
                              >
                                <Text style={styles.zoneHeaderIcon}>⚔️</Text>
                                <Text style={[styles.zoneHeaderText, { color: '#6B0F1A' }]}>Prosecution</Text>
                                <View style={[styles.zoneHeaderBadge, { backgroundColor: '#8B1A24' }]}>
                                  <Text style={styles.zoneHeaderBadgeText}>{prosecutionItems.length}</Text>
                                </View>
                                <Text style={[styles.treeChevron, { color: '#8B1A24', marginLeft: 'auto' }]}>
                                  {expandedHubs.includes('prosecution_resources') ? '▲' : '▼'}
                                </Text>
                              </Pressable>
                              {expandedHubs.includes('prosecution_resources') && (
                                <View style={styles.zoneItemList}>
                                  {renderResourceList(prosecutionItems, '#8B1A24', 'prosecution_resources')}
                                </View>
                              )}
                            </View>
                          )}

                          {/* Defense */}
                          {defenseItems.length > 0 && (
                            <View style={styles.zoneColumn}>
                              <Pressable
                                onPress={() => toggleHub('defense_resources')}
                                style={[styles.zoneHeader, { backgroundColor: '#1B5E3010', borderColor: '#1B5E30' }]}
                              >
                                <Text style={styles.zoneHeaderIcon}>🛡️</Text>
                                <Text style={[styles.zoneHeaderText, { color: '#14421F' }]}>Defense</Text>
                                <View style={[styles.zoneHeaderBadge, { backgroundColor: '#1B5E30' }]}>
                                  <Text style={styles.zoneHeaderBadgeText}>{defenseItems.length}</Text>
                                </View>
                                <Text style={[styles.treeChevron, { color: '#1B5E30', marginLeft: 'auto' }]}>
                                  {expandedHubs.includes('defense_resources') ? '▲' : '▼'}
                                </Text>
                              </Pressable>
                              {expandedHubs.includes('defense_resources') && (
                                <View style={styles.zoneItemList}>
                                  {renderResourceList(defenseItems, '#1B5E30', 'defense_resources')}
                                </View>
                              )}
                            </View>
                          )}
                        </View>
                      </View>
                    )}

                    {/* RIGHT ZONE: Case Law */}
                    {(procedureItems.length > 0 || precedentItems.length > 0 || recentItems.length > 0) && (
                      <View style={[styles.zoneSection, styles.zoneSectionLaw]}>
                        <View style={styles.zoneLabelRow}>
                          <View style={[styles.zoneLabelDot, { backgroundColor: '#1B2B48' }]} />
                          <Text style={[styles.zoneLabel, { color: '#1B2B48' }]}>📚 Case Law Resources</Text>
                        </View>

                        <View style={styles.zoneCaseLawStack}>
                          {procedureItems.length > 0 && (
                            <View>
                              <Pressable
                                onPress={() => toggleHub('procedural_resources')}
                                style={[styles.zoneHeader, { backgroundColor: '#1B2B4810', borderColor: '#1B2B48' }]}
                              >
                                <Text style={styles.zoneHeaderIcon}>⚖️</Text>
                                <Text style={[styles.zoneHeaderText, { color: '#1B2B48' }]}>Procedure</Text>
                                <View style={[styles.zoneHeaderBadge, { backgroundColor: '#1B2B48' }]}>
                                  <Text style={styles.zoneHeaderBadgeText}>{procedureItems.length}</Text>
                                </View>
                                <Text style={[styles.treeChevron, { color: '#1B2B48', marginLeft: 'auto' }]}>
                                  {expandedHubs.includes('procedural_resources') ? '▲' : '▼'}
                                </Text>
                              </Pressable>
                              {expandedHubs.includes('procedural_resources') && (
                                <View style={styles.zoneItemList}>
                                  {renderResourceList(procedureItems, '#1B2B48', 'procedural_resources')}
                                </View>
                              )}
                            </View>
                          )}

                          {precedentItems.length > 0 && (
                            <View>
                              <Pressable
                                onPress={() => toggleHub('binding_precedents')}
                                style={[styles.zoneHeader, { backgroundColor: '#B8860B10', borderColor: '#B8860B' }]}
                              >
                                <Text style={styles.zoneHeaderIcon}>🏛️</Text>
                                <Text style={[styles.zoneHeaderText, { color: '#92400E' }]}>Landmark Cases</Text>
                                <View style={[styles.zoneHeaderBadge, { backgroundColor: '#B8860B' }]}>
                                  <Text style={styles.zoneHeaderBadgeText}>{precedentItems.length}</Text>
                                </View>
                                <Text style={[styles.treeChevron, { color: '#B8860B', marginLeft: 'auto' }]}>
                                  {expandedHubs.includes('binding_precedents') ? '▲' : '▼'}
                                </Text>
                              </Pressable>
                              {expandedHubs.includes('binding_precedents') && (
                                <View style={styles.zoneItemList}>
                                  {renderResourceList(precedentItems, '#B8860B', 'binding_precedents')}
                                </View>
                              )}
                            </View>
                          )}

                          {recentItems.length > 0 && (
                            <View>
                              <Pressable
                                onPress={() => toggleHub('recent_judgments')}
                                style={[styles.zoneHeader, { backgroundColor: '#4A3D6B10', borderColor: '#4A3D6B' }]}
                              >
                                <Text style={styles.zoneHeaderIcon}>📂</Text>
                                <Text style={[styles.zoneHeaderText, { color: '#3B2F5A' }]}>Persuasive Authority</Text>
                                <View style={[styles.zoneHeaderBadge, { backgroundColor: '#4A3D6B' }]}>
                                  <Text style={styles.zoneHeaderBadgeText}>{recentItems.length}</Text>
                                </View>
                                <Text style={[styles.treeChevron, { color: '#4A3D6B', marginLeft: 'auto' }]}>
                                  {expandedHubs.includes('recent_judgments') ? '▲' : '▼'}
                                </Text>
                              </Pressable>
                              {expandedHubs.includes('recent_judgments') && (
                                <View style={styles.zoneItemList}>
                                  {renderResourceList(recentItems, '#4A3D6B', 'recent_judgments')}
                                </View>
                              )}
                            </View>
                          )}
                        </View>
                      </View>
                    )}
                  </View>



                  {/* ── Detail Panel ── */}
                  {selectedCategory && (
                    <View style={styles.detailBox}>
                      <View style={[styles.detailHeader, { backgroundColor: getCategoryColor(selectedCategory) + '15', borderLeftColor: getCategoryColor(selectedCategory) }]}>
                        <Text style={[styles.detailTitle, { color: getCategoryColor(selectedCategory) }]}>
                          {formatCategoryName(selectedCategory)}
                        </Text>
                        <Text style={styles.detailCount}>
                          {((analysisResult?.data?.structured_data as any)?.[selectedCategory] || []).length} resources
                        </Text>
                      </View>
                      <View style={styles.itemContainer}>
                        {analysisResult?.data?.structured_data && Array.isArray((analysisResult.data.structured_data as any)[selectedCategory]) ? (
                          (analysisResult.data.structured_data as any)[selectedCategory].map((item: any, idx: number) => {
                            const itemId = item.id || `${selectedCategory}-${idx}`;
                            const isSelected = selectedResourceId === itemId;
                            return (
                              <View key={itemId} style={[styles.resourceItem, isSelected && styles.resourceItemHighlight]}>
                                <View style={[styles.bullet, { backgroundColor: getCategoryColor(selectedCategory) }]} />
                                <View style={{ flex: 1 }}>
                                  <Text style={styles.resourceTitle}>{item.title || item.name || 'Legal Resource'}</Text>
                                  <Text style={styles.resourceText}>
                                    {item.excerpt || item.summary || (typeof item === 'string' ? item : JSON.stringify(item))}
                                  </Text>
                                  <View style={{ flexDirection: 'row', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
                                    {item.section && <Text style={styles.resourceMeta}>§ {item.section}</Text>}
                                    {item.similarity != null && (
                                      <Text style={[styles.resourceMeta, { color: getCategoryColor(selectedCategory) }]}>
                                        Match: {(item.similarity * 100).toFixed(1)}%
                                      </Text>
                                    )}
                                  </View>
                                </View>
                              </View>
                            );
                          })
                        ) : null}
                      </View>
                    </View>
                  )}
                </Card>
              );
            })()}




          </View>

          {analysisResult && (
            <View style={styles.metadataSection}>
              <Card style={styles.infoCard} title="Engine Analysis Metadata">
                <View style={styles.metadataGrid}>
                  <View style={styles.metaItem}>
                    <Text style={styles.metaLabel}>Pipeline</Text>
                    <Text style={styles.metaValue}>Neuro-Symbolic</Text>
                  </View>
                  <View style={styles.metaItem}>
                    <Text style={styles.metaLabel}>Confidence</Text>
                    <Text style={styles.metaValue}>94.2%</Text>
                  </View>
                </View>
              </Card>
            </View>
          )}

          {/* Recent History - always visible */}
          <View style={styles.metadataSection}>
            <Card title="📜 Recent History" style={{ marginTop: spacing.sm }}>
              <View style={{ gap: spacing.sm }}>
                {loadingHistory ? (
                  <Text style={styles.accuracyDesc}>Loading history...</Text>
                ) : (history || []).length === 0 ? (
                  <Text style={styles.accuracyDesc}>No past cases yet. Run an analysis to save one.</Text>
                ) : (
                  (history || []).slice(0, 5).map((h, i) => (
                    <Pressable
                      key={i}
                      onPress={() => loadFromHistory(h.case_id)}
                      style={{
                        padding: spacing.md,
                        backgroundColor: '#F8FAFC',
                        borderRadius: 12,
                        borderWidth: 1,
                        borderColor: '#E2E8F0',
                        borderLeftWidth: 4,
                        borderLeftColor: colors.accent
                      }}
                    >
                      <Text style={{ fontSize: 13, fontWeight: '700', color: colors.primary }}>{h.case_id}</Text>
                      <Text style={{ fontSize: 11, color: colors.textMuted }}>{new Date(h.timestamp).toLocaleDateString()} · {(h.subject || '').substring(0, 25)}</Text>
                    </Pressable>
                  ))
                )}
              </View>
              <Pressable
                onPress={loadHistoryList}
                style={{ marginTop: spacing.md, alignItems: 'center' }}
              >
                <Text style={{ color: colors.accent, fontWeight: '600', fontSize: 13 }}>↻ Refresh</Text>
              </Pressable>
            </Card>
          </View>

          <Pressable onPress={() => router.push('/')} style={styles.bottomNav}>
            <Text style={styles.backLink}>← Back to Analytical Dashboard</Text>
          </Pressable>
        </View>
      </Container >
    </Layout >
  );
}

const styles = StyleSheet.create({
  row: { width: '100%' },
  mainCol: { width: '100%', gap: spacing.xl },
  graphCard: { marginTop: spacing.sm, borderWidth: 0, backgroundColor: 'transparent', boxShadow: 'none' } as any,
  infoCard: { backgroundColor: '#F8FAFC' },
  desc: { color: colors.textSecondary, marginBottom: spacing.xl, lineHeight: 24, fontSize: 16, textAlign: 'center', maxWidth: 800, alignSelf: 'center' },

  // ── Zone-based graph layout ──────────────────────────────
  zoneRoot: {
    flexDirection: 'row', alignItems: 'center', gap: 16,
    backgroundColor: colors.primary,
    borderRadius: 14, paddingVertical: 14, paddingHorizontal: 24,
    marginBottom: 24,
  },
  zoneRootBadge: {
    width: 40, height: 40, borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.15)',
    alignItems: 'center', justifyContent: 'center',
  },
  zoneRootBadgeText: { fontSize: 20 },
  zoneRootTitle: { color: '#FFF', fontWeight: '900', fontSize: 16 },
  zoneRootSub: { color: 'rgba(255,255,255,0.65)', fontSize: 11, marginTop: 2 },

  zoneTwoCol: {
    flexDirection: 'row', gap: 16, alignItems: 'flex-start', flexWrap: 'wrap',
  },
  zoneSection: {
    flex: 1, minWidth: 280,
    borderRadius: 14, padding: 16, borderWidth: 1,
  },
  zoneSectionPenal: {
    backgroundColor: '#FBF7F8', borderColor: '#C8A0A8',
  },
  zoneSectionLaw: {
    backgroundColor: '#F5F7FA', borderColor: '#B8C4D4',
  },

  zoneLabelRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 14 },
  zoneLabelDot: { width: 8, height: 8, borderRadius: 4 },
  zoneLabel: { fontSize: 12, fontWeight: '800', letterSpacing: 0.6, textTransform: 'uppercase' } as any,

  zoneSideBySide: { flexDirection: 'row', gap: 12, flexWrap: 'wrap' },
  zoneColumn: { flex: 1, minWidth: 160 },

  zoneCaseLawStack: { gap: 10 },

  zoneHeader: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    paddingVertical: 10, paddingHorizontal: 14,
    borderRadius: 10, borderWidth: 1.5,
    marginBottom: 6,
  },
  zoneHeaderIcon: { fontSize: 15 },
  zoneHeaderText: { fontSize: 13, fontWeight: '700', flex: 1 },
  zoneHeaderBadge: {
    paddingHorizontal: 8, paddingVertical: 2,
    borderRadius: 8, minWidth: 26, alignItems: 'center',
  },
  zoneHeaderBadgeText: { color: '#FFF', fontSize: 10, fontWeight: '900' },

  zoneItemList: { gap: 6, paddingBottom: 4 },

  // item row (reused from treeItem)
  treeItem: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: '#FFFFFF', borderRadius: 8,
    paddingVertical: 8, paddingHorizontal: 10,
    borderLeftWidth: 3, gap: 10,
    borderWidth: 1, borderColor: '#F1F5F9',
  },
  treeItemSelected: {
    backgroundColor: '#EFF6FF',
    borderColor: 'rgba(99,102,241,0.3)',
  },
  treeItemTitle: { fontSize: 12, fontWeight: '700', color: colors.primary },
  treeItemSub: { fontSize: 10, color: colors.textMuted, marginTop: 1 },

  scoreBadge: {
    paddingHorizontal: 8, paddingVertical: 3,
    borderRadius: 10, minWidth: 38, alignItems: 'center',
  },
  scoreBadgeText: { color: '#FFF', fontSize: 10, fontWeight: '900' },

  treeChevron: { fontSize: 10, fontWeight: '900' },

  detailHeader: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    borderLeftWidth: 4, paddingVertical: 10, paddingHorizontal: 14,
    borderRadius: 8, marginBottom: spacing.lg,
  },
  detailCount: { fontSize: 12, color: colors.textMuted, fontWeight: '700' },
  // ────────────────────────────────────────────────────────


  resourceItemHighlight: {
    backgroundColor: '#F0F9FF',
    borderRadius: 12,
    paddingHorizontal: 8,
    borderWidth: 1,
    borderColor: '#BAE6FD',
  },

  detailBox: {
    marginTop: spacing.xl,
    padding: spacing.lg,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  detailTitle: { fontSize: 18, fontWeight: 'bold', color: colors.primary, marginBottom: spacing.lg },
  itemContainer: { gap: spacing.md },
  resourceItem: { flexDirection: 'row', alignItems: 'flex-start', gap: 12, paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: '#F1F5F9' },
  bullet: { width: 4, height: 30, borderRadius: 2, marginTop: 4 },
  resourceText: { color: colors.textSecondary, lineHeight: 22, fontSize: 14, flex: 1 },

  para: { color: colors.textSecondary, marginBottom: spacing.md, lineHeight: 22, fontSize: 14 },
  resourceTitle: { fontWeight: '700', color: colors.primary, fontSize: 17, marginBottom: 6 },
  resourceMeta: { color: colors.accent, fontSize: 13, fontWeight: '700', marginTop: 8 },
  backLink: { color: colors.primary, fontWeight: '700', fontSize: 15 },
  bottomNav: { marginTop: spacing.xxl, alignSelf: 'center' },

  metadataSection: { marginTop: spacing.xl },
  metadataGrid: { flexDirection: 'row', justifyContent: 'space-around', paddingVertical: spacing.md },
  metaItem: { alignItems: 'center' },
  metaLabel: { fontSize: 12, color: colors.textMuted, fontWeight: '600', marginBottom: 4, textTransform: 'uppercase' },
  metaValue: { fontSize: 14, color: colors.primary, fontWeight: '800' },

  transcriptCard: { marginTop: spacing.sm, borderRadius: 16 },
  transcriptToggle: { flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.md },
  toggleBtn: { paddingVertical: 8, paddingHorizontal: 16, borderRadius: 24, backgroundColor: '#F1F5F9' },
  toggleBtnActive: { backgroundColor: colors.primary },
  toggleText: { fontSize: 13, fontWeight: '700', color: colors.textSecondary },
  toggleTextActive: { color: '#FFFFFF' },
  transcriptBox: { padding: spacing.lg, backgroundColor: '#FAFBFD', borderRadius: 16, borderLeftWidth: 4, borderLeftColor: colors.primary },
  transcriptText: { fontSize: 16, fontStyle: 'italic', color: colors.textPrimary, lineHeight: 28 },
  langTag: { alignSelf: 'flex-end', marginTop: 12, paddingHorizontal: 10, paddingVertical: 4, backgroundColor: '#E2E8F0', borderRadius: 6 },
  langTagText: { fontSize: 11, fontWeight: '800', color: colors.textSecondary },
  statsRow: { flexDirection: 'row', gap: spacing.lg, marginBottom: spacing.lg },
  statCard: { marginBottom: 0 },
  accuracyCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    borderWidth: 6,
    borderColor: colors.accent,
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'center',
    marginVertical: spacing.md,
  },
  accuracyValue: { fontSize: 18, fontWeight: 'bold', color: colors.primary },
  accuracyLabel: { fontSize: 10, color: colors.textMuted, marginTop: -2 },
  accuracyDesc: { fontSize: 13, color: colors.textMuted, textAlign: 'center', paddingHorizontal: spacing.sm },
  auditMain: { fontSize: 32, fontWeight: 'bold', color: colors.primary, textAlign: 'center', marginTop: spacing.sm },
  auditSub: { fontSize: 14, color: colors.textMuted, textAlign: 'center', marginBottom: spacing.md },
  auditGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, justifyContent: 'center' },
  auditItem: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  auditDot: { width: 8, height: 8, borderRadius: 4 },
  auditText: { fontSize: 12, color: colors.textPrimary },
});
