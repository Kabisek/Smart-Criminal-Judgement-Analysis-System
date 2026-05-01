  Animated,
  Easing,
  useWindowDimensions,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Layout } from '../components/Layout';
import { Container, Card, PageHeader, Button } from '../components/ui';
import { colors, typography, spacing, borderRadius } from '../theme';
import React, { useState, useEffect, useRef } from 'react';
import {
  predictAppealOutcomeDetailed,
  saveComp3History,
  DetailedPredictionRequest,
  AppealPredictionResponse,
  DetailedPredictionResponse,
} from '../api';

// ─── Types ────────────────────────────────────────────────────────────────────

type AnyPredictionResult = AppealPredictionResponse | DetailedPredictionResponse;

interface ContextStat {
  allowed_rate: number;
  partly_rate: number;
  dismissed_rate: number;
  count: number;
}
interface ContextAnalysis {
  offence?: ContextStat;
  location?: ContextStat;
  year?: ContextStat;
}
interface GroundStat {
  allowed_rate: number;
  partly_rate: number;
  dismissed_rate: number;
  count: number;
}

// ─── Design Tokens ────────────────────────────────────────────────────────────

const OUTCOME_THEME = {
  Appeal_Allowed: {
    color: '#059669',
    bg: '#D1FAE5',
    text: '#065F46',
    light: '#ECFDF5',
    icon: '✅',
    label: 'Appeal Allowed',
  },
  Appeal_Dismissed: {
    color: '#DC2626',
    bg: '#FEE2E2',
    text: '#7F1D1D',
    light: '#FEF2F2',
    icon: '❌',
    label: 'Appeal Dismissed',
  },
  Partly_Allowed: {
    color: '#D97706',
    bg: '#FEF3C7',
    text: '#92400E',
    light: '#FFFBEB',
    icon: '⚖️',
    label: 'Partly Allowed',
  },
};

function getTheme(prediction: string) {
  return OUTCOME_THEME[prediction as keyof typeof OUTCOME_THEME] ?? OUTCOME_THEME.Partly_Allowed;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function countDetectedFeatures(features: Record<string, string[]> | undefined): number {
  if (!features) return 0;
  return Object.values(features).reduce((s, a) => s + (Array.isArray(a) ? a.length : 0), 0);
}

function flatFeatures(features: Record<string, string[]> | undefined): string[] {
  if (!features) return [];
  return [
    ...(features.grounds ?? []),
    ...(features.evidence ?? []),
    ...(features.offence ?? []),
    ...(features.other ?? []),
  ].slice(0, 6);
}

function simBadgeStyle(pct: number): { bg: string; text: string } {
  if (pct >= 80) return { bg: '#D1FAE5', text: '#065F46' };
  if (pct >= 60) return { bg: '#FEF3C7', text: '#92400E' };
  return { bg: '#F3F4F6', text: '#6B7280' };
}

// ─── ExpandableText ───────────────────────────────────────────────────────────

const TRUNCATE_LIMIT = 300;

function ExpandableText({ text, style, limit = TRUNCATE_LIMIT }: { text: string; style?: any; limit?: number }) {
  const [expanded, setExpanded] = useState(false);
  const needs = text.length > limit;
  const display = needs && !expanded ? text.substring(0, limit) + '…' : text;
  return (
    <Text style={style}>
      {display}
      {needs && (
        <Text onPress={() => setExpanded(p => !p)} style={styles.readMoreLink}>
          {expanded ? '  Show Less ▲' : '  Read More ▼'}
        </Text>
      )}
    </Text>
  );
}

// ─── AnimatedBar ──────────────────────────────────────────────────────────────

function AnimatedBar({ value, color, height = 8 }: { value: number; color: string; height?: number }) {
  const anim = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.timing(anim, {
      toValue: value,
      duration: 900,
      easing: Easing.out(Easing.cubic),
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

// ─── SectionDivider ───────────────────────────────────────────────────────────

function SectionDivider({ label }: { label: string }) {
  return (
    <View style={styles.dividerRow}>
      <View style={styles.dividerLine} />
      <Text style={styles.dividerLabel}>{label}</Text>
      <View style={styles.dividerLine} />
    </View>
  );
}

// ─── SkeletonCard ─────────────────────────────────────────────────────────────

function SkeletonCard() {
  const shimmer = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(shimmer, { toValue: 1, duration: 900, useNativeDriver: true }),
        Animated.timing(shimmer, { toValue: 0, duration: 900, useNativeDriver: true }),
      ])
    ).start();
  }, []);
  const opacity = shimmer.interpolate({ inputRange: [0, 1], outputRange: [0.4, 0.85] });
  return (
    <Animated.View style={[styles.skeletonCard, { opacity }]}>
      <View style={[styles.skeletonLine, { width: '55%', height: 14, marginBottom: 14 }]} />
      <View style={styles.skeletonGrid}>
        <View style={styles.skeletonBox} />
        <View style={styles.skeletonBox} />
        <View style={styles.skeletonBox} />
      </View>
      <View style={[styles.skeletonLine, { width: '100%', height: 7, marginTop: 16 }]} />
      <View style={[styles.skeletonLine, { width: '80%', height: 7, marginTop: 8 }]} />
      <View style={[styles.skeletonLine, { width: '90%', height: 7, marginTop: 8 }]} />
    </Animated.View>
  );
}

// ─── ConfidenceRing ───────────────────────────────────────────────────────────

function ConfidenceRing({ confidence, color }: { confidence: number; color: string }) {
  return (
    <View style={styles.ringContainer}>
      <View style={[styles.ringOuter, { borderColor: color + '30' }]} />
      <View style={[
        styles.ringProgress,
        {
          borderTopColor: color,
          borderRightColor: confidence > 50 ? color : 'transparent',
          borderBottomColor: confidence > 75 ? color : 'transparent',
          borderLeftColor: 'transparent',
        },
      ]} />
      <View style={styles.ringInner}>
        <Text style={[styles.ringPct, { color }]}>{confidence.toFixed(0)}%</Text>
        <Text style={styles.ringLabel}>confidence</Text>
      </View>
    </View>
  );
}

// ─── VerdictBanner ────────────────────────────────────────────────────────────

function VerdictBanner({ prediction, confidence }: { prediction: string; confidence: number }) {
  const theme = getTheme(prediction);
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(-24)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, { toValue: 1, duration: 500, useNativeDriver: true }),
      Animated.spring(slideAnim, { toValue: 0, friction: 7, tension: 100, useNativeDriver: true }),
    ]).start();
  }, []);

  return (
    <Animated.View
      style={[
        styles.verdictBanner,
        { backgroundColor: theme.color, opacity: fadeAnim, transform: [{ translateY: slideAnim }] },
        isNarrow && styles.verdictBannerNarrow,
      ]}
    >
      <View style={[styles.verdictBannerLeft, isNarrow && styles.verdictBannerLeftNarrow]}>
        <Text style={styles.verdictIcon}>{theme.icon}</Text>
        <View>
          <Text style={styles.verdictBannerLabel}>PREDICTED OUTCOME</Text>
          <Text style={styles.verdictBannerOutcome}>{theme.label}</Text>
        </View>
      </View>
      <View style={[styles.verdictConfBadge, { backgroundColor: 'rgba(255,255,255,0.22)' }]}>
        <Text style={styles.verdictConfText}>{confidence.toFixed(1)}%</Text>
        <Text style={styles.verdictConfLabel}>confidence</Text>
      </View>
    </Animated.View>
  );
}

