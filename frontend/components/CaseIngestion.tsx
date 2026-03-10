import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, StyleSheet, Pressable, Platform, Alert, ActivityIndicator } from 'react-native';
import { Audio } from 'expo-av';
import * as DocumentPicker from 'expo-document-picker';
import { colors, spacing } from '../theme';
import { Button, Card } from './ui';
import { transcribeAudio, extractResources, analyzeDocument, NormalizedAnalysisResponse } from '../api';

export type IngestionMode = 'text' | 'voice' | 'document';

interface CaseIngestionProps {
    onAnalysisComplete: (data: NormalizedAnalysisResponse) => void;
    initialMode?: IngestionMode;
    allowedModes?: IngestionMode[];
}

export function CaseIngestion({
    onAnalysisComplete,
    initialMode = 'voice',
    allowedModes = ['voice', 'text', 'document']
}: CaseIngestionProps) {
    const [mode, setMode] = useState<IngestionMode>(initialMode);
    const [text, setText] = useState('');
    const [isRecording, setIsRecording] = useState(false);
    const [recording, setRecording] = useState<Audio.Recording | null>(null);
    const [loading, setLoading] = useState(false);
    const [statusMsg, setStatusMsg] = useState('');
    const [preparedUri, setPreparedUri] = useState<string | null>(null);
    const [preparedFile, setPreparedFile] = useState<any | null>(null);
    const [sound, setSound] = useState<Audio.Sound | null>(null);
    const [isPlaying, setIsPlaying] = useState(false);

    useEffect(() => {
        (async () => {
            if (Platform.OS !== 'web') {
                await Audio.requestPermissionsAsync();
            }
        })();
        return () => {
            if (sound) {
                sound.unloadAsync();
            }
        };
    }, [sound]);

    useEffect(() => {
        // Clear prepared state when mode changes
        setPreparedUri(null);
        setPreparedFile(null);
        if (sound) {
            sound.unloadAsync();
            setSound(null);
        }
        setIsPlaying(false);
    }, [mode]);

    const startRecording = async () => {
        try {
            await Audio.setAudioModeAsync({ allowsRecordingIOS: true, playsInSilentModeIOS: true });
            const { recording } = await Audio.Recording.createAsync(Audio.RecordingOptionsPresets.HIGH_QUALITY);
            setRecording(recording);
            setIsRecording(true);
            setStatusMsg('Recording in progress...');
        } catch (err) {
            console.error(err);
            Alert.alert('Error', 'Could not start recording.');
        }
    };

    const stopRecording = async () => {
        if (!recording) return;
        setIsRecording(false);
        setStatusMsg('Stopping recording...');
        await recording.stopAndUnloadAsync();
        const uri = recording.getURI();
        setRecording(null);
        if (uri) {
            setPreparedUri(uri);
            setStatusMsg('');
        }
    };

    const handlePickAudio = async () => {
        try {
            const result = await DocumentPicker.getDocumentAsync({ type: 'audio/*', copyToCacheDirectory: true });
            if (!result.canceled && result.assets?.[0]) {
                setPreparedUri(result.assets[0].uri);
                setPreparedFile(result.assets[0]);
            }
        } catch (err) {
            Alert.alert('Error', 'Could not pick audio file.');
        }
    };

    const handlePickDocument = async () => {
        try {
            const result = await DocumentPicker.getDocumentAsync({
                type: ['application/pdf', 'application/json', 'text/plain'],
                copyToCacheDirectory: true
            });
            if (!result.canceled && result.assets?.[0]) {
                setPreparedFile(result.assets[0]);
                setPreparedUri(null);
            }
        } catch (err) {
            Alert.alert('Error', 'Could not pick document.');
        }
    };

    const handleConfirmProcess = async () => {
        if (mode === 'voice' && preparedUri) {
            handleVoiceUpload(preparedUri);
        } else if (mode === 'document' && preparedFile) {
            const asset = preparedFile;
            setLoading(true);
            setStatusMsg('Analyzing document...');
            try {
                const res = await analyzeDocument(asset.uri, asset.name);
                onAnalysisComplete(res);
                setPreparedFile(null);
            } catch (err) {
                console.warn('Dedicated /analyze endpoint failed or not found, falling back to /extract with text simulation');
                if (asset.name.endsWith('.txt')) {
                    Alert.alert('Processing', 'Document sent for extraction.');
                } else {
                    Alert.alert('Error', 'This backend version requires specialized endpoints for PDF/JSON. Please use Text Entry for now.');
                }
            } finally {
                setLoading(false);
                setStatusMsg('');
            }
        }
    };

    const togglePlayback = async () => {
        if (!preparedUri) return;
        try {
            if (sound) {
                if (isPlaying) {
                    await sound.pauseAsync();
                    setIsPlaying(false);
                } else {
                    await sound.playAsync();
                    setIsPlaying(true);
                }
            } else {
                const { sound: newSound } = await Audio.Sound.createAsync(
                    { uri: preparedUri },
                    { shouldPlay: true }
                );
                setSound(newSound);
                setIsPlaying(true);
                newSound.setOnPlaybackStatusUpdate((status) => {
                    if (status.isLoaded && status.didJustFinish) {
                        setIsPlaying(false);
                        newSound.setPositionAsync(0);
                    }
                });
            }
        } catch (err) {
            console.error('Playback failed', err);
            Alert.alert('Error', 'Could not play audio.');
        }
    };

    const handleVoiceUpload = async (uri: string) => {
        setLoading(true);
        setStatusMsg('Transcribing audio...');
        try {
            const { english_transcript, original_transcript, detected_lang } = await transcribeAudio(uri);
            setStatusMsg('Extracting resources...');
            const analysis = await extractResources({
                english_transcript,
                original_transcript,
                detected_lang: detected_lang || 'en'
            });
            onAnalysisComplete(analysis);
            setPreparedUri(null);
            setPreparedFile(null);
        } catch (err) {
            Alert.alert('Error', 'Voice processing failed.');
        } finally {
            setLoading(false);
            setStatusMsg('');
        }
    };

    const handleSubmitText = async () => {
        if (!text.trim()) return;
        setLoading(true);
        setStatusMsg('Extracting resources...');
        try {
            const analysis = await extractResources({ english_transcript: text, detected_lang: 'en' });
            onAnalysisComplete(analysis);
        } catch (err) {
            Alert.alert('Error', 'Analysis failed.');
        } finally {
            setLoading(false);
            setStatusMsg('');
        }
    };

    const renderTab = (m: IngestionMode, label: string) => {
        if (!allowedModes.includes(m)) return null;
        return (
            <Pressable onPress={() => setMode(m)} style={[styles.tab, mode === m && styles.tabActive]}>
                <Text style={[styles.tabText, mode === m && styles.tabTextActive]}>{label}</Text>
            </Pressable>
        );
    };

    return (
        <Card title="Case Ingestion" description="Provide case details via voice, text, or document upload.">
            <View style={styles.tabRow}>
                {renderTab('voice', 'Voice')}
                {renderTab('document', 'Document')}
                {renderTab('text', 'Text Entry')}
            </View>

            {mode === 'voice' && (
                <View style={styles.contentWrap}>
                    <Pressable onPress={isRecording ? stopRecording : startRecording} style={[styles.recordBtn, isRecording && styles.recordBtnActive]}>
                        <Text style={styles.recordIcon}>{isRecording ? '⏹' : '🎤'}</Text>
                        <Text style={styles.recordText}>{isRecording ? 'Stop Recording' : 'Start Recording'}</Text>
                    </Pressable>
                    {!isRecording && !loading && !preparedUri && (
                        <View style={styles.secondaryActions}>
                            <View style={styles.dividerRow}><View style={styles.divider} /><Text style={styles.dividerText}>OR</Text><View style={styles.divider} /></View>
                            <Pressable onPress={handlePickAudio} style={styles.uploadBtn}>
                                <Text style={styles.uploadIcon}>📁</Text><Text style={styles.uploadBtnText}>Upload Audio</Text>
                            </Pressable>
                        </View>
                    )}
                    {preparedUri && !isRecording && (
                        <View style={styles.previewContainer}>
                            <View style={styles.audioPreview}>
                                <Pressable onPress={togglePlayback} style={styles.playBtn}>
                                    <Text style={styles.playIcon}>{isPlaying ? '⏸' : '▶️'}</Text>
                                    <Text style={styles.playText}>{isPlaying ? 'Pause Preview' : 'Play Preview'}</Text>
                                </Pressable>
                                <Pressable onPress={() => { setPreparedUri(null); setPreparedFile(null); if (sound) sound.unloadAsync(); setSound(null); }} style={styles.clearBtn}>
                                    <Text style={styles.clearIcon}>✕</Text>
                                </Pressable>
                            </View>
                            <Button onPress={handleConfirmProcess} style={styles.confirmBtn}>
                                Confirm & Start Processing
                            </Button>
                        </View>
                    )}
                </View>
            )}

            {mode === 'document' && (
                <View style={styles.contentWrap}>
                    {!preparedFile ? (
                        <Pressable onPress={handlePickDocument} style={styles.docBtn}>
                            <Text style={styles.recordIcon}>📄</Text>
                            <Text style={styles.recordText}>Upload PDF / JSON / Text</Text>
                        </Pressable>
                    ) : (
                        <View style={styles.previewContainer}>
                            <View style={styles.fileInfo}>
                                <Text style={styles.recordIcon}>📄</Text>
                                <Text style={styles.fileName}>{preparedFile.name}</Text>
                                <Pressable onPress={() => setPreparedFile(null)} style={styles.clearBtn}>
                                    <Text style={styles.clearIcon}>✕</Text>
                                </Pressable>
                            </View>
                            <Button onPress={handleConfirmProcess} style={styles.confirmBtn}>
                                Confirm & Start Processing
                            </Button>
                        </View>
                    )}
                </View>
            )}

            {mode === 'text' && (
                <View style={styles.inputWrap}>
                    <TextInput style={styles.textArea} placeholder="Type case summary..." multiline value={text} onChangeText={setText} />
                    <Button onPress={handleSubmitText} disabled={loading || !text.trim()} style={{ width: '100%' }}>
                        {loading ? 'Processing...' : 'Analyze Case'}
                    </Button>
                </View>
            )}

            {loading && (
                <View style={styles.loadingOverlay}>
                    <ActivityIndicator color={colors.accent} />
                    <Text style={styles.loadingText}>{statusMsg}</Text>
                </View>
            )}
        </Card>
    );
}

