import React from 'react';
import {
  View,
  Text,
  ScrollView,
  Pressable,
  StyleSheet,
  Platform,
} from 'react-native';
import { colors, spacing, borderRadius, typography } from '../theme';

export interface SourceSpanData {
  field_id: string;
  page: number;
  start_char: number;
  end_char: number;
  matched_text: string;
}

interface Props {
  analyzedCase: Record<string, any>;
  sourceSpans: SourceSpanData[];
  activeFieldId: string | null;
  onFieldClick: (fieldId: string) => void;
}

export function CaseAnalysisPanel({
  analyzedCase,
  sourceSpans,
  activeFieldId,
  onFieldClick,
}: Props) {
  const caseFile =
    analyzedCase?.analyzed_case_file ?? analyzedCase ?? {};

  const spanMap = new Map<string, SourceSpanData>();
  sourceSpans.forEach((sp) => spanMap.set(sp.field_id, sp));

  const hasSpan = (id: string) => spanMap.has(id);

  const fieldProps = (id: string) => ({
    onPress: () => hasSpan(id) && onFieldClick(id),
    style: [
      s.field,
      hasSpan(id) && s.fieldClickable,
      activeFieldId === id && s.fieldActive,
    ] as any,
  });

  const header = caseFile.case_header ?? {};
  const timeline = caseFile.incident_timeline ?? {};
  const parties = caseFile.parties_and_roles ?? {};
  const synthesis = caseFile.argument_synthesis ?? {};
  const opinion = caseFile.final_judicial_opinion;

  return (
    <View style={s.container}>
      <View style={s.titleBar}>
        <Text style={s.title}>Case Analysis</Text>
        <Text style={s.subtitle}>Click fields to highlight in document</Text>
      </View>

      <ScrollView style={s.scroll} contentContainerStyle={s.scrollContent}>
        {/* Case Header */}
        <Section label="Case Header" icon="📋">
          {header.file_number && (
            <Row label="File #" value={header.file_number} />
          )}
          {header.date_of_analysis && (
            <Row label="Date" value={header.date_of_analysis} />
          )}
          {header.subject && (
            <Pressable {...fieldProps('case_header.subject')}>
              <Row label="Subject" value={header.subject} clickable={hasSpan('case_header.subject')} active={activeFieldId === 'case_header.subject'} />
            </Pressable>
          )}
        </Section>

        {/* Incident Timeline */}
        <Section label="Incident Timeline" icon="📅">
          {timeline.what_happened && (
            <Pressable {...fieldProps('incident_timeline.what_happened')}>
              <LongField
                label="What Happened"
                value={timeline.what_happened}
                clickable={hasSpan('incident_timeline.what_happened')}
                active={activeFieldId === 'incident_timeline.what_happened'}
              />
            </Pressable>
          )}
          {timeline.where_it_happened && (
            <Pressable {...fieldProps('incident_timeline.where_it_happened')}>
              <Row label="Location" value={timeline.where_it_happened} clickable={hasSpan('incident_timeline.where_it_happened')} active={activeFieldId === 'incident_timeline.where_it_happened'} />
            </Pressable>
          )}
          {(timeline.key_dates ?? []).map((d: string, i: number) => (
            <Pressable key={i} {...fieldProps(`incident_timeline.key_dates[${i}]`)}>
              <Row label={`Date ${i + 1}`} value={d} clickable={hasSpan(`incident_timeline.key_dates[${i}]`)} active={activeFieldId === `incident_timeline.key_dates[${i}]`} />
            </Pressable>
          ))}
        </Section>

        {/* Parties & Roles */}
        <Section label="Parties & Roles" icon="👥">
          {parties.accused && (
            <Pressable {...fieldProps('parties_and_roles.accused')}>
              <Row label="Accused" value={parties.accused} clickable={hasSpan('parties_and_roles.accused')} active={activeFieldId === 'parties_and_roles.accused'} />
            </Pressable>
          )}
          {parties.complainant && (
            <Pressable {...fieldProps('parties_and_roles.complainant')}>
              <Row label="Complainant" value={parties.complainant} clickable={hasSpan('parties_and_roles.complainant')} active={activeFieldId === 'parties_and_roles.complainant'} />
            </Pressable>
          )}
          {(parties.doubters_witnesses ?? []).map((w: any, i: number) => (
            <Pressable key={i} {...fieldProps(`parties_and_roles.witnesses[${i}]`)}>
              <Row
                label={w.role || `Witness ${i + 1}`}
                value={w.name || w.doubt_factor || JSON.stringify(w)}
                clickable={hasSpan(`parties_and_roles.witnesses[${i}]`)}
                active={activeFieldId === `parties_and_roles.witnesses[${i}]`}
              />
            </Pressable>
          ))}
        </Section>

        {/* Argument Synthesis */}
        <Section label="Argument Synthesis" icon="⚖️">
          {(synthesis.prosecution_logic ?? []).length > 0 && (
            <View style={s.argGroup}>
              <Text style={[s.argGroupLabel, { color: colors.prosecution }]}>Prosecution</Text>
              {synthesis.prosecution_logic.map((p: string, i: number) => (
                <Pressable key={i} {...fieldProps(`argument_synthesis.prosecution[${i}]`)}>
                  <BulletField
                    value={p}
                    accentColor={colors.prosecution}
                    clickable={hasSpan(`argument_synthesis.prosecution[${i}]`)}
                    active={activeFieldId === `argument_synthesis.prosecution[${i}]`}
                  />
                </Pressable>
              ))}
            </View>
          )}
          {(synthesis.defense_logic ?? []).length > 0 && (
            <View style={s.argGroup}>
              <Text style={[s.argGroupLabel, { color: colors.defense }]}>Defense</Text>
              {synthesis.defense_logic.map((d: string, i: number) => (
                <Pressable key={i} {...fieldProps(`argument_synthesis.defense[${i}]`)}>
                  <BulletField
                    value={d}
                    accentColor={colors.defense}
                    clickable={hasSpan(`argument_synthesis.defense[${i}]`)}
                    active={activeFieldId === `argument_synthesis.defense[${i}]`}
                  />
                </Pressable>
              ))}
            </View>
          )}
          {(synthesis.reasonable_doubt_factors ?? []).length > 0 && (
            <View style={s.argGroup}>
              <Text style={[s.argGroupLabel, { color: '#D97706' }]}>Reasonable Doubt</Text>
              {synthesis.reasonable_doubt_factors.map((r: string, i: number) => (
                <Pressable key={i} {...fieldProps(`argument_synthesis.doubt[${i}]`)}>
                  <BulletField
                    value={r}
                    accentColor="#D97706"
                    clickable={hasSpan(`argument_synthesis.doubt[${i}]`)}
                    active={activeFieldId === `argument_synthesis.doubt[${i}]`}
                  />
                </Pressable>
              ))}
            </View>
          )}
        </Section>

        {/* Final Opinion */}
        {opinion && (
          <Section label="Final Judicial Opinion" icon="🔨">
            <Pressable {...fieldProps('final_judicial_opinion')}>
              <LongField
                label=""
                value={opinion}
                clickable={hasSpan('final_judicial_opinion')}
                active={activeFieldId === 'final_judicial_opinion'}
              />
            </Pressable>
          </Section>
        )}
      </ScrollView>
    </View>
  );
}

