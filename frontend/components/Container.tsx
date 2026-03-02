import { View, StyleSheet, Platform } from 'react-native';
import { colors, spacing } from '../theme';

export function Container({
  children,
  narrow,
}: {
  children: React.ReactNode;
  narrow?: boolean;
}) {
  return (
    <View style={[styles.outer, narrow && styles.narrow]}>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  outer: {
    width: '100%',
    maxWidth: 1200,
    marginHorizontal: 'auto',
    paddingHorizontal: spacing.md,
    ...(Platform.OS !== 'web' && { paddingHorizontal: spacing.md }),
  },
  narrow: { maxWidth: 720 },
});
