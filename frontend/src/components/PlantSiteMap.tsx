import React, { useEffect, useRef, useState } from 'react';

/** Single plant site from demographic agent */
export interface PlantSite {
  name: string;
  city?: string;
  country: string;
  lat: number;
  lng: number;
  region_code?: string;
  energy_ease_score?: number;
  land_availability_score?: number;
  market_proximity_score?: number;
  export_supply_score?: number;
  overall_site_score?: number;
  rationale?: Record<string, string>;
}

// Minimal Google Maps types for script-loaded API (no @types/google.maps required)
interface GoogleMapsLatLngBounds {
  extend(latLng: { lat: number; lng: number }): void;
}
interface GoogleMapsMarker {
  setMap(map: GoogleMap | null): void;
  addListener(event: string, handler: () => void): void;
}
interface GoogleMap {
  setCenter(center: { lat: number; lng: number }): void;
  setZoom(zoom: number): void;
  fitBounds(bounds: GoogleMapsLatLngBounds, padding?: { top: number; right: number; bottom: number; left: number }): void;
}
interface GoogleMapsSymbolPath {
  CIRCLE: number;
}
interface GoogleMapsAPI {
  maps: {
    Map: new (el: HTMLElement, opts: Record<string, unknown>) => GoogleMap;
    Marker: new (opts: {
      position: { lat: number; lng: number };
      map: GoogleMap;
      title?: string;
      label?: { text: string; color: string; fontSize: string };
      icon?: { path: number; scale: number; fillColor: string; fillOpacity: number; strokeColor: string; strokeWeight: number };
    }) => GoogleMapsMarker;
    LatLngBounds: new () => GoogleMapsLatLngBounds;
    SymbolPath: GoogleMapsSymbolPath;
  };
}
declare global {
  interface Window {
    google?: GoogleMapsAPI;
  }
}

// India-only map: center and bounds. Include Himachal Pradesh (leading pharma hub, e.g. Baddi).
const INDIA_CENTER = { lat: 20.5937, lng: 78.9629 };
const HIMACHAL_CENTER = { lat: 31.5, lng: 77.0 }; // Himachal Pradesh region
const INDIA_ZOOM = 5;
const INDIA_BOUNDS = { north: 35.5, south: 8.0, west: 68.0, east: 97.5 };

interface PlantSiteMapProps {
  sites: PlantSite[];
  /** Optional Google Maps API key (defaults to VITE_GOOGLE_MAPS_API_KEY) */
  apiKey?: string | null;
  /** Optional drug/molecule name for title */
  drugName?: string | null;
}

