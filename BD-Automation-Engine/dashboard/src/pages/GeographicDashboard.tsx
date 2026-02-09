import { useState, useEffect, useMemo, useCallback } from 'react';
import { MapPin, Filter, X, Loader2, Users, Building2, ChevronDown } from 'lucide-react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import type { Contact, Program } from '../types';

// ─── Hardcoded Defense Location Coordinates ────────────────────────────────

const LOCATION_COORDS: Record<string, [number, number]> = {
  // Military Installations
  'Fort Meade, MD': [39.1086, -76.7711],
  'Fort Meade': [39.1086, -76.7711],
  'Fort Belvoir, VA': [38.7119, -77.1448],
  'Fort Belvoir': [38.7119, -77.1448],
  'Fort Huachuca, AZ': [31.5533, -110.3445],
  'Fort Bragg, NC': [35.1390, -79.0064],
  'Fort Liberty, NC': [35.1390, -79.0064],
  'Fort Gordon, GA': [33.4274, -82.1338],
  'Wright-Patterson AFB, OH': [39.8261, -84.0486],
  'Wright-Patterson, OH': [39.8261, -84.0486],
  'Langley AFB, VA': [37.0830, -76.3606],
  'Langley, VA': [38.9330, -77.1753],
  'Joint Base Andrews, MD': [38.8108, -76.8660],
  'Peterson AFB, CO': [38.8024, -104.7030],
  'Lackland AFB, TX': [29.3842, -98.6170],
  'Scott AFB, IL': [38.5453, -89.8506],
  'Offutt AFB, NE': [41.1186, -95.9126],
  'MacDill AFB, FL': [27.8494, -82.5218],
  'Camp Pendleton, CA': [33.2983, -117.3811],
  'Joint Base Pearl Harbor, HI': [21.3525, -157.9744],

  // Major Metro Areas (Defense Hubs)
  'San Diego, CA': [32.7157, -117.1611],
  'Norfolk, VA': [36.8508, -76.2859],
  'Tampa, FL': [27.9506, -82.4572],
  'Colorado Springs, CO': [38.8339, -104.8214],
  'Huntsville, AL': [34.7304, -86.5861],
  'San Antonio, TX': [29.4241, -98.4936],
  'Augusta, GA': [33.4735, -82.0105],
  'Fayetteville, NC': [35.0527, -78.8784],
  'Dayton, OH': [39.7589, -84.1916],

  // DC Metro / Northern Virginia
  'Washington, DC': [38.9072, -77.0369],
  'Arlington, VA': [38.8799, -77.1068],
  'Falls Church, VA': [38.8826, -77.1712],
  'Herndon, VA': [38.9696, -77.3861],
  'Reston, VA': [38.9587, -77.3570],
  'Springfield, VA': [38.7893, -77.1872],
  'Chantilly, VA': [38.8943, -77.4311],
  'McLean, VA': [38.9339, -77.1773],
  'Tysons, VA': [38.9187, -77.2311],
  'Fairfax, VA': [38.8462, -77.3064],
  'Bethesda, MD': [38.9847, -77.0947],
  'Columbia, MD': [39.2037, -76.8610],
  'Annapolis Junction, MD': [39.1240, -76.7770],
  'Aberdeen, MD': [39.5096, -76.1641],
  'Aberdeen Proving Ground, MD': [39.4663, -76.1306],
  'Linthicum, MD': [39.2051, -76.6633],
  'Hanover, MD': [39.1929, -76.7241],

  // Other Defense Cities
  'Huntsville, Alabama': [34.7304, -86.5861],
  'El Segundo, CA': [33.9192, -118.4165],
  'Melbourne, FL': [28.0836, -80.6081],
  'St. Louis, MO': [38.6270, -90.1994],
  'Omaha, NE': [41.2565, -95.9345],
  'Sierra Vista, AZ': [31.5455, -110.3030],
};

// ─── Geocoding Helper ──────────────────────────────────────────────────────

function geocodeLocation(location: string | undefined): [number, number] | null {
  if (!location) return null;

  // Exact match
  if (LOCATION_COORDS[location]) return LOCATION_COORDS[location];

  // Partial match
  const loc = location.toLowerCase();
  for (const [key, coords] of Object.entries(LOCATION_COORDS)) {
    if (loc.includes(key.toLowerCase()) || key.toLowerCase().includes(loc)) {
      return coords;
    }
  }

  // Try matching just city name
  const city = location.split(',')[0].trim();
  for (const [key, coords] of Object.entries(LOCATION_COORDS)) {
    if (key.toLowerCase().startsWith(city.toLowerCase())) {
      return coords;
    }
  }

  return null;
}

// ─── Priority Colors ───────────────────────────────────────────────────────