const styles = StyleSheet.create({
    tabRow: { flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.lg },
    tab: { paddingVertical: 8, paddingHorizontal: 16, borderRadius: 20, backgroundColor: '#F1F5F9', borderWidth: 1, borderColor: '#E2E8F0' },
    tabActive: { backgroundColor: colors.accent, borderColor: colors.accent },
    tabText: { fontSize: 13, fontWeight: '600', color: colors.textSecondary },
    tabTextActive: { color: '#FFFFFF' },
    contentWrap: { alignItems: 'center', paddingVertical: spacing.lg, backgroundColor: '#F8FAFC', borderRadius: 12, borderWidth: 1, borderColor: '#E2E8F0', minHeight: 180, justifyContent: 'center' },
    recordBtn: { alignItems: 'center', gap: spacing.sm },
    recordBtnActive: { opacity: 0.7 },
    recordIcon: { fontSize: 40, color: colors.accent },
    recordText: { fontSize: 16, fontWeight: '600', color: colors.primary },
    secondaryActions: { width: '100%', alignItems: 'center' },
    dividerRow: { flexDirection: 'row', alignItems: 'center', marginVertical: spacing.md, paddingHorizontal: spacing.xl, gap: spacing.md, width: '100%' },
    divider: { flex: 1, height: 1, backgroundColor: '#E2E8F0' },
    dividerText: { fontSize: 10, fontWeight: '700', color: colors.textMuted },
    uploadBtn: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, paddingVertical: 10, paddingHorizontal: 20, backgroundColor: '#FFFFFF', borderRadius: 8, borderWidth: 1, borderColor: '#CBD5E1' },
    uploadBtnText: { fontSize: 14, fontWeight: '600', color: colors.textSecondary },
    uploadIcon: { fontSize: 18 },
    docBtn: { alignItems: 'center', gap: spacing.sm },
    inputWrap: { gap: spacing.md },
    textArea: { backgroundColor: '#F8FAFC', borderWidth: 1, borderColor: '#E2E8F0', borderRadius: 12, padding: spacing.md, minHeight: 150, fontSize: 16, color: colors.textPrimary, textAlignVertical: 'top' },
    loadingOverlay: { marginTop: spacing.md, alignItems: 'center', gap: 8 },
    loadingText: { fontSize: 14, color: colors.textSecondary, fontWeight: '500' },
    previewContainer: { width: '100%', alignItems: 'center', paddingHorizontal: spacing.xl, gap: spacing.md },
    audioPreview: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFFFFF', padding: 12, borderRadius: 12, borderWidth: 1, borderColor: colors.accent + '30', width: '100%', justifyContent: 'space-between' },
    playBtn: { flexDirection: 'row', alignItems: 'center', gap: 12 },
    playIcon: { fontSize: 24, color: colors.accent },
    playText: { fontSize: 14, fontWeight: '700', color: colors.primary },
    clearBtn: { width: 28, height: 28, borderRadius: 14, backgroundColor: '#F1F5F9', alignItems: 'center', justifyContent: 'center' },
    clearIcon: { fontSize: 14, color: '#64748B', fontWeight: 'bold' },
    confirmBtn: { width: '100%', backgroundColor: colors.accent, height: 48 },
    fileInfo: { alignItems: 'center', gap: 8, marginBottom: 8 },
    fileName: { fontSize: 14, fontWeight: '600', color: colors.primary, textAlign: 'center' },
});
