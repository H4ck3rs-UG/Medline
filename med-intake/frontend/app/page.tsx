'use client';

import {useEffect, useMemo, useState, type CSSProperties} from 'react';

import {
  HStack,
  Layout,
  LayoutContent,
  LayoutHeader,
  StackItem,
  VStack,
} from '@astryxdesign/core/Layout';
import {ResizeHandle, useResizable} from '@astryxdesign/core/Resizable';
import {LayoutPanel} from '@astryxdesign/core/Layout';
import {Heading, Text} from '@astryxdesign/core/Text';
import {Button} from '@astryxdesign/core/Button';
import {Icon} from '@astryxdesign/core/Icon';
import {Divider} from '@astryxdesign/core/Divider';
import {EmptyState} from '@astryxdesign/core/EmptyState';
import {List, ListItem} from '@astryxdesign/core/List';
import {MetadataList, MetadataListItem} from '@astryxdesign/core/MetadataList';
import {
  SegmentedControl,
  SegmentedControlItem,
} from '@astryxdesign/core/SegmentedControl';
import {StatusDot} from '@astryxdesign/core/StatusDot';
import {Token} from '@astryxdesign/core/Token';
import {useMediaQuery} from '@astryxdesign/core/hooks';
import {BellAlertIcon} from '@heroicons/react/24/outline';
import {STRINGS, UI_LANGS, type UiLang} from './i18n';

const API = process.env.NEXT_PUBLIC_API || 'http://localhost:8000';
const LANG_KEY = 'dashboard-lang';

const styles: Record<string, CSSProperties> = {
  contentFill: {height: '100%', minHeight: 0},
  rows: {overflowY: 'auto', minHeight: 0},
  inspector: {padding: 'var(--spacing-4)', height: '100%', overflowY: 'auto'},
  groupHeader: {
    padding: 'var(--spacing-2) var(--spacing-3)',
    backgroundColor: 'var(--color-background-muted)',
  },
};

interface Ticket extends Record<string, unknown> {
  id: number;
  caller: string;
  lang: string;
  symptoms: string;
  tier: 'emergency' | 'urgent' | 'self_care';
  reason: string;
  confidence: number;
  status: string;
}

const TIER_DOT = {emergency: 'error', urgent: 'warning', self_care: 'success'} as const;
const TIER_ORDER = ['emergency', 'urgent', 'self_care'] as const;
const TIER_LABEL: Record<string, string> = {
  emergency: 'Emergency',
  urgent: 'Urgent',
  self_care: 'Self-care',
};

