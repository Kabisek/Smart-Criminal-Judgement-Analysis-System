import { View, Text, StyleSheet, Platform } from 'react-native';
import { colors, spacing, typography, borderRadius } from '../theme';

export function Card({
  children,
  title,
  description,
}: {
  children: React.ReactNode;
  title?: string;
  description?: string;
}) {
  return (
    <View style={styles.card}>
      {title ? (
        <>
          <Text style={styles.title}>{title}</Text>
          {description ? <Text style={styles.description}>{description}</Text> : null}
        </>
      ) : null}
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.bgCard,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
    marginBottom: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
    ...(Platform.OS === 'web' && {
      // @ts-expect-error web
      boxShadow: '0 4px 20px rgba(44, 31, 31, 0.08)',
    }),
  },
  title: {
    fontSize: typography.sizes.xl,
    fontWeight: typography.weights.bold,
    color: colors.primaryDark,
    marginBottom: spacing.sm,
    paddingBottom: spacing.sm,
    borderBottomWidth: 2,
    borderBottomColor: colors.primary,
  },
  description: {
    fontSize: typography.sizes.base,
    color: colors.textSecondary,
    marginBottom: spacing.md,
    lineHeight: 24,
  },
});
