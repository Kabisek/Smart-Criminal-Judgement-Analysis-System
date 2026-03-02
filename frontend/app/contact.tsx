import { useState } from 'react';
import { View, Text, TextInput, StyleSheet, Pressable, ScrollView, Linking, KeyboardAvoidingView, Platform } from 'react-native';
import { Layout } from '../components/Layout';
import { Container, Card, PageHeader, Button } from '../components/ui';
import { colors, typography, spacing } from '../theme';

const REGISTRY_CONTACTS = [
  { office: 'Main Registry', phone: '+94 11 243 5501', hours: '8:30 AM - 4:15 PM' },
  { office: 'Research Division', phone: '+94 11 243 5505', hours: '9:00 AM - 3:00 PM' },
];

export default function ContactScreen() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [sent, setSent] = useState(false);

  const submit = () => {
    if (!name.trim() || !email.trim()) return;
    setSent(true);
    setName('');
    setEmail('');
    setMessage('');
  };

  return (
    <Layout>
      <Container>
        <PageHeader title="Get in Touch" breadcrumb="Home → Connect" />

        <View style={styles.splitRow}>
          <View style={styles.formCol}>
            <Card title="Direct Inquiry" style={styles.formCard}>
              <Text style={styles.formText}>
                Have a technical inquiry or feedback about the system? Our administrative team will route your message accordingly.
              </Text>

              <View style={styles.field}>
                <Text style={styles.label}>Full Name</Text>
                <TextInput
                  value={name}
                  onChangeText={setName}
                  placeholder="Enter your name"
                  style={styles.input}
                  placeholderTextColor={colors.textMuted}
                />
              </View>

              <View style={styles.field}>
                <Text style={styles.label}>Professional Email</Text>
                <TextInput
                  value={email}
                  onChangeText={setEmail}
                  placeholder="name@organization.com"
                  keyboardType="email-address"
                  style={styles.input}
                  placeholderTextColor={colors.textMuted}
                />
              </View>

              <View style={styles.field}>
                <Text style={styles.label}>Message</Text>
                <TextInput
                  value={message}
                  onChangeText={setMessage}
                  placeholder="Describe your inquiry..."
                  multiline
                  numberOfLines={5}
                  style={[styles.input, styles.textArea]}
                  placeholderTextColor={colors.textMuted}
                />
              </View>

              {sent ? (
                <View style={styles.successBox}>
                  <Text style={styles.successText}>Message transmitted successfully. We will respond within 48 hours.</Text>
                </View>
              ) : (
                <Button onPress={submit} style={styles.submitBtn}>Transmit Inquiry</Button>
              )}
            </Card>
          </View>

          <View style={styles.infoCol}>
            <Card title="Practitioner Channels" style={styles.infoCard}>
              <Text style={styles.infoDesc}>Instant access to judicial registries and supportive institutions.</Text>

              {REGISTRY_CONTACTS.map((c, i) => (
                <View key={i} style={styles.contactItem}>
                  <Text style={styles.contactOffice}>{c.office}</Text>
                  <Text style={styles.contactPhone}>{c.phone}</Text>
                  <Text style={styles.contactHours}>{c.hours}</Text>
                </View>
              ))}

              <View style={styles.legalSection}>
                <Text style={styles.legalLabel}>Legal Resources</Text>
                <Pressable onPress={() => Linking.openURL('https://basl.lk')} style={styles.linkRow}>
                  <Text style={styles.linkText}>Bar Association of Sri Lanka (BASL) →</Text>
                </Pressable>
                <Pressable onPress={() => Linking.openURL('https://www.lac.gov.lk')} style={styles.linkRow}>
                  <Text style={styles.linkText}>Legal Aid Commission →</Text>
                </Pressable>
              </View>
            </Card>

            <View style={styles.addressBox}>
              <Text style={styles.addressTitle}>Innovation Hub</Text>
              <Text style={styles.addressText}>Sri Lanka Institute of Information Technology (SLIIT),</Text>
              <Text style={styles.addressText}>New Kandy Road, Malabe, Sri Lanka.</Text>
            </View>
          </View>
        </View>
      </Container>
    </Layout>
  );
}

const styles = StyleSheet.create({
  splitRow: { flexDirection: Platform.OS === 'web' ? 'row' : 'column', gap: spacing.xl },
  formCol: { flex: 1.5 },
  infoCol: { flex: 1 },
  formCard: {
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.05,
    shadowRadius: 20
  },
  formText: { color: colors.textSecondary, marginBottom: spacing.xl, lineHeight: 22 },
  field: { marginBottom: spacing.md },
  label: { fontSize: 13, fontWeight: '700', color: colors.primary, marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 },
  input: {
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 10,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    fontSize: 16,
    color: colors.textPrimary,
    ...(Platform.OS === 'web' && { outlineStyle: 'none' } as any),
  },
  textArea: { minHeight: 150, textAlignVertical: 'top' },
  submitBtn: { width: '100%', marginTop: spacing.md },
  successBox: { backgroundColor: '#F0FDF4', padding: spacing.md, borderRadius: 10, borderWidth: 1, borderColor: '#BBF7D0' },
  successText: { color: '#166534', fontWeight: '600', textAlign: 'center' },
  infoCard: { backgroundColor: colors.bgSection },
  infoDesc: { fontSize: 14, color: colors.textSecondary, marginBottom: spacing.lg, lineHeight: 20 },
  contactItem: { marginBottom: spacing.md, paddingBottom: spacing.md, borderBottomWidth: 1, borderBottomColor: colors.border },
  contactOffice: { fontSize: 13, fontWeight: '800', color: colors.primary, textTransform: 'uppercase' },
  contactPhone: { fontSize: 15, fontWeight: '700', color: colors.accent, marginTop: 2 },
  contactHours: { fontSize: 12, color: colors.textMuted },
  legalSection: { marginTop: spacing.lg },
  legalLabel: { fontSize: 14, fontWeight: 'bold', color: colors.primary, marginBottom: 12 },
  linkRow: { marginBottom: 10 },
  linkText: { color: colors.primary, fontSize: 14, fontWeight: '500', textDecorationLine: 'underline' },
  addressBox: { marginTop: spacing.lg, padding: spacing.lg },
  addressTitle: { fontSize: 16, fontWeight: 'bold', color: colors.primary, marginBottom: 8 },
  addressText: { fontSize: 14, color: colors.textSecondary, lineHeight: 20 },
});