// ─── PillChip ─────────────────────────────────────────────────────────────────

function PillChip({ label, accentColor }: { label: string; accentColor: string }) {
  return (
    <View style={[styles.pillChip, { borderLeftColor: accentColor }]}>
      <Text style={styles.pillChipText}>{label}</Text>
    </View>
  );
}

// ─── TemplateSection ──────────────────────────────────────────────────────────

function TemplateSection({ number, title, description }: { number: string; title: string; description: string }) {
  return (
    <View style={styles.templateSection}>
      <View style={styles.templateNumBadge}>
        <Text style={styles.templateNumText}>{number}</Text>
      </View>
      <View style={styles.sectionContent}>
        <Text style={styles.templateSectionTitle}>{title}</Text>
        <Text style={styles.sectionDesc}>{description}</Text>
      </View>
    </View>
  );
}

// ─── ProgressTracker ──────────────────────────────────────────────────────────

function ProgressTracker({ step, text }: { step: number; text: string }) {
  const steps = ['Extract', 'Embeddings', 'Model', 'Complete'];
  const barAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(barAnim, {
      toValue: ((step + 1) / 4) * 100,
      duration: 400,
      easing: Easing.out(Easing.quad),
      useNativeDriver: false,
    }).start();
  }, [step]);

  const barWidth = barAnim.interpolate({ inputRange: [0, 100], outputRange: ['0%', '100%'] });

  return (
    <Card style={styles.progressCard} title="🔄 Processing Analysis">
      <View style={styles.progressContainer}>
        <Text style={styles.progressText}>{text}</Text>
        <View style={[styles.progressSteps, isNarrow && styles.progressStepsNarrow]}>
          {steps.map((label, idx) => (
            <View key={idx} style={[styles.progressStep, isNarrow && styles.progressStepNarrow]}>
              <View style={[styles.progressStepCircle, step >= idx && { backgroundColor: colors.accent }]}>
                {step > idx
                  ? <Text style={styles.progressStepCheck}>✓</Text>
                  : <Text style={[styles.progressStepNum, step >= idx && styles.progressStepNumActive]}>{idx + 1}</Text>
                }
              </View>
              <Text style={[styles.progressStepLabel, step >= idx && { color: colors.accent, fontWeight: '600' }]}>{label}</Text>
            </View>
          ))}
        </View>
        <View style={styles.progressBarContainer}>
          <Animated.View style={[styles.progressBar, { width: barWidth }]} />
        </View>
      </View>
    </Card>
  );
}

// ─── ProbabilityMeters ────────────────────────────────────────────────────────

function ProbabilityMeters({ probabilities }: { probabilities: Record<string, number> }) {
  const config: Record<string, { label: string; color: string }> = {
    Appeal_Allowed: { label: 'Appeal Allowed', color: '#059669' },
    Appeal_Dismissed: { label: 'Appeal Dismissed', color: '#DC2626' },
    Partly_Allowed: { label: 'Partly Allowed', color: '#D97706' },
  };
  return (
    <Card style={styles.resultCard} title="📊 Probability Distribution">
      {Object.entries(probabilities).map(([key, value]) => {
        const cfg = config[key] ?? { label: key, color: colors.textMuted };
        return (
          <View key={key} style={styles.meterRow}>
            <Text style={styles.meterLabel}>{cfg.label}</Text>
            <View style={{ flex: 2 }}>
              <AnimatedBar value={value} color={cfg.color} />
            </View>
            <Text style={[styles.meterPct, { color: cfg.color }]}>{value.toFixed(1)}%</Text>
          </View>
        );
      })}
    </Card>
  );
}

// ─── ContextSection ───────────────────────────────────────────────────────────

function ContextSection({ context }: { context: ContextAnalysis }) {
  const rows: Array<{ label: string; stat: ContextStat }> = [];
  if (context.offence) rows.push({ label: 'Offence Group', stat: context.offence });
  if (context.location) rows.push({ label: 'High Court Location', stat: context.location });
  if (context.year) rows.push({ label: 'Appeal Year', stat: context.year });
  if (!rows.length) return null;
  return (
    <Card style={styles.resultCard} title="📈 Contextual Analysis">
      {rows.map(({ label, stat }) => (
        <View key={label} style={styles.analysisRow}>
          <View style={styles.analysisRowHeader}>
            <Text style={styles.analysisLabel}>{label}</Text>
            <View style={styles.caseCountBadge}>
              <Text style={styles.caseCountText}>{stat.count} cases</Text>
            </View>
          </View>
          <View style={styles.stackedBarContainer}>
            <View style={[styles.stackedSegment, { flex: stat.allowed_rate || 0, backgroundColor: '#059669' }]} />
            <View style={[styles.stackedSegment, { flex: stat.partly_rate || 0, backgroundColor: '#D97706' }]} />
            <View style={[styles.stackedSegment, { flex: stat.dismissed_rate || 0, backgroundColor: '#DC2626' }]} />
          </View>
          <View style={styles.analysisLegend}>
            <Text style={[styles.legendItem, { color: '#059669' }]}>✅ {(stat.allowed_rate * 100).toFixed(1)}%</Text>
            <Text style={[styles.legendItem, { color: '#D97706' }]}>⚖️ {(stat.partly_rate * 100).toFixed(1)}%</Text>
            <Text style={[styles.legendItem, { color: '#DC2626' }]}>❌ {(stat.dismissed_rate * 100).toFixed(1)}%</Text>
          </View>
        </View>
      ))}
    </Card>
  );
}

// ─── GroundsOrEvidenceSection ─────────────────────────────────────────────────

