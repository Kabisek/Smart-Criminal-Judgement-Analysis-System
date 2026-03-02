import * as React from 'react';
import { useRouter, usePathname } from 'expo-router';
import {
  View,
  Text,
  StyleSheet,
  Pressable,
  ScrollView,
  useWindowDimensions,
  Platform,
  Linking,
} from 'react-native';
import { colors, spacing, typography } from '../theme';
import { useAuth } from './AuthContext';

const NAV_LINKS = [
  { href: '/', label: 'Home' },
  { href: '/about', label: 'About Us' },
  { href: '/contact', label: 'Contact Us' },
];

const ANALYSIS_TOOLS = [
  { href: '/component1', label: 'Legal Resource Extractor', restricted: true },
  { href: '/component2', label: 'Argument Synthesis Engine', restricted: true },
  { href: '/component3', label: 'Outcome Prediction Model', restricted: true },
  { href: '/component4', label: 'Public Legal Assistant', restricted: false },
];

export function Header({ onMenuPress }: { onMenuPress?: () => void }) {
  const router = useRouter();
  const pathname = usePathname();
  const { width } = useWindowDimensions();
  const { isLoggedIn, user, role } = useAuth();
  const isWeb = Platform.OS === 'web';
  const isNarrow = width < 768;
  const [componentsOpen, setComponentsOpen] = React.useState(false);

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/';
    return pathname.startsWith(href);
  };

  return (
    <View style={[styles.header, isWeb && { borderBottomWidth: 3, borderBottomColor: colors.accent }]}>
      <View style={[styles.headerInner, isWeb && styles.headerInnerWeb]}>
        <Pressable
          onPress={() => router.push('/')}
          style={({ pressed }) => [styles.logoWrap, pressed && styles.pressed]}
        >
          {/* Professional SVG Logo Representation */}
          <View style={styles.logoIconContainer}>
            <Text style={styles.logoIcon}>⚖</Text>
          </View>
          <View>
            <Text style={styles.logoText}>Smart Criminal Judgment</Text>
            <Text style={styles.logoSubtext}>Analysis System</Text>
          </View>
        </Pressable>
        {isNarrow && onMenuPress ? (
          <Pressable onPress={onMenuPress} style={styles.menuBtn}>
            <Text style={styles.menuBtnText}>☰</Text>
          </Pressable>
        ) : (
          <View style={styles.nav}>
            {NAV_LINKS.filter((l) => l.href !== '/').map((link) => (
              <Pressable
                key={link.href}
                onPress={() => router.push(link.href as '/')}
                style={[
                  styles.navLink,
                  isActive(link.href) && styles.navLinkActive,
                ]}
              >
                <Text
                  style={[
                    styles.navLinkText,
                    isActive(link.href) && styles.navLinkTextActive,
                  ]}
                >
                  {link.label}
                </Text>
              </Pressable>
            ))}

            <View style={styles.dropdown}>
              <Pressable
                onPress={() => setComponentsOpen((o) => !o)}
                style={styles.dropdownTrigger}
              >
                <Text style={[styles.navLinkText, styles.dropdownLabel]}>
                  Analytical Tools ▾
                </Text>
              </Pressable>
              {componentsOpen && (
                <View style={styles.dropdownContent}>
                  {ANALYSIS_TOOLS.map((link) => (
                    <Pressable
                      key={link.href}
                      onPress={() => {
                        if (link.restricted && role !== 'lawyer') {
                          router.push('/login');
                        } else {
                          router.push(link.href as '/');
                        }
                        setComponentsOpen(false);
                      }}
                      style={({ pressed }) => [
                        styles.dropdownItem,
                        pressed && { backgroundColor: '#F0F0F0' }
                      ]}
                    >
                      <View style={styles.dropdownItemContent}>
                        <Text style={styles.dropdownItemText}>{link.label}</Text>
                        {link.restricted && role !== 'lawyer' && (
                          <Text style={styles.lockedIcon}>🔒</Text>
                        )}
                      </View>
                    </Pressable>
                  ))}
                </View>
              )}
            </View>

            <View style={styles.authPanel}>
              {isLoggedIn ? (
                <Pressable
                  onPress={() => router.push('/profile')}
                  style={[styles.profileBtn, isActive('/profile') && styles.navLinkActive]}
                >
                  <View style={styles.avatarMini}>
                    <Text style={styles.avatarTextMini}>{user?.name.charAt(0)}</Text>
                  </View>
                  <Text style={styles.navLinkText}>Profile</Text>
                </Pressable>
              ) : (
                <Pressable
                  onPress={() => router.push('/login')}
                  style={styles.loginBtn}
                >
                  <Text style={styles.loginBtnText}>Lawyer Login</Text>
                </Pressable>
              )}
            </View>
          </View>
        )}
      </View>
    </View>
  );
}

export function Footer() {
  const router = useRouter();
  const open = (url: string) => () => Linking.openURL(url);
  return (
    <View style={styles.footer}>
      <View style={[styles.footerInner, Platform.OS === 'web' && styles.footerInnerWeb]}>
        <View style={styles.footerGrid}>
          <View style={styles.footerBlock}>
            <Text style={styles.footerTitle}>Smart Criminal Judgment Analysis</Text>
            <Text style={styles.footerText}>
              Research project for Sri Lankan Courts. Case analysis, argument generation, and decision support.
            </Text>
          </View>
          <View style={styles.footerBlock}>
            <Text style={styles.footerTitle}>Useful Links</Text>
            <Pressable onPress={open('https://www.supremecourt.lk')}>
              <Text style={styles.footerLink}>Supreme Court of Sri Lanka</Text>
            </Pressable>
            <Pressable onPress={open('https://www.courtappeal.lk')}>
              <Text style={styles.footerLink}>Court of Appeal</Text>
            </Pressable>
            <Pressable onPress={open('https://basl.lk')}>
              <Text style={styles.footerLink}>Bar Association of Sri Lanka (BASL)</Text>
            </Pressable>
          </View>
          <View style={styles.footerBlock}>
            <Text style={styles.footerTitle}>Contact</Text>
            <Pressable onPress={() => router.push('/contact')}>
              <Text style={styles.footerLink}>Contact Us</Text>
            </Pressable>
          </View>
        </View>
        <Text style={styles.footerBottom}>
          © 2025–2026 Smart Criminal Judgment Analysis System. Research Project. SLIIT.
        </Text>
      </View>
    </View>
  );
}

