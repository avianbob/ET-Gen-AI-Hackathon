/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  /** Google Maps JavaScript API key (for plant site map). Enable Maps JavaScript API in Google Cloud. */
  readonly VITE_GOOGLE_MAPS_API_KEY: string | undefined;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}