import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Calendar as CalendarIcon, ChevronLeft, ChevronRight, Loader2,
  Video, Phone, Users, MapPin, FileText, X, Sparkles, Clock,
} from 'lucide-react';

// ─── Types ───────────────────────────────────────────────────────────────────

interface Meeting {
  id: string;
  contact_name: string;
  company?: string;
  program?: string;
  date: string;      // ISO date
  time?: string;
  type: 'call' | 'video' | 'in-person';
  notes?: string;
  status?: 'scheduled' | 'completed' | 'cancelled';
}

interface MeetingPrepBrief {
  contact_summary: string;
  program_context: string;
  talking_points: string[];
  recent_activity: string;
}

interface MeetingCalendarProps {
  onNavigateToContact?: (name: string) => void;
}

const MEETING_ICONS: Record<string, typeof Phone> = {
  call: Phone, video: Video, 'in-person': Users,
};

const TYPE_COLORS: Record<string, string> = {
  call: 'bg-green-500', video: 'bg-blue-500', 'in-person': 'bg-purple-500',
};

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

// ─── Helpers ─────────────────────────────────────────────────────────────────

function getDaysInMonth(year: number, month: number): Date[] {
  const days: Date[] = [];
  const first = new Date(year, month, 1);
  const last = new Date(year, month + 1, 0);

  // Pad start
  for (let i = 0; i < first.getDay(); i++) {
    const d = new Date(year, month, -first.getDay() + i + 1);
    days.push(d);
  }
  // Days of month
  for (let d = 1; d <= last.getDate(); d++) {
    days.push(new Date(year, month, d));
  }
  // Pad end
  while (days.length % 7 !== 0) {
    const d = new Date(year, month + 1, days.length - last.getDate() - first.getDay() + 1);
    days.push(d);
  }
  return days;
}

function isSameDay(a: Date, b: Date): boolean {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}

function formatDate(d: Date): string {
  return d.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
}

// ─── Component ───────────────────────────────────────────────────────────────

