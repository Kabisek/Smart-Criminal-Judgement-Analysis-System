import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { colors, spacing, borderRadius } from '../../theme';

const TRUNCATE_LIMIT = 300;

export function ExpandableText({
  text,
  style,
  limit = TRUNCATE_LIMIT,
}: {
  text: string;
  style?: any;
  limit?: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const needs = text.length > limit;
  const display = needs && !expanded ? text.substring(0, limit) + '…' : text;
  return (
    <Text style={style}>
      {display}
      {needs && (
        <Text onPress={() => setExpanded((p) => !p)} style={styles.readMoreLink}>
          {expanded ? '  Show Less ▲' : '  Read More ▼'}
        </Text>
      )}
    </Text>
  );
}

export function AnimatedBar({ value, color, height = 8 }: { value: number; color: string; height?: number }) {
  const anim = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.timing(anim, {
      toValue: value,
      duration: 900,
      useNativeDriver: false,
    }).start();
  }, [value]);

  const width = anim.interpolate({ inputRange: [0, 100], outputRange: ['0%', '100%'] });
  return (
    <View style={[styles.barTrack, { height }]}>
      <Animated.View style={[styles.barFill, { width, backgroundColor: color, height }]} />
    </View>
  );
}

export function SectionDivider({ label }: { label: string }) {
  return (
    <View style={styles.dividerRow}>
      <View style={styles.dividerLine} />
      <Text style={styles.dividerLabel}>{label}</Text>
      <View style={styles.dividerLine} />
    </View>
  );
}

export function PillChip({ label, accentColor }: { label: string; accentColor: string }) {
  return (
    <View style={[styles.pillChip, { borderLeftColor: accentColor }]}>
      <Text style={styles.pillChipText}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  readMoreLink: { color: colors.accent, fontWeight: '700', fontSize: 12 },
  barTrack: { backgroundColor: colors.border, borderRadius: 4, overflow: 'hidden' },
  barFill: { borderRadius: 4 },
  dividerRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginTop: spacing.sm },
  dividerLine: { flex: 1, height: 1, backgroundColor: colors.border },
  dividerLabel: { fontSize: 11, fontWeight: '700', color: colors.textMuted, letterSpacing: 1 },
  pillChip: {
    borderLeftWidth: 3,
    backgroundColor: colors.bgSection,
    paddingVertical: 5,
    paddingHorizontal: spacing.sm,
    borderRadius: borderRadius.sm,
    marginBottom: spacing.xs,
  },
  pillChipText: { fontSize: 12, fontWeight: '500', color: colors.textPrimary },
});