function TicketRows({
  tickets,
  selectedId,
  onSelect,
  emptyLabel,
}: {
  tickets: Ticket[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  emptyLabel: string;
}) {
  const groups = TIER_ORDER.map(tier => ({
    tier,
    items: tickets.filter(t => t.tier === tier),
  })).filter(g => g.items.length > 0);

  if (groups.length === 0) {
    return (
      <EmptyState
        title={emptyLabel}
        description=""
        icon={<Icon icon={BellAlertIcon} size="lg" />}
      />
    );
  }

  return (
    <VStack gap={0}>
      {groups.map(group => (
        <VStack gap={0} key={group.tier}>
          <HStack gap={2} vAlign="center" style={styles.groupHeader}>
            <StatusDot variant={TIER_DOT[group.tier]} label={TIER_LABEL[group.tier]} />
            <Text type="label" color="secondary">
              {TIER_LABEL[group.tier]}
            </Text>
            <Text type="supporting" color="secondary">
              {group.items.length}
            </Text>
          </HStack>
          <List density="compact" hasDividers>
            {group.items.map(t => (
              <ListItem
                key={t.id}
                label={`#${t.id} · ${t.caller || 'unknown'}`}
                description={`${t.symptoms} · ${t.reason}`}
                startContent={
                  <StatusDot
                    variant={TIER_DOT[t.tier]}
                    label={t.tier}
                    isPulsing={t.tier === 'emergency' && t.status === 'open'}
                  />
                }
                endContent={
                  <Token
                    size="sm"
                    color={t.status === 'open' ? 'blue' : 'gray'}
                    label={t.status}
                  />
                }
                onClick={() => onSelect(t.id)}
                isSelected={t.id === selectedId}
              />
            ))}
          </List>
        </VStack>
      ))}
    </VStack>
  );
}

function TicketInspector({
  ticket,
  closeLabel,
  onClose,
}: {
  ticket: Ticket;
  closeLabel: string;
  onClose: (id: number) => void;
}) {
  return (
    <VStack gap={4} style={styles.inspector}>
      <VStack gap={2}>
        <HStack gap={2} vAlign="center">
          <StatusDot variant={TIER_DOT[ticket.tier]} label={ticket.tier} />
          <Text type="supporting" color="secondary">
            #{ticket.id}
          </Text>
          <Token
            size="sm"
            color={ticket.status === 'open' ? 'blue' : 'gray'}
            label={ticket.status}
          />
        </HStack>
        <Heading level={2}>{TIER_LABEL[ticket.tier]}</Heading>
      </VStack>

      {ticket.status === 'open' && (
        <HStack gap={2}>
          <Button label={closeLabel} size="sm" onClick={() => onClose(ticket.id)} />
        </HStack>
      )}

      <Divider />

      <MetadataList columns="single" label={{position: 'start', width: 96}}>
        <MetadataListItem label="Caller">
          <Text type="body">{ticket.caller || '—'}</Text>
        </MetadataListItem>
        <MetadataListItem label="Language">
          <Text type="body">{ticket.lang}</Text>
        </MetadataListItem>
        <MetadataListItem label="Symptoms">
          <Text type="body">{ticket.symptoms || '—'}</Text>
        </MetadataListItem>
        <MetadataListItem label="Reason">
          <Text type="body">{ticket.reason}</Text>
        </MetadataListItem>
        <MetadataListItem label="Confidence">
          <Text type="body">{ticket.confidence > 0 ? `${ticket.confidence}%` : '—'}</Text>
        </MetadataListItem>
      </MetadataList>
    </VStack>
  );
}

export default function Page() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [tierFilter, setTierFilter] = useState('all');
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [lang, setLang] = useState<UiLang>('en');

  useEffect(() => {
    try {
      const v = localStorage.getItem(LANG_KEY);
      if (v === 'en' || v === 'sw') setLang(v);
    } catch {}
  }, []);

  const load = () =>
    fetch(`${API}/api/tickets`)
      .then(r => r.json())
      .then((rows: Ticket[]) => {
        setTickets(rows);
        setSelectedId(prev => prev ?? rows[0]?.id ?? null);
      })
      .catch(() => {});

  useEffect(() => {
    load();
    const i = setInterval(load, 3000);
    return () => clearInterval(i);
  }, []);

  const close = (id: number) =>
    fetch(`${API}/api/tickets/${id}`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({status: 'closed'}),
    }).then(load);

  const isNarrow = useMediaQuery('(max-width: 1024px)');
  const inspectorPanel = useResizable({defaultSize: 380, minSize: 320, maxSize: 480});

  const visible = useMemo(
    () => (tierFilter === 'all' ? tickets : tickets.filter(t => t.tier === tierFilter)),
    [tickets, tierFilter],
  );
  const selected = visible.find(t => t.id === selectedId) ?? null;
  const openCount = tickets.filter(t => t.status === 'open').length;
  const s = STRINGS[lang];

  return (
    <Layout
      height="fill"
      header={
        <LayoutHeader hasDivider>
          <HStack gap={3} vAlign="center">
            <StackItem size="fill">
              <HStack gap={2} vAlign="center">
                <Heading level={1}>{s.title}</Heading>
                <Text type="supporting" color="secondary">
                  {openCount} open
                </Text>
              </HStack>
            </StackItem>
            <SegmentedControl
              label="Filter by tier"
              value={tierFilter}
              onChange={setTierFilter}
              size="sm">
              <SegmentedControlItem label="All" value="all" />
              <SegmentedControlItem label="Emergency" value="emergency" />
              <SegmentedControlItem label="Urgent" value="urgent" />
              <SegmentedControlItem label="Self-care" value="self_care" />
            </SegmentedControl>
            <SegmentedControl
              label={s.language}
              value={lang}
              onChange={v => {
                setLang(v as UiLang);
                try {
                  localStorage.setItem(LANG_KEY, v);
                } catch {}
              }}
              size="sm">
              {(Object.keys(UI_LANGS) as UiLang[]).map(l => (
                <SegmentedControlItem key={l} label={UI_LANGS[l]} value={l} />
              ))}
            </SegmentedControl>
          </HStack>
        </LayoutHeader>
      }
      content={
        <LayoutContent padding={0}>
          <VStack gap={0} style={styles.contentFill}>
            <StackItem size="fill" style={styles.rows}>
              <TicketRows
                tickets={visible}
                selectedId={selected?.id ?? null}
                onSelect={setSelectedId}
                emptyLabel={s.empty}
              />
            </StackItem>
          </VStack>
        </LayoutContent>
      }
      end={
        isNarrow ? undefined : (
          <>
            <ResizeHandle
              direction="horizontal"
              hasDivider
              isAlwaysVisible={false}
              resizable={inspectorPanel.props}
              label="Resize inspector"
            />
            <LayoutPanel width={inspectorPanel.size} padding={0} label="Ticket details">
              {selected ? (
                <TicketInspector ticket={selected} closeLabel={s.close} onClose={close} />
              ) : (
                <EmptyState
                  title="No ticket selected"
                  description="Select a ticket to see details."
                  icon={<Icon icon={BellAlertIcon} size="lg" />}
                  isCompact
                />
              )}
            </LayoutPanel>
          </>
        )
      }
    />
  );
}