/* ── Sub-components ────────────────────────────────────────────────── */

function Section({ label, icon, children }: { label: string; icon: string; children: React.ReactNode }) {
  return (
    <View style={s.section}>
      <View style={s.sectionHeader}>
        <Text style={s.sectionIcon}>{icon}</Text>
        <Text style={s.sectionLabel}>{label}</Text>
      </View>
      {children}
    </View>
  );
}

function Row({ label, value, clickable, active }: { label: string; value: string; clickable?: boolean; active?: boolean }) {
  return (
    <View style={[s.row, clickable && s.rowClickable, active && s.rowActive]}>
      <Text style={s.rowLabel}>{label}</Text>
      <Text style={s.rowValue} numberOfLines={3}>{value}</Text>
      {clickable && <Text style={s.locateIcon}>📍</Text>}
    </View>
  );
}

function LongField({ label, value, clickable, active }: { label: string; value: string; clickable?: boolean; active?: boolean }) {
  return (
    <View style={[s.longField, clickable && s.rowClickable, active && s.rowActive]}>
      {label ? <Text style={s.rowLabel}>{label}</Text> : null}
      <Text style={s.longValue}>{value}</Text>
      {clickable && <Text style={s.locateIcon}>📍</Text>}
    </View>
  );
}

function BulletField({ value, accentColor, clickable, active }: { value: string; accentColor: string; clickable?: boolean; active?: boolean }) {
  return (
    <View style={[s.bulletRow, clickable && s.rowClickable, active && s.rowActive]}>
      <View style={[s.bulletDot, { backgroundColor: accentColor }]} />
      <Text style={s.bulletText}>{value}</Text>
      {clickable && <Text style={s.locateIconSmall}>📍</Text>}
    </View>
  );
}

