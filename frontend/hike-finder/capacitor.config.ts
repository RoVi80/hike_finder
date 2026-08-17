import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.jrva.wanderig',
  appName: 'wanderig',
  webDir: 'build',
  server: {
    cleartext: true, // 👈 THIS is what tells Android to allow HTTP
    androidScheme: 'http' 
  }
};

export default config;