export function Layout({
  children,
  noPadding,
}: {
  children: React.ReactNode;
  noPadding?: boolean;
}) {
  const isWeb = Platform.OS === 'web';
  return (
    <View style={styles.page}>
      <View style={isWeb ? styles.boxedShell : undefined}>
        <Header onMenuPress={() => { }} />
        <ScrollView
          style={styles.scroll}
          contentContainerStyle={[styles.main, !noPadding && styles.mainPadding]}
          showsVerticalScrollIndicator={false}
        >
          {children}
          <Footer />
        </ScrollView>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: '#E8ECF0' },
  boxedShell: {
    flex: 1,
    maxWidth: 1280,
    width: '100%',
    alignSelf: 'center',
    backgroundColor: colors.bgBody,
    ...(Platform.OS === 'web' && {
      boxShadow: '0 0 30px rgba(0,0,0,0.08)',
    }),
  },
  header: {
    backgroundColor: colors.bgHeader,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.1)',
    zIndex: 1000, // Ensure header is above scroll content
    elevation: 8, // For Android
  },
  headerInner: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  headerInnerWeb: { width: '100%' },
  logoWrap: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  logoIconContainer: {
    backgroundColor: colors.accent,
    width: 40,
    height: 40,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    ...(Platform.OS === 'web' && {
      boxShadow: '0 4px 10px rgba(184, 134, 11, 0.3)',
    }),
  },
  logoIcon: { fontSize: 24, color: '#FFFFFF' },
  logoText: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.textOnDark,
    letterSpacing: 0.5,
    marginBottom: -2,
  },
  logoSubtext: {
    fontSize: 12,
    color: colors.accent,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 1.5,
  },
  pressed: { opacity: 0.85 },
  menuBtn: { padding: spacing.sm },
  menuBtnText: { color: colors.textOnDark, fontSize: 22 },
  nav: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, flexWrap: 'wrap' },
  navLink: { paddingVertical: spacing.sm, paddingHorizontal: spacing.md, borderRadius: 6 },
  navLinkActive: { backgroundColor: 'rgba(255,255,255,0.05)' },
  navLinkText: { color: colors.textOnDark, fontSize: 15, fontWeight: '500' },
  navLinkTextActive: { color: colors.accent },
  dropdown: { position: 'relative' },
  dropdownTrigger: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: 6,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.05)',
  },
  dropdownLabel: { fontWeight: '600' },
  authPanel: {
    marginLeft: spacing.lg,
    paddingLeft: spacing.lg,
    borderLeftWidth: 1,
    borderLeftColor: 'rgba(255,255,255,0.15)',
  },
  loginBtn: {
    backgroundColor: colors.accent,
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 6,
  },
  loginBtnText: {
    color: '#FFFFFF',
    fontWeight: 'bold',
    fontSize: 14,
  },
  profileBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 6,
  },
  avatarMini: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: colors.accent,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarTextMini: {
    color: '#FFFFFF',
    fontWeight: 'bold',
    fontSize: 14,
  },
  dropdownContent: {
    position: 'absolute',
    top: '100%',
    left: 0,
    marginTop: 4,
    backgroundColor: colors.bgCard,
    borderRadius: 10,
    minWidth: 260,
    paddingVertical: spacing.xs,
    borderWidth: 1,
    borderColor: '#E0E0E0',
    ...(Platform.OS === 'web' && {
      boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
    }),
    zIndex: 9999,
    elevation: 10,
  },
  dropdownItem: {
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: '#F5F5F5',
  },
  dropdownItemText: {
    color: colors.textPrimary,
    fontSize: 15,
    fontWeight: '500',
  },
  dropdownItemContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: '100%',
  },
  lockedIcon: {
    fontSize: 12,
    marginLeft: 8,
    opacity: 0.7,
  },
  scroll: { flex: 1 },
  main: { flexGrow: 1 },
  mainPadding: { padding: spacing.lg },
  footer: {
    backgroundColor: colors.bgFooter,
    paddingVertical: spacing.lg,
    paddingHorizontal: spacing.md,
  },
  footerInner: {},
  footerInnerWeb: { width: '100%' },
  footerGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.lg,
    marginBottom: spacing.lg,
  },
  footerBlock: { flex: 1, minWidth: 180 },
  footerTitle: {
    fontSize: 16,
    fontWeight: typography.weights.semibold,
    color: colors.accent,
    marginBottom: spacing.sm,
  },
  footerText: { fontSize: 14, color: colors.textOnDark, opacity: 0.9 },
  footerLink: { fontSize: 14, color: colors.textOnDark, opacity: 0.9, marginBottom: 4 },
  footerBottom: {
    textAlign: 'center',
    paddingTop: spacing.md,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.15)',
    fontSize: 13,
    color: colors.textOnDark,
    opacity: 0.85,
  },
});
