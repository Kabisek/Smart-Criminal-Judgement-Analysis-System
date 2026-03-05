import React, { useState, useRef } from 'react';
import { View, Text, Pressable, StyleSheet, TextInput, ScrollView, Platform, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { Layout } from '../components/Layout';
import { Container, Card, PageHeader, Button } from '../components/ui';
import { colors, typography, spacing } from '../theme';
import { chatWithComp4 } from '../api';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  lang?: 'en' | 'si' | 'ta';
}

const INITIAL_MESSAGES: Message[] = [
  { id: '1', sender: 'bot', text: 'Hello! I am your Legal Guide. How can I assist you today with Sri Lankan law?', lang: 'en' },
  { id: '2', sender: 'bot', text: 'ආයුබෝවන්! මම ඔබේ නීති උපදේශකයා. ශ්‍රී ලංකාවේ නීතිය පිළිබඳව අද ඔබට මා උදවු කරන්නේ කෙසේද?', lang: 'si' },
  { id: '3', sender: 'bot', text: 'வணக்கம்! நான் உங்கள் சட்ட வழிகாட்டி. இலங்கைச் சட்டத்தில் இன்று நான் உங்களுக்கு எவ்வாறு உதவ முடியும்?', lang: 'ta' },
];

// ── UPDATE to your FastAPI base URL ──────────────────────────────────────────
const API_BASE = 'http://localhost:8000';

