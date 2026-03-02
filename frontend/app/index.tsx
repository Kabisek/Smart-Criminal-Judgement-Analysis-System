import { View, Text, Pressable, StyleSheet, useWindowDimensions, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { Layout } from '../components/Layout';
import { Container, Card, Button } from '../components/ui';
import { colors, spacing, typography } from '../theme';
import { FileUploadSection } from '../components/FileUploadSection';
import { useAuth } from '../components/AuthContext';

const FEATURES = [
  {
    href: '/component1',
    icon: '🔍',
    title: 'Legal Resource Extractor',
    desc: 'High-dimensional extraction of statutory provisions, landmark cases, and legal principles.',
    restricted: true,
  },
  {
    href: '/component2',
    icon: '⚔',
    title: 'Argument Synthesis Engine',
    desc: 'Upload a case document and get key argument points and supportive reasoning.',
    restricted: true,
  },
  {
    href: '/component3',
    icon: '📈',
    title: 'Outcome Prediction Model',
    desc: 'Input appeal case details and receive predicted outcome probabilities.',
    restricted: true,
  },
  {
    href: '/component4',
    icon: '🌐',
    title: 'Public Legal Assistant',
    desc: 'Find laws, understand rights, and practical guidance in Sinhala, Tamil, and English.',
    restricted: false,
  },
];

export default function HomeScreen() {
  const router = useRouter();
  const { width } = useWindowDimensions();
  const { role } = useAuth();
  const isNarrow = width < 768;

  const handlePress = (href: string, restricted: boolean) => {
    if (restricted && role !== 'lawyer') {
      router.push('/login');
    } else {
      router.push(href as any);
    }
  };

  return (
    <Layout>
      <Container>
        <View style={[styles.hero, Platform.OS === 'web' && styles.heroWeb]}>
          <View style={styles.heroOverlay} />
          <Text style={styles.heroTag}>SRI LANKA'S PREMIER LEGAL AI</Text>
          <Text style={[styles.heroTitle, isNarrow && styles.heroTitleSmall]}>
            Transforming Jurisprudence with Intelligent Insights
          </Text>
          <Text style={styles.heroSubtitle}>
            High-dimensional semantic analysis and argument synthesis designed for the modern legal practitioner.
          </Text>
          <View style={styles.heroBtnRow}>
            <Button onPress={() => router.push('/login')} style={styles.heroMainBtn} textStyle={styles.heroMainBtnText}>Professional Access</Button>
            <Button variant="secondary" onPress={() => router.push('/about')} style={styles.heroSecBtn} textStyle={styles.heroSecBtnText}>Our Mission</Button>
          </View>
        </View>

        <View style={styles.toolsHeader}>
          <Text style={styles.sectionTag}>ANALYTICAL SUITE</Text>
          <Text style={styles.sectionHeading}>Empowering Justice through Data</Text>
          <Text style={styles.sectionSub}>Our integrated modules provide a comprehensive 360° view of criminal legal data.</Text>
        </View>

        <View style={[styles.grid, isNarrow && styles.gridStack]}>
          {FEATURES.map((c) => (
            <Pressable
              key={c.href}
              onPress={() => handlePress(c.href, c.restricted)}
              style={({ pressed }) => [
                styles.featureCard,
                pressed && styles.featureCardPressed,
                c.restricted && role !== 'lawyer' && styles.restrictedCard
              ]}
            >
              <View style={styles.featureIconWrap}>
                <Text style={styles.featureIcon}>{c.icon}</Text>
              </View>
              <Text style={styles.featureTitle}>{c.title}</Text>
              <Text style={styles.featureDesc}>{c.desc}</Text>
              {c.restricted && role !== 'lawyer' ? (
                <View style={styles.featureBadgeLocked}>
                  <Text style={styles.badgeTextLock}>🔒 Practitioner Only</Text>
                </View>
              ) : (
                <View style={styles.featureBadgeOpen}>
                  <Text style={styles.badgeTextOpen}>Access Tool →</Text>
                </View>
              )}
            </Pressable>
          ))}
        </View>

        {role !== 'lawyer' && (
          <View style={styles.ctaBanner}>
            <View style={styles.ctaText}>
              <Text style={styles.ctaTitle}>Are you a Registered Lawyer?</Text>
              <Text style={styles.ctaSub}>Authenticate your credentials to unlock the full predictive modeling and argument synthesis suite.</Text>
            </View>
            <Button onPress={() => router.push('/login')} style={styles.ctaBtn}>Verified Login</Button>
          </View>
        )}

        <View style={styles.trustSection}>
          <Text style={styles.sectionTagCenter}>WHY TRUST US?</Text>
          <View style={styles.trustGrid}>
            <View style={styles.trustItem}>
              <View style={styles.trustIcon}><Text style={styles.trustIconText}>🛡</Text></View>
              <Text style={styles.trustTitle}>Data Security</Text>
              <Text style={styles.trustPara}>Encrypted processing of sensitive case files with strictly local inference.</Text>
            </View>
            <View style={styles.trustItem}>
              <View style={styles.trustIcon}><Text style={styles.trustIconText}>🎓</Text></View>
              <Text style={styles.trustTitle}>Academic Integrity</Text>
              <Text style={styles.trustPara}>Developed under the supervision of SLIIT's senior legal research faculty.</Text>
            </View>
            <View style={styles.trustItem}>
              <View style={styles.trustIcon}><Text style={styles.trustIconText}>🏛</Text></View>
              <Text style={styles.trustTitle}>Court-Aligned</Text>
              <Text style={styles.trustPara}>Logic models trained specifically on Sri Lankan Criminal Procedure & Statutes.</Text>
            </View>
          </View>
        </View>

        <View style={styles.statsStrip}>
          <View style={styles.statLine}>
            <Text style={styles.statNum}>50K+</Text>
            <Text style={styles.statName}>JUDGMENTS</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statLine}>
            <Text style={styles.statNum}>92%</Text>
            <Text style={styles.statName}>ACCURACY</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statLine}>
            <Text style={styles.statNum}>24/7</Text>
            <Text style={styles.statName}>AVAILABILITY</Text>
          </View>
        </View>
      </Container>
    </Layout>
  );
}

