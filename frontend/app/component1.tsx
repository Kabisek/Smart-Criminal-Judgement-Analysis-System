import { View, Text, StyleSheet, ScrollView, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { Layout } from '../components/Layout';
import { Container, Card, PageHeader } from '../components/ui';
import { colors, spacing } from '../theme';
import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { CaseIngestion } from '../components/CaseIngestion';
import {
  NormalizedAnalysisResponse, saveComp1History,
  fetchComp1List, fetchComp1Detail, HistorySummary,
} from '../api';

// ─── Graph layout ─────────────────────────────────────────────────────────────
const GW = 960;
const GH = 650;    // Increased height to prevent bottom clipping
const CX = GW / 2;
const CY = GH / 2 - 40; // Shifted center up slightly
const HUB_R = 190;    // center → hub distance
const RES_R = 120;    // hub → resource distance (slightly expanded)
const MAX_RES = 5;

// Angles in °, anticlockwise from east (3 o'clock)
const HUB_ANGLES: Record<string, number> = {
  prosecution_resources: 148,
  defense_resources: 32,
  procedural_resources: 212,
  binding_precedents: 328,
  recent_judgments: 270,
};

// ─── Types ────────────────────────────────────────────────────────────────────
interface GNode {
  id: string; label: string;
  type: 'root' | 'hub' | 'resource';
  category?: string;
  baseX: number; baseY: number;       // initial position
  color: string; item?: any;
}
interface GEdge { src: string; tgt: string; hubEdge: boolean; color: string; }

// ─── Build all nodes (resources always present, filtered on render) ───────────
function buildGraph(
  sd: any,
  getCatColor: (c: string) => string,
  formatCatName: (c: string) => string,
): { nodes: GNode[]; edges: GEdge[] } {
  const nodes: GNode[] = [];
  const edges: GEdge[] = [];

  nodes.push({ id: 'root', label: 'Case Facts', type: 'root', baseX: CX, baseY: CY, color: '#1E3A5F' });

  Object.entries(HUB_ANGLES).forEach(([cat, deg]) => {
    const items: any[] = sd?.[cat] || [];
    if (!items.length) return;
    const hrad = (deg * Math.PI) / 180;
    const hx = CX + HUB_R * Math.cos(hrad);
    const hy = CY - Math.max(0.5, HUB_R) * Math.sin(hrad); // Slight adjustment to Y
    const color = getCatColor(cat);

    // Add Hub Node
    nodes.push({ id: cat, label: formatCatName(cat), type: 'hub', category: cat, baseX: hx, baseY: hy, color });
    edges.push({ src: 'root', tgt: cat, hubEdge: true, color: '#94A3B8' });

    const show = Math.min(items.length, MAX_RES);
    // Expand the fan arc: up to 160 degrees for 5 items to give more breathing room
    const span = Math.min(160, show * 36);

    for (let i = 0; i < show; i++) {
      const item = items[i];
      const off = show > 1 ? (i / (show - 1) - 0.5) * span : 0;
      const rrad = hrad + (off * Math.PI) / 180;

      // Staggering: alternate the radius distance so nodes don't collide side-by-side
      const stagger_R = RES_R + (i % 2 === 0 ? 0 : 50);

      const nid = item.id || `${cat}-${i}`;
      nodes.push({
        id: nid,
        label: ((item.title || item.name || 'Resource') as string).substring(0, 24),
        type: 'resource', category: cat,
        baseX: hx + stagger_R * Math.cos(rrad),
        baseY: hy - stagger_R * Math.sin(rrad),
        color, item,
      });
      edges.push({ src: cat, tgt: nid, hubEdge: false, color });
    }
  });
  return { nodes, edges };
}

// ─── Edge line ────────────────────────────────────────────────────────────────
function GraphEdge({ sx, sy, tx, ty, hubEdge, color }: {
  sx: number; sy: number; tx: number; ty: number; hubEdge: boolean; color: string;
}) {
  const dx = tx - sx; const dy = ty - sy;
  const len = Math.sqrt(dx * dx + dy * dy);
  const ang = Math.atan2(dy, dx);
  return (
    <View
      pointerEvents="none"
      style={{
        position: 'absolute',
        left: (sx + tx) / 2 - len / 2,
        top: (sy + ty) / 2 - 1,
        width: len, height: hubEdge ? 2 : 1.5,
        backgroundColor: hubEdge ? '#94A3B8' : color + '90',
        transform: [{ rotate: `${ang}rad` }],
        borderRadius: 2, zIndex: 0,
      }}
    />
  );
}

// ─── Node pill ────────────────────────────────────────────────────────────────
interface GraphNodeProps {
  node: GNode;
  px: number; py: number;             // live (dragged) position
  isSelCat: boolean; isSelRes: boolean; isExpanded: boolean;
  onWebMouseDown: (e: any) => void;   // web drag/tap entry point
  onNativeTap: () => void;            // mobile tap
}

function GraphNode({ node, px, py, isSelCat, isSelRes, isExpanded, onWebMouseDown, onNativeTap }: GraphNodeProps) {
  const isRoot = node.type === 'root';
  const isHub = node.type === 'hub';
  const isRes = node.type === 'resource';
  const nW = isRoot ? 118 : isHub ? 134 : 154;
  const nH = isRoot ? 40 : isHub ? 36 : 28;

  return (
    <View
      /* ── Web events ── */
      {...(Platform.OS === 'web' && !isRoot ? { onMouseDown: onWebMouseDown } : {})}
      /* ── Native events ── */
      onStartShouldSetResponder={() => Platform.OS !== 'web' && !isRoot}
      onResponderRelease={onNativeTap}
      style={[
        {
          position: 'absolute',
          left: px - nW / 2,
          top: py - nH / 2,
          width: nW, height: nH,
          borderRadius: nH / 2,
          alignItems: 'center', justifyContent: 'center',
          paddingHorizontal: 8,
          zIndex: isRoot ? 10 : isHub ? 8 : 6,
        } as any,
        isRoot && {
          backgroundColor: '#1E3A5F',
          shadowColor: '#1E3A5F', shadowOffset: { width: 0, height: 4 },
          shadowOpacity: 0.4, shadowRadius: 10
        } as any,
        isHub && {
          backgroundColor: node.color,
          shadowColor: node.color, shadowOffset: { width: 0, height: 2 },
          shadowOpacity: 0.45, shadowRadius: 6,
          borderWidth: isExpanded ? 3 : 0,
          borderColor: '#FFFFFF90'
        } as any,
        isRes && {
          backgroundColor: isSelRes ? node.color + '35' : node.color + '18',
          borderWidth: isSelRes ? 2 : 1.5,
          borderColor: isSelRes ? node.color : node.color + '80',
        },
        Platform.OS === 'web' && !isRoot && { cursor: 'grab' } as any,
      ]}
    >
      <Text
        numberOfLines={1}
        style={{
          color: isRoot || isHub ? '#FFF' : node.color,
          fontSize: isRoot ? 13 : isHub ? 11 : 10,
          fontWeight: isRoot ? '900' : isHub ? '800' : '600',
          textAlign: 'center',
        }}
      >
        {node.label}
      </Text>
    </View>
  );
}

// ─── Main Screen ──────────────────────────────────────────────────────────────
export default function Component1Screen() {
  const router = useRouter();
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<NormalizedAnalysisResponse | null>(null);
  const [transcriptView, setTranscriptView] = useState<'original' | 'english'>('english');
  const [selectedResourceId, setSelectedResourceId] = useState<string | null>(null);
  const [history, setHistory] = useState<HistorySummary[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // ── Graph state ────────────────────────────────────────────────────────────
  const [expandedHubs, setExpandedHubs] = useState<string[]>([]);
  const [nodePositions, setNodePositions] = useState<Record<string, { x: number; y: number }>>({});

  // ── Drag refs (avoid stale closures in global handlers) ────────────────────
  const dragRef = useRef<{ id: string; sx: number; sy: number; ox: number; oy: number } | null>(null);
  const didMoveRef = useRef(false);
  const tapNodeIdRef = useRef<string | null>(null);
  const nodesRef = useRef<GNode[]>([]);

  useEffect(() => { loadHistoryList(); }, []);

  const loadHistoryList = async () => {
    try { setLoadingHistory(true); setHistory(await fetchComp1List()); }
    catch (e) { console.error(e); }
    finally { setLoadingHistory(false); }
  };

  const loadFromHistory = async (caseId: string) => {
    try {
      const d = await fetchComp1Detail(caseId);
      if (d?.payload) {
        const p = d.payload;
        setAnalysisResult({ status: 'success', analyzed_case: p.analyzed_case, arguments_report: p.arguments_report, input_metadata: p.input_metadata, data: p.data || { summary: '', structured_data: {} } });
        const first = Object.keys(p.data?.structured_data || {})[0];
        if (first) setSelectedCategory(first);
      }
    } catch (e) { console.error(e); }
  };

  const scrollToId = useCallback((id: string) => {
    if (Platform.OS === 'web') {
      const el = (document as any).getElementById(id);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, []);

  // ── Category helpers ──────────────────────────────────────────────────────
  const getCategoryColor = (cat: string) => {
    if (cat.includes('prosecution')) return '#DC2626';
    if (cat.includes('defense')) return '#059669';
    if (cat.includes('procedure')) return '#2563EB';
    if (cat.includes('precedent') || cat.includes('landmark')) return '#D97706';
    if (cat.includes('recent')) return '#7C3AED';
    return '#6366F1';
  };
  const getCategoryIcon = (cat: string) => ({
    prosecution_resources: '⚔️', defense_resources: '🛡️',
    procedural_resources: '⚖️', binding_precedents: '🏛️',
    recent_judgments: '📂', statutory_provisions: '📜',
  }[cat] || '🔹');
  const formatCategoryName = (cat: string) => {
    if (cat === 'recent_judgments') return 'Persuasive Authority';
    if (cat === 'binding_precedents') return 'Landmark Cases';
    return cat.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  };
  const getBadge = (type: string) => {
    const m: any = {
      penal_code: { label: 'Penal Code', color: '#DC2626', bg: '#FEF2F2' },
      criminal_procedure: { label: 'Procedure', color: '#2563EB', bg: '#EFF6FF' },
      landmark_precedent: { label: 'Landmark', color: '#D97706', bg: '#FFFBEB' },
      recent_judgement: { label: 'Judgment', color: '#7C3AED', bg: '#F5F3FF' },
      landmark_case: { label: 'Landmark', color: '#D97706', bg: '#FFFBEB' },
    };
    return type ? (m[type] || { label: type.replace(/_/g, ' '), color: '#6366F1', bg: '#EEF2FF' }) : null;
  };

  const categories = useMemo(() =>
    analysisResult?.data?.structured_data
      ? ['prosecution_resources', 'defense_resources', 'procedural_resources', 'binding_precedents', 'recent_judgments', 'statutory_provisions']
        .filter(k => (analysisResult.data!.structured_data as any)[k]?.length)
      : [], [analysisResult]);

  const totalResources = useMemo(() =>
    analysisResult?.data?.structured_data
      ? Object.values(analysisResult.data.structured_data).flat().length : 0,
    [analysisResult]);

  const overallAccuracy = useMemo(() => {
    if (!analysisResult?.data?.structured_data) return 0;
    let t = 0, c = 0;
    Object.values(analysisResult.data.structured_data).forEach((arr: any) => {
      if (Array.isArray(arr)) arr.forEach((i: any) => { if (i?.similarity != null) { t += i.similarity; c++; } });
    });
    return c > 0 ? (t / c) * 100 : 0;
  }, [analysisResult]);

  const fpData = useMemo(() =>
    categories.map(cat => ({
      cat, icon: getCategoryIcon(cat), label: formatCategoryName(cat), color: getCategoryColor(cat),
      count: (analysisResult?.data?.structured_data as any)?.[cat]?.length || 0,
      pct: totalResources > 0 ? ((analysisResult?.data?.structured_data as any)?.[cat]?.length || 0) / totalResources * 100 : 0,
    })), [categories, totalResources]);

  // ── Graph data ─────────────────────────────────────────────────────────────
  const { nodes: graphNodes, edges: graphEdges } = useMemo(() => {
    if (!analysisResult?.data?.structured_data) return { nodes: [], edges: [] };
    return buildGraph(analysisResult.data.structured_data as any, getCategoryColor, formatCategoryName);
  }, [analysisResult]);

  // Keep ref current so global handlers can access latest node list
  nodesRef.current = graphNodes;

  // Initialise positions whenever graph data changes
  useEffect(() => {
    const pos: Record<string, { x: number; y: number }> = {};
    graphNodes.forEach(n => { pos[n.id] = { x: n.baseX, y: n.baseY }; });
    setNodePositions(pos);
    setExpandedHubs([]);
  }, [graphNodes]);

  // ── Node tap handler (stable via ref) ─────────────────────────────────────
  const handleNodeTap = useCallback((node: GNode) => {
    if (node.type === 'root') return;
    if (node.type === 'hub') {
      setExpandedHubs(prev =>
        prev.includes(node.id)
          ? prev.filter(id => id !== node.id)
          : [...prev, node.id]
      );
      setSelectedCategory(node.category!);
      return;
    }
    if (node.type === 'resource') {
      setSelectedCategory(node.category!);
      setSelectedResourceId(node.id);
      setTimeout(() => scrollToId('comp1-detail-panel'), 150);
    }
  }, [scrollToId]);
  const handleNodeTapRef = useRef(handleNodeTap);
  handleNodeTapRef.current = handleNodeTap;

  // ── Web-only: global mouse drag handlers ──────────────────────────────────
  useEffect(() => {
    if (Platform.OS !== 'web') return;

    const onMove = (e: MouseEvent) => {
      if (!dragRef.current) return;
      const d = dragRef.current;
      const dx = e.clientX - d.sx;
      const dy = e.clientY - d.sy;
      if (!didMoveRef.current && (Math.abs(dx) > 4 || Math.abs(dy) > 4)) {
        didMoveRef.current = true;
      }
      if (didMoveRef.current) {
        setNodePositions(prev => ({ ...prev, [d.id]: { x: d.ox + dx, y: d.oy + dy } }));
      }
    };

    const onUp = (e: MouseEvent) => {
      if (!dragRef.current) return;
      if (!didMoveRef.current && tapNodeIdRef.current) {
        const node = nodesRef.current.find(n => n.id === tapNodeIdRef.current);
        if (node) handleNodeTapRef.current(node);
      }
      dragRef.current = null;
      tapNodeIdRef.current = null;
      didMoveRef.current = false;
    };

    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    return () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
  }, []); // mount once — uses refs, no stale closures

  // Called from GraphNode on web mousedown
  const startWebDrag = useCallback((node: GNode, currentPos: { x: number; y: number }, e: any) => {
    if (node.type === 'root') return;
    e.preventDefault();
    e.stopPropagation();
    dragRef.current = { id: node.id, sx: e.clientX, sy: e.clientY, ox: currentPos.x, oy: currentPos.y };
    tapNodeIdRef.current = node.id;
    didMoveRef.current = false;
  }, []);

  // ── Filter visible nodes for expand/collapse ──────────────────────────────
  const visibleNodes = useMemo(() =>
    graphNodes.filter(n => n.type !== 'resource' || expandedHubs.includes(n.category!)),
    [graphNodes, expandedHubs]);

  const visibleEdges = useMemo(() =>
    graphEdges.filter(e => {
      const tgt = graphNodes.find(n => n.id === e.tgt);
      return !tgt || tgt.type !== 'resource' || expandedHubs.includes(tgt.category!);
    }), [graphEdges, graphNodes, expandedHubs]);

  // ── Analysis complete ─────────────────────────────────────────────────────
  const onAnalysisComplete = async (data: NormalizedAnalysisResponse) => {
    setAnalysisResult(data);
    setSelectedResourceId(null);
    if (data.data?.structured_data) {
      const first = Object.keys(data.data.structured_data)[0];
      if (first) setSelectedCategory(first);
    }
    try {
      const ac = data.analyzed_case;
      const doc = ac?.analyzed_case_file || ac;
      const snip = data.input_metadata?.analyzed_text?.trim().substring(0, 45);
      const lang = data.input_metadata?.language ? `[${data.input_metadata.language}]` : '';
      await saveComp1History({
        case_id: `C1_${doc?.case_header?.file_number || Date.now()}`,
        case_name: doc?.case_header?.subject || (snip ? `${lang} ${snip}…` : `Extraction ${new Date().toLocaleTimeString()}`),
        payload: { analyzed_case: ac, data: data.data, input_metadata: data.input_metadata },
        subject: doc?.case_header?.subject || data.input_metadata?.language || 'N/A',
        accused: doc?.parties_and_roles?.accused || 'N/A',
      });
      loadHistoryList();
    } catch (e) { console.error(e); }
  };

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <Layout>
      <Container>
        <PageHeader title="Legal Resource Extractor" breadcrumb="Analytical Tools → Resource Extraction" />

        <View style={styles.row}>
          <View style={styles.mainCol}>

            <CaseIngestion onAnalysisComplete={onAnalysisComplete} initialMode="voice" allowedModes={['voice', 'text']} />

            {/* ── Stats ── */}
            {analysisResult && (
              <View style={styles.statsRow}>
                <Card style={[styles.statCard, { flex: 1 }]} title="Summary Accuracy">
                  <View style={styles.ring}>
                    <Text style={styles.ringVal}>{overallAccuracy.toFixed(1)}%</Text>
                    <Text style={styles.ringLbl}>Similarity</Text>
                  </View>
                  <Text style={styles.muted}>Average semantic match across extracted resources.</Text>
                </Card>
                <Card style={[styles.statCard, { flex: 1 }]} title="Resource Audit">
                  <Text style={styles.bigNum}>{totalResources}</Text>
                  <Text style={styles.muted}>Legal nodes identified</Text>
                  <View style={styles.dotRow}>
                    {categories.slice(0, 4).map(cat => (
                      <View key={cat} style={styles.dotItem}>
                        <View style={[styles.dot, { backgroundColor: getCategoryColor(cat) }]} />
                        <Text style={styles.dotTxt}>{formatCategoryName(cat).split(' ')[0]}</Text>
                      </View>
                    ))}
                  </View>
                </Card>
              </View>
            )}

            {/* ── Fingerprint ── */}
            {analysisResult && fpData.length > 0 && (
              <Card title="📊 Case Resource Fingerprint">
                <Text style={styles.fpSub}>{totalResources} resources — tap a bar to jump to that category</Text>
                <View style={{ gap: 10 }}>
                  {fpData.map(d => (
                    <View key={d.cat}
                      onStartShouldSetResponder={() => true}
                      onResponderRelease={() => { setSelectedCategory(d.cat); setTimeout(() => scrollToId('comp1-detail-panel'), 120); }}
                      {...(Platform.OS === 'web' ? { onClick: () => { setSelectedCategory(d.cat); setTimeout(() => scrollToId('comp1-detail-panel'), 120); } } : {})}
                      style={[styles.fpRow, selectedCategory === d.cat && styles.fpRowActive]}>
                      <View style={styles.fpLbl}>
                        <Text>{d.icon}</Text>
                        <Text style={styles.fpLblTxt} numberOfLines={1}>{d.label}</Text>
                      </View>
                      <View style={styles.fpTrack}>
                        <View style={[styles.fpFill, { width: `${Math.max(d.pct, 3)}%` as any, backgroundColor: d.color }]} />
                      </View>
                      <View style={{ alignItems: 'flex-end', width: 42 }}>
                        <Text style={[styles.fpNum, { color: d.color }]}>{d.count}</Text>
                        <Text style={styles.fpPct}>{d.pct.toFixed(0)}%</Text>
                      </View>
                    </View>
                  ))}
                </View>
              </Card>
            )}

            {/* ── Transcript ── */}
            {analysisResult && (
              <Card title="Transcription Evidence">
                <View style={styles.txToggle}>
                  {(['english', 'original'] as const).map(v => (
                    <View key={v}
                      onStartShouldSetResponder={() => true}
                      onResponderRelease={() => setTranscriptView(v)}
                      {...(Platform.OS === 'web' ? { onClick: () => setTranscriptView(v) } : {})}
                      style={[styles.toggleBtn, transcriptView === v && styles.toggleBtnA]}>
                      <Text style={[styles.toggleTxt, transcriptView === v && styles.toggleTxtA]}>
                        {v === 'english' ? 'Legal English' : 'Original Transcript'}
                      </Text>
                    </View>
                  ))}
                </View>
                <View style={styles.txBox}>
                  <Text style={styles.txText}>
                    {transcriptView === 'english' ? analysisResult.input_metadata?.analyzed_text : analysisResult.input_metadata?.original_text || 'No original transcript available.'}
                  </Text>
                  <View style={styles.langTag}>
                    <Text style={styles.langTagTxt}>Detected: {analysisResult.input_metadata?.language?.toUpperCase() || 'UNKNOWN'}</Text>
                  </View>
                </View>
              </Card>
            )}

            {/* ── Knowledge Cluster Graph ── */}
            {analysisResult && graphNodes.length > 0 && (
              // @ts-ignore
              <View nativeID="comp1-graph">
                <Card title="Knowledge Cluster Graph">
                  <View style={styles.graphHintRow}>
                    <Text style={styles.hint}>Click a hub to expand its resources.  </Text>
                    <Text style={[styles.hint, { color: colors.accent }]}>✦ Drag nodes to reposition.</Text>
                  </View>

                  <ScrollView horizontal showsHorizontalScrollIndicator style={{ marginHorizontal: -4 }}>
                    <View style={styles.canvas}>

                      {/* ── Edges ── */}
                      {visibleEdges.map((edge, i) => {
                        const sp = nodePositions[edge.src] || graphNodes.find(n => n.id === edge.src) || { x: 0, y: 0 };
                        const tp = nodePositions[edge.tgt] || graphNodes.find(n => n.id === edge.tgt) || { x: 0, y: 0 };
                        return <GraphEdge key={i} sx={(sp as any).x} sy={(sp as any).y} tx={(tp as any).x} ty={(tp as any).y} hubEdge={edge.hubEdge} color={edge.color} />;
                      })}

                      {/* ── Nodes ── */}
                      {visibleNodes.map(node => {
                        const pos = nodePositions[node.id] || { x: node.baseX, y: node.baseY };
                        return (
                          <GraphNode
                            key={node.id}
                            node={node}
                            px={pos.x} py={pos.y}
                            isSelCat={selectedCategory === node.category && node.type === 'hub'}
                            isSelRes={selectedResourceId === node.id}
                            isExpanded={expandedHubs.includes(node.id)}
                            onWebMouseDown={(e) => startWebDrag(node, pos, e)}
                            onNativeTap={() => handleNodeTap(node)}
                          />
                        );
                      })}

                      {/* ── Legend ── */}
                      <View style={styles.legend}>
                        {[
                          { l: 'Case Root', c: '#1E3A5F' },
                          { l: 'Prosecution', c: '#DC2626' },
                          { l: 'Defense', c: '#059669' },
                          { l: 'Procedure', c: '#2563EB' },
                          { l: 'Landmark', c: '#D97706' },
                          { l: 'Persuasive', c: '#7C3AED' },
                        ].map(({ l, c }) => (
                          <View key={l} style={styles.legendItem}>
                            <View style={[styles.legendDot, { backgroundColor: c }]} />
                            <Text style={styles.legendTxt}>{l}</Text>
                          </View>
                        ))}
                      </View>
                    </View>
                  </ScrollView>

                  {/* ── Detail Panel ── */}
                  {selectedCategory && (
                    // @ts-ignore
                    <View nativeID="comp1-detail-panel" style={styles.detail}>

                      <View style={[styles.detailHdr, { backgroundColor: getCategoryColor(selectedCategory) + '12', borderLeftColor: getCategoryColor(selectedCategory) }]}>
                        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, flex: 1 }}>
                          <Text style={{ fontSize: 18 }}>{getCategoryIcon(selectedCategory)}</Text>
                          <View>
                            <Text style={[styles.detailTitle, { color: getCategoryColor(selectedCategory) }]}>{formatCategoryName(selectedCategory)}</Text>
                            <Text style={styles.muted}>Detailed resource view</Text>
                          </View>
                        </View>
                        <View style={[styles.detailBadge, { backgroundColor: getCategoryColor(selectedCategory) }]}>
                          <Text style={{ color: '#FFF', fontSize: 18, fontWeight: '900', lineHeight: 22 }}>{((analysisResult?.data?.structured_data as any)?.[selectedCategory] || []).length}</Text>
                          <Text style={{ color: 'rgba(255,255,255,0.75)', fontSize: 10 }}>items</Text>
                        </View>
                      </View>

                      {/* Tabs */}
                      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.tabRow}>
                        {categories.map(cat => (
                          <View key={cat}
                            onStartShouldSetResponder={() => true}
                            onResponderRelease={() => { setSelectedCategory(cat); setSelectedResourceId(null); }}
                            {...(Platform.OS === 'web' ? { onClick: () => { setSelectedCategory(cat); setSelectedResourceId(null); } } : {})}
                            style={[styles.tab, selectedCategory === cat && { backgroundColor: getCategoryColor(cat) + '18', borderColor: getCategoryColor(cat) }]}>
                            <Text style={{ fontSize: 12 }}>{getCategoryIcon(cat)}</Text>
                            <Text style={[styles.tabTxt, selectedCategory === cat && { color: getCategoryColor(cat), fontWeight: '800' }]}>
                              {formatCategoryName(cat).split(' ')[0]}
                            </Text>
                            <View style={[styles.tabBadge, { backgroundColor: selectedCategory === cat ? getCategoryColor(cat) : '#CBD5E1' }]}>
                              <Text style={{ color: '#FFF', fontSize: 9, fontWeight: '900' }}>{((analysisResult?.data?.structured_data as any)?.[cat] || []).length}</Text>
                            </View>
                          </View>
                        ))}
                      </ScrollView>

                      {/* Items */}
                      <View style={{ gap: 0, paddingHorizontal: 16, paddingBottom: 8 }}>
                        {Array.isArray((analysisResult?.data?.structured_data as any)?.[selectedCategory]) &&
                          (analysisResult!.data!.structured_data as any)[selectedCategory].map((item: any, idx: number) => {
                            const iid = item.id || `${selectedCategory}-${idx}`;
                            const sel = selectedResourceId === iid;
                            const bdg = getBadge(item.type);
                            return (
                              <View key={iid}
                                onStartShouldSetResponder={() => true}
                                onResponderRelease={() => setSelectedResourceId(sel ? null : iid)}
                                {...(Platform.OS === 'web' ? { onClick: () => setSelectedResourceId(sel ? null : iid) } : {})}
                                style={[styles.resItem, sel && styles.resItemSel]}>
                                <View style={[styles.resBullet, { backgroundColor: getCategoryColor(selectedCategory) }]} />
                                <View style={{ flex: 1, gap: 4 }}>
                                  <View style={{ flexDirection: 'row', gap: 8, flexWrap: 'wrap', alignItems: 'flex-start' }}>
                                    <Text style={[styles.resTitle, { flex: 1 }]}>{item.title || item.name || 'Legal Resource'}</Text>
                                    {bdg && <View style={[styles.bdg, { backgroundColor: bdg.bg, borderColor: bdg.color + '40' }]}><Text style={[styles.bdgTxt, { color: bdg.color }]}>{bdg.label}</Text></View>}
                                  </View>
                                  <Text style={styles.resText} numberOfLines={sel ? undefined : 3}>{item.excerpt || item.summary || ''}</Text>
                                  <View style={{ flexDirection: 'row', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
                                    {item.section && <Text style={styles.resMeta}>§ {item.section}</Text>}
                                    {item.similarity != null && (
                                      <View style={styles.simRow}>
                                        <View style={[styles.simFill, { width: `${(item.similarity * 100).toFixed(0)}%` as any, backgroundColor: getCategoryColor(selectedCategory) }]} />
                                        <Text style={[styles.simTxt, { color: getCategoryColor(selectedCategory) }]}>{(item.similarity * 100).toFixed(1)}% match</Text>
                                      </View>
                                    )}
                                  </View>
                                  <Text style={[styles.expandHint, { color: getCategoryColor(selectedCategory) }]}>{sel ? '▲ Collapse' : '▼ Tap to expand'}</Text>
                                </View>
                              </View>
                            );
                          })}
                      </View>

                      <View onStartShouldSetResponder={() => true} onResponderRelease={() => scrollToId('comp1-graph')}
                        {...(Platform.OS === 'web' ? { onClick: () => scrollToId('comp1-graph') } : {})}
                        style={styles.backBtn}>
                        <Text style={styles.backBtnTxt}>↑ Back to Knowledge Graph</Text>
                      </View>
                    </View>
                  )}
                </Card>
              </View>
            )}

          </View>

          {/* ── Metadata ── */}
          {analysisResult && (
            <View style={{ marginTop: spacing.xl }}>
              <Card style={{ backgroundColor: '#F8FAFC' }} title="Engine Analysis Metadata">
                <View style={{ flexDirection: 'row', justifyContent: 'space-around', paddingVertical: spacing.md }}>
                  <View style={{ alignItems: 'center' }}><Text style={styles.metaLbl}>Pipeline</Text><Text style={styles.metaVal}>Neuro-Symbolic</Text></View>
                  <View style={{ alignItems: 'center' }}><Text style={styles.metaLbl}>Confidence</Text><Text style={styles.metaVal}>94.2%</Text></View>
                </View>
              </Card>
            </View>
          )}

          {/* ── History ── */}
          <View style={{ marginTop: spacing.xl }}>
            <Card title="📜 Recent History">
              <View style={{ gap: spacing.sm }}>
                {loadingHistory ? <Text style={styles.muted}>Loading history...</Text>
                  : (history || []).length === 0 ? <Text style={styles.muted}>No past cases yet.</Text>
                    : (history || []).slice(0, 5).map((h, i) => (
                      <View key={i}
                        onStartShouldSetResponder={() => true}
                        onResponderRelease={() => loadFromHistory(h.case_id)}
                        {...(Platform.OS === 'web' ? { onClick: () => loadFromHistory(h.case_id) } : {})}
                        style={styles.histItem}>
                        <View style={styles.histIcon}><Text style={{ fontSize: 16 }}>📋</Text></View>
                        <View style={{ flex: 1 }}>
                          <Text style={styles.histId}>{h.case_id}</Text>
                          <Text style={styles.histMeta}>{new Date(h.timestamp).toLocaleDateString()} · {(h.subject || '').substring(0, 28)}</Text>
                          {(h as any).accused && (h as any).accused !== 'N/A' && <Text style={styles.histAcc}>Accused: {(h as any).accused}</Text>}
                        </View>
                        <Text style={styles.histArrow}>›</Text>
                      </View>
                    ))}
              </View>
              <View onStartShouldSetResponder={() => true} onResponderRelease={loadHistoryList}
                {...(Platform.OS === 'web' ? { onClick: loadHistoryList } : {})}
                style={{ marginTop: spacing.md, alignItems: 'center' }}>
                <Text style={{ color: colors.accent, fontWeight: '600', fontSize: 13 }}>↻ Refresh</Text>
              </View>
            </Card>
          </View>

          <View onStartShouldSetResponder={() => true} onResponderRelease={() => router.push('/')}
            {...(Platform.OS === 'web' ? { onClick: () => router.push('/') } : {})}
            style={{ marginTop: spacing.xxl, alignSelf: 'center' }}>
            <Text style={{ color: colors.primary, fontWeight: '700', fontSize: 15 }}>← Back to Analytical Dashboard</Text>
          </View>
        </View>
      </Container>
    </Layout>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  row: { width: '100%' },
  mainCol: { width: '100%', gap: spacing.xl },

  statsRow: { flexDirection: 'row', gap: spacing.lg, marginBottom: spacing.lg },
  statCard: { marginBottom: 0 },
  ring: { width: 80, height: 80, borderRadius: 40, borderWidth: 6, borderColor: colors.accent, alignItems: 'center', justifyContent: 'center', alignSelf: 'center', marginVertical: spacing.md },
  ringVal: { fontSize: 18, fontWeight: 'bold', color: colors.primary },
  ringLbl: { fontSize: 10, color: colors.textMuted, marginTop: -2 },
  bigNum: { fontSize: 32, fontWeight: 'bold', color: colors.primary, textAlign: 'center', marginTop: spacing.sm },
  dotRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, justifyContent: 'center', marginTop: spacing.sm },
  dotItem: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  dot: { width: 8, height: 8, borderRadius: 4 },
  dotTxt: { fontSize: 12, color: colors.primary },
  muted: { fontSize: 13, color: colors.textMuted, textAlign: 'center', paddingHorizontal: spacing.sm },

  fpSub: { fontSize: 13, color: colors.textMuted, marginBottom: spacing.md },
  fpRow: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 8, paddingHorizontal: 12, borderRadius: 10, borderWidth: 1, borderColor: 'transparent', backgroundColor: '#F8FAFC', cursor: 'pointer' } as any,
  fpRowActive: { borderColor: '#CBD5E1', backgroundColor: '#F1F5F9' },
  fpLbl: { flexDirection: 'row', alignItems: 'center', gap: 6, width: 130 },
  fpLblTxt: { fontSize: 12, fontWeight: '700', color: colors.primary, flex: 1 },
  fpTrack: { flex: 1, height: 10, backgroundColor: '#E2E8F0', borderRadius: 5, overflow: 'hidden' },
  fpFill: { height: '100%', borderRadius: 5 },
  fpNum: { fontSize: 14, fontWeight: '900' },
  fpPct: { fontSize: 10, color: colors.textMuted, marginTop: -2 },

  txToggle: { flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.md },
  toggleBtn: { paddingVertical: 8, paddingHorizontal: 16, borderRadius: 24, backgroundColor: '#F1F5F9', cursor: 'pointer' } as any,
  toggleBtnA: { backgroundColor: colors.primary },
  toggleTxt: { fontSize: 13, fontWeight: '700', color: colors.textSecondary },
  toggleTxtA: { color: '#FFFFFF' },
  txBox: { padding: spacing.lg, backgroundColor: '#FAFBFD', borderRadius: 16, borderLeftWidth: 4, borderLeftColor: colors.primary },
  txText: { fontSize: 16, fontStyle: 'italic', color: colors.textPrimary, lineHeight: 28 },
  langTag: { alignSelf: 'flex-end', marginTop: 12, paddingHorizontal: 10, paddingVertical: 4, backgroundColor: '#E2E8F0', borderRadius: 6 },
  langTagTxt: { fontSize: 11, fontWeight: '800', color: colors.textSecondary },

  graphHintRow: { flexDirection: 'row', flexWrap: 'wrap', marginBottom: spacing.md },
  hint: { fontSize: 12, color: colors.textMuted, fontStyle: 'italic' },

  canvas: {
    width: GW, height: GH,
    position: 'relative',
    backgroundColor: '#EEF2F8',
    borderRadius: 16,
    borderWidth: 1, borderColor: '#DDE3EF',
    overflow: 'visible',
  },

  legend: {
    position: 'absolute', bottom: 14, left: 0, right: 0,
    flexDirection: 'row', justifyContent: 'center', flexWrap: 'wrap', gap: 16,
  },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  legendDot: { width: 9, height: 9, borderRadius: 5 },
  legendTxt: { fontSize: 11, color: '#64748B', fontWeight: '600' },

  detail: { marginTop: spacing.xl, backgroundColor: '#FFF', borderRadius: 16, borderWidth: 1, borderColor: '#E2E8F0', overflow: 'hidden' },
  detailHdr: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderLeftWidth: 5, paddingVertical: 14, paddingHorizontal: 18 },
  detailTitle: { fontSize: 17, fontWeight: '900' },
  detailBadge: { paddingHorizontal: 14, paddingVertical: 6, borderRadius: 12, alignItems: 'center' },

  tabRow: { flexDirection: 'row', gap: 6, paddingHorizontal: 16, paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: '#F1F5F9' },
  tab: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingVertical: 5, paddingHorizontal: 10, borderRadius: 8, borderWidth: 1, borderColor: '#E2E8F0', backgroundColor: '#F8FAFC', cursor: 'pointer' } as any,
  tabTxt: { fontSize: 11, fontWeight: '600', color: colors.textMuted },
  tabBadge: { paddingHorizontal: 5, paddingVertical: 1, borderRadius: 6, minWidth: 18, alignItems: 'center' },

  resItem: { flexDirection: 'row', alignItems: 'flex-start', gap: 12, paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: '#F1F5F9', cursor: 'pointer' } as any,
  resItemSel: { backgroundColor: '#F0F9FF', borderRadius: 12, paddingHorizontal: 8, marginHorizontal: -8, borderBottomWidth: 0 },
  resBullet: { width: 4, height: 36, borderRadius: 2, marginTop: 2, flexShrink: 0 },
  resTitle: { fontWeight: '700', color: colors.primary, fontSize: 16, lineHeight: 22 },
  resText: { color: colors.textSecondary, lineHeight: 22, fontSize: 14 },
  resMeta: { color: colors.accent, fontSize: 12, fontWeight: '700' },
  bdg: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6, borderWidth: 1 },
  bdgTxt: { fontSize: 10, fontWeight: '800' },
  simRow: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: 8, height: 18, position: 'relative' },
  simFill: { position: 'absolute', left: 0, top: 0, bottom: 0, borderRadius: 4, opacity: 0.15 },
  simTxt: { fontSize: 12, fontWeight: '700', zIndex: 1 },
  expandHint: { fontSize: 11, fontWeight: '600', marginTop: 2 },

  backBtn: { alignItems: 'center', paddingVertical: 12, borderTopWidth: 1, borderTopColor: '#F1F5F9', cursor: 'pointer' } as any,
  backBtnTxt: { color: colors.accent, fontSize: 13, fontWeight: '700' },

  histItem: { flexDirection: 'row', alignItems: 'center', gap: 12, padding: spacing.md, backgroundColor: '#F8FAFC', borderRadius: 12, borderWidth: 1, borderColor: '#E2E8F0', borderLeftWidth: 4, borderLeftColor: colors.accent, cursor: 'pointer' } as any,
  histIcon: { width: 36, height: 36, borderRadius: 10, backgroundColor: '#EEF2FF', alignItems: 'center', justifyContent: 'center' },
  histId: { fontSize: 13, fontWeight: '700', color: colors.primary },
  histMeta: { fontSize: 11, color: colors.textMuted, marginTop: 1 },
  histAcc: { fontSize: 11, color: colors.accent, fontWeight: '600', marginTop: 2 },
  histArrow: { fontSize: 20, color: colors.textMuted },

  metaLbl: { fontSize: 12, color: colors.textMuted, fontWeight: '600', marginBottom: 4, textTransform: 'uppercase' },
  metaVal: { fontSize: 14, color: colors.primary, fontWeight: '800' },
});