export default function Component4Screen() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>(INITIAL_MESSAGES);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollViewRef = useRef<ScrollView>(null);

  // ── SEND MESSAGE (unchanged) ──────────────────────────────────────────────
  const handleSend = async () => {
    if (!inputText.trim()) return;

    const userMsg: Message = { id: Date.now().toString(), text: inputText, sender: 'user' };
    setMessages(prev => [...prev, userMsg]);
    setInputText('');
    setLoading(true);

    try {
      const resp = await chatWithComp4({ message: userMsg.text });

      let replyData = resp.english_data;
      let langLabel: 'en' | 'si' | 'ta' = 'en';

      if (resp.detected_lang === 'si' && resp.sinhala_data) {
        replyData = resp.sinhala_data;
        langLabel = 'si';
      } else if (resp.detected_lang === 'ta' && resp.tamil_data) {
        replyData = resp.tamil_data;
        langLabel = 'ta';
      }

      let botText = '';
      if (replyData.Section && replyData.Section !== 'Not Mentioned') {
        botText += `Section: ${replyData.Section}\n\n`;
      }
      botText += `Explanation: ${replyData.Simple_Explanation || 'N/A'}`;

      if (replyData.Example && replyData.Example !== 'N/A' && replyData.Example !== '-') {
        botText += `\n\nExample: ${replyData.Example}`;
      }
      if (replyData.Punishment && replyData.Punishment !== 'N/A' && replyData.Punishment !== '-') {
        botText += `\n\nPunishment: ${replyData.Punishment}`;
      }
      if (replyData.Next_Steps && replyData.Next_Steps.length > 0) {
        botText += `\n\nNext Steps:\n• ${replyData.Next_Steps.join('\n• ')}`;
      }

      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        text: botText,
        lang: langLabel,
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (error) {
      console.error(error);
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        text: 'Sorry, I encountered an error connecting to the legal database. Please try again later.',
        lang: 'en',
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  // ── NEW: DELETE CHAT ──────────────────────────────────────────────────────
  const handleDeleteChat = () => {
    if (Platform.OS === 'web') {
      if (window.confirm('Clear all chat messages?')) {
        setMessages(INITIAL_MESSAGES);
      }
    } else {
      Alert.alert('Clear Chat', 'Clear all chat messages?', [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Clear', style: 'destructive', onPress: () => setMessages(INITIAL_MESSAGES) },
      ]);
    }
  };

  // ── NEW: CLEAR CACHE ──────────────────────────────────────────────────────
  const handleClearCache = async () => {
    const doIt = async () => {
      try {
        const res = await fetch(`${API_BASE}/comp4/cache`, { method: 'DELETE' });
        if (!res.ok) throw new Error(`Status ${res.status}`);
        const data = await res.json();
        const msg = `Cache cleared — ${data.deleted} entr${data.deleted === 1 ? 'y' : 'ies'} removed.`;
        if (Platform.OS === 'web') {
          window.alert(msg);
        } else {
          Alert.alert('Cache Cleared', msg);
        }
      } catch (e) {
        const errMsg = 'Could not clear cache. Is the API running?';
        if (Platform.OS === 'web') {
          window.alert(errMsg);
        } else {
          Alert.alert('Error', errMsg);
        }
      }
    };

    if (Platform.OS === 'web') {
      if (window.confirm('Clear all cached answers from the server?')) {
        await doIt();
      }
    } else {
      Alert.alert('Clear Cache', 'Clear all cached answers from the server?', [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Clear', style: 'destructive', onPress: doIt },
      ]);
    }
  };

  // ── RENDER (identical to original, two buttons added in infoSideCard) ────
  return (
    <Layout noPadding>
      <Container style={styles.fullContainer}>
        <PageHeader
          title="Public Legal Assistant"
          breadcrumb="Public Access → Multilingual Law Support"
        />

        <View style={styles.chatWrapper}>
          {/* ── CHAT CARD (unchanged) ── */}
          <Card style={styles.chatCard}>
            <ScrollView
              ref={scrollViewRef}
              style={styles.msgScroll}
              onContentSizeChange={() => scrollViewRef.current?.scrollToEnd({ animated: true })}
              contentContainerStyle={styles.msgContent}
            >
              {messages.map((m) => (
                <View
                  key={m.id}
                  style={[styles.msgBubble, m.sender === 'user' ? styles.userBubble : styles.botBubble]}
                >
                  {m.lang && (
                    <Text style={styles.langIndicator}>{m.lang.toUpperCase()}</Text>
                  )}
                  <Text style={[styles.msgText, m.sender === 'user' ? styles.userText : styles.botText]}>
                    {m.text}
                  </Text>
                </View>
              ))}

              {loading && (
                <View style={[styles.msgBubble, styles.botBubble]}>
                  <Text style={styles.botText}>Assistant is typing...</Text>
                </View>
              )}
            </ScrollView>

            <View style={styles.inputArea}>
              <TextInput
                style={styles.input}
                placeholder="Ask a legal question in English, Sinhala, or Tamil..."
                value={inputText}
                onChangeText={setInputText}
                onSubmitEditing={handleSend}
              />
              <Pressable onPress={handleSend} style={styles.sendBtn}>
                <Text style={styles.sendBtnText}>Send</Text>
              </Pressable>
            </View>
          </Card>

          {/* ── SIDE CARD (original content + two new buttons at top) ── */}
          <Card style={styles.infoSideCard}>

            {/* NEW: action buttons */}
            <View style={styles.actionRow}>
              <Pressable style={styles.actionBtn} onPress={handleDeleteChat}>
                <Text style={styles.actionBtnText}>🗑 Delete Chat</Text>
              </Pressable>
              <Pressable style={[styles.actionBtn, styles.actionBtnDanger]} onPress={handleClearCache}>
                <Text style={[styles.actionBtnText, styles.actionBtnTextDanger]}>💥 Clear Cache</Text>
              </Pressable>
            </View>

            {/* original side card content below — unchanged */}
            <Text style={styles.sideTitle}>Help Topics</Text>
            <View style={styles.topicList}>
              <Pressable style={styles.topicItem} onPress={() => setInputText('How to file a police report?')}>
                <Text style={styles.topicText}>📝 How to file a police report?</Text>
              </Pressable>
              <Pressable style={styles.topicItem} onPress={() => setInputText('What is bail?')}>
                <Text style={styles.topicText}>⚖ What is bail?</Text>
              </Pressable>
              <Pressable style={styles.topicItem} onPress={() => setInputText('Fundamental rights in Sri Lanka')}>
                <Text style={styles.topicText}>📜 Fundamental rights</Text>
              </Pressable>
            </View>

            <Text style={styles.disclaimer}>
              Disclaimer: This AI chatbot provides general legal information, not professional legal advice.
            </Text>
          </Card>
        </View>
      </Container>
    </Layout>
  );
}

const styles = StyleSheet.create({
  // ── original styles (all unchanged) ────────────────────────────────────
  fullContainer: { flex: 1, paddingVertical: spacing.lg },
  chatWrapper: {
    flexDirection: Platform.OS === 'web' ? 'row' : 'column',
    gap: spacing.lg,
    flex: 1,
  },
  chatCard: {
    flex: 3,
    height: Platform.OS === 'web' ? 600 : 500,
    padding: 0,
    overflow: 'hidden',
  },
  infoSideCard: { flex: 1, padding: spacing.lg },
  msgScroll: { flex: 1, backgroundColor: '#F9FAFB' },
  msgContent: { padding: spacing.md },
  msgBubble: {
    maxWidth: '85%',
    padding: 12,
    borderRadius: 12,
    marginBottom: spacing.md,
  },
  botBubble: {
    alignSelf: 'flex-start',
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: colors.primary,
  },
  msgText: { fontSize: 15, lineHeight: 22 },
  botText: { color: colors.textPrimary },
  userText: { color: '#FFFFFF' },
  langIndicator: {
    fontSize: 10,
    fontWeight: 'bold',
    color: colors.accent,
    marginBottom: 4,
    opacity: 0.8,
  },
  inputArea: {
    flexDirection: 'row',
    padding: spacing.md,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    alignItems: 'center',
    gap: spacing.sm,
  },
  input: {
    flex: 1,
    height: 48,
    backgroundColor: '#F3F4F6',
    borderRadius: 24,
    paddingHorizontal: 16,
    fontSize: 15,
    ...(Platform.OS === 'web' ? { outlineWidth: 0 } : {}),
  },
  sendBtn: {
    backgroundColor: colors.primary,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
  },
  sendBtnText: { color: '#FFFFFF', fontWeight: 'bold' },
  sideTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.primary,
    marginBottom: spacing.md,
  },
  topicList: { gap: spacing.sm },
  topicItem: {
    padding: 12,
    backgroundColor: colors.bgSection,
    borderRadius: 8,
  },
  topicText: { fontSize: 14, color: colors.textPrimary },
  disclaimer: {
    fontSize: 11,
    color: colors.textMuted,
    marginTop: spacing.xl,
    fontStyle: 'italic',
  },

  // ── NEW styles for the two buttons only ─────────────────────────────────
  actionRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  actionBtn: {
    flex: 1,
    paddingVertical: 9,
    borderRadius: 8,
    backgroundColor: colors.bgSection,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    alignItems: 'center',
  },
  actionBtnDanger: {
    backgroundColor: '#FEF2F2',
    borderColor: '#FECACA',
  },
  actionBtnText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  actionBtnTextDanger: {
    color: '#DC2626',
  },
});