const styles = StyleSheet.create({
  hero: {
    borderRadius: 24,
    paddingVertical: 100,
    paddingHorizontal: spacing.xl,
    marginBottom: spacing.xxl,
    alignItems: 'center',
    overflow: 'hidden',
    backgroundColor: '#1B2B48',
    position: 'relative',
    ...(Platform.OS === 'web' && {
      boxShadow: '0 20px 50px rgba(27, 43, 72, 0.2)',
    }),
  },
  heroWeb: {
    // @ts-expect-error web
    backgroundImage: 'linear-gradient(135deg, #1B2B48 0%, #2D3E5E 100%)',
  },
  heroOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.1)',
  },
  heroTag: {
    color: colors.accent,
    fontWeight: '800',
    letterSpacing: 3,
    fontSize: 12,
    marginBottom: spacing.md,
    textTransform: 'uppercase',
  },
  heroTitle: {
    fontSize: 48,
    fontWeight: '800',
    color: '#FFFFFF',
    textAlign: 'center',
    maxWidth: 900,
    lineHeight: 58,
    letterSpacing: -1,
    alignSelf: 'center',
  },
  heroTitleSmall: { fontSize: 32, lineHeight: 40 },
  heroSubtitle: {
    fontSize: 18,
    color: '#D1D5DB',
    textAlign: 'center',
    maxWidth: 700,
    marginTop: spacing.lg,
    lineHeight: 28,
    fontWeight: '400',
    opacity: 0.9,
    alignSelf: 'center',
  },
  heroBtnRow: {
    flexDirection: 'row',
    gap: spacing.md,
    marginTop: spacing.xl,
    flexWrap: 'wrap',
    justifyContent: 'center',
  },
  heroMainBtn: {
    minWidth: 200,
    backgroundColor: colors.accent,
    borderWidth: 0,
  },
  heroSecBtn: {
    minWidth: 160,
    borderColor: '#FFFFFF',
    borderWidth: 1.5,
  },
  heroMainBtnText: {
    color: colors.primary,
    fontWeight: '800',
  },
  heroSecBtnText: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  toolsHeader: { alignItems: 'center', marginBottom: spacing.xxl },
  sectionTag: { color: colors.accent, fontWeight: '700', letterSpacing: 2, fontSize: 12, marginBottom: spacing.sm },
  sectionTagCenter: { color: colors.accent, fontWeight: '700', letterSpacing: 2, fontSize: 12, marginBottom: spacing.xxl, textAlign: 'center' },
  sectionHeading: { fontSize: 32, fontWeight: '800', color: colors.primary, marginBottom: spacing.sm, textAlign: 'center' },
  sectionSub: { fontSize: 16, color: colors.textSecondary, textAlign: 'center', maxWidth: 600, opacity: 0.8 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.lg },
  gridStack: { flexDirection: 'column' },
  featureCard: {
    flex: 1,
    minWidth: 280,
    backgroundColor: '#FFFFFF',
    padding: spacing.xl,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#F1F5F9',
    alignItems: 'flex-start',
    ...(Platform.OS === 'web' && {
      boxShadow: '0 4px 15px rgba(0,0,0,0.03)',
      transition: 'all 0.3s ease',
    }),
  },
  featureCardPressed: {
    borderColor: colors.accent,
    ...(Platform.OS === 'web' && {
      transform: 'translateY(-8px)',
      boxShadow: '0 20px 40px rgba(27, 43, 72, 0.08)',
    }),
  },
  featureIconWrap: {
    width: 56,
    height: 56,
    borderRadius: 16,
    backgroundColor: '#F8FAFC',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.lg,
  },
  featureIcon: { fontSize: 28 },
  featureTitle: { fontSize: 19, fontWeight: '700', color: colors.primary, marginBottom: spacing.sm },
  featureDesc: { fontSize: 15, color: colors.textSecondary, lineHeight: 22, opacity: 0.9, marginBottom: spacing.lg },
  featureBadgeLocked: { backgroundColor: '#FEE2E2', paddingVertical: 4, paddingHorizontal: 10, borderRadius: 20 },
  badgeTextLock: { color: '#B91C1C', fontSize: 11, fontWeight: '700' },
  featureBadgeOpen: { backgroundColor: '#F0FDF4', paddingVertical: 4, paddingHorizontal: 10, borderRadius: 20 },
  badgeTextOpen: { color: '#15803D', fontSize: 11, fontWeight: '700' },
  ctaBanner: {
    backgroundColor: '#FFFFFF',
    padding: spacing.xl,
    borderRadius: 20,
    marginTop: spacing.xxl,
    flexDirection: Platform.OS === 'web' ? 'row' : 'column',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderWidth: 1,
    borderColor: colors.accent,
    gap: spacing.lg,
  },
  ctaText: { flex: 1 },
  ctaTitle: { fontSize: 20, fontWeight: '800', color: colors.primary, marginBottom: 4 },
  ctaSub: { fontSize: 14, color: colors.textSecondary, opacity: 1 },
  ctaBtn: { minWidth: 180 },
  trustSection: { paddingVertical: spacing.xxl, marginTop: spacing.xxl },
  trustGrid: { flexDirection: Platform.OS === 'web' ? 'row' : 'column', gap: spacing.xl },
  trustItem: { flex: 1, alignItems: 'center', textAlign: 'center' },
  trustIcon: { width: 48, height: 48, borderRadius: 24, backgroundColor: '#EFF6FF', alignItems: 'center', justifyContent: 'center', marginBottom: spacing.md },
  trustIconText: { fontSize: 24 },
  trustTitle: { fontSize: 18, fontWeight: '700', color: colors.primary, marginBottom: 8 },
  trustPara: { fontSize: 14, color: colors.textSecondary, textAlign: 'center', lineHeight: 20 },
  statsStrip: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: spacing.xxl,
    marginTop: spacing.xxl,
    paddingVertical: 60,
    borderTopWidth: 1,
    borderTopColor: '#E2E8F0',
  },
  statLine: { alignItems: 'center' },
  statNum: { fontSize: 32, fontWeight: '900', color: colors.accent },
  statName: { fontSize: 12, fontWeight: '700', color: colors.textMuted, letterSpacing: 1, marginTop: 4 },
  statDivider: { width: 1, height: 40, backgroundColor: '#E2E8F0' },
  restrictedCard: { opacity: 0.8 },
});