const PRIORITY_STYLES: Record<string, { color: string; label: string }> = {
  critical: { color: '#dc2626', label: 'Critical' },
  high: { color: '#ea580c', label: 'High' },
  medium: { color: '#ca8a04', label: 'Medium' },
  standard: { color: '#6b7280', label: 'Standard' },
};

function getPriorityStyle(priority: string | undefined): { color: string; label: string } {
  if (!priority) return PRIORITY_STYLES.standard;
  const p = priority.toLowerCase();
  return PRIORITY_STYLES[p] || PRIORITY_STYLES.standard;
}

// ─── Map Auto-Fit Component ────────────────────────────────────────────────

function MapBoundsUpdater({ markers }: { markers: Array<{ coords: [number, number] }> }) {
  const map = useMap();

  useEffect(() => {
    if (markers.length > 0) {
      const bounds = markers.map((m) => m.coords);
      map.fitBounds(bounds as [number, number][], { padding: [40, 40] });
    }
  }, [markers, map]);

  return null;
}

// ─── Types ─────────────────────────────────────────────────────────────────

interface GeoContact {
  contact: Contact;
  coords: [number, number];
  location: string;
}

interface GeographicDashboardProps {
  contacts: Record<string, Contact[]>;
  programs: Program[];
  loading: boolean;
}

// ─── Main Component ────────────────────────────────────────────────────────

