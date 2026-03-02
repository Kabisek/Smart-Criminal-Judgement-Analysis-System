import { View, Text, StyleSheet, Pressable, Platform } from 'react-native';
import { colors, spacing, typography, borderRadius } from '../theme';

export function Container({
  children,
  style,
}: {
  children: React.ReactNode;
  style?: object;
}) {
  return (
    <View style={[styles.container, Platform.OS === 'web' && styles.containerWeb, style]}>
      {children}
    </View>
  );
}

export function Card({
  children,
  title,
  description,
  style,
}: {
  children?: React.ReactNode;
  title?: string;
  description?: string;
  style?: object;
}) {
  return (
    <View style={[styles.card, style]}>
      {title ? <Text style={styles.cardTitle}>{title}</Text> : null}
      {description ? <Text style={styles.cardDescription}>{description}</Text> : null}
      {children}
    </View>
  );
}

export function Button({
  onPress,
  children,
  variant = 'primary',
  disabled,
  style,
  textStyle,
}: {
  onPress: () => void;
  children: string;
  variant?: 'primary' | 'secondary';
  disabled?: boolean;
  style?: object;
  textStyle?: object;
}) {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      style={({ pressed }) => [
        styles.btn,
        variant === 'primary' ? styles.btnPrimary : styles.btnSecondary,
        pressed && styles.btnPressed,
        disabled && styles.btnDisabled,
        style,
      ]}
    >
      <Text
        style={[
          styles.btnText,
          variant === 'primary' ? styles.btnTextPrimary : styles.btnTextSecondary,
          textStyle,
        ]}
      >
        {children}
      </Text>
    </Pressable>
  );
}

export function PageHeader({
  title,
  breadcrumb,
  onBack,
  backHref,
}: {
  title: string;
  breadcrumb?: React.ReactNode;
  onBack?: () => void;
  backHref?: string;
}) {
  const { useRouter } = require('expo-router');
  const router = useRouter();
  const handleBack = onBack ?? (backHref ? () => router.push(backHref as '/') : undefined);
  return (
    <View style={styles.pageHeader}>
      {handleBack ? (
        <Pressable onPress={handleBack} style={styles.backLink}>
          <Text style={styles.backLinkText}>← Back</Text>
        </Pressable>
      ) : null}
      {breadcrumb ? <Text style={styles.breadcrumb}>{breadcrumb}</Text> : null}
      <Text style={styles.pageTitle}>{title}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { paddingHorizontal: spacing.md, width: '100%' },
  containerWeb: { maxWidth: 1200, alignSelf: 'center' },
  card: {
    backgroundColor: colors.bgCard,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
    marginBottom: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
    ...(Platform.OS === 'web' && {
      boxShadow: '0 10px 30px rgba(27, 43, 72, 0.06), 0 1px 8px rgba(27, 43, 72, 0.04)',
      transition: 'all 0.3s ease-in-out',
    }),
  },
  cardTitle: {
    fontSize: typography.sizes.xl,
    fontWeight: typography.weights.bold,
    color: colors.primary,
    marginBottom: spacing.sm,
    paddingBottom: spacing.sm,
    borderBottomWidth: 3,
    borderBottomColor: colors.accent,
    letterSpacing: 0.5,
  },
  cardDescription: {
    color: colors.textSecondary,
    marginBottom: spacing.md,
    fontSize: typography.sizes.base,
    lineHeight: 24,
    opacity: 0.85,
  },
  btn: {
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.xl,
    borderRadius: borderRadius.md,
    alignSelf: 'flex-start',
    ...(Platform.OS === 'web' && {
      transition: 'transform 0.2s ease',
    }),
  },
  btnPrimary: {
    backgroundColor: colors.primary,
    ...(Platform.OS === 'web' && {
      boxShadow: '0 4px 12px rgba(27, 43, 72, 0.2)',
    }),
  },
  btnSecondary: {
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: colors.primary,
  },
  btnPressed: {
    opacity: 0.9,
    ...(Platform.OS === 'web' && {
      transform: 'scale(0.98)',
    }),
  },
  btnDisabled: { opacity: 0.5 },
  btnText: { fontSize: 16, fontWeight: typography.weights.semibold },
  btnTextPrimary: { color: colors.textOnPrimary },
  btnTextSecondary: { color: colors.primary },
  pageHeader: { marginBottom: spacing.lg },
  backLink: { marginBottom: spacing.sm },
  backLinkText: { color: colors.primary, fontSize: 15, fontWeight: '500' },
  breadcrumb: { fontSize: 14, color: colors.textMuted, marginBottom: spacing.sm },
  pageTitle: {
    fontSize: typography.sizes.xxl,
    fontWeight: typography.weights.bold,
    color: colors.textPrimary,
  },
});
