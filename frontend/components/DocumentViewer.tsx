import React, { useRef, useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  Pressable,
  StyleSheet,
  Platform,
} from 'react-native';
import { colors, spacing, borderRadius, typography } from '../theme';

export interface PageData {
  page_num: number;
  text: string;
}

export interface HighlightSpan {
  page: number;
  start_char: number;
  end_char: number;
}

interface Props {
  pages: PageData[];
  activeHighlight?: HighlightSpan | null;
  onClearHighlight?: () => void;
}

export function DocumentViewer({ pages, activeHighlight, onClearHighlight }: Props) {
  const scrollRef = useRef<ScrollView>(null);
  const [fontSize, setFontSize] = useState(13);
  const [activePage, setActivePage] = useState(0);
  const highlightRef = useRef<View>(null);

  const totalPages = pages.length;
  const currentPage = pages[activePage] ?? pages[0];

  useEffect(() => {
    if (activeHighlight) {
      setActivePage(activeHighlight.page);
    }
  }, [activeHighlight]);

  useEffect(() => {
    if (activeHighlight && activeHighlight.page === activePage) {
      setTimeout(() => {
        if (Platform.OS === 'web' && highlightRef.current) {
          (highlightRef.current as any).measureLayout?.(
            (scrollRef.current as any),
            (_x: number, y: number) => {
              scrollRef.current?.scrollTo({ y: Math.max(0, y - 80), animated: true });
            },
            () => {}
          );
        }
      }, 100);
    }
  }, [activeHighlight, activePage]);

  if (!currentPage) {
    return (
      <View style={s.container}>
        <Text style={s.emptyText}>No document loaded</Text>
      </View>
    );
  }

  const pageCharOffset = pages
    .slice(0, activePage)
    .reduce((sum, p) => sum + p.text.length, 0);

  const renderTextWithHighlight = () => {
    const text = currentPage.text;
    if (
      !activeHighlight ||
      activeHighlight.page !== activePage
    ) {
      return <Text style={[s.docText, { fontSize }]}>{text}</Text>;
    }

    const localStart = activeHighlight.start_char - pageCharOffset;
    const localEnd = activeHighlight.end_char - pageCharOffset;

    if (localStart < 0 || localEnd > text.length || localStart >= localEnd) {
      return <Text style={[s.docText, { fontSize }]}>{text}</Text>;
    }

    const before = text.slice(0, localStart);
    const highlighted = text.slice(localStart, localEnd);
    const after = text.slice(localEnd);

    return (
      <Text style={[s.docText, { fontSize }]}>
        {before}
        <View ref={highlightRef} collapsable={false}>
          <Text style={s.highlighted}>{highlighted}</Text>
        </View>
        {after}
      </Text>
    );
  };

  return (
    <View style={s.container}>
      {/* Toolbar */}
      <View style={s.toolbar}>
        <Text style={s.toolbarTitle}>Source Document</Text>
        <View style={s.zoomRow}>
          <Pressable onPress={() => setFontSize(f => Math.max(10, f - 1))} style={s.zoomBtn}>
            <Text style={s.zoomBtnText}>A-</Text>
          </Pressable>
          <Text style={s.zoomLabel}>{fontSize}px</Text>
          <Pressable onPress={() => setFontSize(f => Math.min(22, f + 1))} style={s.zoomBtn}>
            <Text style={s.zoomBtnText}>A+</Text>
          </Pressable>
        </View>
      </View>

      {/* Document text */}
      <ScrollView
        ref={scrollRef}
        style={s.scroll}
        contentContainerStyle={s.scrollContent}
      >
        <Pressable onPress={onClearHighlight}>
          {renderTextWithHighlight()}
        </Pressable>
      </ScrollView>

      {/* Pagination */}
      {totalPages > 1 && (
        <View style={s.pagination}>
          <Pressable
            onPress={() => setActivePage(p => Math.max(0, p - 1))}
            disabled={activePage === 0}
            style={[s.pageBtn, activePage === 0 && s.pageBtnDisabled]}
          >
            <Text style={s.pageBtnText}>Prev</Text>
          </Pressable>
          <Text style={s.pageInfo}>
            Page {activePage + 1} of {totalPages}
          </Text>
          <Pressable
            onPress={() => setActivePage(p => Math.min(totalPages - 1, p + 1))}
            disabled={activePage === totalPages - 1}
            style={[s.pageBtn, activePage === totalPages - 1 && s.pageBtnDisabled]}
          >
            <Text style={s.pageBtnText}>Next</Text>
          </Pressable>
        </View>
      )}
    </View>
  );
}

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
  emptyText: {
    padding: spacing.lg,
    color: colors.textMuted,
    textAlign: 'center',
  },
  toolbar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    backgroundColor: colors.bgSection,
  },
  toolbarTitle: {
    fontSize: typography.sizes.sm,
    fontWeight: typography.weights.semibold,
    color: colors.primary,
    letterSpacing: 0.3,
  },
  zoomRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  zoomBtn: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: borderRadius.sm,
    backgroundColor: colors.bgCard,
    borderWidth: 1,
    borderColor: colors.borderStrong,
  },
  zoomBtnText: {
    fontSize: 12,
    fontWeight: typography.weights.semibold,
    color: colors.primary,
  },
  zoomLabel: {
    fontSize: 11,
    color: colors.textMuted,
    minWidth: 32,
    textAlign: 'center',
  },
  scroll: {
    flex: 1,
    maxHeight: 600,
  },
  scrollContent: {
    padding: spacing.md,
  },
  docText: {
    fontFamily: Platform.OS === 'web' ? '"Courier New", monospace' : 'monospace',
    color: colors.textPrimary,
    lineHeight: 22,
  },
  highlighted: {
    backgroundColor: '#BBF7D0',
    borderWidth: 1,
    borderColor: '#22C55E',
    borderRadius: 3,
    paddingHorizontal: 2,
    color: colors.textPrimary,
    fontFamily: Platform.OS === 'web' ? '"Courier New", monospace' : 'monospace',
    fontWeight: typography.weights.semibold,
  },
  pagination: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    backgroundColor: colors.bgSection,
    gap: 12,
  },
  pageBtn: {
    paddingHorizontal: 14,
    paddingVertical: 5,
    borderRadius: borderRadius.sm,
    backgroundColor: colors.primary,
  },
  pageBtnDisabled: {
    opacity: 0.35,
  },
  pageBtnText: {
    color: colors.textOnPrimary,
    fontSize: 12,
    fontWeight: typography.weights.semibold,
  },
  pageInfo: {
    fontSize: 12,
    color: colors.textSecondary,
    fontWeight: typography.weights.medium,
  },
});