/* ── Styles ────────────────────────────────────────────────────────── */

const s = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bgCard,
    borderRadius: borderRadius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: 'hidden',
    ...(Platform.OS === 'web' && {
      boxShadow: '0 4px 16px rgba(27,43,72,0.06)',
    }),
  },
  titleBar: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    backgroundColor: colors.bgSection,
  },
  title: {
    fontSize: typography.sizes.sm,
    fontWeight: typography.weights.semibold,
    color: colors.primary,
    letterSpacing: 0.3,
  },
  subtitle: {
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 2,
  },
  scroll: {
    flex: 1,
    maxHeight: 600,
  },
  scrollContent: {
    padding: spacing.sm,
  },
  section: {
    marginBottom: spacing.md,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: spacing.xs,
    paddingBottom: spacing.xs,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  sectionIcon: {
    fontSize: 14,
  },
  sectionLabel: {
    fontSize: typography.sizes.sm,
    fontWeight: typography.weights.bold,
    color: colors.primary,
    letterSpacing: 0.3,
  },
  field: {},
  fieldClickable: {
    ...(Platform.OS === 'web' && { cursor: 'pointer' }),
  },
  fieldActive: {},
  row: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingVertical: 5,
    paddingHorizontal: 6,
    borderRadius: borderRadius.sm,
    gap: 6,
  },
  rowClickable: {
    borderWidth: 1,
    borderColor: 'transparent',
    borderStyle: 'dashed',
    ...(Platform.OS === 'web' && {
      cursor: 'pointer',
      transition: 'all 0.15s ease',
    }),
  },
  rowActive: {
    backgroundColor: '#ECFDF5',
    borderColor: '#22C55E',
    borderWidth: 1,
    borderStyle: 'solid',
  },
  rowLabel: {
    fontSize: 12,
    fontWeight: typography.weights.semibold,
    color: colors.textMuted,
    minWidth: 80,
  },
  rowValue: {
    fontSize: 13,
    color: colors.textPrimary,
    flex: 1,
    lineHeight: 19,
  },
  locateIcon: {
    fontSize: 12,
    marginLeft: 4,
  },
  locateIconSmall: {
    fontSize: 10,
    marginLeft: 4,
  },
  longField: {
    paddingVertical: 5,
    paddingHorizontal: 6,
    borderRadius: borderRadius.sm,
  },
  longValue: {
    fontSize: 13,
    color: colors.textPrimary,
    lineHeight: 20,
    marginTop: 2,
  },
  argGroup: {
    marginBottom: spacing.sm,
  },
  argGroupLabel: {
    fontSize: 12,
    fontWeight: typography.weights.bold,
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  bulletRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingVertical: 4,
    paddingHorizontal: 6,
    borderRadius: borderRadius.sm,
    gap: 8,
  },
  bulletDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginTop: 6,
  },
  bulletText: {
    fontSize: 13,
    color: colors.textPrimary,
    flex: 1,
    lineHeight: 19,
  },
});