export const PlantSiteMap: React.FC<PlantSiteMapProps> = ({
  sites,
  apiKey: apiKeyProp,
  drugName,
}) => {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<GoogleMap | null>(null);
  const markersRef = useRef<GoogleMapsMarker[]>([]);
  const [mapReady, setMapReady] = useState(false);
  const [selectedSite, setSelectedSite] = useState<PlantSite | null>(null);
  const [scriptError, setScriptError] = useState<string | null>(null);

  const apiKey = apiKeyProp ?? (import.meta as ImportMeta).env?.VITE_GOOGLE_MAPS_API_KEY ?? '';
  const hasKey = Boolean(apiKey?.trim());

  const indiaSitesForMap = sites.filter((s) => (s.country || '').toLowerCase() === 'india');
  const hasSites = indiaSitesForMap.length > 0;

  useEffect(() => {
    if (window.google?.maps) {
      initMap(indiaSitesForMap);
      return;
    }

    const scriptId = 'google-maps-pharmai';
    if (document.getElementById(scriptId)) {
      if (window.google?.maps) initMap(indiaSitesForMap);
      return;
    }

    // Google Maps JS: with key = production map; without key = dev-only map (shows "For development purposes only" watermark)
    const script = document.createElement('script');
    script.id = scriptId;
    script.src = hasKey
      ? `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places`
      : 'https://maps.googleapis.com/maps/api/js';
    script.async = true;
    script.defer = true;
    script.onload = () => {
      if (window.google?.maps) initMap(indiaSitesForMap);
      else setScriptError('Maps API failed to load.');
    };
    script.onerror = () => setScriptError('Failed to load Google Maps script.');
    document.head.appendChild(script);

    return () => {
      markersRef.current.forEach((m) => m.setMap(null));
      markersRef.current = [];
      mapInstanceRef.current = null;
    };
  }, [hasKey, apiKey, indiaSitesForMap.length]);

  const initMap = (sitesToShow: PlantSite[]) => {
    if (!mapRef.current || !window.google?.maps) return;
    const map = new window.google!.maps.Map(mapRef.current, {
      center: sitesToShow.length ? INDIA_CENTER : HIMACHAL_CENTER,
      zoom: sitesToShow.length ? INDIA_ZOOM : 7,
      restriction: { latLngBounds: INDIA_BOUNDS, strictBounds: false },
      mapTypeControl: true,
      streetViewControl: false,
      fullscreenControl: true,
      zoomControl: true,
      styles: [
        { featureType: 'poi', stylers: [{ visibility: 'off' }] },
        { featureType: 'transit', stylers: [{ visibility: 'off' }] },
      ],
    });
    mapInstanceRef.current = map;

    const bounds = new window.google.maps.LatLngBounds();
    const markers: GoogleMapsMarker[] = [];

    if (sitesToShow.length > 0) {
      sitesToShow.forEach((site, i) => {
        const pos = { lat: site.lat, lng: site.lng };
        bounds.extend(pos);
        const marker = new window.google!.maps.Marker({
          position: pos,
          map,
          title: site.name,
          label: { text: String(i + 1), color: 'white', fontSize: '12px' },
          icon: {
            path: window.google!.maps.SymbolPath.CIRCLE as number,
            scale: 22,
            fillColor: '#0ea5e9',
            fillOpacity: 1,
            strokeColor: '#0369a1',
            strokeWeight: 2,
          },
        });
        marker.addListener('click', () => setSelectedSite(site));
        markers.push(marker);
      });
      if (sitesToShow.length === 1) {
        map.setCenter({ lat: sitesToShow[0].lat, lng: sitesToShow[0].lng });
        map.setZoom(7);
      } else if (sitesToShow.length > 1) {
        bounds.extend(HIMACHAL_CENTER);
        map.fitBounds(bounds, { top: 48, right: 48, bottom: 48, left: 48 });
      }
    } else {
      bounds.extend(HIMACHAL_CENTER);
      map.setCenter(HIMACHAL_CENTER);
      map.setZoom(7);
    }

    markersRef.current = markers;
    setMapReady(true);
  };

  const titleSuffix = drugName?.trim() ? ` · ${drugName}` : '';
  const indiaSites = sites.filter((s) => (s.country || '').toLowerCase() === 'india');

  return (
    <div className="w-full space-y-4">
      <div className="flex items-center gap-3">
        <span className="w-8 h-8 rounded-lg bg-cyan-100 flex items-center justify-center text-cyan-600 shrink-0">
          <i className="fas fa-map-marker-alt text-sm"></i>
        </span>
        <h2 className="text-base sm:text-lg font-bold text-slate-800 truncate">Recommended plant locations{titleSuffix}</h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 md:gap-6">
        <div className="lg:col-span-2 rounded-xl sm:rounded-2xl overflow-hidden border border-slate-200 bg-slate-50 min-h-[280px] sm:min-h-[360px] relative">
          {scriptError ? (
            <div className="h-full min-h-[280px] sm:min-h-[360px] flex flex-col items-center justify-center p-6 sm:p-8 text-center">
              <i className="fas fa-exclamation-triangle text-3xl sm:text-4xl text-amber-500 mb-4"></i>
              <p className="font-medium text-slate-600 mb-1 text-sm sm:text-base">Map could not be loaded</p>
              <p className="text-xs sm:text-sm text-slate-500">{scriptError}</p>
            </div>
          ) : (
            <>
              <div ref={mapRef} className="w-full h-[280px] sm:h-[360px]" />
              {!hasSites && mapReady && (
                <div className="absolute bottom-3 left-3 right-3 rounded-lg bg-white/95 border border-slate-200 px-3 py-2 text-xs sm:text-sm text-slate-600 shadow-sm">
                  <strong>Leading pharma hub:</strong> Himachal Pradesh (Baddi belt) — map centered on region.
                </div>
              )}
            </>
          )}
        </div>

        {/* Site list + selected detail (India only); when no sites, show Himachal note */}
        <div className="space-y-3 max-h-[320px] sm:max-h-[420px] overflow-y-auto overflow-x-auto-touch">
          {!hasSites ? (
            <div className="rounded-xl border-2 border-dashed border-slate-200 bg-slate-50 p-4 text-slate-600 text-sm">
              <p className="font-semibold text-slate-700 mb-1">No site recommendations for this query.</p>
              <p>Map is centered on <strong>Himachal Pradesh</strong>, a leading pharmaceutical manufacturing hub in India.</p>
            </div>
          ) : null}
          {indiaSites.map((site, i) => (
            <button
              key={`${site.name}-${site.lat}-${site.lng}`}
              type="button"
              onClick={() => setSelectedSite(site)}
              className={`w-full text-left rounded-xl border-2 p-4 transition-all ${
                selectedSite === site
                  ? 'border-cyan-500 bg-cyan-50 shadow-md'
                  : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <span className="flex-shrink-0 w-7 h-7 rounded-full bg-cyan-500 text-white flex items-center justify-center text-sm font-bold">
                  {i + 1}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="font-semibold text-slate-800 truncate">{site.name}</p>
                  <p className="text-xs text-slate-500">{site.city ?? ''}, {site.country}</p>
                  <p className="text-xs text-cyan-600 mt-1">
                    Score: {((site.overall_site_score ?? 0) * 100).toFixed(0)}/100
                  </p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Selected site detail */}
      {selectedSite && (
        <div className="rounded-xl sm:rounded-2xl border border-slate-200 bg-white p-4 sm:p-6 shadow-sm">
          <h3 className="font-bold text-slate-800 mb-2">{selectedSite.name}</h3>
          <p className="text-sm text-slate-500 mb-4">{selectedSite.city}, {selectedSite.country}</p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
            <div className="bg-slate-50 rounded-lg p-3">
              <p className="text-xs font-semibold text-slate-500 uppercase">Energy ease</p>
              <p className="text-lg font-bold text-slate-800">{((selectedSite.energy_ease_score ?? 0) * 100).toFixed(0)}</p>
            </div>
            <div className="bg-slate-50 rounded-lg p-3">
              <p className="text-xs font-semibold text-slate-500 uppercase">Land</p>
              <p className="text-lg font-bold text-slate-800">{((selectedSite.land_availability_score ?? 0) * 100).toFixed(0)}</p>
            </div>
            <div className="bg-slate-50 rounded-lg p-3">
              <p className="text-xs font-semibold text-slate-500 uppercase">Market proximity</p>
              <p className="text-lg font-bold text-slate-800">{((selectedSite.market_proximity_score ?? 0) * 100).toFixed(0)}</p>
            </div>
            <div className="bg-slate-50 rounded-lg p-3">
              <p className="text-xs font-semibold text-slate-500 uppercase">Export / supply</p>
              <p className="text-lg font-bold text-slate-800">{((selectedSite.export_supply_score ?? 0) * 100).toFixed(0)}</p>
            </div>
          </div>
          {selectedSite.rationale && Object.keys(selectedSite.rationale).length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-semibold text-slate-500 uppercase">Rationale</p>
              <ul className="text-sm text-slate-600 space-y-1">
                {Object.entries(selectedSite.rationale).map(([k, v]) => (
                  <li key={k}><strong className="capitalize text-slate-700">{k}:</strong> {v}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
