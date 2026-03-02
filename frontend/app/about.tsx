import { View, Text, StyleSheet, Platform, ScrollView } from 'react-native';
import { Layout } from '../components/Layout';
import { Container, Card, PageHeader } from '../components/ui';
import { colors, typography, spacing } from '../theme';

export default function AboutScreen() {
  return (
    <Layout noPadding>
      <ScrollView style={styles.scroll}>
        <View style={styles.hero}>
          <Container>
            <Text style={styles.heroTag}>OUR VISION</Text>
            <Text style={styles.heroTitle}>Pioneering Legal AI for the Sri Lankan Justice System</Text>
            <Text style={styles.heroSub}>
              Bridging the gap between historical precedent and modern efficiency through high-dimensional semantic analysis.
            </Text>
          </Container>
        </View>

        <Container style={styles.content}>
          <View style={styles.sectionRow}>
            <View style={styles.textBlock}>
              <Text style={styles.sectionHeading}>The Mission</Text>
              <Text style={styles.para}>
                The Smart Criminal Judgment Analysis System is a flagship research initiative dedicated to empowering legal practitioners in Sri Lanka.
                By digitizing and clustering decades of criminal judgments, we provide unprecedented access to the intricate logic of the courts.
              </Text>
            </View>
            <View style={styles.highlightCard}>
              <Text style={styles.highlightVal}>50K+</Text>
              <Text style={styles.highlightLabel}>Judgments Indexed</Text>
            </View>
          </View>

          <Text style={styles.subHeading}>Core Pillars of Innovation</Text>
          <View style={styles.pillGrid}>
            <View style={[styles.pillCard, { borderLeftColor: '#3B82F6' }]}>
              <Text style={styles.pillIcon}>📊</Text>
              <Text style={styles.pillTitle}>Semantic Graphing</Text>
              <Text style={styles.pillText}>Mapping legal logic into searchable multidimensional graphs.</Text>
            </View>
            <View style={[styles.pillCard, { borderLeftColor: '#F59E0B' }]}>
              <Text style={styles.pillIcon}>⚖</Text>
              <Text style={styles.pillTitle}>Argument Synthesis</Text>
              <Text style={styles.pillText}>Automated extraction of supportive reasoning from landmark cases.</Text>
            </View>
            <View style={[styles.pillCard, { borderLeftColor: '#10B981' }]}>
              <Text style={styles.pillIcon}>📈</Text>
              <Text style={styles.pillTitle}>Outcome Prediction</Text>
              <Text style={styles.pillText}>Probability modeling for appeal outcomes based on HC history.</Text>
            </View>
          </View>

          <Card style={styles.institutionCard}>
            <Text style={styles.instTitle}>Research & Institutional Integrity</Text>
            <Text style={styles.instPara}>
              Developed as a final-year research project at **SLIIT**, this system represents the intersection of Sri Lankan jurisprudence and state-of-the-art Natural Language Processing.
              We are committed to the administration of justice through data-driven insight.
            </Text>
            <View style={styles.badgeRow}>
              <View style={styles.badge}><Text style={styles.badgeText}>SLIIT Research</Text></View>
              <View style={styles.badge}><Text style={styles.badgeText}>Legal AI 2026</Text></View>
            </View>
          </Card>
        </Container>
      </ScrollView>
    </Layout>
  );
}

const styles = StyleSheet.create({
  scroll: { flex: 1, backgroundColor: '#F8FAFC' },
  hero: {
    backgroundColor: colors.primary,
    paddingVertical: 80,
    alignItems: 'center',
    textAlign: 'center',
    ...(Platform.OS === 'web' && {
      backgroundImage: 'linear-gradient(135deg, #1B2B48 0%, #2C3E5B 100%)',
    }),
  },
  heroTag: { color: colors.accent, fontWeight: '700', letterSpacing: 2, fontSize: 13, marginBottom: spacing.md, textAlign: 'center' },
  heroTitle: { color: '#FFFFFF', fontSize: 40, fontWeight: '800', textAlign: 'center', maxWidth: 900, lineHeight: 52, alignSelf: 'center' },
  heroSub: { color: '#E0E6ED', fontSize: 18, textAlign: 'center', maxWidth: 700, marginTop: spacing.md, opacity: 0.9, lineHeight: 28, alignSelf: 'center' },
  content: { paddingVertical: spacing.xxl },
  sectionRow: { flexDirection: Platform.OS === 'web' ? 'row' : 'column', gap: spacing.xl, marginBottom: 60, alignItems: 'center' },
  textBlock: { flex: 2 },
  sectionHeading: { fontSize: 28, fontWeight: 'bold', color: colors.primary, marginBottom: spacing.md },
  para: { fontSize: 16, color: colors.textSecondary, lineHeight: 28 },
  highlightCard: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    padding: spacing.xl,
    borderRadius: 20,
    alignItems: 'center',
    boxShadow: '0 10px 25px rgba(27, 43, 72, 0.05)',
  },
  highlightVal: { fontSize: 48, fontWeight: '800', color: colors.accent },
  highlightLabel: { fontSize: 14, color: colors.textMuted, fontWeight: '600', textTransform: 'uppercase', marginTop: 8 },
  subHeading: { fontSize: 22, fontWeight: 'bold', color: colors.primary, marginBottom: spacing.xl, textAlign: Platform.OS === 'web' ? 'center' : 'left' },
  pillGrid: { flexDirection: Platform.OS === 'web' ? 'row' : 'column', gap: spacing.lg, marginBottom: 60 },
  pillCard: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    padding: spacing.lg,
    borderRadius: 16,
    borderLeftWidth: 5,
    boxShadow: '0 4px 12px rgba(0,0,0,0.03)',
  },
  pillIcon: { fontSize: 32, marginBottom: spacing.sm },
  pillTitle: { fontSize: 18, fontWeight: '700', color: colors.primary, marginBottom: 8 },
  pillText: { fontSize: 14, color: colors.textSecondary, lineHeight: 22 },
  institutionCard: { backgroundColor: '#FFFFFF', borderTopWidth: 4, borderTopColor: colors.accent, padding: spacing.xl },
  instTitle: { fontSize: 20, fontWeight: 'bold', color: colors.primary, marginBottom: spacing.md },
  instPara: { fontSize: 15, color: colors.textSecondary, lineHeight: 26, marginBottom: spacing.lg },
  badgeRow: { flexDirection: 'row', gap: spacing.sm },
  badge: { backgroundColor: colors.bgSection, paddingVertical: 6, paddingHorizontal: 12, borderRadius: 20 },
  badgeText: { fontSize: 12, color: colors.primary, fontWeight: '600' },
});