function GroundsOrEvidenceSection({ title, data }: { title: string; data: Record<string, GroundStat> }) {
  const entries = Object.entries(data);
  if (!entries.length) return null;
  return (
    <Card style={styles.resultCard} title={title}>
      {entries.map(([name, stats]) => (
        <View key={name} style={styles.analysisRow}>
          <View style={styles.analysisRowHeader}>
            <Text style={styles.analysisLabel}>{name}</Text>
            <View style={styles.caseCountBadge}>
              <Text style={styles.caseCountText}>{stats.count} cases</Text>
            </View>
          </View>
          <View style={styles.stackedBarContainer}>
            <View style={[styles.stackedSegment, { flex: stats.allowed_rate || 0, backgroundColor: '#059669' }]} />
            <View style={[styles.stackedSegment, { flex: stats.partly_rate || 0, backgroundColor: '#D97706' }]} />
            <View style={[styles.stackedSegment, { flex: stats.dismissed_rate || 0, backgroundColor: '#DC2626' }]} />
          </View>
          <View style={styles.analysisLegend}>
            <Text style={[styles.legendItem, { color: '#059669' }]}>✅ {(stats.allowed_rate * 100).toFixed(1)}%</Text>
            <Text style={[styles.legendItem, { color: '#D97706' }]}>⚖️ {(stats.partly_rate * 100).toFixed(1)}%</Text>
            <Text style={[styles.legendItem, { color: '#DC2626' }]}>❌ {(stats.dismissed_rate * 100).toFixed(1)}%</Text>
          </View>
        </View>
      ))}
    </Card>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function Component3Screen() {
  const router = useRouter();
  const { width } = useWindowDimensions();
  const isNarrow = width < 768;
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<AnyPredictionResult | null>(null);
  const [caseDescription, setCaseDescription] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [progressStep, setProgressStep] = useState(0);
  const [progressText, setProgressText] = useState('');
  const [inputFocused, setInputFocused] = useState(false);

  const isDetailed = (r: AnyPredictionResult): r is DetailedPredictionResponse =>
    'legal_reasoning' in r;

  const handlePredict = async () => {
    if (!caseDescription.trim() || caseDescription.length < 50) {
      setError('Please provide a detailed case description (at least 50 characters)');
      return;
    }
    setAnalyzing(true);
    setError(null);
    setResult(null);
    setProgressStep(0);
    setProgressText('⏳ Step 1/4: Extracting features...');
    try {
      await new Promise(r => setTimeout(r, 800));
      setProgressStep(1);
      setProgressText('⏳ Step 2/4: Analyzing legal patterns...');
      await new Promise(r => setTimeout(r, 800));
      setProgressStep(2);
      setProgressText('⏳ Step 3/4: Running ensemble model...');

      const request: DetailedPredictionRequest = {
        case_description: caseDescription,
        user_type: 'general',
        analysis_level: 'detailed',
        include_precedents: true,
        language: 'en',
      };
      const predictionResult = await predictAppealOutcomeDetailed(request);
      setProgressStep(3);
      setProgressText('⏳ Step 4/4: Complete!');
      await new Promise(r => setTimeout(r, 500));

      if (predictionResult) {
        setResult(predictionResult);
        await saveComp3History({
          case_id: `case_${Date.now()}`,
          case_name: caseDescription.substring(0, 50) + (caseDescription.length > 50 ? '...' : ''),
          payload: predictionResult,
          user_type: 'general',
          analysis_level: 'detailed',
          timestamp: new Date().toISOString(),
        });
      } else {
        setError('Failed to get prediction. Please try again.');
      }
    } catch (err) {
      setError('Error connecting to prediction service.');
      console.error('Prediction error:', err);
    } finally {
      setAnalyzing(false);
      setProgressStep(0);
      setProgressText('');
    }
  };

  const wordCount = caseDescription.split(/\s+/).filter(w => w.length > 0).length;
  const charProgress = Math.min(caseDescription.length / 500, 1);
  const extResult = result as any;

  return (
    <Layout>
      <Container>
        <PageHeader
          title="Outcome Prediction Model"
          breadcrumb="Analytical Tools → Probability Analysis"
        />

        <View style={styles.mainCol}>

          {/* ── Input Card ── */}
          <Card style={styles.inputCard} title="📋 Case Analysis Template">
            <Text style={styles.templateTitle}>
              Include the following in your case description:
            </Text>

            {[
              { n: '1', t: '📄 Basic Information', d: 'Offence type & penal code section, original sentence/conviction' },
              { n: '2', t: '⚖️ Case Facts', d: 'Brief description of the incident, date, location, parties involved' },
              { n: '3', t: '🔬 Evidence', d: 'Eyewitness, medical/forensic, documentary, expert evidence (JMO, analysts)' },
              { n: '4', t: '⚖️ Grounds of Appeal', d: 'Contradictions, procedural errors, misdirection on law, chain of custody, identification' },
              { n: '5', t: '🛡️ Defence Position', d: "Accused's statement, defence witnesses, alibi or alternative theories" },
            ].map(s => (
              <TemplateSection key={s.n} number={s.n} title={s.t} description={s.d} />
            ))}

            <TextInput
              style={[styles.textArea, inputFocused && styles.textAreaFocused]}
              placeholder="Enter your case description following the template above..."
              placeholderTextColor={colors.textMuted}
              value={caseDescription}
              onChangeText={setCaseDescription}
              onFocus={() => setInputFocused(true)}
              onBlur={() => setInputFocused(false)}
              multiline
              editable={!analyzing}
              textAlignVertical="top"
            />

            <View style={styles.countRow}>
              <Text style={styles.countText}>📝 {wordCount} words · {caseDescription.length} chars</Text>
              <View style={styles.charProgressTrack}>
                <View style={[styles.charProgressFill, {
                  width: `${charProgress * 100}%` as any,
                  backgroundColor: charProgress >= 1 ? '#059669' : colors.accent,
                }]} />
              </View>
            </View>

            {caseDescription.length > 0 && caseDescription.length < 100 && (
              <Text style={styles.warningText}>⚠️ At least 100 characters needed for accurate prediction</Text>
            )}
            {error && (
              <View style={styles.errorBox}>
                <Text style={styles.errorText}>⚠️ {error}</Text>
              </View>
            )}

            <Button
              onPress={handlePredict}
              disabled={analyzing || !caseDescription.trim()}
              style={styles.analyzeBtn}
            >
              {analyzing ? '⏳ Analyzing...' : '🔮 Predict Appeal Outcome'}
            </Button>
          </Card>

          {/* ── Progress + Skeletons ── */}
          {analyzing && (
            <>
              <ProgressTracker step={progressStep} text={progressText} />
              <SkeletonCard />
              <SkeletonCard />
            </>
          )}

          {/* ── Results ── */}
          {result && (() => {
            const theme = getTheme(result.prediction);
            return (
              <>
                {/* 1. Animated Verdict Banner */}
                <VerdictBanner prediction={result.prediction} confidence={result.confidence} />

                <SectionDivider label="📊 PREDICTION ANALYSIS" />

                {/* 2. Confidence Ring + hero stats */}
                <Card style={[styles.resultCard, { borderTopWidth: 4, borderTopColor: theme.color }]}>
                  <View style={[styles.heroRow, isNarrow && styles.heroRowNarrow]}>
                    <ConfidenceRing confidence={result.confidence} color={theme.color} />
                    <View style={[styles.heroStats, isNarrow && styles.heroStatsNarrow]}>
                      <View style={[styles.heroStatItem, { backgroundColor: theme.light }]}>
                        <Text style={[styles.heroStatNum, { color: theme.color }]}>
                          {theme.icon} {theme.label}
                        </Text>
                        <Text style={styles.heroStatLabel}>Predicted Outcome</Text>
                      </View>
                      <View style={styles.heroStatItem}>
                        <Text style={styles.heroStatNum}>
                          {isDetailed(result) ? '⚡ Enhanced' : `${countDetectedFeatures(result.detected_features)} found`}
                        </Text>
                        <Text style={styles.heroStatLabel}>
                          {isDetailed(result) ? 'Analysis Level' : 'Features Detected'}
                        </Text>
                      </View>
                    </View>
                  </View>
                </Card>

                {/* 3. Detected Features with pill chips */}
                <Card style={styles.resultCard} title="🔍 AI-Detected Features">
                  {isDetailed(result) ? (
                    <View style={styles.enhancedSection}>
                      <View style={styles.legalReasoningBox}>
                        <Text style={styles.legalReasoningEyebrow}>AI Legal Reasoning</Text>
                        <Text style={styles.legalReasoning}>{result.legal_reasoning}</Text>
                      </View>
                      <View style={[styles.detectedFeaturesGrid, isNarrow && styles.detectedFeaturesGridNarrow]}>
                        <View style={styles.featureCol}>
                          <Text style={styles.featureSectionTitle}>⚖️ Grounds</Text>
                          {(result.key_factors?.length ?? 0) > 0
                            ? result.key_factors.slice(0, 3).map((f: any, i: number) => (
                                <PillChip key={i} label={f.factor_name} accentColor="#059669" />
                              ))
                            : <Text style={styles.noFeaturesText}>None detected</Text>}
                        </View>
                        <View style={styles.featureCol}>
                          <Text style={styles.featureSectionTitle}>🔬 Evidence</Text>
                          {(result.detected_features?.evidence?.length ?? 0) > 0
                            ? result.detected_features.evidence.slice(0, 3).map((ev: string, i: number) => (
                                <PillChip key={i} label={ev} accentColor="#D97706" />
                              ))
                            : <Text style={styles.noFeaturesText}>None detected</Text>}
                        </View>
                      </View>
                      <View style={[styles.compactRow, isNarrow && styles.compactRowNarrow]}>
                        {result.risk_assessment && (
                          <View style={styles.compactItem}>
                            <Text style={styles.compactLabel}>⚠️ Risk Level</Text>
                            <Text style={styles.compactValue}>{result.risk_assessment.split(':')[0]}</Text>
                          </View>
                        )}
                        {(result.strategy_recommendations?.length ?? 0) > 0 && (
                          <View style={styles.compactItem}>
                            <Text style={styles.compactLabel}>💡 Strategy</Text>
                            <Text style={styles.compactValue}>{result.strategy_recommendations[0].recommendation.split(' ')[0]}</Text>
                          </View>
                        )}
                      </View>
                    </View>
                  ) : (
                    <View>
                      {result.detected_features && countDetectedFeatures(result.detected_features) > 0 ? (
                        <>
                          <View style={[styles.featuresSuccessBanner, { backgroundColor: '#ECFDF5', borderColor: '#059669' }]}>
                            <Text style={{ color: '#059669', fontWeight: '700', fontSize: 14 }}>
                              ✅ {countDetectedFeatures(result.detected_features)} features detected
                            </Text>
                          </View>
                          <View style={styles.detectedFeaturesGrid}>
                            {(result.detected_features.grounds?.length ?? 0) > 0 && (
                              <View style={styles.featureCol}>
                                <Text style={styles.featureSectionTitle}>⚖️ Grounds</Text>
                                {result.detected_features.grounds.slice(0, 3).map((g: string, i: number) => (
                                  <PillChip key={i} label={g} accentColor="#059669" />
                                ))}
                              </View>
                            )}
                            {(result.detected_features.evidence?.length ?? 0) > 0 && (
                              <View style={styles.featureCol}>
                                <Text style={styles.featureSectionTitle}>🔬 Evidence</Text>
                                {result.detected_features.evidence.slice(0, 3).map((e: string, i: number) => (
                                  <PillChip key={i} label={e} accentColor="#D97706" />
                                ))}
                              </View>
                            )}
                            {(result.detected_features.offence?.length ?? 0) > 0 && (
                              <View style={styles.featureCol}>
                                <Text style={styles.featureSectionTitle}>📋 Offence</Text>
                                {result.detected_features.offence.slice(0, 2).map((o: string, i: number) => (
                                  <PillChip key={i} label={o} accentColor="#6366F1" />
                                ))}
                              </View>
                            )}
                          </View>
                        </>
                      ) : (
                        <View style={styles.limitedInfoBox}>
                          <Text style={styles.limitedInfoTitle}>⚠️ Limited Features Detected</Text>
                          <Text style={styles.limitedInfoText}>
                            {`Include:\n• Grounds of appeal (contradictions, chain of custody)\n• Evidence types (eyewitness, medical, forensic)\n• Offence category (murder, drug trafficking, etc.)`}
                          </Text>
                        </View>
                      )}
                    </View>
                  )}
                </Card>

                {/* Enhanced Legal Analysis */}
                {isDetailed(result) && (
                  <Card style={styles.resultCard} title="⚖️ Legal Analysis">
                    <View style={styles.enhancedSection}>
                      <View style={styles.legalReasoningBox}>
                        <Text style={styles.legalReasoningEyebrow}>Detailed Reasoning</Text>
                        <Text style={styles.legalReasoning}>{result.legal_reasoning}</Text>
                      </View>
                      {(result.key_factors?.length ?? 0) > 0 && (
                        <View>
                          <Text style={styles.compactSectionLabel}>🎯 Key Factors</Text>
                          {result.key_factors.slice(0, 3).map((factor: any, i: number) => (
                            <View key={i} style={styles.factorItem}>
                              <View style={[styles.factorDot, { backgroundColor: theme.color }]} />
                              <Text style={styles.factorName}>{factor.factor_name}</Text>
                            </View>
                          ))}
                        </View>
                      )}
                      <View style={styles.compactRow}>
                        {result.risk_assessment && (
                          <View style={styles.compactItem}>
                            <Text style={styles.compactLabel}>⚠️ Risk</Text>
                            <Text style={styles.compactValue}>{result.risk_assessment.split(':')[0]}</Text>
                          </View>
                        )}
                        {(result.strategy_recommendations?.length ?? 0) > 0 && (
                          <View style={styles.compactItem}>
                            <Text style={styles.compactLabel}>💡 Strategy</Text>
                            <Text style={styles.compactValue}>{result.strategy_recommendations[0].recommendation.split(' ')[0]}</Text>
                          </View>
                        )}
                      </View>
                    </View>
                  </Card>
                )}

                {/* 4. Animated Probability Bars */}
                <ProbabilityMeters probabilities={result.probabilities} />

                {extResult?.context_analysis && <ContextSection context={extResult.context_analysis} />}
                {extResult?.grounds_analysis && Object.keys(extResult.grounds_analysis).length > 0 && (
                  <GroundsOrEvidenceSection title="⚖️ Grounds Analysis" data={extResult.grounds_analysis} />
                )}
                {extResult?.evidence_analysis && Object.keys(extResult.evidence_analysis).length > 0 && (
                  <GroundsOrEvidenceSection title="🔬 Evidence Impact" data={extResult.evidence_analysis} />
                )}

                {/* Why This Prediction */}
                <Card style={styles.resultCard} title="💡 Why This Prediction?">
                  <View style={styles.reasoningSection}>
                    <Text style={styles.reasoningText}>
                      {'Based on '}
                      <Text style={{ fontWeight: '700' }}>{flatFeatures(result.detected_features).join(', ')}</Text>
                      {' and legal pattern analysis:'}
                    </Text>
                    {result.prediction === 'Appeal_Allowed' && result.confidence > 60 && (
                      <View style={[styles.reasoningBlock, { borderLeftColor: '#059669', backgroundColor: '#ECFDF5' }]}>
                        <Text style={[styles.reasoningTitle, { color: '#059669' }]}>🟢 Strong indicators for Appeal Allowed</Text>
                        <Text style={styles.reasoningPoints}>
                          {`• Grounds: ${result.detected_features?.grounds?.slice(0, 3).join(', ') || 'Procedural/evidentiary issues'}\n• Pattern matches successful appeal precedents\n• Confidence ${result.confidence.toFixed(1)}% indicates strong legal grounds`}
                        </Text>
                      </View>
                    )}
                    {result.prediction === 'Appeal_Dismissed' && result.confidence > 60 && (
                      <View style={[styles.reasoningBlock, { borderLeftColor: '#DC2626', backgroundColor: '#FEF2F2' }]}>
                        <Text style={[styles.reasoningTitle, { color: '#DC2626' }]}>🔴 Strong indicators for Dismissal</Text>
                        <Text style={styles.reasoningPoints}>
                          {`• Evidence: ${result.detected_features?.evidence?.slice(0, 3).join(', ') || 'Strong prosecution evidence'}\n• Historical similar cases mostly dismissed\n• Confidence ${result.confidence.toFixed(1)}% suggests solid conviction basis`}
                        </Text>
                      </View>
                    )}
                    {result.confidence < 55 && (
                      <View style={[styles.reasoningBlock, { borderLeftColor: '#D97706', backgroundColor: '#FFFBEB' }]}>
                        <Text style={[styles.reasoningTitle, { color: '#D97706' }]}>🟡 Mixed signals — borderline case</Text>
                        <Text style={styles.reasoningPoints}>
                          {`• Competing factors make outcome uncertain\n• Both prosecution strengths and defence grounds present\n• Low confidence (${result.confidence.toFixed(1)}%) indicates close case`}
                        </Text>
                      </View>
                    )}
                  </View>
                </Card>

                {/* Feature Detection */}
                <Card style={styles.resultCard} title="🔍 Feature Detection">
                  <View style={styles.zoneRoot}>
                    <View style={[styles.zoneRootBadge, { backgroundColor: theme.color }]}>
                      <Text style={styles.zoneRootBadgeText}>⚖</Text>
                    </View>
                    <View>
                      <Text style={styles.zoneRootTitle}>Legal Analysis Complete</Text>
                      <Text style={styles.zoneRootSub}>{countDetectedFeatures(result.detected_features)} features extracted</Text>
                    </View>
                  </View>
                  <View style={styles.zoneTwoCol}>
                    <View style={styles.zoneSection}>
                      <Text style={[styles.zoneLabel, { color: '#059669' }]}>⚖️ Grounds</Text>
                      {(result.detected_features?.grounds?.length ?? 0) > 0
                        ? result.detected_features.grounds.map((g: string, i: number) => (
                            <View key={i} style={[styles.treeItem, { borderLeftColor: '#059669' }]}>
                              <Text style={styles.treeItemTitle}>{g}</Text>
                            </View>
                          ))
                        : <Text style={styles.emptyState}>None detected</Text>}
                    </View>
                    <View style={styles.zoneSection}>
                      <Text style={[styles.zoneLabel, { color: '#D97706' }]}>🔬 Evidence</Text>
                      {(result.detected_features?.evidence?.length ?? 0) > 0
                        ? result.detected_features.evidence.map((e: string, i: number) => (
                            <View key={i} style={[styles.treeItem, { borderLeftColor: '#D97706' }]}>
                              <Text style={styles.treeItemTitle}>{e}</Text>
                            </View>
                          ))
                        : <Text style={styles.emptyState}>None detected</Text>}
                    </View>
                  </View>
                  <View style={styles.zoneSideBySide}>
                    {(result.detected_features?.offence?.length ?? 0) > 0 && (
                      <View style={styles.zoneColumn}>
                        <Text style={[styles.zoneLabel, { color: '#6366F1' }]}>📋 Offence</Text>
                        {result.detected_features.offence.map((o: string, i: number) => (
                          <View key={i} style={[styles.treeItem, { borderLeftColor: '#6366F1' }]}>
                            <Text style={styles.treeItemTitle}>{o}</Text>
                          </View>
                        ))}
                      </View>
                    )}
                    {(result.detected_features?.other?.length ?? 0) > 0 && (
                      <View style={styles.zoneColumn}>
                        <Text style={[styles.zoneLabel, { color: colors.textSecondary }]}>📎 Other</Text>
                        {result.detected_features.other.slice(0, 3).map((o: string, i: number) => (
                          <View key={i} style={styles.treeItem}>
                            <Text style={styles.treeItemTitle}>{o}</Text>
                          </View>
                        ))}
                      </View>
                    )}
                  </View>
                </Card>

                <SectionDivider label="📚 SIMILAR PRECEDENTS" />

                {/* 5. Similar Cases with all improvements */}
                <Card style={styles.resultCard} title="📚 Similar Historical Cases">
                  <Text style={styles.sectionSubtitle}>AI-matched court case precedents</Text>

                  {/* Aggregate outcome bar */}
                  {(() => {
                    const cases = result.similar_cases.slice(0, 3);
                    const allowed = cases.filter(c => c.outcome === 'Appeal_Allowed').length;
                    const dismissed = cases.filter(c => c.outcome === 'Appeal_Dismissed').length;
                    const partly = cases.filter(c => c.outcome === 'Partly_Allowed').length;
                    return (
                      <View style={styles.aggregateBar}>
                        <Text style={styles.aggregateLabel}>Precedent Outcome Split ({cases.length} cases)</Text>
                        <View style={styles.stackedBarContainer}>
                          {allowed > 0 && <View style={[styles.stackedSegment, { flex: allowed, backgroundColor: '#059669' }]} />}
                          {partly > 0 && <View style={[styles.stackedSegment, { flex: partly, backgroundColor: '#D97706' }]} />}
                          {dismissed > 0 && <View style={[styles.stackedSegment, { flex: dismissed, backgroundColor: '#DC2626' }]} />}
                        </View>
                        <View style={styles.analysisLegend}>
                          {allowed > 0 && <Text style={[styles.legendItem, { color: '#059669' }]}>✅ {allowed} Allowed</Text>}
                          {partly > 0 && <Text style={[styles.legendItem, { color: '#D97706' }]}>⚖️ {partly} Partly</Text>}
                          {dismissed > 0 && <Text style={[styles.legendItem, { color: '#DC2626' }]}>❌ {dismissed} Dismissed</Text>}
                        </View>
                      </View>
                    );
                  })()}

                  {result.similar_cases.slice(0, 3).map((c, idx) => {
                    const simPct = c.similarity_score ? Math.round(c.similarity_score * 100) : 0;
                    const cTheme = getTheme(c.outcome ?? '');
                    const simBadge = simBadgeStyle(simPct);
                    const summary = c.case_summary || c.facts || 'Details not available';

                    return (
                      <View key={idx} style={[styles.caseCard, { borderLeftWidth: 4, borderLeftColor: cTheme.color }]}>
                        {/* Case header */}
                        <View style={styles.caseHeader}>
                          <View style={{ flex: 1 }}>
                            <Text style={styles.caseId}>#{idx + 1} {c.case_id}</Text>
                          </View>
                          <View style={{ flexDirection: 'row', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
                            <View style={[styles.simBadge, { backgroundColor: simBadge.bg }]}>
                              <Text style={[styles.simBadgeText, { color: simBadge.text }]}>{simPct}% match</Text>
                            </View>
                            <View style={[styles.caseOutcome, { backgroundColor: cTheme.bg }]}>
                              <Text style={[styles.caseOutcomeText, { color: cTheme.text }]}>
                                {cTheme.icon} {cTheme.label}
                              </Text>
                            </View>
                          </View>
                        </View>

                        {/* 2-column metadata grid */}
                        <View style={styles.metaGrid}>
                          {c.decision_date && (
                            <View style={styles.metaGridItem}>
                              <Text style={styles.metaGridLabel}>📅 Decision Date</Text>
                              <Text style={styles.metaGridValue}>{c.decision_date}</Text>
                            </View>
                          )}
                          {c.offence && c.offence !== 'Not specified' && (
                            <View style={styles.metaGridItem}>
                              <Text style={styles.metaGridLabel}>📋 Offence</Text>
                              <Text style={styles.metaGridValue}>{c.offence}</Text>
                            </View>
                          )}
                          {c.high_court && c.high_court !== 'Not specified' && (
                            <View style={styles.metaGridItem}>
                              <Text style={styles.metaGridLabel}>🏛️ High Court</Text>
                              <Text style={styles.metaGridValue}>{c.high_court}</Text>
                            </View>
                          )}
                          {c.conviction_status && c.conviction_status !== 'Not specified' && (
                            <View style={styles.metaGridItem}>
                              <Text style={styles.metaGridLabel}>✓ Conviction</Text>
                              <Text style={styles.metaGridValue}>{c.conviction_status}</Text>
                            </View>
                          )}
                        </View>

                        {/* Case Details */}
                        <View style={styles.caseFacts}>
                          <Text style={styles.caseFactsLabel}>📖 Case Details</Text>
                          <ExpandableText text={summary} style={styles.caseFactsText} />
                        </View>

                        {/* Verdict Reasoning */}
                        {c.verdict_reasoning && c.verdict_reasoning !== 'Not specified' && (
                          <View style={[styles.reasoningBlock, { marginTop: 12, borderLeftColor: cTheme.color, backgroundColor: cTheme.light }]}>
                            <Text style={[styles.reasoningTitle, { color: cTheme.color }]}>⚖️ Verdict Reasoning</Text>
                            <ExpandableText text={c.verdict_reasoning} style={styles.reasoningPoints} />
                          </View>
                        )}

                        {/* Judge Commentary */}
                        {c.judge_commentary && c.judge_commentary !== 'Not specified' && (
                          <View style={[styles.reasoningBlock, { marginTop: 12, borderLeftColor: '#8B5CF6', backgroundColor: '#F5F3FF' }]}>
                            <Text style={[styles.reasoningTitle, { color: '#8B5CF6' }]}>💬 Judge's Commentary</Text>
                            <ExpandableText text={c.judge_commentary} style={styles.reasoningPoints} />
                          </View>
                        )}

                        {/* Appeal grounds as pill chips */}
                        {(c.appeal_grounds_list?.length ?? 0) > 0 && (
                          <View style={{ marginTop: 12 }}>
                            <Text style={styles.compactSectionLabel}>🔗 Appeal Grounds</Text>
                            {c.appeal_grounds_list.slice(0, 3).map((g: string, gIdx: number) => (
                              <PillChip key={gIdx} label={g} accentColor={cTheme.color} />
                            ))}
                            {c.appeal_grounds_list.length > 3 && (
                              <Text style={styles.moreLabel}>+{c.appeal_grounds_list.length - 3} more</Text>
                            )}
                          </View>
                        )}

                        {/* Evidence type chips */}
                        {(c.evidence_types?.length ?? 0) > 0 && (
                          <View style={{ marginTop: 12 }}>
                            <Text style={styles.compactSectionLabel}>🔬 Evidence Types</Text>
                            <View style={styles.chipRow}>
                              {c.evidence_types.slice(0, 4).map((ev: string, eIdx: number) => (
                                <View key={eIdx} style={styles.evidenceChip}>
                                  <Text style={styles.evidenceChipText}>{ev}</Text>
                                </View>
                              ))}
                              {c.evidence_types.length > 4 && (
                                <Text style={styles.moreLabel}>+{c.evidence_types.length - 4} more</Text>
                              )}
                            </View>
                          </View>
                        )}

                        {/* Animated success rate bar */}
                        {c.appeal_success_rate != null && (
                          <View style={{ marginTop: 12 }}>
                            <View style={styles.meterRow}>
                              <Text style={styles.meterLabel}>📈 Success Rate</Text>
                              <View style={{ flex: 2 }}>
                                <AnimatedBar value={c.appeal_success_rate * 100} color="#059669" height={6} />
                              </View>
                              <Text style={[styles.meterPct, { color: '#059669' }]}>
                                {(c.appeal_success_rate * 100).toFixed(0)}%
                              </Text>
                            </View>
                          </View>
                        )}

                        {/* Footer row */}
                        <View style={styles.caseFooterRow}>
                          {c.precedent_value && (
                            <View style={[styles.precedentBadge, {
                              backgroundColor: c.precedent_value.includes('High') ? '#DBEAFE' : '#F3E8FF',
                            }]}>
                              <Text style={[styles.precedentText, {
                                color: c.precedent_value.includes('High') ? '#1E40AF' : '#6D28D9',
                              }]}>
                                🏅 {c.precedent_value}
                              </Text>
                            </View>
                          )}
                          {c.year && <Text style={styles.yearLabel}>📅 {c.year}</Text>}
                        </View>
                      </View>
                    );
                  })}
                </Card>
              </>
            );
          })()}

        </View>
      </Container>
    </Layout>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  mainCol: { flex: 1, gap: spacing.lg },

  // ── Read More ──
  readMoreLink: { color: colors.accent, fontWeight: '700', fontSize: 12 },

  // ── Input ──
  inputCard: { marginTop: spacing.sm },
  templateTitle: { fontSize: 15, fontWeight: '600', color: colors.textSecondary, marginBottom: spacing.md },
  templateSection: {
    flexDirection: 'row', alignItems: 'flex-start',
    marginBottom: spacing.sm, padding: spacing.sm,
    backgroundColor: colors.bgSection, borderRadius: borderRadius.md, gap: spacing.sm,
  },
  templateNumBadge: {
    width: 26, height: 26, borderRadius: 13,
    backgroundColor: colors.accent, alignItems: 'center', justifyContent: 'center', marginTop: 1,
  },
  templateNumText: { fontSize: 12, fontWeight: '800', color: '#fff' },
  sectionContent: { flex: 1 },
  templateSectionTitle: { fontSize: 13, fontWeight: '700', color: colors.textPrimary, marginBottom: 2 },
  sectionDesc: { fontSize: 12, color: colors.textSecondary, lineHeight: 16 },

  textArea: {
    marginTop: spacing.md, borderWidth: 1.5, borderColor: colors.border,
    borderRadius: borderRadius.md, padding: spacing.md, minHeight: 140,
    fontSize: 14, color: colors.textPrimary, backgroundColor: colors.bgCard, textAlignVertical: 'top',
  },
  textAreaFocused: {
    borderColor: colors.accent,
    shadowColor: colors.accent,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.2, shadowRadius: 6, elevation: 4,
  },

  countRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: spacing.sm },
  countText: { fontSize: 12, color: colors.textMuted },
  charProgressTrack: { width: 80, height: 4, backgroundColor: colors.border, borderRadius: 2, overflow: 'hidden' },
  charProgressFill: { height: '100%', borderRadius: 2 },

  warningText: { fontSize: 12, color: '#D97706', marginTop: spacing.xs },
  errorBox: {
    backgroundColor: '#FEF2F2', borderRadius: borderRadius.sm,
    padding: spacing.sm, marginTop: spacing.sm, borderWidth: 1, borderColor: '#FCA5A5',
  },
  errorText: { color: '#DC2626', fontSize: 13 },
  analyzeBtn: { width: '100%', marginTop: spacing.md },

  // ── Progress ──
  progressCard: { marginTop: spacing.md },
  progressContainer: { gap: spacing.md },
  progressText: { fontSize: 14, fontWeight: '500', color: colors.primary, textAlign: 'center' },
  progressSteps: { flexDirection: 'row', justifyContent: 'space-between' },
  progressStepsNarrow: { flexDirection: 'column', gap: spacing.md, alignItems: 'center' },
  progressStep: { alignItems: 'center', flex: 1 },
  progressStepNarrow: { width: '100%', flexDirection: 'row', gap: spacing.md, justifyContent: 'flex-start' },
  progressStepCircle: {
    width: 28, height: 28, borderRadius: 14, backgroundColor: colors.border,
    alignItems: 'center', justifyContent: 'center', marginBottom: 4,
  },
  progressStepCheck: { fontSize: 13, color: '#fff', fontWeight: '700' },
  progressStepNum: { fontSize: 12, fontWeight: '600', color: colors.textMuted },
  progressStepNumActive: { color: '#fff' },
  progressStepLabel: { fontSize: 10, color: colors.textMuted, textAlign: 'center' },
  progressBarContainer: { height: 5, backgroundColor: colors.border, borderRadius: 3, overflow: 'hidden' },
  progressBar: { height: '100%', backgroundColor: colors.accent, borderRadius: 3 },

  // ── Skeleton ──
  skeletonCard: {
    backgroundColor: colors.bgCard, borderRadius: borderRadius.md,
    padding: spacing.md, borderWidth: 1, borderColor: colors.border, marginTop: spacing.md,
  },
  skeletonLine: { backgroundColor: colors.border, borderRadius: 4 },
  skeletonGrid: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.sm },
  skeletonBox: { flex: 1, height: 60, backgroundColor: colors.border, borderRadius: borderRadius.sm },

  // ── Verdict Banner ──
  verdictBanner: {
    borderRadius: borderRadius.lg, padding: spacing.md,
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    marginTop: spacing.sm,
    shadowColor: '#000', shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.18, shadowRadius: 8, elevation: 6,
  },
  verdictBannerNarrow: {
    flexDirection: 'column',
    gap: spacing.md,
    alignItems: 'center',
  },
  verdictBannerLeft: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  verdictBannerLeftNarrow: {
    flexDirection: 'column',
    alignItems: 'center',
    textAlign: 'center',
  },
  verdictIcon: { fontSize: 32 },
  verdictBannerLabel: {
    fontSize: 10, fontWeight: '700', color: 'rgba(255,255,255,0.75)',
    letterSpacing: 1, textTransform: 'uppercase',
  },
  verdictBannerOutcome: { fontSize: 18, fontWeight: '800', color: '#fff', marginTop: 2 },
  verdictConfBadge: { alignItems: 'center', padding: spacing.sm, borderRadius: borderRadius.md },
  verdictConfText: { fontSize: 22, fontWeight: '800', color: '#fff' },
  verdictConfLabel: { fontSize: 10, color: 'rgba(255,255,255,0.8)', textTransform: 'uppercase', letterSpacing: 0.5 },

  // ── Section Divider ──
  dividerRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginTop: spacing.sm },
  dividerLine: { flex: 1, height: 1, backgroundColor: colors.border },
  dividerLabel: { fontSize: 11, fontWeight: '700', color: colors.textMuted, letterSpacing: 1 },

  // ── Result Card ──
  resultCard: {
    marginTop: spacing.md, backgroundColor: colors.bgCard,
    borderWidth: 1, borderColor: colors.border,
    borderRadius: borderRadius.lg, overflow: 'hidden',
  },

  // ── Hero Row ──
  heroRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.lg, padding: spacing.sm },
  heroRowNarrow: { flexDirection: 'column' },
  heroStats: { flex: 1, gap: spacing.sm },
  heroStatsNarrow: { width: '100%' },
  heroStatItem: { backgroundColor: colors.bgSection, borderRadius: borderRadius.md, padding: spacing.sm },
  heroStatNum: { fontSize: 14, fontWeight: '700', color: colors.textPrimary },
  heroStatLabel: { fontSize: 11, color: colors.textSecondary, marginTop: 2 },

  // ── Confidence Ring ──
  ringContainer: { width: 100, height: 100, alignItems: 'center', justifyContent: 'center' },
  ringOuter: { position: 'absolute', width: 96, height: 96, borderRadius: 48, borderWidth: 8 },
  ringProgress: { position: 'absolute', width: 96, height: 96, borderRadius: 48, borderWidth: 8 },
  ringInner: { alignItems: 'center', justifyContent: 'center' },
  ringPct: { fontSize: 22, fontWeight: '800' },
  ringLabel: { fontSize: 10, color: colors.textMuted, textTransform: 'uppercase', letterSpacing: 0.5 },

  // ── Animated Bars ──
  barTrack: { backgroundColor: colors.border, borderRadius: 4, overflow: 'hidden' },
  barFill: { borderRadius: 4 },

  // ── Pill Chips ──
  pillChip: {
    borderLeftWidth: 3, backgroundColor: colors.bgSection,
    paddingVertical: 5, paddingHorizontal: spacing.sm,
    borderRadius: borderRadius.sm, marginBottom: spacing.xs,
  },
  pillChipText: { fontSize: 12, fontWeight: '500', color: colors.textPrimary },

  // ── Features ──
  enhancedSection: { gap: spacing.md },
  legalReasoningBox: {
    backgroundColor: colors.bgSection, borderRadius: borderRadius.md,
    padding: spacing.md, borderLeftWidth: 3, borderLeftColor: colors.accent,
  },
  legalReasoningEyebrow: {
    fontSize: 10, fontWeight: '700', color: colors.accent,
    textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4,
  },
  legalReasoning: { fontSize: 14, lineHeight: 21, color: colors.textPrimary },
  detectedFeaturesGrid: { flexDirection: 'row', gap: spacing.md, marginTop: spacing.sm },
  featureCol: { flex: 1 },
  featureSectionTitle: { fontSize: 13, fontWeight: '700', color: colors.textPrimary, marginBottom: spacing.sm },
  noFeaturesText: { fontSize: 11, color: colors.textMuted, fontStyle: 'italic' },
  featuresSuccessBanner: { padding: spacing.sm, borderRadius: borderRadius.sm, borderWidth: 1, marginBottom: spacing.md },
  limitedInfoBox: {
    backgroundColor: '#FEF3C7', padding: spacing.md,
    borderRadius: borderRadius.md, borderWidth: 1, borderColor: '#F59E0B',
  },
  limitedInfoTitle: { fontSize: 14, fontWeight: '600', color: '#D97706', marginBottom: spacing.sm },
  limitedInfoText: { fontSize: 12, color: '#92400E', lineHeight: 18 },

  // ── Compact ──
  compactRow: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.sm },
  compactItem: { flex: 1, backgroundColor: colors.bgSection, padding: spacing.sm, borderRadius: borderRadius.sm },
  compactLabel: { fontSize: 11, color: colors.textMuted, marginBottom: 2 },
  compactValue: { fontSize: 12, fontWeight: '600', color: colors.textPrimary },
  compactSectionLabel: { fontSize: 13, fontWeight: '700', color: colors.textPrimary, marginBottom: spacing.sm },
  factorItem: {
    flexDirection: 'row', alignItems: 'center', gap: spacing.sm,
    paddingVertical: spacing.xs, paddingHorizontal: spacing.sm,
    backgroundColor: colors.bgSection, borderRadius: borderRadius.sm, marginBottom: spacing.xs,
  },
  factorDot: { width: 8, height: 8, borderRadius: 4 },
  factorName: { fontSize: 13, fontWeight: '500', color: colors.textPrimary, flex: 1 },

  // ── Probability Meters ──
  meterRow: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.sm, gap: spacing.sm },
  meterLabel: { flex: 1, fontSize: 13, color: colors.textSecondary, fontWeight: '500' },
  meterPct: { fontSize: 13, fontWeight: '700', minWidth: 42, textAlign: 'right' },

  // ── Stacked Bars ──
  stackedBarContainer: {
    flexDirection: 'row', height: 10, borderRadius: 5,
    overflow: 'hidden', backgroundColor: colors.border, marginBottom: spacing.xs,
  },
  stackedSegment: { height: '100%' },
  caseCountBadge: { backgroundColor: colors.bgSection, paddingHorizontal: 8, paddingVertical: 2, borderRadius: 10 },
  caseCountText: { fontSize: 11, color: colors.textMuted, fontWeight: '600' },
  aggregateBar: {
    marginBottom: spacing.lg, padding: spacing.md,
    backgroundColor: colors.bgSection, borderRadius: borderRadius.md,
  },
  aggregateLabel: { fontSize: 12, fontWeight: '600', color: colors.textSecondary, marginBottom: spacing.sm },

  // ── Context / Analysis ──
  analysisRow: { marginBottom: spacing.md },
  analysisRowHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.xs },
  analysisLabel: { fontSize: 13, fontWeight: '600', color: colors.textPrimary, flex: 1, marginRight: spacing.sm },
  analysisLegend: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 4 },
  legendItem: { fontSize: 11, fontWeight: '600' },

  // ── Reasoning ──
  reasoningSection: { gap: spacing.md },
  reasoningText: { fontSize: 14, color: colors.textPrimary, lineHeight: 20 },
  reasoningBlock: { padding: spacing.md, borderRadius: borderRadius.md, borderLeftWidth: 4 },
  reasoningTitle: { fontSize: 14, fontWeight: '700', marginBottom: spacing.sm },
  reasoningPoints: { fontSize: 13, color: colors.textPrimary, lineHeight: 18 },

  // ── Zone / Tree ──
  zoneRoot: {
    flexDirection: 'row', alignItems: 'center', marginBottom: spacing.md,
    padding: spacing.md, backgroundColor: colors.bgSection,
    borderRadius: borderRadius.md, gap: spacing.md,
  },
  zoneRootBadge: { width: 42, height: 42, borderRadius: 21, alignItems: 'center', justifyContent: 'center' },
  zoneRootBadgeText: { fontSize: 20, color: '#fff' },
  zoneRootTitle: { fontSize: 15, fontWeight: '700', color: colors.textPrimary },
  zoneRootSub: { fontSize: 12, color: colors.textSecondary, marginTop: 2 },
  zoneTwoCol: { flexDirection: 'row', gap: spacing.md, marginBottom: spacing.md },
  zoneSection: { flex: 1 },
  zoneLabel: { fontSize: 13, fontWeight: '700', marginBottom: spacing.sm },
  zoneSideBySide: { flexDirection: 'row', gap: spacing.md },
  zoneColumn: { flex: 1 },
  treeItem: {
    paddingVertical: spacing.sm, paddingHorizontal: spacing.sm,
    borderLeftWidth: 3, borderLeftColor: colors.border,
    backgroundColor: colors.bgSection, borderRadius: borderRadius.sm, marginBottom: spacing.xs,
  },
  treeItemTitle: { fontSize: 12, fontWeight: '600', color: colors.textPrimary },
  emptyState: { fontSize: 12, color: colors.textMuted, fontStyle: 'italic', textAlign: 'center', padding: spacing.sm },

  // ── Similar Cases ──
  sectionSubtitle: { fontSize: 13, color: colors.textMuted, fontStyle: 'italic', marginBottom: spacing.md },
  caseCard: {
    backgroundColor: colors.bgCard, borderRadius: borderRadius.lg,
    padding: spacing.md, borderWidth: 1, borderColor: colors.border, marginBottom: spacing.md,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06, shadowRadius: 4, elevation: 2,
  },
  caseHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: spacing.sm },
  caseId: { fontSize: 14, fontWeight: '700', color: colors.textPrimary },
  simBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 10 },
  simBadgeText: { fontSize: 11, fontWeight: '700' },
  caseOutcome: { paddingHorizontal: spacing.sm, paddingVertical: 4, borderRadius: 10 },
  caseOutcomeText: { fontSize: 11, fontWeight: '700' },

  // 2-column metadata grid
  metaGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginBottom: spacing.sm },
  metaGridItem: { width: '47%', backgroundColor: colors.bgSection, padding: spacing.sm, borderRadius: borderRadius.sm },
  metaGridLabel: {
    fontSize: 10, color: colors.textMuted, fontWeight: '600',
    textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 2,
  },
  metaGridValue: { fontSize: 12, color: colors.textPrimary, fontWeight: '500' },

  caseFacts: { marginTop: spacing.xs },
  caseFactsLabel: {
    fontSize: 11, color: colors.textMuted, fontWeight: '700',
    marginBottom: 4, textTransform: 'uppercase', letterSpacing: 0.5,
  },
  caseFactsText: { fontSize: 13, color: colors.textSecondary, lineHeight: 18 },

  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  evidenceChip: { backgroundColor: colors.bgSection, paddingHorizontal: spacing.sm, paddingVertical: 4, borderRadius: 10 },
  evidenceChipText: { fontSize: 12, fontWeight: '500', color: colors.textPrimary },
  moreLabel: { fontSize: 12, color: colors.textMuted, marginTop: 4 },

  caseFooterRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginTop: spacing.md },
  precedentBadge: { paddingHorizontal: spacing.sm, paddingVertical: 4, borderRadius: 10 },
  precedentText: { fontSize: 12, fontWeight: '700' },
  yearLabel: { fontSize: 12, color: colors.textMuted },
});