export function GeographicDashboard({ contacts, programs, loading }: GeographicDashboardProps) {
  const [filterProgram, setFilterProgram] = useState('');
  const [filterTier, setFilterTier] = useState<number | null>(null);
  const [filterCompany, setFilterCompany] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  // Flatten contacts and geocode
  const geoContacts = useMemo(() => {
    const result: GeoContact[] = [];
    for (const group of Object.values(contacts)) {
      for (const c of group) {
        const loc = c.location || c.program;
        const coords = geocodeLocation(loc);
        if (coords) {
          result.push({ contact: c, coords, location: loc || '' });
        }
      }
    }
    return result;
  }, [contacts]);

  // Apply filters
  const filteredContacts = useMemo(() => {
    return geoContacts.filter((gc) => {
      if (filterProgram && !gc.contact.program?.toLowerCase().includes(filterProgram.toLowerCase())) return false;
      if (filterTier !== null && gc.contact.tier !== filterTier) return false;
      if (filterCompany && !gc.contact.company?.toLowerCase().includes(filterCompany.toLowerCase())) return false;
      return true;
    });
  }, [geoContacts, filterProgram, filterTier, filterCompany]);

  // Unique companies & programs for filter dropdowns
  const uniqueCompanies = useMemo(() => {
    const set = new Set<string>();
    geoContacts.forEach((gc) => { if (gc.contact.company) set.add(gc.contact.company); });
    return Array.from(set).sort();
  }, [geoContacts]);

  const uniquePrograms = useMemo(() => {
    const set = new Set<string>();
    geoContacts.forEach((gc) => { if (gc.contact.program) set.add(gc.contact.program); });
    return Array.from(set).sort();
  }, [geoContacts]);

  // Regional stats
  const regionStats = useMemo(() => {
    const regions: Record<string, number> = {
      'DC Metro': 0,
      'Southeast': 0,
      'Midwest': 0,
      'West Coast': 0,
      'Southwest': 0,
      'Other': 0,
    };
    filteredContacts.forEach((gc) => {
      const [lat, lng] = gc.coords;
      if (lat > 38 && lat < 40 && lng > -78 && lng < -76) regions['DC Metro']++;
      else if (lat < 35 && lng > -90) regions['Southeast']++;
      else if (lat > 38 && lng > -95 && lng < -80) regions['Midwest']++;
      else if (lng < -115) regions['West Coast']++;
      else if (lat < 35 && lng < -95) regions['Southwest']++;
      else regions['Other']++;
    });
    return regions;
  }, [filteredContacts]);

  const clearFilters = useCallback(() => {
    setFilterProgram('');
    setFilterTier(null);
    setFilterCompany('');
  }, []);

  const hasFilters = filterProgram || filterTier !== null || filterCompany;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        <span className="ml-3 text-slate-500">Loading geographic data...</span>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-100 dark:bg-green-900/30">
              <MapPin className="w-5 h-5 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 dark:text-white">Geographic Dashboard</h1>
              <p className="text-sm text-slate-500">
                {filteredContacts.length} geocoded contacts across {Object.keys(regionStats).filter(k => regionStats[k] > 0).length} regions
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                showFilters || hasFilters
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                  : 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300'
              }`}
            >
              <Filter className="w-4 h-4" />
              Filters
              {hasFilters && (
                <span className="ml-1 px-1.5 py-0.5 text-xs bg-blue-500 text-white rounded-full">!</span>
              )}
            </button>
            {hasFilters && (
              <button onClick={clearFilters} className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700">
                <X className="w-4 h-4 text-slate-400" />
              </button>
            )}
          </div>
        </div>

        {/* Filter Bar */}
        {showFilters && (
          <div className="mt-3 flex items-center gap-3 flex-wrap">
            <div className="relative">
              <select
                value={filterProgram}
                onChange={(e) => setFilterProgram(e.target.value)}
                className="appearance-none pl-3 pr-8 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-200"
              >
                <option value="">All Programs</option>
                {uniquePrograms.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-2 w-3.5 h-3.5 text-slate-400 pointer-events-none" />
            </div>

            <div className="relative">
              <select
                value={filterTier ?? ''}
                onChange={(e) => setFilterTier(e.target.value ? Number(e.target.value) : null)}
                className="appearance-none pl-3 pr-8 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-200"
              >
                <option value="">All Tiers</option>
                {[1, 2, 3, 4, 5, 6].map((t) => (
                  <option key={t} value={t}>Tier {t}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-2 w-3.5 h-3.5 text-slate-400 pointer-events-none" />
            </div>

            <div className="relative">
              <select
                value={filterCompany}
                onChange={(e) => setFilterCompany(e.target.value)}
                className="appearance-none pl-3 pr-8 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-200"
              >
                <option value="">All Companies</option>
                {uniqueCompanies.slice(0, 50).map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-2 w-3.5 h-3.5 text-slate-400 pointer-events-none" />
            </div>
          </div>
        )}
      </div>

      {/* Stats Bar */}
      <div className="px-6 py-2 bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-700 flex-shrink-0">
        <div className="flex items-center gap-4 text-xs">
          {Object.entries(regionStats)
            .filter(([, count]) => count > 0)
            .sort(([, a], [, b]) => b - a)
            .map(([region, count]) => (
              <div key={region} className="flex items-center gap-1.5">
                <span className="font-medium text-slate-700 dark:text-slate-300">{region}:</span>
                <span className="px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded font-semibold">
                  {count}
                </span>
              </div>
            ))}
        </div>
      </div>

      {/* Map */}
      <div className="flex-1 relative">
        <MapContainer
          center={[38.5, -96.0]}
          zoom={4}
          style={{ height: '100%', width: '100%' }}
          className="z-0"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {filteredContacts.length > 0 && <MapBoundsUpdater markers={filteredContacts} />}

          {filteredContacts.map((gc, idx) => {
            const style = getPriorityStyle(gc.contact.bd_priority);
            return (
              <CircleMarker
                key={`${gc.contact.id}-${idx}`}
                center={gc.coords}
                radius={gc.contact.tier <= 2 ? 8 : gc.contact.tier <= 4 ? 6 : 4}
                fillColor={style.color}
                color="#fff"
                weight={1.5}
                fillOpacity={0.8}
              >
                <Popup>
                  <div className="min-w-[200px]">
                    <div className="flex items-center gap-2 mb-1">
                      <Users className="w-3.5 h-3.5 text-blue-500" />
                      <span className="font-semibold text-sm">{gc.contact.name}</span>
                    </div>
                    {gc.contact.title && (
                      <p className="text-xs text-slate-600">{gc.contact.title}</p>
                    )}
                    {gc.contact.company && (
                      <div className="flex items-center gap-1.5 mt-1">
                        <Building2 className="w-3 h-3 text-slate-400" />
                        <span className="text-xs">{gc.contact.company}</span>
                      </div>
                    )}
                    {gc.contact.program && (
                      <p className="text-xs mt-1">
                        <span className="text-slate-500">Program:</span>{' '}
                        <span className="font-medium">{gc.contact.program}</span>
                      </p>
                    )}
                    <div className="flex items-center gap-2 mt-1.5">
                      <span className="text-xs px-1.5 py-0.5 rounded" style={{ backgroundColor: `${style.color}20`, color: style.color }}>
                        {style.label}
                      </span>
                      <span className="text-xs px-1.5 py-0.5 bg-slate-100 rounded text-slate-600">
                        Tier {gc.contact.tier}
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-400 mt-1">{gc.location}</p>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>

        {/* Legend */}
        <div className="absolute bottom-4 right-4 z-[1000] bg-white dark:bg-slate-800 rounded-lg shadow-lg p-3 border border-slate-200 dark:border-slate-700">
          <p className="text-xs font-semibold text-slate-600 dark:text-slate-300 mb-2">Priority</p>
          <div className="space-y-1">
            {Object.entries(PRIORITY_STYLES).map(([, { color, label }]) => (
              <div key={label} className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                <span className="text-xs text-slate-600 dark:text-slate-400">{label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Empty State */}
        {filteredContacts.length === 0 && !loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/80 dark:bg-slate-900/80 z-[500]">
            <div className="text-center">
              <MapPin className="w-12 h-12 text-slate-300 mx-auto mb-3" />
              <p className="text-slate-500 font-medium">No contacts match the current filters</p>
              <p className="text-sm text-slate-400 mt-1">Try adjusting your filter criteria</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
