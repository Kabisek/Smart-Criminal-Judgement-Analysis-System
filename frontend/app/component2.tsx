import {
  View,
  Text,
  Pressable,
  StyleSheet,
  Platform,
  TextInput,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import * as DocumentPicker from 'expo-document-picker';
import { Layout } from '../components/Layout';
import { Container, Card, PageHeader } from '../components/ui';
import { useComp2 } from '../components/Comp2Context';
import { colors, spacing } from '../theme';
import React, { useState, useEffect } from 'react';
import { fetchComp2List, fetchComp2Detail, HistorySummary } from '../api';

export default function Component2Screen() {
  const router = useRouter();
  const { file, setFile, setTextInput, clear } = useComp2();

  const [fileName, setFileName] = useState<string | null>(null);
  const [textMode, setTextMode] = useState(false);
  const [text, setText] = useState('');
  const [history, setHistory] = useState<HistorySummary[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  useEffect(() => {
    loadHistoryList();
  }, []);

  const loadHistoryList = async () => {
    try {
      setLoadingHistory(true);
      const list = await fetchComp2List();
      setHistory(list);
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handlePickDocument = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['application/pdf', 'application/json', 'text/plain'],
        copyToCacheDirectory: true,
      });
      if (!result.canceled && result.assets?.[0]) {
        const asset = result.assets[0];
        setFile({ uri: asset.uri, name: asset.name });
        setFileName(asset.name);
        setTextMode(false);
        setText('');
      }
    } catch (err) {
      Alert.alert('Error', 'Could not pick document.');
    }
  };

  const handleTextReady = () => {
    if (!text.trim()) return;
    setTextInput(text.trim());
    setFile(null);
    setFileName(null);
  };

  const hasInput = !!file || (textMode && text.trim().length > 0);

  const goToAnalysis = () => {
    if (textMode && text.trim()) {
      setTextInput(text.trim());
    }
    router.push('/component2-analysis');
  };

  const goToArguments = () => {
    if (textMode && text.trim()) {
      setTextInput(text.trim());
    }
    router.push('/component2-arguments');
  };

  const handleClear = () => {
    clear();
    setFileName(null);
    setText('');
    setTextMode(false);
  };

  const loadFromHistory = async (caseId: string) => {
    try {
      const detail = await fetchComp2Detail(caseId);
      if (detail?.payload) {
        router.push('/component2-arguments');
      }
    } catch (err) {
      console.error('Failed to load history detail:', err);
    }
  };

  return (
    <Layout>
      <Container>
        <PageHeader
          title="Argument Synthesis Engine"
          breadcrumb="Analytical Tools → Logic Synthesis"
        />

        <View style={styles.row}>
          <View style={styles.mainCol}>
            {/* File Upload Card */}
            <Card title="Upload Case Document" description="Upload a PDF, JSON, or text file to begin analysis.">
              <View style={styles.inputToggle}>
                <Pressable
                  onPress={() => { setTextMode(false); }}
                  style={[styles.toggleBtn, !textMode && styles.toggleBtnActive]}
                >
                  <Text style={[styles.toggleText, !textMode && styles.toggleTextActive]}>Document Upload</Text>
                </Pressable>
                <Pressable
                  onPress={() => { setTextMode(true); }}
                  style={[styles.toggleBtn, textMode && styles.toggleBtnActive]}
                >
                  <Text style={[styles.toggleText, textMode && styles.toggleTextActive]}>Text Entry</Text>
                </Pressable>
              </View>

              {!textMode ? (
                <View style={styles.uploadArea}>
                  <Pressable onPress={handlePickDocument} style={styles.uploadBtn}>
                    <Text style={styles.uploadIcon}>📄</Text>
                    <Text style={styles.uploadLabel}>
                      {fileName ? fileName : 'Choose PDF / JSON / Text file'}
                    </Text>
                  </Pressable>
                  {fileName && (
                    <Text style={styles.fileHint}>
                      File selected. Choose an action below.
                    </Text>
                  )}
                </View>
              ) : (
                <View style={styles.textArea}>
                  <TextInput
                    style={styles.textInput}
                    placeholder="Paste or type case text here..."
                    placeholderTextColor={colors.textMuted}
                    multiline
                    value={text}
                    onChangeText={setText}
                  />
                  {text.trim().length > 0 && (
                    <Text style={styles.fileHint}>
                      Text ready. Choose an action below.
                    </Text>
                  )}
                </View>
              )}

              {(file || fileName) && !textMode && (
                <Pressable onPress={handleClear} style={styles.clearBtn}>
                  <Text style={styles.clearText}>Clear selection</Text>
                </Pressable>
              )}
            </Card>

            {/* Action Buttons */}
            <View style={styles.actionSection}>
              <Text style={styles.actionTitle}>Choose an Action</Text>
              <Text style={styles.actionSubtitle}>
                Select one or both operations to perform on your document.
              </Text>

              <View style={styles.actionRow}>
                <Pressable
                  style={[styles.actionCard, !hasInput && styles.actionCardDisabled]}
                  onPress={hasInput ? goToAnalysis : undefined}
                >
                  <View style={[styles.actionIconWrap, { backgroundColor: '#EDE9FE' }]}>
                    <Text style={styles.actionIconText}>🔍</Text>
                  </View>
                  <Text style={styles.actionCardTitle}>Case Analysis</Text>
                  <Text style={styles.actionCardDesc}>
                    Extract structured fields from the document with bounding-box highlighting on the original text.
                  </Text>
                  <View style={[styles.actionBadge, { backgroundColor: '#7C3AED' }]}>
                    <Text style={styles.actionBadgeText}>Analyze</Text>
                  </View>
                </Pressable>

                <Pressable
                  style={[styles.actionCard, !hasInput && styles.actionCardDisabled]}
                  onPress={hasInput ? goToArguments : undefined}
                >
                  <View style={[styles.actionIconWrap, { backgroundColor: '#FEF3C7' }]}>
                    <Text style={styles.actionIconText}>⚖️</Text>
                  </View>
                  <Text style={styles.actionCardTitle}>Generate Arguments</Text>
                  <Text style={styles.actionCardDesc}>
                    Produce strategic arguments, adversarial simulations, and a print-ready report.
                  </Text>
                  <View style={[styles.actionBadge, { backgroundColor: '#B8860B' }]}>
                    <Text style={styles.actionBadgeText}>Generate</Text>
                  </View>
                </Pressable>
              </View>

              {!hasInput && (
                <Text style={styles.hintText}>
                  Upload a document or enter text above to enable these actions.
                </Text>
              )}
            </View>

            {/* Capabilities Info */}
            <Card
              title="Synthesis Capabilities"
              description="This component receives relevant case clusters and synthesizes arguments based on historical legal reasoning."
            >
              <Text style={styles.bullet}>• Provides lawyers with ready-made, structured arguments.</Text>
              <Text style={styles.bullet}>• Saves time by analysing large volumes of case law.</Text>
              <Text style={styles.bullet}>• Enhances decision-making and strengthens case preparation.</Text>
              <Text style={styles.bullet}>• Highlights source text positions for extracted case fields.</Text>
            </Card>
          </View>

          {/* RIGHT SIDEBAR */}
          <View style={styles.sideCol}>
            <Card title="Recent Analyses" style={{ marginTop: spacing.md }}>
              <View style={styles.historyList}>
                {loadingHistory ? (
                  <Text style={styles.noData}>Loading...</Text>
                ) : (history || []).length === 0 ? (
                  <Text style={styles.noData}>No past analyses found.</Text>
                ) : (
                  (history || []).slice(0, 5).map((h, i) => (
                    <Pressable
                      key={i}
                      onPress={() => loadFromHistory(h.case_id)}
                      style={styles.historyItem}
                    >
                      <Text style={styles.historyName}>{h.case_name}</Text>
                      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Text style={styles.historyDate}>{new Date(h.timestamp).toLocaleDateString()}</Text>
                        <Text style={[styles.historyDate, { color: colors.accent, fontWeight: '700' }]}>
                          {h.subject.substring(0, 15)}
                        </Text>
                      </View>
                    </Pressable>
                  ))
                )}
              </View>
              <Pressable style={styles.viewAll} onPress={loadHistoryList}>
                <Text style={styles.viewAllText}>Refresh History</Text>
              </Pressable>
            </Card>
          </View>
        </View>

        <Pressable onPress={() => router.push('/')}>
          <Text style={styles.backLink}>← Back to Home</Text>
        </Pressable>
      </Container>
    </Layout>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: Platform.OS === 'web' ? 'row' : 'column',
    gap: spacing.lg,
    alignItems: 'flex-start',
  },
  mainCol: { flex: 2, minWidth: 0 },
  sideCol: { flex: 1, minWidth: 260 },
  bullet: { color: colors.textSecondary, marginBottom: 8, lineHeight: 22 },
  backLink: { color: colors.primary, fontWeight: '500', marginTop: 8 },

  inputToggle: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: spacing.md,
  },
  toggleBtn: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 8,
    backgroundColor: '#F1F5F9',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    alignItems: 'center',
  },
  toggleBtnActive: {
    backgroundColor: colors.accent,
    borderColor: colors.accent,
  },
  toggleText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textSecondary,
  },
  toggleTextActive: {
    color: '#FFFFFF',
  },

  uploadArea: {
    alignItems: 'center',
    paddingVertical: spacing.lg,
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderStyle: 'dashed' as any,
  },
  uploadBtn: {
    alignItems: 'center',
    gap: 8,
    paddingVertical: 12,
    paddingHorizontal: 24,
  },
  uploadIcon: { fontSize: 36 },
  uploadLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.primary,
  },
  fileHint: {
    fontSize: 12,
    color: colors.accent,
    fontWeight: '600',
    marginTop: 8,
    textAlign: 'center',
  },

  textArea: {
    gap: spacing.sm,
  },
  textInput: {
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 12,
    padding: spacing.md,
    minHeight: 140,
    fontSize: 15,
    color: colors.textPrimary,
    textAlignVertical: 'top',
  },

  clearBtn: {
    alignSelf: 'center',
    marginTop: spacing.sm,
    paddingVertical: 6,
    paddingHorizontal: 16,
  },
  clearText: {
    fontSize: 12,
    color: colors.textMuted,
    fontWeight: '600',
    textDecorationLine: 'underline',
  },

  actionSection: {
    marginVertical: spacing.lg,
  },
  actionTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: colors.primary,
    marginBottom: 4,
  },
  actionSubtitle: {
    fontSize: 13,
    color: colors.textMuted,
    marginBottom: spacing.md,
  },
  actionRow: {
    flexDirection: Platform.OS === 'web' ? 'row' : 'column',
    gap: spacing.md,
  },
  actionCard: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 20,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
    alignItems: 'center',
    gap: 10,
  },
  actionCardDisabled: {
    opacity: 0.45,
  },
  actionIconWrap: {
    width: 56,
    height: 56,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  actionIconText: { fontSize: 28 },
  actionCardTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: colors.primary,
    textAlign: 'center',
  },
  actionCardDesc: {
    fontSize: 12,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 18,
  },
  actionBadge: {
    borderRadius: 20,
    paddingHorizontal: 18,
    paddingVertical: 8,
    marginTop: 4,
  },
  actionBadgeText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '700',
  },
  hintText: {
    textAlign: 'center',
    fontSize: 12,
    color: colors.textMuted,
    fontStyle: 'italic',
    marginTop: spacing.md,
  },

  noData: { color: colors.textMuted, fontStyle: 'italic', textAlign: 'center', padding: 20 },
  historyList: { gap: spacing.sm, marginBottom: spacing.md },
  historyItem: {
    padding: spacing.md,
    backgroundColor: '#F8FAFC',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  historyName: { fontSize: 14, fontWeight: '700', color: colors.primary, marginBottom: 2 },
  historyDate: { fontSize: 12, color: colors.textMuted },
  viewAll: { alignItems: 'center', marginTop: spacing.sm },
  viewAllText: { color: colors.accent, fontWeight: '600', fontSize: 13 },
});
