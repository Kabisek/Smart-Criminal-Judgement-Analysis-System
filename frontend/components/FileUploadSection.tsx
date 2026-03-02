import { useState, useCallback } from 'react';
import { View, Text, Pressable, StyleSheet, Alert, Platform } from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import { Button } from './ui';
import { colors, spacing, typography } from '../theme';
import { uploadAndAnalyze } from '../api';

const ALLOWED = ['.pdf', '.txt', '.json', '.docx'];
const MAX_MB = 10;

function formatSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + ['B', 'KB', 'MB', 'GB'][i];
}

export function FileUploadSection({ onStartAnalysis }: { onStartAnalysis: () => void }) {
  const [file, setFile] = useState<{ name: string; size: number; uri: string } | null>(null);
  const [loading, setLoading] = useState(false);

  const pick = useCallback(async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['application/pdf', 'text/plain', 'application/json', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
        copyToCacheDirectory: true,
      });
      if (result.canceled) return;
      const f = result.assets[0];
      const ext = '.' + (f.name?.split('.').pop() || '').toLowerCase();
      if (!ALLOWED.includes(ext)) {
        Alert.alert('Invalid file', 'Please upload a PDF, TXT, JSON, or DOCX file.');
        return;
      }
      if (f.size && f.size > MAX_MB * 1024 * 1024) {
        Alert.alert('File too large', `File size must be less than ${MAX_MB}MB.`);
        return;
      }
      setFile({ name: f.name, size: f.size || 0, uri: f.uri });
    } catch (e) {
      Alert.alert('Error', 'Could not pick file.');
    }
  }, []);

  const start = useCallback(async () => {
    if (!file) {
      Alert.alert('No file', 'Please select a file first.');
      return;
    }
    setLoading(true);
    try {
      // On native we have a URI; for real API we'd need to send multipart from URI.
      // For web we could use File from input. For demo we store pending and go to processing.
      if (typeof window !== 'undefined' && (window as unknown as { sessionStorage?: Storage }).sessionStorage) {
        (window as unknown as { sessionStorage: Storage }).sessionStorage.setItem('uploadFileName', file.name);
        (window as unknown as { sessionStorage: Storage }).sessionStorage.setItem('uploadFileSize', String(file.size));
      }
      // Try real API on web when we have File (from a file input). For now use demo flow.
      onStartAnalysis();
    } catch (e) {
      Alert.alert('Error', 'Analysis could not be started.');
    } finally {
      setLoading(false);
    }
  }, [file, onStartAnalysis]);

  return (
    <View style={styles.wrap}>
      <Pressable onPress={pick} style={({ pressed }) => [styles.uploadArea, pressed && styles.uploadAreaPressed]}>
        <Text style={styles.uploadIcon}>📄</Text>
        <Text style={styles.uploadText}>Tap to choose a file</Text>
        <Text style={styles.uploadSub}>PDF, TXT, JSON, DOCX (max {MAX_MB}MB)</Text>
      </Pressable>
      {file ? (
        <View style={styles.fileInfo}>
          <View style={styles.fileRow}>
            <Text style={styles.fileName}>{file.name}</Text>
            <Text style={styles.fileSize}>{formatSize(file.size)}</Text>
          </View>
          <Button onPress={start} disabled={loading}>
            {loading ? 'Starting…' : 'Start Analysis'}
          </Button>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { marginTop: spacing.sm },
  uploadArea: {
    borderWidth: 2,
    borderStyle: 'dashed',
    borderColor: colors.primary,
    borderRadius: 10,
    paddingVertical: spacing.lg,
    paddingHorizontal: spacing.xl,
    alignItems: 'center',
    backgroundColor: colors.accentMuted,
  },
  uploadAreaPressed: { opacity: 0.9 },
  uploadIcon: { fontSize: 40, marginBottom: spacing.sm },
  uploadText: { fontSize: 16, fontWeight: '600', color: colors.textPrimary },
  uploadSub: { fontSize: 14, color: colors.textMuted, marginTop: 4 },
  fileInfo: { marginTop: spacing.md, paddingTop: spacing.md, borderTopWidth: 1, borderTopColor: colors.border },
  fileRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.md },
  fileName: { fontWeight: '600', flex: 1 },
  fileSize: { fontSize: 14, color: colors.textMuted },
});