export function MeetingCalendar({ onNavigateToContact }: MeetingCalendarProps) {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);
  const [serviceOnline, setServiceOnline] = useState(false);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [prepBrief, setPrepBrief] = useState<MeetingPrepBrief | null>(null);
  const [prepLoading, setPrepLoading] = useState(false);
  const [showPrepModal, setShowPrepModal] = useState<Meeting | null>(null);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();
  const days = useMemo(() => getDaysInMonth(year, month), [year, month]);
  const today = useMemo(() => new Date(), []);

  // Fetch meetings
  useEffect(() => {
    async function load() {
      try {
        const res = await fetch('/outreach/meetings', { signal: AbortSignal.timeout(5000) });
        if (!res.ok) throw new Error();
        const data = await res.json();
        setMeetings(data.meetings || data || []);
        setServiceOnline(true);
      } catch {
        setServiceOnline(false);
        setMeetings(generateMockMeetings());
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const meetingsByDate = useMemo(() => {
    const map = new Map<string, Meeting[]>();
    meetings.forEach(m => {
      const key = m.date.split('T')[0];
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(m);
    });
    return map;
  }, [meetings]);

  const selectedMeetings = useMemo(() => {
    if (!selectedDate) return [];
    const key = `${selectedDate.getFullYear()}-${String(selectedDate.getMonth() + 1).padStart(2, '0')}-${String(selectedDate.getDate()).padStart(2, '0')}`;
    return meetingsByDate.get(key) || [];
  }, [selectedDate, meetingsByDate]);

  const upcomingMeetings = useMemo(() => {
    const now = new Date();
    const week = new Date(now.getTime() + 7 * 86400000);
    return meetings
      .filter(m => {
        const d = new Date(m.date);
        return d >= now && d <= week;
      })
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  }, [meetings]);

  const handlePrevMonth = () => setCurrentDate(new Date(year, month - 1, 1));
  const handleNextMonth = () => setCurrentDate(new Date(year, month + 1, 1));

  const handleGeneratePrep = useCallback(async (meeting: Meeting) => {
    setShowPrepModal(meeting);
    setPrepLoading(true);
    setPrepBrief(null);
    try {
      const res = await fetch('/outreach/meeting-prep', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ contact_name: meeting.contact_name, program: meeting.program }),
      });
      if (!res.ok) throw new Error();
      const data = await res.json();
      setPrepBrief(data);
    } catch {
      setPrepBrief({
        contact_summary: `${meeting.contact_name} — ${meeting.company || 'Unknown company'}`,
        program_context: meeting.program || 'General BD discussion',
        talking_points: ['Review recent engagement history', 'Discuss program requirements', 'Identify next steps'],
        recent_activity: 'No recent activity data available (API offline)',
      });
    } finally {
      setPrepLoading(false);
    }
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="p-6 overflow-auto h-full space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
            <CalendarIcon className="h-7 w-7 text-blue-500" /> Meeting Calendar
          </h1>
          <p className="text-slate-500 dark:text-slate-400">
            {meetings.length} meetings
            {!serviceOnline && <span className="ml-2 text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded">Offline — mock data</span>}
          </p>
        </div>
      </div>

      <div className="flex gap-6">
        {/* Calendar Grid */}
        <div className="flex-1">
          {/* Month nav */}
          <div className="flex items-center justify-between mb-4">
            <button onClick={handlePrevMonth} className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700">
              <ChevronLeft className="h-5 w-5 text-slate-600 dark:text-slate-300" />
            </button>
            <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100">{formatDate(currentDate)}</h2>
            <button onClick={handleNextMonth} className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700">
              <ChevronRight className="h-5 w-5 text-slate-600 dark:text-slate-300" />
            </button>
          </div>

          {/* Day headers */}
          <div className="grid grid-cols-7 mb-1">
            {DAYS.map(d => (
              <div key={d} className="text-center text-xs font-medium text-slate-500 py-2">{d}</div>
            ))}
          </div>

          {/* Calendar cells */}
          <div className="grid grid-cols-7 border-t border-l border-slate-200 dark:border-slate-700">
            {days.map((day, idx) => {
              const key = `${day.getFullYear()}-${String(day.getMonth() + 1).padStart(2, '0')}-${String(day.getDate()).padStart(2, '0')}`;
              const dayMeetings = meetingsByDate.get(key) || [];
              const isCurrentMonth = day.getMonth() === month;
              const isToday = isSameDay(day, today);
              const isSelected = selectedDate && isSameDay(day, selectedDate);

              return (
                <button key={idx} onClick={() => setSelectedDate(day)}
                  className={`relative border-b border-r border-slate-200 dark:border-slate-700 p-2 min-h-[80px] text-left transition-colors
                    ${isCurrentMonth ? '' : 'opacity-40'}
                    ${isSelected ? 'bg-blue-50 dark:bg-blue-900/20' : 'hover:bg-slate-50 dark:hover:bg-slate-800'}
                    ${isToday ? 'ring-2 ring-inset ring-blue-500' : ''}`}>
                  <span className={`text-xs font-medium ${isToday ? 'text-blue-600 font-bold' : 'text-slate-600 dark:text-slate-400'}`}>
                    {day.getDate()}
                  </span>
                  <div className="mt-1 space-y-0.5">
                    {dayMeetings.slice(0, 3).map((m, i) => (
                      <div key={i} className="flex items-center gap-1">
                        <span className={`w-1.5 h-1.5 rounded-full ${TYPE_COLORS[m.type] || 'bg-gray-400'}`} />
                        <span className="text-[10px] text-slate-600 dark:text-slate-400 truncate">{m.contact_name}</span>
                      </div>
                    ))}
                    {dayMeetings.length > 3 && <span className="text-[10px] text-slate-400">+{dayMeetings.length - 3} more</span>}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Sidebar: selected date or upcoming */}
        <div className="w-80 space-y-4">
          {selectedDate && selectedMeetings.length > 0 ? (
            <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
              <h3 className="font-semibold text-sm text-slate-800 dark:text-slate-100 mb-3">
                {selectedDate.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}
              </h3>
              <div className="space-y-3">
                {selectedMeetings.map((m, i) => {
                  const Icon = MEETING_ICONS[m.type] || Phone;
                  return (
                    <div key={i} className="bg-slate-50 dark:bg-slate-900/50 rounded-lg p-3 border border-slate-100 dark:border-slate-700">
                      <div className="flex items-center gap-2 mb-1">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center text-white ${TYPE_COLORS[m.type] || 'bg-gray-400'}`}>
                          <Icon className="h-3 w-3" />
                        </div>
                        <span className="font-medium text-sm text-slate-800 dark:text-slate-100">{m.contact_name}</span>
                      </div>
                      <div className="text-xs text-slate-500 space-y-0.5 ml-8">
                        {m.company && <p>{m.company}</p>}
                        {m.program && <p>{m.program}</p>}
                        {m.time && <p className="flex items-center gap-1"><Clock className="h-3 w-3" /> {m.time}</p>}
                      </div>
                      <div className="flex gap-2 mt-2 ml-8">
                        <button onClick={() => handleGeneratePrep(m)}
                          className="flex items-center gap-1 px-2 py-1 bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300 rounded text-[10px] font-medium hover:bg-indigo-100">
                          <FileText className="h-3 w-3" /> Prep Brief
                        </button>
                        {onNavigateToContact && (
                          <button onClick={() => onNavigateToContact(m.contact_name)}
                            className="flex items-center gap-1 px-2 py-1 bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 rounded text-[10px] font-medium hover:bg-blue-100">
                            <MapPin className="h-3 w-3" /> Profile
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
              <h3 className="font-semibold text-sm text-slate-800 dark:text-slate-100 mb-3">Upcoming (Next 7 Days)</h3>
              {upcomingMeetings.length > 0 ? (
                <div className="space-y-2">
                  {upcomingMeetings.map((m, i) => {
                    const Icon = MEETING_ICONS[m.type] || Phone;
                    const d = new Date(m.date);
                    return (
                      <div key={i} onClick={() => setSelectedDate(d)}
                        className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/50 cursor-pointer">
                        <div className={`w-6 h-6 shrink-0 rounded-full flex items-center justify-center text-white ${TYPE_COLORS[m.type] || 'bg-gray-400'}`}>
                          <Icon className="h-3 w-3" />
                        </div>
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-slate-800 dark:text-slate-100 truncate">{m.contact_name}</p>
                          <p className="text-[10px] text-slate-500">{d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-sm text-slate-400 text-center py-4">No upcoming meetings</p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Prep Brief Modal */}
      {showPrepModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-indigo-500" /> Meeting Prep: {showPrepModal.contact_name}
              </h2>
              <button onClick={() => { setShowPrepModal(null); setPrepBrief(null); }} className="p-1 hover:bg-slate-100 dark:hover:bg-slate-700 rounded">
                <X className="h-5 w-5 text-slate-400" />
              </button>
            </div>
            {prepLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-indigo-500" />
                <span className="ml-2 text-sm text-slate-500">Generating brief...</span>
              </div>
            ) : prepBrief ? (
              <div className="space-y-4 text-sm">
                <Section title="Contact Summary" content={prepBrief.contact_summary} />
                <Section title="Program Context" content={prepBrief.program_context} />
                <div>
                  <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-1">Talking Points</h4>
                  <ul className="list-disc list-inside text-slate-600 dark:text-slate-400 space-y-1">
                    {prepBrief.talking_points.map((tp, i) => <li key={i}>{tp}</li>)}
                  </ul>
                </div>
                <Section title="Recent Activity" content={prepBrief.recent_activity} />
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}

function Section({ title, content }: { title: string; content: string }) {
  return (
    <div>
      <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-1">{title}</h4>
      <p className="text-slate-600 dark:text-slate-400">{content}</p>
    </div>
  );
}

// ─── Mock Data ───────────────────────────────────────────────────────────────

function generateMockMeetings(): Meeting[] {
  const now = new Date();
  const contacts = [
    { name: 'Sarah Mitchell', company: 'Leidos', program: 'AF DCGS - Langley', type: 'video' as const },
    { name: 'James Rodriguez', company: 'Northrop Grumman', program: 'Army DCGS-A', type: 'call' as const },
    { name: 'Maria Chen', company: 'GDIT', program: 'Navy DCGS-N', type: 'in-person' as const },
    { name: 'David Park', company: 'Raytheon', program: 'GBSD', type: 'video' as const },
    { name: 'Karen Williams', company: 'BAE Systems', program: 'AF DCGS - PACAF', type: 'call' as const },
  ];

  return contacts.flatMap((c, i) => {
    const dates: Meeting[] = [];
    // One meeting in next 7 days
    const d1 = new Date(now.getTime() + (i + 1) * 86400000);
    dates.push({
      id: `mock-${i}-1`,
      contact_name: c.name, company: c.company, program: c.program,
      date: d1.toISOString().split('T')[0],
      time: `${9 + i}:00 AM`,
      type: c.type,
      status: 'scheduled',
    });
    // One meeting later in month
    const d2 = new Date(now.getTime() + (i + 10) * 86400000);
    dates.push({
      id: `mock-${i}-2`,
      contact_name: c.name, company: c.company, program: c.program,
      date: d2.toISOString().split('T')[0],
      time: `${14 - i}:00 PM`,
      type: c.type,
      status: 'scheduled',
    });
    return dates;
  });
}
